"""
Trajectory Agent — Product Recommendation Engine (PRS-001 v2.2 Compliance)
=========================================================================

Proactive recommendation engine. Called when the system needs to SUGGEST
a product to a customer from scratch, as opposed to VALIDATING an already-
assigned recommended_product (which is handled by
rag_querys.validate_product_recommendation).

Key changes in v2.2:
  - Priority order corrected to match PRS-001 Section 3:
      Student Loan > Car Loan > Investment Plan > Personal Loan > Trust Fund
    (Was reversed in previous version: Personal Loan priority=1 was wrong.)
  - Trust Fund context inflow threshold corrected to N1,000,000
    (Was N5,000,000 — that figure applies to min_balance for wealth check,
     not the inflow context threshold used by validate_product_recommendation)
  - DSR (Debt Service Ratio) validation retained as a CREDIT-QUALITY signal.
    DSR failure does NOT set recommendation = None; it downgrades confidence
    and surfaces a warning so the credit officer can make the final call.
    This aligns behavioral signals with the PRS-001 v2 model where such
    signals are context for explainability, not hard eligibility gates.
  - Result dict now includes: is_eligible, met_criteria, unmet_criteria,
    score_range — matching the shape expected by test_agents.py and
    consistent with validate_product_recommendation().
  - uber_tracker removed as a hard gate for Car Loan. It is included as
    a supporting context signal in met_criteria when present.

CBN-aligned interest rate benchmarks (February 2026):
  Personal Loan   : 30% APR (2.5% monthly)
  Car Loan        : 24% APR (2.0% monthly)
  Student Loan    : 18% APR (1.5% monthly)
  Investment Plan : 0% (savings/investment product — no repayment)
  Trust Fund      : 0% (managed wealth product — no repayment)

Author: AI Engineer 2
Date: February 2026
"""

from typing import Dict, Any, List, Optional
import math

# =============================================================================
# Product Policy Definitions (Aligned to PRS-001 v2.2)
# =============================================================================
# signal_threshold : Loan_signal_score floor from LOAN_SIGNAL_SCORE_RANGES
# score_ceiling    : Loan_signal_score ceiling from LOAN_SIGNAL_SCORE_RANGES
# interest_rate    : Annual rate (CBN-aligned, February 2026)
# max_tenure_months: Maximum repayment period
# min_inflow       : Minimum monthly_inflow for DSR context check
# priority         : PRS-001 Section 3 recommendation hierarchy
#                    (lower number = higher priority)
# dsr_cap          : CBN Debt Service Ratio cap (33.3% of monthly inflow)

PRODUCT_POLICIES: Dict[str, Dict] = {
    "Student Loan": {
        "signal_threshold":   0.80,
        "score_ceiling":      0.98,
        "interest_rate":      0.18,    # 18% APR (1.5% monthly)
        "max_tenure_months":  48,
        "min_inflow":         150_000, # Context inflow floor for DSR check
        "priority":           1,       # Highest priority (PRS-001 Section 3)
        "dsr_cap":            0.333,
    },
    "Car Loan": {
        "signal_threshold":   0.75,
        "score_ceiling":      0.95,
        "interest_rate":      0.24,    # 24% APR (2.0% monthly)
        "max_tenure_months":  60,
        "min_inflow":         500_000,
        "priority":           2,
        "dsr_cap":            0.333,
    },
    "Investment Plan": {
        "signal_threshold":   0.70,
        "score_ceiling":      0.90,
        "interest_rate":      0.0,     # Investment product — no interest charged
        "max_tenure_months":  0,       # Open-ended
        "min_inflow":         2_000_000,
        "priority":           3,
        "dsr_cap":            None,    # No DSR — no repayment obligation
    },
    "Personal Loan": {
        "signal_threshold":   0.70,
        "score_ceiling":      0.92,
        "interest_rate":      0.30,    # 30% APR (2.5% monthly)
        "max_tenure_months":  36,
        "min_inflow":         100_000,
        "priority":           4,
        "dsr_cap":            0.333,
    },
    "Trust Fund": {
        "signal_threshold":   0.65,
        "score_ceiling":      0.85,
        "interest_rate":      0.0,
        "max_tenure_months":  0,
        "min_inflow":         1_000_000, # Context indicator, not a hard gate
        "priority":           5,
        "dsr_cap":            None,
    },
}

# DSR cap (CBN standard): monthly EMI must not exceed 33.3% of monthly inflow
DSR_CAP = 0.333


# =============================================================================
# Financial Logic Helpers
# =============================================================================

