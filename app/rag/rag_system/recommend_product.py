"""
Trajectory Agent — Product Recommendation Engine (PRS-001 v2.2 Compliance)
=========================================================================

Proactive recommendation engine. Called when the system needs to SUGGEST
a product to a customer from scratch, as opposed to VALIDATING an already-
assigned recommended_product (which is handled by
rag_querys.validate_product_recommendation).

Architecture:
  RecommendationEngine is the primary class, consumed by RAGQueryEngine
  (rag_querys.py) via composition. test_agents.py imports the class and
  calls engine.recommend(customer) directly for the proactive leg of each
  Trajectory test case.

  The module also exposes a convenience function recommend_product() for
  backward compatibility with any existing callers.

Key changes in v2.2:
  - Priority order corrected to match PRS-001 Section 3:
      Student Loan > Car Loan > Investment Plan > Personal Loan > Trust Fund
  - Trust Fund context inflow threshold corrected to N1,000,000
  - DSR (Debt Service Ratio) retained as a CREDIT-QUALITY context signal.
    DSR failure does NOT block recommendation — it surfaces a warning for
    the credit officer (PRS-001 v2 behavioral-signals-as-context model).
  - Result dict includes: is_eligible, met_criteria, unmet_criteria,
    score_range — matching validate_product_recommendation() shape.
  - uber_tracker removed as a hard gate for Car Loan.
  - v2.3 (class refactor): logic moved into RecommendationEngine class.
    Module-level helpers and constants unchanged for compatibility.

CBN-aligned interest rate benchmarks (February 2026):
  Personal Loan   : 30% APR (2.5% monthly)
  Car Loan        : 24% APR (2.0% monthly)
  Student Loan    : 18% APR (1.5% monthly)
  Investment Plan : 0%  (investment product — no repayment)
  Trust Fund      : 0%  (managed wealth product — no repayment)

Author: AI Engineer 2
Date: February 2026
"""

from typing import Dict, Any, List, Optional
import math

# =============================================================================
# Product Policy Definitions (Aligned to PRS-001 v2.2)
# =============================================================================
# signal_threshold  : Loan_signal_score floor (from LOAN_SIGNAL_SCORE_RANGES)
# score_ceiling     : Loan_signal_score ceiling
# interest_rate     : Annual rate (CBN-aligned, February 2026)
# max_tenure_months : Maximum repayment period
# min_inflow        : Monthly inflow context benchmark (not a hard gate)
# priority          : PRS-001 Section 3 hierarchy (lower = higher priority)
# dsr_cap           : CBN Debt Service Ratio cap (33.3% of monthly inflow)

PRODUCT_POLICIES: Dict[str, Dict] = {
    "Student Loan": {
        "signal_threshold":   0.80,
        "score_ceiling":      0.98,
        "interest_rate":      0.18,       # 18% APR (1.5% monthly)
        "max_tenure_months":  48,
        "min_inflow":         150_000,    # Context floor for DSR check
        "priority":           1,          # Highest priority (PRS-001 Section 3)
        "dsr_cap":            0.333,
    },
    "Car Loan": {
        "signal_threshold":   0.75,
        "score_ceiling":      0.95,
        "interest_rate":      0.24,       # 24% APR (2.0% monthly)
        "max_tenure_months":  60,
        "min_inflow":         500_000,
        "priority":           2,
        "dsr_cap":            0.333,
    },
    "Investment Plan": {
        "signal_threshold":   0.70,
        "score_ceiling":      0.90,
        "interest_rate":      0.0,        # Investment product — no interest
        "max_tenure_months":  0,          # Open-ended
        "min_inflow":         2_000_000,
        "priority":           3,
        "dsr_cap":            None,       # No DSR — no repayment obligation
    },
    "Personal Loan": {
        "signal_threshold":   0.70,
        "score_ceiling":      0.92,
        "interest_rate":      0.30,       # 30% APR (2.5% monthly)
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
        "min_inflow":         1_000_000,  # Context indicator — not a hard gate
        "priority":           5,
        "dsr_cap":            None,
    },
}

# CBN standard: monthly EMI must not exceed 33.3% of monthly inflow
DSR_CAP: float = 0.333


# =============================================================================
# Module-Level Financial Helpers
# =============================================================================
# Kept at module level so they can be imported and unit-tested independently.