def compute_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Compute monthly EMI using the standard amortization formula.

    EMI = P * r*(1+r)^n / ((1+r)^n - 1)
    Where r = monthly_rate, n = tenure_months

    Returns 0.0 for investment/trust products (no repayment).
    """
    if tenure_months == 0 or annual_rate == 0:
        if tenure_months == 0:
            return 0.0
        return round(principal / tenure_months, 2)

    monthly_rate = annual_rate / 12
    emi = (principal * monthly_rate * (1 + monthly_rate) ** tenure_months) / \
          ((1 + monthly_rate) ** tenure_months - 1)
    return round(emi, 2)


def compute_dsr(emi: float, monthly_inflow: float) -> Optional[float]:
    """
    Compute Debt Service Ratio: EMI / monthly_inflow.
    Returns None if inflow is zero or product has no repayment.
    """
    if monthly_inflow <= 0 or emi == 0:
        return None
    return round(emi / monthly_inflow, 4)


def is_dsr_compliant(emi: float, monthly_inflow: float, cap: float = DSR_CAP) -> bool:
    """Validate that EMI is within the DSR cap."""
    dsr = compute_dsr(emi, monthly_inflow)
    if dsr is None:
        return True  # No repayment obligation — compliant by default
    return dsr <= cap


# =============================================================================
# Main Recommendation Engine
# =============================================================================

def recommend_product(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Proactively recommend a product for a customer.

    Evaluates all 5 products in PRS-001 priority order and returns the
    highest-priority product for which the customer meets the
    Loan_signal_score threshold.

    DSR is computed and included as a context signal. A DSR breach does
    NOT block the recommendation — it surfaces a warning for the credit
    officer (aligned with PRS-001 v2 behavioral-signals-as-context model).

    Args:
        customer: Dict with keys:
            Loan_signal_score  : float  — master eligibility score (capital L)
            monthly_inflow     : float  — cumulative monthly inflow
            salary_detected    : bool   — salary proxy from fintech credits
            uber_tracker       : int    — ride-hailing trip count
            age                : int    — customer age
            account_type       : str    — savings | solo | current
            current_balance    : float  — current account balance
            desired_loan_amount: float  — optional, used for EMI calculation

    Returns:
        Dict:
          primary_product   : product name or None
          monthly_emi       : computed EMI (0 for wealth products)
          tenure_months     : repayment period
          confidence        : "High" | "Medium" | "Low"
          reasoning         : list of reason strings
          dsr_ratio         : computed DSR string or "N/A"
          dsr_warning       : bool — True if DSR exceeds cap
          is_eligible       : bool
          met_criteria      : list of met criteria (matches validate_product shape)
          unmet_criteria    : list of unmet criteria
          score_range       : (floor, ceiling) tuple for selected product
          all_qualifying    : list of all products meeting score threshold
    """
    loan_score      = float(customer.get("Loan_signal_score", 0.0))
    monthly_inflow  = float(customer.get("monthly_inflow",    0.0))
    salary_detected = bool( customer.get("salary_detected",   False))
    uber_trips      = int(  customer.get("uber_tracker",      0))
    age             = int(  customer.get("age",               0))
    account_type    = str(  customer.get("account_type",      ""))
    balance         = float(customer.get("current_balance",   0.0))

    # Sort products by priority (ascending — 1 is highest)
    ordered_products = sorted(
        PRODUCT_POLICIES.items(),
        key=lambda x: x[1]["priority"]
    )

    qualifying: List[Dict] = []
    all_qualifying_names: List[str] = []

    for product_name, policy in ordered_products:
        floor   = policy["signal_threshold"]
        ceiling = policy["score_ceiling"]

        # Primary gate: Loan_signal_score >= floor (PRS-001 Section 2)
        if loan_score < floor:
            continue

        all_qualifying_names.append(product_name)
        met: List[str]   = []
        unmet: List[str] = []
        warnings: List[str] = []

        # Score check (always met at this point — we already filtered)
        met.append(
            f"Loan_signal_score {loan_score:.2f} >= {floor:.2f} "
            f"{product_name} floor threshold (range {floor:.2f}-{ceiling:.2f})"
        )

        # ── Per-product behavioral context signals ────────────────────────
        if product_name == "Student Loan":
            if 18 <= age <= 30:
                met.append(f"Age {age} within Student Loan target band (18-30)")
            elif age > 0:
                met.append(
                    f"Age {age} — Student Loan primarily targets ages 18-30 "
                    f"(solo_candidate accounts)"
                )
            if salary_detected:
                met.append("Salary inflow detected (additional repayment strength)")
            else:
                met.append(
                    "No salary pattern detected — irregular inflow expected "
                    "for student segment"
                )

        elif product_name == "Car Loan":
            if salary_detected:
                met.append("Salary inflow detected (supports repayment capacity)")
            else:
                met.append(
                    "No confirmed salary pattern — recommend salary routing "
                    "via Remita or Paystack to strengthen application"
                )
            if uber_trips >= 6:
                met.append(
                    f"uber_tracker = {uber_trips} (>= 6) — high ride-hailing "
                    f"frequency signals vehicle demand"
                )
            elif uber_trips > 0:
                met.append(
                    f"uber_tracker = {uber_trips} — transport usage noted "
                    f"(< 6 trips in 90 days; not a strong vehicle-demand signal)"
                )
            if monthly_inflow >= 500_000:
                met.append(
                    f"Monthly inflow ₦{monthly_inflow:,.0f} >= ₦500,000 "
                    f"inflow context signal"
                )
            else:
                unmet.append(
                    f"Monthly inflow ₦{monthly_inflow:,.0f} below ₦500,000 "
                    f"Car Loan context benchmark (context only — not a hard gate)"
                )

        elif product_name == "Investment Plan":
            if monthly_inflow >= 2_000_000:
                met.append(
                    f"Monthly inflow ₦{monthly_inflow:,.0f} >= ₦2,000,000 "
                    f"— high-value investment capacity confirmed"
                )
            else:
                met.append(
                    f"Monthly inflow ₦{monthly_inflow:,.0f} on record "
                    f"(₦2,000,000 threshold is a context benchmark, not a gate)"
                )
            if account_type == "current":
                met.append("Current account detected — full Investment Plan access")
            else:
                met.append(
                    f"Account type: {account_type} — Tier 3 current account "
                    f"preferred for full Investment Plan access"
                )

        elif product_name == "Personal Loan":
            if salary_detected:
                met.append("Salary inflow detected (repayment capacity context)")
            else:
                met.append(
                    "No salary pattern detected — recommend routing salary "
                    "via Remita or Paystack to strengthen profile"
                )
            if monthly_inflow >= 300_000:
                met.append(
                    f"Monthly inflow ₦{monthly_inflow:,.0f} >= ₦300,000 "
                    f"inflow context signal"
                )
            else:
                unmet.append(
                    f"Monthly inflow ₦{monthly_inflow:,.0f} below ₦300,000 "
                    f"Personal Loan context benchmark (context only)"
                )

        elif product_name == "Trust Fund":
            if monthly_inflow >= 1_000_000:
                met.append(
                    f"Monthly inflow ₦{monthly_inflow:,.0f} >= ₦1,000,000 "
                    f"— high-net-worth profile indicator"
                )
            else:
                met.append(
                    f"Monthly inflow ₦{monthly_inflow:,.0f} on record "
                    f"(₦1,000,000 is the context benchmark for Trust Fund)"
                )
            if balance >= 5_000_000:
                met.append(
                    f"Balance ₦{balance:,.0f} >= ₦5,000,000 — strong "
                    f"wealth preservation candidate"
                )
            if account_type == "current":
                met.append("Current account detected — Tier 3 access confirmed")

        # ── DSR / EMI calculation for loan products ───────────────────────
        emi       = 0.0
        dsr       = None
        dsr_warn  = False
        tenure    = policy["max_tenure_months"]

        if policy["interest_rate"] > 0 and tenure > 0:
            default_principals = {
                "Student Loan": 500_000,
                "Car Loan":     5_000_000,
                "Personal Loan": monthly_inflow * 3 if monthly_inflow else 1_000_000,
            }
            principal = float(customer.get(
                "desired_loan_amount",
                default_principals.get(product_name, 1_000_000)
            ))
            emi = compute_emi(principal, policy["interest_rate"], tenure)
            dsr = compute_dsr(emi, monthly_inflow)

            if dsr is not None:
                dsr_pct = f"{dsr * 100:.1f}%"
                if dsr <= DSR_CAP:
                    met.append(
                        f"DSR {dsr_pct} <= 33.3% CBN cap "
                        f"(EMI ₦{emi:,.0f} / inflow ₦{monthly_inflow:,.0f}) — compliant"
                    )
                else:
                    dsr_warn = True
                    warnings.append(
                        f"DSR {dsr_pct} exceeds 33.3% CBN cap "
                        f"(EMI ₦{emi:,.0f} / inflow ₦{monthly_inflow:,.0f}) — "
                        f"refer to credit officer for manual review"
                    )

        qualifying.append({
            "product":     product_name,
            "emi":         emi,
            "tenure":      tenure,
            "priority":    policy["priority"],
            "floor":       floor,
            "ceiling":     ceiling,
            "met":         met,
            "unmet":       unmet,
            "warnings":    warnings,
            "dsr":         dsr,
            "dsr_warn":    dsr_warn,
        })

    # ── No qualifying product ─────────────────────────────────────────────
    if not qualifying:
        return {
            "primary_product": None,
            "monthly_emi":     0.0,
            "tenure_months":   0,
            "confidence":      "Low",
            "reasoning":       [
                f"Loan_signal_score {loan_score:.2f} is below all product "
                f"floor thresholds. Minimum required: 0.65 (Trust Fund)."
            ],
            "dsr_ratio":       "N/A",
            "dsr_warning":     False,
            "is_eligible":     False,
            "met_criteria":    [],
            "unmet_criteria":  [
                f"Loan_signal_score {loan_score:.2f} < 0.65 Trust Fund floor "
                f"(lowest threshold)"
            ],
            "score_range":     None,
            "all_qualifying":  [],
        }

    # ── Select top-priority qualifying product ────────────────────────────
    # Already sorted by priority; qualifying[0] is highest priority
    top = qualifying[0]

    # Confidence from score position within range
    floor, ceiling = top["floor"], top["ceiling"]
    score_position = (loan_score - floor) / (ceiling - floor) if (ceiling > floor) else 0
    if loan_score >= 0.85 or score_position >= 0.5:
        confidence = "High"
    elif score_position >= 0.2:
        confidence = "Medium"
    else:
        confidence = "Low"

    dsr_ratio_str = (
        f"{top['dsr'] * 100:.2f}%"
        if top["dsr"] is not None else "N/A"
    )

    reasoning = top["met"] + top["warnings"]

    return {
        "primary_product": top["product"],
        "monthly_emi":     top["emi"],
        "tenure_months":   top["tenure"],
        "confidence":      confidence,
        "reasoning":       reasoning,
        "dsr_ratio":       dsr_ratio_str,
        "dsr_warning":     top["dsr_warn"],
        "is_eligible":     True,
        "met_criteria":    top["met"],
        "unmet_criteria":  top["unmet"],
        "score_range":     (floor, ceiling),
        "all_qualifying":  all_qualifying_names,
    }