def compute_emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """
    Compute monthly EMI using the standard amortization formula.

        EMI = P * r*(1+r)^n / ((1+r)^n - 1)

    Where r = monthly_rate = annual_rate / 12, n = tenure_months.
    Returns 0.0 for investment/trust products (no repayment obligation).
    """
    if tenure_months == 0 or annual_rate == 0:
        return 0.0 if tenure_months == 0 else round(principal / tenure_months, 2)
    r   = annual_rate / 12
    emi = (principal * r * (1 + r) ** tenure_months) / ((1 + r) ** tenure_months - 1)
    return round(emi, 2)


def compute_dsr(emi: float, monthly_inflow: float) -> Optional[float]:
    """
    Compute Debt Service Ratio: EMI / monthly_inflow.
    Returns None if inflow is zero or the product has no repayment.
    """
    if monthly_inflow <= 0 or emi == 0:
        return None
    return round(emi / monthly_inflow, 4)


def is_dsr_compliant(emi: float, monthly_inflow: float, cap: float = DSR_CAP) -> bool:
    """Return True if EMI is within the DSR cap (or product has no repayment)."""
    dsr = compute_dsr(emi, monthly_inflow)
    return dsr is None or dsr <= cap


# =============================================================================
# RecommendationEngine Class
# =============================================================================

class RecommendationEngine:
    """
    Trajectory Agent — proactive product recommendation engine.

    Evaluates all five Sentinel Bank products in PRS-001 priority order
    and returns the highest-priority product for which the customer's
    Loan_signal_score meets the floor threshold.

    Behavioral signals (salary_detected, uber_tracker, monthly_inflow,
    account_type, current_balance) are used as CONTEXT for explainability
    and DSR calculation only. They do NOT gate the recommendation —
    consistent with the PRS-001 v2 behavioral-signals-as-context model.

    Usage (standalone):
        engine = RecommendationEngine()
        result = engine.recommend(customer_dict)

    Usage (via RAGQueryEngine — rag_querys.py):
        # RAGQueryEngine instantiates RecommendationEngine internally:
        self.recommender = RecommendationEngine()
        # Then calls it for the proactive leg:
        result = self.recommender.recommend(customer)

    Result dict shape (identical to validate_product_recommendation()):
        primary_product   : str | None
        monthly_emi       : float
        tenure_months     : int
        confidence        : "High" | "Medium" | "Low"
        reasoning         : List[str]
        dsr_ratio         : str          e.g. "18.4%" or "N/A"
        dsr_warning       : bool
        is_eligible       : bool
        met_criteria      : List[str]
        unmet_criteria    : List[str]
        score_range       : tuple(float, float) | None
        all_qualifying    : List[str]
    """

    # Class-level reference to module constants — no duplication
    POLICIES: Dict[str, Dict] = PRODUCT_POLICIES
    DSR_CAP:  float           = DSR_CAP

    def __init__(self) -> None:
        # Products sorted by priority once at construction time
        self._ordered: List[tuple] = sorted(
            self.POLICIES.items(),
            key=lambda x: x[1]["priority"]
        )

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def recommend(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Proactively recommend the best Sentinel Bank product for a customer.

        Args:
            customer: Dict produced by data_generator.py / transactions.csv:
                Loan_signal_score   float  Master eligibility score (capital L)
                monthly_inflow      float  Cumulative monthly credit total
                salary_detected     bool   >= 2 Paystack/Remita credits > N200K
                uber_tracker        int    Uber/Bolt/LagRide trips in 90 days
                age                 int    Customer age
                account_type        str    "savings" | "solo" | "current"
                current_balance     float  Current account balance
                desired_loan_amount float  Optional — used for EMI calculation

        Returns:
            Structured dict (see class docstring for full schema).
        """
        loan_score      = float(customer.get("Loan_signal_score", 0.0))
        monthly_inflow  = float(customer.get("monthly_inflow",    0.0))
        salary_detected = bool( customer.get("salary_detected",   False))
        uber_trips      = int(  customer.get("uber_tracker",      0))
        age             = int(  customer.get("age",               0))
        account_type    = str(  customer.get("account_type",      ""))
        balance         = float(customer.get("current_balance",   0.0))

        qualifying:          List[Dict] = []
        all_qualifying_names: List[str] = []

        for product_name, policy in self._ordered:
            floor   = policy["signal_threshold"]
            ceiling = policy["score_ceiling"]

            # Primary gate: Loan_signal_score must meet floor (PRS-001 §2)
            if loan_score < floor:
                continue

            all_qualifying_names.append(product_name)
            met:      List[str] = []
            unmet:    List[str] = []
            warnings: List[str] = []

            # Score always passes at this point (filtered above)
            met.append(
                f"Loan_signal_score {loan_score:.2f} >= {floor:.2f} "
                f"{product_name} floor (range {floor:.2f}-{ceiling:.2f})"
            )

            # Per-product behavioral context signals
            self._add_context_signals(
                product_name, policy,
                loan_score, monthly_inflow, salary_detected,
                uber_trips, age, account_type, balance,
                met, unmet,
            )

            # EMI and DSR for loan products
            emi, dsr, dsr_warn = self._compute_loan_metrics(
                product_name, policy, customer, monthly_inflow, met, warnings
            )

            qualifying.append({
                "product":  product_name,
                "emi":      emi,
                "tenure":   policy["max_tenure_months"],
                "priority": policy["priority"],
                "floor":    floor,
                "ceiling":  ceiling,
                "met":      met,
                "unmet":    unmet,
                "warnings": warnings,
                "dsr":      dsr,
                "dsr_warn": dsr_warn,
            })

        return self._build_result(loan_score, qualifying, all_qualifying_names)

    # -------------------------------------------------------------------------
    # Private helpers
    # -------------------------------------------------------------------------

    def _add_context_signals(
        self,
        product_name:    str,
        policy:          Dict,
        loan_score:      float,
        monthly_inflow:  float,
        salary_detected: bool,
        uber_trips:      int,
        age:             int,
        account_type:    str,
        balance:         float,
        met:             List[str],
        unmet:           List[str],
    ) -> None:
        """Append behavioral context strings to met / unmet lists."""

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
                    "No confirmed salary pattern — recommend routing salary "
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
                    f"Monthly inflow N{monthly_inflow:,.0f} >= N500,000 "
                    f"inflow context signal"
                )
            else:
                unmet.append(
                    f"Monthly inflow N{monthly_inflow:,.0f} below N500,000 "
                    f"Car Loan context benchmark (context only — not a hard gate)"
                )

        elif product_name == "Investment Plan":
            if monthly_inflow >= 2_000_000:
                met.append(
                    f"Monthly inflow N{monthly_inflow:,.0f} >= N2,000,000 "
                    f"— high-value investment capacity confirmed"
                )
            else:
                met.append(
                    f"Monthly inflow N{monthly_inflow:,.0f} on record "
                    f"(N2,000,000 threshold is a context benchmark, not a gate)"
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
                    f"Monthly inflow N{monthly_inflow:,.0f} >= N300,000 "
                    f"inflow context signal"
                )
            else:
                unmet.append(
                    f"Monthly inflow N{monthly_inflow:,.0f} below N300,000 "
                    f"Personal Loan context benchmark (context only)"
                )

        elif product_name == "Trust Fund":
            if monthly_inflow >= 1_000_000:
                met.append(
                    f"Monthly inflow N{monthly_inflow:,.0f} >= N1,000,000 "
                    f"— high-net-worth profile indicator"
                )
            else:
                met.append(
                    f"Monthly inflow N{monthly_inflow:,.0f} on record "
                    f"(N1,000,000 is the context benchmark for Trust Fund)"
                )
            if balance >= 5_000_000:
                met.append(
                    f"Balance N{balance:,.0f} >= N5,000,000 — strong "
                    f"wealth preservation candidate"
                )
            if account_type == "current":
                met.append("Current account detected — Tier 3 access confirmed")

    def _compute_loan_metrics(
        self,
        product_name:   str,
        policy:         Dict,
        customer:       Dict[str, Any],
        monthly_inflow: float,
        met:            List[str],
        warnings:       List[str],
    ) -> tuple:
        """
        Calculate EMI, DSR, and DSR warning flag for loan products.

        Returns:
            (emi: float, dsr: Optional[float], dsr_warn: bool)
        """
        emi      = 0.0
        dsr      = None
        dsr_warn = False
        tenure   = policy["max_tenure_months"]

        if policy["interest_rate"] > 0 and tenure > 0:
            # Default principal if desired_loan_amount not supplied
            default_principals = {
                "Student Loan":  500_000,
                "Car Loan":      5_000_000,
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
                if dsr <= self.DSR_CAP:
                    met.append(
                        f"DSR {dsr_pct} <= 33.3% CBN cap "
                        f"(EMI N{emi:,.0f} / inflow N{monthly_inflow:,.0f}) — compliant"
                    )
                else:
                    dsr_warn = True
                    warnings.append(
                        f"DSR {dsr_pct} exceeds 33.3% CBN cap "
                        f"(EMI N{emi:,.0f} / inflow N{monthly_inflow:,.0f}) — "
                        f"refer to credit officer for manual review"
                    )

        return emi, dsr, dsr_warn

    def _build_result(
        self,
        loan_score:           float,
        qualifying:           List[Dict],
        all_qualifying_names: List[str],
    ) -> Dict[str, Any]:
        """Assemble the final result dict from qualifying products."""

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

        # qualifying is already sorted by priority — first entry is top pick
        top    = qualifying[0]
        floor  = top["floor"]
        ceiling= top["ceiling"]

        # Confidence: based on score position within the product's range
        score_position = (
            (loan_score - floor) / (ceiling - floor)
            if ceiling > floor else 0
        )
        if loan_score >= 0.85 or score_position >= 0.5:
            confidence = "High"
        elif score_position >= 0.2:
            confidence = "Medium"
        else:
            confidence = "Low"

        dsr_ratio_str = (
            f"{top['dsr'] * 100:.2f}%" if top["dsr"] is not None else "N/A"
        )

        return {
            "primary_product": top["product"],
            "monthly_emi":     top["emi"],
            "tenure_months":   top["tenure"],
            "confidence":      confidence,
            "reasoning":       top["met"] + top["warnings"],
            "dsr_ratio":       dsr_ratio_str,
            "dsr_warning":     top["dsr_warn"],
            "is_eligible":     True,
            "met_criteria":    top["met"],
            "unmet_criteria":  top["unmet"],
            "score_range":     (floor, ceiling),
            "all_qualifying":  all_qualifying_names,
        }


# =============================================================================
# Convenience wrapper — backward compatibility
# =============================================================================

_default_engine = RecommendationEngine()


def recommend_product(customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Module-level convenience function — wraps RecommendationEngine.recommend().

    Preserved for backward compatibility with any callers that import
    the function directly. Internally delegates to a shared engine instance.

        from recommend_product import recommend_product
        result = recommend_product(customer)           # unchanged call site

    Prefer importing the class for new code:
        from recommend_product import RecommendationEngine
        engine = RecommendationEngine()
        result = engine.recommend(customer)
    """
    return _default_engine.recommend(customer)


# =============================================================================
# Simulation / Demo
# =============================================================================

if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  SENTINEL BANK — RECOMMENDATION ENGINE v2.3")
    print("  PRS-001 Aligned | CBN DSR Validation | Class-Based")
    print("=" * 65)

    engine = RecommendationEngine()

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
            "label":               "NYSC student, low inflow",
            "Loan_signal_score":   0.88,
            "monthly_inflow":      80_000,
            "salary_detected":     False,
            "uber_tracker":        1,
            "age":                 21,
            "account_type":        "solo",
            "current_balance":     45_000,
            "desired_loan_amount": 500_000,
        },
        {
            "label":               "Entrepreneur, high inflow, Investment Plan",
            "Loan_signal_score":   0.76,
            "monthly_inflow":      3_200_000,
            "salary_detected":     True,
            "uber_tracker":        4,
            "age":                 42,
            "account_type":        "current",
            "current_balance":     6_500_000,
        },
        {
            "label":               "HNI, Trust Fund candidate",
            "Loan_signal_score":   0.70,
            "monthly_inflow":      1_800_000,
            "salary_detected":     True,
            "uber_tracker":        3,
            "age":                 50,
            "account_type":        "current",
            "current_balance":     12_000_000,
        },
        {
            "label":               "Below all thresholds (score 0.50)",
            "Loan_signal_score":   0.50,
            "monthly_inflow":      80_000,
            "salary_detected":     False,
            "uber_tracker":        1,
            "age":                 25,
            "account_type":        "savings",
            "current_balance":     15_000,
        },
    ]

    for c in demo_customers:
        label  = c.pop("label")
        result = engine.recommend(c)

        print(f"\n  Customer  : {label}")
        print(f"  Score     : {c['Loan_signal_score']:.2f}  |  "
              f"Inflow: N{c['monthly_inflow']:,.0f}")

        if result["primary_product"]:
            sr = result["score_range"]
            print(f"  Product   : {result['primary_product']}  "
                  f"(range {sr[0]:.2f}-{sr[1]:.2f})")
            print(f"  Confidence: {result['confidence']}")
            if result["monthly_emi"] > 0:
                print(f"  EMI       : N{result['monthly_emi']:,.2f} / month  "
                      f"({result['tenure_months']} months)")
                print(f"  DSR       : {result['dsr_ratio']}"
                      + (" WARNING: EXCEEDS CAP" if result["dsr_warning"]
                         else " (compliant)"))
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