# =============================================================================
# Simulation / Demo
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  SENTINEL BANK — RECOMMENDATION ENGINE v2.2")
    print("  PRS-001 Aligned | CBN DSR Validation")
    print("=" * 65)

    demo_customers = [
        {
            "label":               "Salaried professional, Car Loan candidate",
            "Loan_signal_score":   0.82,
            "monthly_inflow":      600_000,
            "salary_detected":     True,
            "uber_tracker":        12,
            "age":                 30,
            "account_type":        "current",
            "current_balance":     450_000,
            "desired_loan_amount": 3_000_000,
        },
        {
            "label":               "Student, low inflow",
            "Loan_signal_score":   0.88,
            "monthly_inflow":      120_000,
            "salary_detected":     False,
            "uber_tracker":        2,
            "age":                 21,
            "account_type":        "solo",
            "current_balance":     45_000,
            "desired_loan_amount": 500_000,
        },
        {
            "label":               "High-inflow current account, Investment Plan",
            "Loan_signal_score":   0.78,
            "monthly_inflow":      3_500_000,
            "salary_detected":     True,
            "uber_tracker":        5,
            "age":                 42,
            "account_type":        "current",
            "current_balance":     8_000_000,
        },
        {
            "label":               "Below all thresholds",
            "Loan_signal_score":   0.55,
            "monthly_inflow":      80_000,
            "salary_detected":     False,
            "uber_tracker":        1,
            "age":                 25,
            "account_type":        "savings",
            "current_balance":     15_000,
        },
        {
            "label":               "Trust Fund candidate, high balance",
            "Loan_signal_score":   0.71,
            "monthly_inflow":      1_800_000,
            "salary_detected":     True,
            "uber_tracker":        3,
            "age":                 48,
            "account_type":        "current",
            "current_balance":     12_000_000,
        },
    ]

    for c in demo_customers:
        label = c.pop("label")
        result = recommend_product(c)

        print(f"\n  Customer  : {label}")
        print(f"  Score     : {c['Loan_signal_score']:.2f}  |  Inflow: ₦{c['monthly_inflow']:,.0f}")

        if result["primary_product"]:
            sr = result["score_range"]
            print(f"  Product   : {result['primary_product']}  "
                  f"(range {sr[0]:.2f}-{sr[1]:.2f})")
            print(f"  Confidence: {result['confidence']}")
            if result["monthly_emi"] > 0:
                print(f"  EMI       : ₦{result['monthly_emi']:,.2f} / month  "
                      f"({result['tenure_months']} months)")
                print(f"  DSR       : {result['dsr_ratio']}"
                      + (" ⚠ EXCEEDS CAP" if result["dsr_warning"] else " (compliant)"))
            if result["all_qualifying"]:
                print(f"  Qualifies : {', '.join(result['all_qualifying'])}")
            for m in result["met_criteria"]:
                print(f"    + {m}")
            for u in result["unmet_criteria"]:
                print(f"    ~ {u}  (context only)")
        else:
            print(f"  Product   : None")
            print(f"  Reason    : {result['reasoning'][0]}")

    print("\n" + "=" * 65 + "\n")