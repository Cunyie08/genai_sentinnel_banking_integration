"""
Sentinel Bank RAG System — Interactive Agent Demo & Test Suite
==============================================================

Tests and demonstrates all four AI agents:

  Dispatcher Agent  → Routes customer complaints to correct department
  Sentinel Agent    → Calculates fraud risk for transactions
  Trajectory Agent  → Validates product eligibility AND runs proactive
                       recommend_product() using each customer's full
                       transaction-derived behavioral profile
  Policy Agent      → Answers general banking policy questions

Usage (from project root):

    # As a module (recommended):
    python -m app.rag.rag_system.test_agents

    # Standalone (from the rag_system directory):
    python test_agents.py

    # Automated tests only (no menu):
    python -m app.rag.rag_system.test_agents --auto

Trajectory Agent architecture (v2.2):
  The Trajectory Agent operates in two modes:

  1. VALIDATION mode (rag_querys.validate_product_recommendation)
     Called when a recommended_product is already assigned in
     transactions.csv. Checks if the Loan_signal_score meets the
     product's floor threshold. Returns APPROVED / NOT_ELIGIBLE.

  2. PROACTIVE mode (recommend_product.recommend_product)
     Called when the bank wants to actively suggest a product based
     on the customer's full behavioral profile from transactions.csv:
       - Loan_signal_score (primary eligibility score)
       - monthly_inflow (salary/credits pattern)
       - salary_detected (fintech credit >= 2 x N200K)
       - uber_tracker (ride-hailing trips in 90 days)
       - age / account_type / current_balance
     Returns highest-priority qualifying product with EMI, DSR,
     and detailed reasoning grounded in PRS-001 v2.2.

  Tests cover BOTH modes for each customer profile so the full
  pipeline from raw behavioral data to recommendation to validation
  to explanation is exercised end to end.

Changes vs previous version:
  - TRAJECTORY_CASES now carry full customer profiles matching the
    fields produced by data_generator.py (uber_tracker, account_type,
    current_balance, desired_loan_amount)
  - run_trajectory_tests() now calls BOTH validate_product_recommendation
    (eligibility gate) AND RecommendationEngine.recommend() (tailored suggestion)
  - EMI, tenure, DSR ratio, and DSR warning displayed per test case
  - interactive_trajectory() now also runs RecommendationEngine.recommend() and
    collects uber_tracker, account_type, balance, desired amount
  - POLICY_CASES expanded with DSR and interest rate queries (PRS-001 v2.2)
  - Import block updated to import RecommendationEngine class (not standalone
    function) from recommend_product — AgentTester holds a shared instance at
    self.recommender and calls self.recommender.recommend(customer)
  - LOAN_SIGNAL_SCORE_RANGES imported for reference

Author: AI Engineer 2
Date: February 2026
"""

import asyncio
import sys
import time
from typing import Dict, Any, List, Optional

# =============================================================================
# Import path handling — works both as module and standalone
# =============================================================================

try:
    # Running as module: python -m app.rag.rag_system.test_agents
    from app.rag.rag_system.rag_querys import RAGQueryEngine
    from app.rag.rag_system.chromadb_config import initialize_chromadb
    from app.rag.knowledge_base.generate_policies import (
        EXPECTED_SLA, DEPT_NAMES, MERCHANT_RISK, FLAG_WEIGHTS,
        LOAN_SIGNAL_SCORE_RANGES,
    )
    from app.rag.rag_system.recommend_product import RecommendationEngine
except ImportError:
    try:
        # Running from rag_system/ directory
        from .rag_querys import RAGQueryEngine
        from .chromadb_config import initialize_chromadb
        from policy_generator import (
            EXPECTED_SLA, DEPT_NAMES, MERCHANT_RISK, FLAG_WEIGHTS,
            LOAN_SIGNAL_SCORE_RANGES,
        )
        from recommend_product import RecommendationEngine
    except ImportError as e:
        print(f"\n[ERROR] Could not import RAG system: {e}")
        print("Make sure you have run ingest_documents.py first.")
        print("Run from project root: python -m app.rag.rag_system.test_agents")
        sys.exit(1)


# =============================================================================
# Terminal Colors — Extended Palette
# =============================================================================

class C:
    """ANSI color codes for terminal output — extended palette."""
    RESET      = "\033[0m"
    BOLD       = "\033[1m"
    DIM        = "\033[2m"
    ITALIC     = "\033[3m"
    UNDERLINE  = "\033[4m"
    BLINK      = "\033[5m"
    REVERSE    = "\033[7m"

    # Standard foreground
    BLACK      = "\033[30m"
    RED        = "\033[91m"
    GREEN      = "\033[92m"
    YELLOW     = "\033[93m"
    BLUE       = "\033[94m"
    MAGENTA    = "\033[95m"
    CYAN       = "\033[96m"
    WHITE      = "\033[97m"

    # Bright/vivid foreground
    BRIGHT_RED    = "\033[91;1m"
    BRIGHT_GREEN  = "\033[92;1m"
    BRIGHT_YELLOW = "\033[93;1m"
    BRIGHT_BLUE   = "\033[94;1m"
    BRIGHT_MAGENTA= "\033[95;1m"
    BRIGHT_CYAN   = "\033[96;1m"
    BRIGHT_WHITE  = "\033[97;1m"

    # Dark/muted
    DARK_RED   = "\033[31m"
    DARK_GREEN = "\033[32m"
    DARK_YELLOW= "\033[33m"
    DARK_BLUE  = "\033[34m"
    DARK_CYAN  = "\033[36m"
    ORANGE     = "\033[38;5;208m"
    PURPLE     = "\033[38;5;135m"
    TEAL       = "\033[38;5;37m"
    PINK       = "\033[38;5;213m"
    GOLD       = "\033[38;5;220m"
    LIME       = "\033[38;5;118m"
    CORAL      = "\033[38;5;203m"
    SKY        = "\033[38;5;117m"
    INDIGO     = "\033[38;5;99m"

    # Background highlights
    BG_RED     = "\033[41m"
    BG_GREEN   = "\033[42m"
    BG_YELLOW  = "\033[43m"
    BG_BLUE    = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN    = "\033[46m"
    BG_WHITE   = "\033[47m"
    BG_DARK    = "\033[40m"
    BG_ORANGE  = "\033[48;5;208m"
    BG_PURPLE  = "\033[48;5;57m"

    # ── Shortcut static methods ──────────────────────────────────────────────
    @staticmethod
    def green(s):         return f"{C.GREEN}{s}{C.RESET}"
    @staticmethod
    def red(s):           return f"{C.RED}{s}{C.RESET}"
    @staticmethod
    def yellow(s):        return f"{C.YELLOW}{s}{C.RESET}"
    @staticmethod
    def cyan(s):          return f"{C.CYAN}{s}{C.RESET}"
    @staticmethod
    def blue(s):          return f"{C.BLUE}{s}{C.RESET}"
    @staticmethod
    def bold(s):          return f"{C.BOLD}{s}{C.RESET}"
    @staticmethod
    def magenta(s):       return f"{C.MAGENTA}{s}{C.RESET}"
    @staticmethod
    def dim(s):           return f"{C.DIM}{s}{C.RESET}"
    @staticmethod
    def orange(s):        return f"{C.ORANGE}{s}{C.RESET}"
    @staticmethod
    def gold(s):          return f"{C.GOLD}{s}{C.RESET}"
    @staticmethod
    def teal(s):          return f"{C.TEAL}{s}{C.RESET}"
    @staticmethod
    def pink(s):          return f"{C.PINK}{s}{C.RESET}"
    @staticmethod
    def lime(s):          return f"{C.LIME}{s}{C.RESET}"
    @staticmethod
    def coral(s):         return f"{C.CORAL}{s}{C.RESET}"
    @staticmethod
    def sky(s):           return f"{C.SKY}{s}{C.RESET}"
    @staticmethod
    def indigo(s):        return f"{C.INDIGO}{s}{C.RESET}"
    @staticmethod
    def purple(s):        return f"{C.PURPLE}{s}{C.RESET}"
    @staticmethod
    def highlight(s, bg=None):
        bg = bg or C.BG_DARK
        return f"{bg}{C.WHITE}{C.BOLD} {s} {C.RESET}"
    @staticmethod
    def tag(label, colour):
        """Render a coloured [LABEL] badge."""
        return f"{colour}{C.BOLD}[{label}]{C.RESET}"


# =============================================================================
# Rendering helpers
# =============================================================================

# ── Risk-level colour map ────────────────────────────────────────────────────
RISK_COLOURS = {
    "CRITICAL": C.BRIGHT_RED,
    "HIGH":     C.ORANGE,
    "MEDIUM":   C.BRIGHT_YELLOW,
    "LOW":      C.BRIGHT_GREEN,
}

# ── Priority colour map ──────────────────────────────────────────────────────
PRIORITY_COLOURS = {
    "Critical": C.BRIGHT_RED,
    "High":     C.ORANGE,
    "Medium":   C.BRIGHT_CYAN,
    "Low":      C.BRIGHT_GREEN,
}

# ── Department colour map ────────────────────────────────────────────────────
DEPT_COLOURS = {
    "FRM": C.BRIGHT_RED,
    "TSU": C.ORANGE,
    "COC": C.YELLOW,
    "DCS": C.SKY,
    "AOD": C.CYAN,
    "CLS": C.TEAL,
}

# ── Product colour map ───────────────────────────────────────────────────────
PRODUCT_COLOURS = {
    "Car Loan":       C.ORANGE,
    "Personal Loan":  C.BRIGHT_CYAN,
    "Student Loan":   C.LIME,
    "Investment Plan":C.GOLD,
    "Trust Fund":     C.PURPLE,
}


def confidence_bar(score: float, width: int = 25) -> str:
    """
    Render a gradient confidence bar with block characters and percentage.

    Colour tiers:
      >= 0.90  → bright green   ██████████████████████████  96.0%
      >= 0.75  → lime/green     ████████████████░░░░░░░░░░  77.5%
      >= 0.60  → yellow         ████████████░░░░░░░░░░░░░░  62.0%
      >= 0.40  → orange         ████████░░░░░░░░░░░░░░░░░░  44.0%
       < 0.40  → red            ████░░░░░░░░░░░░░░░░░░░░░░  18.0%
    """
    filled  = int(score * width)
    empty   = width - filled

    if score >= 0.90:
        fill_colour = C.BRIGHT_GREEN
        pct_colour  = C.BRIGHT_GREEN
    elif score >= 0.75:
        fill_colour = C.LIME
        pct_colour  = C.LIME
    elif score >= 0.60:
        fill_colour = C.BRIGHT_YELLOW
        pct_colour  = C.YELLOW
    elif score >= 0.40:
        fill_colour = C.ORANGE
        pct_colour  = C.ORANGE
    else:
        fill_colour = C.BRIGHT_RED
        pct_colour  = C.RED

    bar = (
        f"{fill_colour}{'█' * filled}{C.RESET}"
        f"{C.DIM}{'░' * empty}{C.RESET}"
    )
    return f"{bar}  {pct_colour}{C.BOLD}{score:.1%}{C.RESET}"


def score_gradient_bar(score: float, lo: float, hi: float, width: int = 20) -> str:
    """
    Render a score bar normalised between [lo, hi] with a position marker.
    Used for Loan_signal_score display within its product range.
    """
    if hi == lo:
        normalised = 1.0
    else:
        normalised = max(0.0, min(1.0, (score - lo) / (hi - lo)))

    filled = int(normalised * width)
    empty  = width - filled
    colour = C.BRIGHT_GREEN if normalised >= 0.5 else C.ORANGE

    bar = (
        f"{colour}{'▓' * filled}{C.RESET}"
        f"{C.DIM}{'░' * empty}{C.RESET}"
    )
    return f"{bar}  {colour}{C.BOLD}{score:.2f}{C.RESET} {C.DIM}[{lo:.2f}–{hi:.2f}]{C.RESET}"


def dsr_bar(ratio_str: str, width: int = 20) -> str:
    """
    Render a DSR (Debt Service Ratio) bar.
    ratio_str expected format: '18.4%' or similar.
    Cap is 33.3%.
    """
    try:
        val = float(ratio_str.strip("%")) / 100.0
    except (ValueError, AttributeError):
        return ratio_str

    cap        = 0.333
    proportion = min(1.0, val / cap)
    filled     = int(proportion * width)
    empty      = width - filled
    over_cap   = val > cap

    if over_cap:
        fill_colour = C.BRIGHT_RED
        pct_colour  = C.BRIGHT_RED
    elif val >= 0.25:
        fill_colour = C.ORANGE
        pct_colour  = C.ORANGE
    else:
        fill_colour = C.BRIGHT_GREEN
        pct_colour  = C.BRIGHT_GREEN

    bar = (
        f"{fill_colour}{'█' * filled}{C.RESET}"
        f"{C.DIM}{'░' * empty}{C.RESET}"
    )
    cap_marker = f" {C.DIM}/ {cap:.0%} cap{C.RESET}"
    return f"{bar}  {pct_colour}{C.BOLD}{ratio_str}{C.RESET}{cap_marker}"


def risk_score_bar(score: int, width: int = 20) -> str:
    """Render a 0–100 risk score bar."""
    proportion = score / 100.0
    filled     = int(proportion * width)
    empty      = width - filled

    if score >= 75:
        colour = C.BRIGHT_RED
    elif score >= 50:
        colour = C.ORANGE
    elif score >= 30:
        colour = C.BRIGHT_YELLOW
    else:
        colour = C.BRIGHT_GREEN

    bar = (
        f"{colour}{'█' * filled}{C.RESET}"
        f"{C.DIM}{'░' * empty}{C.RESET}"
    )
    return f"{bar}  {colour}{C.BOLD}{score}/100{C.RESET}"


def pass_fail(ok: bool) -> str:
    if ok:
        return f"{C.BG_GREEN}{C.BLACK}{C.BOLD}  PASS  {C.RESET}"
    else:
        return f"{C.BG_RED}{C.WHITE}{C.BOLD}  FAIL  {C.RESET}"


def result_badge(text: str, ok: bool) -> str:
    """Render APPROVED / NOT_ELIGIBLE / etc. as a coloured badge."""
    colour = C.BRIGHT_GREEN if ok else C.BRIGHT_RED
    bg     = C.BG_GREEN     if ok else C.BG_RED
    fg     = C.BLACK        if ok else C.WHITE
    return f"{bg}{fg}{C.BOLD} {text} {C.RESET}"


def section(title: str, colour: str = C.CYAN) -> None:
    """Print a bold coloured section divider."""
    width   = 70
    pad     = max(0, (width - len(title) - 4) // 2)
    top     = f"{colour}{'═' * width}{C.RESET}"
    mid     = f"{colour}╠{'═' * pad}  {C.BOLD}{C.WHITE}{title}{C.RESET}{colour}  {'═' * pad}╣{C.RESET}"
    bot     = f"{colour}{'═' * width}{C.RESET}"
    print(f"\n{top}\n{mid}\n{bot}\n")


def sub_section(title: str, colour: str = C.DIM) -> None:
    """Print a lighter sub-divider."""
    width = 60
    pad   = max(0, (width - len(title) - 2) // 2)
    print(f"  {colour}{'─' * pad} {C.BOLD}{title}{C.RESET}{colour} {'─' * pad}{C.RESET}")


def naira(amount: float) -> str:
    return f"{C.GOLD}N{C.RESET}{C.BOLD}{amount:,.0f}{C.RESET}"


def elapsed_str(seconds: float) -> str:
    if seconds < 1.0:
        return f"{C.TEAL}{seconds * 1000:.0f}ms{C.RESET}"
    return f"{C.TEAL}{seconds:.2f}s{C.RESET}"


def label(text: str, colour: str = C.CYAN) -> str:
    """Left-aligned label with consistent width."""
    return f"{colour}{C.BOLD}{text:<16}{C.RESET}"


def bullet_ok(text: str) -> str:
    return f"  {C.BRIGHT_GREEN}✔{C.RESET}  {text}"


def bullet_fail(text: str) -> str:
    return f"  {C.BRIGHT_RED}✘{C.RESET}  {text}"


def bullet_note(text: str) -> str:
    return f"  {C.DIM}◦{C.RESET}  {C.DIM}{text}{C.RESET}"


# =============================================================================
# DISPATCHER TEST CASES
# =============================================================================

DISPATCHER_CASES: List[Dict] = [
    {
        "name":              "Transfer not received",
        "complaint":         "I transferred money to a friend but he hasn't received it yet.",
        "expected_dept":     "TSU",
        "expected_priority": "High",
    },
    {
        "name":              "ATM card swallowed",
        "complaint":         "My card was swallowed by the ATM machine at FirstBank Ikeja.",
        "expected_dept":     "COC",
        "expected_priority": "High",
    },
    {
        "name":              "Unauthorized transaction (fraud)",
        "complaint":         "I see an unauthorized debit of N250,000 I did not authorise. My account may be hacked.",
        "expected_dept":     "FRM",
        "expected_priority": "Critical",
    },
    {
        "name":              "Mobile app login failure",
        "complaint":         "I cannot log into my mobile banking app — it keeps saying wrong password even after reset.",
        "expected_dept":     "DCS",
        "expected_priority": "Medium",
    },
    {
        "name":              "Account restriction",
        "complaint":         "My account has been restricted and I cannot make any transactions. Please help me.",
        "expected_dept":     "AOD",
        "expected_priority": "Medium",
    },
    {
        "name":              "Loan status enquiry",
        "complaint":         "I applied for a car loan two weeks ago and want to know the current status.",
        "expected_dept":     "CLS",
        "expected_priority": "Low",
    },
]


# =============================================================================
# SENTINEL TEST CASES
# =============================================================================

SENTINEL_CASES: List[Dict] = [
    {
        "name": "LOW risk — normal grocery purchase",
        "transaction": {
            "fraud_explainability_trace": "normal_pattern",
            "merchant_category":          "grocery",
            "amount":                     5_200,
            "transaction_timestamp":      "2026-02-22 14:35:00",
        },
        "expected_level": "LOW",
    },
    {
        "name": "HIGH risk — fintech, late night, large amount",
        "transaction": {
            "fraud_explainability_trace": "high_amount_spike,mobile_channel_risk",
            "merchant_category":          "fintech",
            "amount":                     450_000,
            "transaction_timestamp":      "2026-02-22 02:15:00",
        },
        "expected_level": "HIGH",
    },
    {
        "name": "CRITICAL risk — multiple failures at 3am",
        "transaction": {
            "fraud_explainability_trace": "multiple_failures,high_amount_spike",
            "merchant_category":          "fintech",
            "amount":                     520_000,
            "transaction_timestamp":      "2026-02-23 03:05:00",
        },
        "expected_level": "CRITICAL",
    },
]


# =============================================================================
# TRAJECTORY TEST CASES
# =============================================================================

TRAJECTORY_CASES: List[Dict] = [
    # ── Student Loan ──────────────────────────────────────────────────────────
    {
        "name":    "Student Loan -- APPROVED | NYSC corps member, solo account",
        "product": "Student Loan",
        "customer_data": {
            "Loan_signal_score":   0.88,
            "monthly_inflow":      80_000,
            "salary_detected":     False,
            "uber_tracker":        1,
            "age":                 21,
            "account_type":        "solo",
            "current_balance":     45_000,
            "desired_loan_amount": 500_000,
        },
        "expected_result":         "APPROVED",
        "expected_recommendation": "Student Loan",
    },
    {
        "name":    "Student Loan -- NOT ELIGIBLE | Score below 0.80 floor",
        "product": "Student Loan",
        "customer_data": {
            "Loan_signal_score":   0.74,
            "monthly_inflow":      60_000,
            "salary_detected":     False,
            "uber_tracker":        0,
            "age":                 22,
            "account_type":        "solo",
            "current_balance":     20_000,
            "desired_loan_amount": 500_000,
        },
        "expected_result":         "NOT_ELIGIBLE",
        "expected_recommendation": "Student Loan",
    },
    # ── Car Loan ──────────────────────────────────────────────────────────────
    {
        "name":    "Car Loan -- APPROVED | Lagos commuter, 14 ride-hailing trips",
        "product": "Car Loan",
        "customer_data": {
            "Loan_signal_score":   0.82,
            "monthly_inflow":      620_000,
            "salary_detected":     True,
            "uber_tracker":        14,
            "age":                 30,
            "account_type":        "savings",
            "current_balance":     180_000,
            "desired_loan_amount": 4_000_000,
        },
        "expected_result":         "APPROVED",
        "expected_recommendation": "Car Loan",
    },
    {
        "name":    "Car Loan -- NOT ELIGIBLE | Score below 0.75 floor",
        "product": "Car Loan",
        "customer_data": {
            "Loan_signal_score":   0.60,
            "monthly_inflow":      400_000,
            "salary_detected":     False,
            "uber_tracker":        3,
            "age":                 25,
            "account_type":        "savings",
            "current_balance":     90_000,
            "desired_loan_amount": 3_000_000,
        },
        "expected_result":         "NOT_ELIGIBLE",
        "expected_recommendation": None,
    },
    # ── Personal Loan ─────────────────────────────────────────────────────────
    {
        "name":    "Personal Loan -- APPROVED | Mid-career professional, salary earner",
        "product": "Personal Loan",
        "customer_data": {
            "Loan_signal_score":   0.72,
            "monthly_inflow":      480_000,
            "salary_detected":     True,
            "uber_tracker":        2,
            "age":                 33,
            "account_type":        "savings",
            "current_balance":     220_000,
            "desired_loan_amount": 1_500_000,
        },
        "expected_result":         "APPROVED",
        "expected_recommendation": "Personal Loan",
    },
    # ── Investment Plan ───────────────────────────────────────────────────────
    {
        "name":    "Investment Plan -- APPROVED | Entrepreneur, high inflow current account",
        "product": "Investment Plan",
        "customer_data": {
            "Loan_signal_score":   0.76,
            "monthly_inflow":      3_200_000,
            "salary_detected":     True,
            "uber_tracker":        4,
            "age":                 42,
            "account_type":        "current",
            "current_balance":     6_500_000,
            "desired_loan_amount": 0,
        },
        "expected_result":         "APPROVED",
        "expected_recommendation": "Investment Plan",
    },
    {
        "name":    "Investment Plan -- NOT ELIGIBLE | Score below 0.70 floor",
        "product": "Investment Plan",
        "customer_data": {
            "Loan_signal_score":   0.63,
            "monthly_inflow":      2_800_000,
            "salary_detected":     True,
            "uber_tracker":        2,
            "age":                 39,
            "account_type":        "current",
            "current_balance":     4_000_000,
            "desired_loan_amount": 0,
        },
        "expected_result":         "NOT_ELIGIBLE",
        "expected_recommendation": None,
    },
    # ── Trust Fund ────────────────────────────────────────────────────────────
    {
        "name":    "Trust Fund -- APPROVED | HNI customer, high balance current account",
        "product": "Trust Fund",
        "customer_data": {
            "Loan_signal_score":   0.70,
            "monthly_inflow":      1_800_000,
            "salary_detected":     True,
            "uber_tracker":        3,
            "age":                 50,
            "account_type":        "current",
            "current_balance":     12_000_000,
            "desired_loan_amount": 0,
        },
        "expected_result":         "APPROVED",
        "expected_recommendation": "Trust Fund",
    },
    {
        "name":    "Trust Fund -- NOT ELIGIBLE | Score below 0.65 floor",
        "product": "Trust Fund",
        "customer_data": {
            "Loan_signal_score":   0.50,
            "monthly_inflow":      500_000,
            "salary_detected":     False,
            "uber_tracker":        1,
            "age":                 35,
            "account_type":        "savings",
            "current_balance":     80_000,
            "desired_loan_amount": 0,
        },
        "expected_result":         "NOT_ELIGIBLE",
        "expected_recommendation": None,
    },
]


# =============================================================================
# POLICY TEST CASES
# =============================================================================

POLICY_CASES: List[Dict] = [
    {
        "name":     "TSU SLA policy",
        "question": "What is the SLA resolution time for transaction disputes?",
        "keywords": ["48", "hours", "transaction", "sla", "resolution"],
    },
    {
        "name":     "Fraud risk scoring",
        "question": "How is the fraud risk score calculated and what are the thresholds?",
        "keywords": ["risk", "score", "high", "critical", "flag"],
    },
    {
        "name":     "Merchant risk categories",
        "question": "Which merchant categories have the highest fraud risk weights?",
        "keywords": ["fintech", "merchant", "risk", "weight"],
    },
    {
        "name":     "FRM escalation SLA",
        "question": "What is the SLA for the Fraud Risk Management department?",
        "keywords": ["24", "fraud", "frm", "hours"],
    },
    {
        "name":     "DSR cap and EMI policy",
        "question": "What is the Debt Service Ratio cap and how is EMI calculated for loans?",
        "keywords": ["dsr", "33", "emi", "monthly", "repayment"],
    },
    {
        "name":     "Loan product interest rates",
        "question": "What are the interest rates for Car Loan, Personal Loan and Student Loan?",
        "keywords": ["24", "30", "18", "apr", "loan"],
    },
]

CONFIDENCE_THRESHOLD = 0.85


# =============================================================================
# Main Tester Class
# =============================================================================

class AgentTester:
    """Runs automated tests and interactive demos for all four agents."""

    def __init__(self) -> None:
        self.engine:      Optional[RAGQueryEngine]  = None
        self.results:     List[Dict]                = []
        self.recommender: RecommendationEngine      = RecommendationEngine()

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    async def initialize(self) -> None:
        """Initialize RAG engine with persistent ChromaDB client."""
        print(f"\n{C.INDIGO}{'▓' * 70}{C.RESET}")
        print(f"{C.INDIGO}▓{C.RESET}  {C.GOLD}{C.BOLD}{'Sentinel Bank RAG System — Agent Demo & Test Suite':^64}{C.RESET}  {C.INDIGO}▓{C.RESET}")
        print(f"{C.INDIGO}{'▓' * 70}{C.RESET}\n")

        print(f"  {C.DIM}Initializing ChromaDB and loading embedding model ...{C.RESET}")
        start = time.time()

        client, config = initialize_chromadb()
        self.engine    = RAGQueryEngine(client, config)

        elapsed = time.time() - start
        print(f"  {C.BRIGHT_GREEN}✔  Engine ready{C.RESET}  {elapsed_str(elapsed)}\n")

        stats = self.engine.retrieval.get_collection_stats()
        print(f"  {C.CYAN}Collections:{C.RESET}")
        print(f"    {C.TEAL}Policy chunks {C.RESET}: {C.BOLD}{stats['policies']:>4}{C.RESET}")
        print(f"    {C.TEAL}FAQ chunks    {C.RESET}: {C.BOLD}{stats['faqs']:>4}{C.RESET}")
        print(f"    {C.TEAL}Total chunks  {C.RESET}: {C.BOLD}{stats['total']:>4}{C.RESET}")
        print()

    # =========================================================================
    # DISPATCHER TESTS
    # =========================================================================

    async def run_dispatcher_tests(self) -> int:
        """Run all Dispatcher Agent test cases. Returns pass count."""
        section("DISPATCHER AGENT — Complaint Routing", C.BLUE)

        passed = 0
        for i, tc in enumerate(DISPATCHER_CASES, 1):
            dept_colour = DEPT_COLOURS.get(tc["expected_dept"], C.CYAN)
            print(f"  {C.BOLD}{C.WHITE}Test {i}/{len(DISPATCHER_CASES)}{C.RESET}"
                  f"  {dept_colour}{C.BOLD}{tc['name']}{C.RESET}")
            print(f"  {C.DIM}Complaint:{C.RESET} {C.ITALIC}{tc['complaint']}{C.RESET}")

            start   = time.time()
            result  = await self.engine.detect_complaint_category(tc["complaint"])
            elapsed = time.time() - start

            dept       = result["department_code"]
            dept_name  = result["department_name"]
            priority   = result["priority_level"]
            sla        = result["sla_hours"]
            confidence = result["confidence"]
            method     = result["routing_method"]
            keywords   = result.get("keyword_matches", [])

            dept_ok       = dept == tc["expected_dept"]
            confidence_ok = confidence >= CONFIDENCE_THRESHOLD
            ok            = dept_ok and confidence_ok

            if ok:
                passed += 1

            dc = DEPT_COLOURS.get(dept, C.CYAN)
            pc = PRIORITY_COLOURS.get(priority, C.WHITE)

            print(f"  {C.DIM}{'─' * 62}{C.RESET}")
            print(f"  {label('Department')}  {dc}{C.BOLD}{dept} — {dept_name}{C.RESET}"
                  f"  {C.DIM}(expected: {tc['expected_dept']}){C.RESET}  {pass_fail(dept_ok)}")
            print(f"  {label('Priority')}  {pc}{C.BOLD}{priority}{C.RESET}"
                  f"  {C.DIM}SLA:{C.RESET} {C.GOLD}{C.BOLD}{sla}h{C.RESET}")
            print(f"  {label('Confidence')}  {confidence_bar(confidence)}")
            print(f"  {label('Method')}  {C.TEAL}{method}{C.RESET}"
                  f"  {C.DIM}|  Keywords:{C.RESET} {C.SKY}{keywords[:4]}{C.RESET}")
            print(f"  {label('Response time')}  {elapsed_str(elapsed)}"
                  f"   {pass_fail(ok)}")
            print()

            self.results.append({
                "suite":      "Dispatcher",
                "name":       tc["name"],
                "passed":     ok,
                "confidence": confidence,
            })

        return passed

    # =========================================================================
    # SENTINEL TESTS
    # =========================================================================

    async def run_sentinel_tests(self) -> int:
        """Run all Sentinel Agent test cases. Returns pass count."""
        section("SENTINEL AGENT — Fraud Risk Scoring", C.CORAL)

        passed = 0
        for i, tc in enumerate(SENTINEL_CASES, 1):
            txn = tc["transaction"]
            lc  = RISK_COLOURS.get(tc["expected_level"], C.WHITE)

            print(f"  {C.BOLD}{C.WHITE}Test {i}/{len(SENTINEL_CASES)}{C.RESET}"
                  f"  {lc}{C.BOLD}{tc['name']}{C.RESET}")
            print(f"  {C.DIM}Amount:{C.RESET}  {naira(txn['amount'])}"
                  f"  {C.DIM}Merchant:{C.RESET}  {C.TEAL}{txn['merchant_category']}{C.RESET}"
                  f"  {C.DIM}Flags:{C.RESET}  {C.ORANGE}{txn['fraud_explainability_trace']}{C.RESET}")

            start   = time.time()
            result  = await self.engine.calculate_fraud_risk(txn)
            elapsed = time.time() - start

            score      = result["total_risk_score"]
            level      = result["risk_level"]
            breakdown  = result["risk_breakdown"]
            action     = result["recommended_action"]
            block      = result["should_block"]
            challenge  = result["requires_challenge"]
            confidence = result["confidence"]

            level_ok = level == tc["expected_level"]
            ok       = level_ok
            if ok:
                passed += 1

            rc = RISK_COLOURS.get(level, C.WHITE)

            print(f"  {C.DIM}{'─' * 62}{C.RESET}")
            print(f"  {label('Risk Score')}  {risk_score_bar(score)}")
            print(f"  {label('Risk Level')}  {rc}{C.BOLD}{level}{C.RESET}"
                  f"  {C.DIM}(expected: {tc['expected_level']}){C.RESET}  {pass_fail(level_ok)}")

            # Breakdown mini-bars
            f_score = breakdown['flag_score']
            m_risk  = breakdown['merchant_risk']
            t_risk  = breakdown['timing_risk']
            print(f"  {label('Breakdown')}"
                  f"  flags {C.ORANGE}{f_score:>3}{C.RESET}"
                  f"  merchant {C.CORAL}{m_risk:>3}{C.RESET}"
                  f"  timing {C.YELLOW}{t_risk:>3}{C.RESET}")

            block_str     = f"{C.BRIGHT_RED}{C.BOLD}YES — immediate freeze{C.RESET}" if block else f"{C.DIM}No{C.RESET}"
            challenge_str = f"{C.ORANGE}YES{C.RESET}" if challenge else f"{C.DIM}No{C.RESET}"
            print(f"  {label('Action')}  {C.BRIGHT_YELLOW}{action}{C.RESET}")
            print(f"  {label('Block?')}  {block_str}   {C.DIM}Challenge:{C.RESET}  {challenge_str}")

            if result.get("policy_explanation"):
                expl = result["policy_explanation"][:110]
                print(f"  {label('Policy basis')}  {C.DIM}{expl}…{C.RESET}")

            print(f"  {label('Response time')}  {elapsed_str(elapsed)}"
                  f"   {pass_fail(ok)}")
            print()

            self.results.append({
                "suite":      "Sentinel",
                "name":       tc["name"],
                "passed":     ok,
                "confidence": confidence,
            })

        return passed

    # =========================================================================
    # TRAJECTORY TESTS
    # =========================================================================

    async def run_trajectory_tests(self) -> int:
        """
        Run all Trajectory Agent test cases.

        Each test runs BOTH:
          1. validate_product_recommendation() — eligibility gate (RAG-grounded)
          2. recommend_product()               — proactive tailored suggestion

        Returns:
            pass count (int)
        """
        section("TRAJECTORY AGENT — Eligibility + Tailored Recommendation", C.MAGENTA)

        passed = 0
        for i, tc in enumerate(TRAJECTORY_CASES, 1):
            cd      = tc["customer_data"]
            product = tc["product"]
            pc      = PRODUCT_COLOURS.get(product, C.CYAN)

            score   = cd.get("Loan_signal_score", 0)
            inflow  = cd.get("monthly_inflow", 0)
            age     = cd.get("age", "N/A")
            uber    = cd.get("uber_tracker", 0)
            salary  = cd.get("salary_detected", False)
            acct    = cd.get("account_type", "savings")
            balance = cd.get("current_balance", 0)
            desired = cd.get("desired_loan_amount", 0)

            print(f"  {C.BOLD}{C.WHITE}Test {i}/{len(TRAJECTORY_CASES)}{C.RESET}"
                  f"  {pc}{C.BOLD}{tc['name']}{C.RESET}")

            # Profile summary line
            salary_tag = (f"{C.BRIGHT_GREEN}salary ✔{C.RESET}" if salary
                          else f"{C.DIM}no salary{C.RESET}")
            uber_tag   = (f"{C.ORANGE}🚗 {uber} trips{C.RESET}" if uber
                          else f"{C.DIM}uber: 0{C.RESET}")
            print(f"  {C.DIM}Profile :{C.RESET}"
                  f"  age {C.LIME}{age}{C.RESET}"
                  f"  acct {C.TEAL}{acct}{C.RESET}"
                  f"  inflow {naira(inflow)}"
                  f"  bal {naira(balance)}")
            print(f"  {C.DIM}Signals :{C.RESET}"
                  f"  {salary_tag}  {uber_tag}"
                  + (f"  desired {naira(desired)}" if desired > 0 else ""))

            # ── 1. VALIDATION ─────────────────────────────────────────────────
            v_start   = time.time()
            val       = await self.engine.validate_product_recommendation(cd, product)
            v_elapsed = time.time() - v_start

            eligible    = val["is_eligible"]
            recommend   = val["recommendation"]
            met         = val["met_criteria"]
            unmet       = val["unmet_criteria"]
            confidence  = val["confidence"]
            score_range = val.get("score_range")
            policy      = val.get("policy_basis", "")

            val_ok   = recommend == tc["expected_result"]
            r_lo, r_hi = (score_range if score_range else (0.0, 1.0))

            sub_section(f"① VALIDATION — {product}", pc)
            print(f"  {label('Score range')}  {score_gradient_bar(score, r_lo, r_hi)}")
            print(f"  {label('Eligibility')}  {result_badge(recommend, eligible)}"
                  f"  {C.DIM}(expected: {tc['expected_result']}){C.RESET}  {pass_fail(val_ok)}")
            print(f"  {label('RAG confidence')}  {confidence_bar(confidence)}")
            for m in met:
                print(bullet_ok(m))
            for u in unmet:
                print(bullet_fail(u))
            if policy:
                print(f"  {C.DIM}Policy:{C.RESET}  {C.DIM}{policy[:110]}…{C.RESET}")
            print(f"  {label('Response time')}  {elapsed_str(v_elapsed)}")

            # ── 2. PROACTIVE RECOMMENDATION ───────────────────────────────────
            sub_section("② RECOMMENDATION ENGINE — behavioral profile", C.SKY)

            r_start    = time.time()
            rec_result = await self.recommender.recommend(cd)
            r_elapsed  = time.time() - r_start

            primary   = rec_result["primary_product"]
            r_met     = rec_result["met_criteria"]
            r_unmet   = rec_result["unmet_criteria"]
            r_conf    = rec_result["confidence"]
            emi       = rec_result["monthly_emi"]
            tenure    = rec_result["tenure_months"]
            dsr_ratio = rec_result["dsr_ratio"]
            dsr_warn  = rec_result["dsr_warning"]
            all_q     = rec_result["all_qualifying"]
            r_range   = rec_result.get("score_range")

            if primary:
                rpc     = PRODUCT_COLOURS.get(primary, C.CYAN)
                p_range = (f"{r_range[0]:.2f}–{r_range[1]:.2f}" if r_range else "N/A")
                print(f"  {label('Recommended')}  {rpc}{C.BOLD}{primary}{C.RESET}"
                      f"  {C.DIM}range {p_range}  conf {r_conf}{C.RESET}")

                if emi > 0:
                    print(f"  {label('Monthly EMI')}  {C.BOLD}{naira(emi)}{C.RESET}"
                          f"  {C.DIM}over{C.RESET} {C.GOLD}{tenure} months{C.RESET}")
                    dsr_warn_txt = (
                        f"  {C.BRIGHT_RED}{C.BOLD}⚠  EXCEEDS 33.3% CBN CAP — refer to credit officer{C.RESET}"
                        if dsr_warn else ""
                    )
                    print(f"  {label('DSR')}  {dsr_bar(dsr_ratio)}{dsr_warn_txt}")
                else:
                    print(f"  {label('EMI / DSR')}  {C.DIM}N/A  (investment or wealth product){C.RESET}")

                if all_q and len(all_q) > 1:
                    all_coloured = [f"{PRODUCT_COLOURS.get(p, C.CYAN)}{p}{C.RESET}" for p in all_q]
                    print(f"  {label('All qualifying')}  {', '.join(all_coloured)}")

                for m in r_met:
                    print(bullet_ok(m))
                for u in r_unmet:
                    print(bullet_note(u))

            else:
                print(f"  {C.BRIGHT_YELLOW}⚠  No product qualifies —"
                      f" Loan_signal_score {C.BOLD}{score:.2f}{C.RESET}"
                      f"{C.BRIGHT_YELLOW} is below all product floors{C.RESET}")
                for r in rec_result.get("reasoning", []):
                    print(bullet_note(r))

            print(f"  {label('Calc time')}  {elapsed_str(r_elapsed)}")

            # ── Overall ───────────────────────────────────────────────────────
            ok = val_ok
            if ok:
                passed += 1

            print(f"\n  {C.BOLD}Overall  {pass_fail(ok)}{C.RESET}")
            print()

            self.results.append({
                "suite":      "Trajectory",
                "name":       tc["name"],
                "passed":     ok,
                "confidence": confidence,
            })

        return passed

    # =========================================================================
    # POLICY QUERY TESTS
    # =========================================================================

    async def run_policy_tests(self) -> int:
        """Run general policy query tests. Returns pass count."""
        section("POLICY AGENT — General Knowledge Queries", C.TEAL)

        passed = 0
        for i, tc in enumerate(POLICY_CASES, 1):
            print(f"  {C.BOLD}{C.WHITE}Test {i}/{len(POLICY_CASES)}{C.RESET}"
                  f"  {C.TEAL}{C.BOLD}{tc['name']}{C.RESET}")
            print(f"  {C.DIM}Q:{C.RESET}  {C.ITALIC}{tc['question']}{C.RESET}")

            start   = time.time()
            result  = await self.engine.query(tc["question"])
            elapsed = time.time() - start

            answer      = result.get("answer", "") or ""
            confidence  = result.get("confidence", 0.0)
            sources     = result.get("sources", [])
            grounded    = result.get("grounded", False)

            answer_lower = answer.lower()
            keyword_hits = [kw for kw in tc["keywords"] if kw in answer_lower]
            keyword_ok   = len(keyword_hits) >= 1
            confidence_ok= confidence >= CONFIDENCE_THRESHOLD
            ok           = grounded and keyword_ok

            if ok:
                passed += 1

            source_str   = sources[0]["source"] if sources else "None"
            grnd_colour  = C.BRIGHT_GREEN if grounded else C.BRIGHT_RED
            grnd_icon    = "✔" if grounded else "✘"

            print(f"  {C.DIM}{'─' * 62}{C.RESET}")
            print(f"  {label('Confidence')}  {confidence_bar(confidence)}")
            print(f"  {label('Grounded')}  {grnd_colour}{grnd_icon}  {grounded}{C.RESET}"
                  f"  {C.DIM}|  Source:{C.RESET}  {C.SKY}{source_str}{C.RESET}")

            hits_coloured = [f"{C.LIME}{kw}{C.RESET}" for kw in keyword_hits]
            print(f"  {label('Keyword hits')}  {', '.join(hits_coloured) or C.DIM + 'none' + C.RESET}"
                  f"   {pass_fail(keyword_ok)}")

            if answer:
                preview = answer[:180].replace("\n", " ")
                print(f"  {label('Answer')}  {C.DIM}{preview}…{C.RESET}")

            print(f"  {label('Response time')}  {elapsed_str(elapsed)}"
                  f"   {pass_fail(ok)}")
            print()

            self.results.append({
                "suite":      "Policy",
                "name":       tc["name"],
                "passed":     ok,
                "confidence": confidence,
            })

        return passed

    # =========================================================================
    # AUTOMATED FULL SUITE
    # =========================================================================

    async def run_all_tests(self) -> None:
        """Run complete automated test suite for all four agents."""
        self.results.clear()
        total_start = time.time()

        d_pass = await self.run_dispatcher_tests()
        s_pass = await self.run_sentinel_tests()
        t_pass = await self.run_trajectory_tests()
        p_pass = await self.run_policy_tests()

        section("FINAL TEST RESULTS", C.GOLD)

        suites = [
            ("Dispatcher",  len(DISPATCHER_CASES),  d_pass,  C.BLUE),
            ("Sentinel",    len(SENTINEL_CASES),     s_pass,  C.CORAL),
            ("Trajectory",  len(TRAJECTORY_CASES),   t_pass,  C.MAGENTA),
            ("Policy",      len(POLICY_CASES),        p_pass,  C.TEAL),
        ]

        total_tests  = sum(n for _, n, _, _ in suites)
        total_passed = sum(p for _, _, p, _ in suites)

        # Per-suite summary rows
        for suite, total, p, colour in suites:
            rate   = p / total if total else 0
            bar    = confidence_bar(rate, width=20)
            status = (f"{C.BG_GREEN}{C.BLACK}{C.BOLD}  PASS  {C.RESET}"
                      if p == total
                      else f"{C.BG_RED}{C.WHITE}{C.BOLD}  FAIL  {C.RESET}")
            print(f"  {colour}{C.BOLD}{suite:<12}{C.RESET}  {p}/{total}  {bar}  {status}")

        print()
        overall_rate = total_passed / total_tests if total_tests else 0
        elapsed      = time.time() - total_start

        print(f"  {C.BOLD}Overall    :{C.RESET}  {C.BOLD}{total_passed}/{total_tests} tests passed{C.RESET}")
        print(f"  {C.BOLD}Success    :{C.RESET}  {confidence_bar(overall_rate, width=30)}")
        print(f"  {C.BOLD}Total time :{C.RESET}  {elapsed_str(elapsed)}")
        print()

        # Average RAG confidence per suite
        print(f"  {C.CYAN}Average RAG confidence by suite:{C.RESET}")
        by_suite: Dict[str, List[float]] = {}
        for r in self.results:
            by_suite.setdefault(r["suite"], []).append(r["confidence"])

        for suite, scores in by_suite.items():
            avg    = sum(scores) / len(scores) if scores else 0
            colour = dict((s, c) for s, _, _, c in suites).get(suite, C.CYAN)
            print(f"    {colour}{C.BOLD}{suite:<12}{C.RESET}  {confidence_bar(avg, width=20)}")

        print()
        if total_passed == total_tests:
            print(f"  {C.BG_GREEN}{C.BLACK}{C.BOLD}  ✔  ALL AGENTS WORKING CORRECTLY  {C.RESET}\n")
        else:
            failed = [r for r in self.results if not r["passed"]]
            print(f"  {C.BG_RED}{C.WHITE}{C.BOLD}  ✘  Some tests failed — review above  {C.RESET}")
            for f in failed:
                print(f"    {C.BRIGHT_RED}✘{C.RESET}  {C.DIM}[{f['suite']}]{C.RESET}  {f['name']}")
            print()

    # =========================================================================
    # INTERACTIVE DEMOS
    # =========================================================================

    async def interactive_dispatcher(self) -> None:
        """Interactive Dispatcher Agent demo."""
        section("INTERACTIVE — Dispatcher Agent", C.BLUE)
        print(f"  {C.DIM}Type a customer complaint and the Dispatcher Agent will route it.{C.RESET}")
        print(f"  {C.DIM}Type 'back' to return to the menu.{C.RESET}\n")

        samples = [
            "I transferred N50,000 to my cousin yesterday but it hasn't arrived",
            "My debit card was blocked after I tried to use it at a POS terminal",
            "Someone made an unauthorized transaction on my account last night",
            "The Sentinel Bank mobile app won't let me log in",
        ]
        print(f"  {C.TEAL}Sample complaints:{C.RESET}")
        for s in samples:
            print(f"    {C.DIM}•  {s}{C.RESET}")
        print()

        while True:
            try:
                complaint = input(f"  {C.BRIGHT_CYAN}Enter complaint:{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not complaint or complaint.lower() == "back":
                break
            print()
            start   = time.time()
            result  = await self.engine.detect_complaint_category(complaint)
            elapsed = time.time() - start

            dept      = result["department_code"]
            dept_name = result["department_name"]
            priority  = result["priority_level"]
            sla       = result["sla_hours"]
            conf      = result["confidence"]
            reasoning = result.get("reasoning", "")
            method    = result.get("routing_method", "")
            keywords  = result.get("keyword_matches", [])

            dc = DEPT_COLOURS.get(dept, C.CYAN)
            pc = PRIORITY_COLOURS.get(priority, C.WHITE)

            print(f"  {C.DIM}{'─' * 62}{C.RESET}")
            print(f"  {label('Department')}  {dc}{C.BOLD}{dept} — {dept_name}{C.RESET}")
            print(f"  {label('Priority')}  {pc}{C.BOLD}{priority}{C.RESET}"
                  f"  {C.DIM}|{C.RESET}  SLA {C.GOLD}{C.BOLD}{sla}h{C.RESET}")
            print(f"  {label('Confidence')}  {confidence_bar(conf)}")
            print(f"  {label('Method')}  {C.TEAL}{method}{C.RESET}"
                  f"  {C.DIM}|  Keywords:{C.RESET}  {C.SKY}{keywords[:5]}{C.RESET}")
            if reasoning:
                print(f"  {label('Policy basis')}  {C.DIM}{reasoning[:200]}…{C.RESET}")
            print(f"  {elapsed_str(elapsed)}")
            print()

    async def interactive_sentinel(self) -> None:
        """Interactive Sentinel Agent demo with preset transactions."""
        section("INTERACTIVE — Sentinel Agent", C.CORAL)
        print(f"  {C.DIM}Select a sample transaction to analyse.{C.RESET}\n")

        presets = [
            {
                "label": "1.  Low risk — grocery, daytime, small amount",
                "transaction": {"fraud_explainability_trace": "normal_pattern",
                                "merchant_category": "grocery", "amount": 4_800,
                                "transaction_timestamp": "2026-02-22 11:20:00"},
            },
            {
                "label": "2.  High risk — fintech, 2am, N450K",
                "transaction": {"fraud_explainability_trace": "high_amount_spike,mobile_channel_risk",
                                "merchant_category": "fintech", "amount": 450_000,
                                "transaction_timestamp": "2026-02-22 02:15:00"},
            },
            {
                "label": "3.  Critical — multiple failures at 3am, N520K",
                "transaction": {"fraud_explainability_trace": "multiple_failures,high_amount_spike",
                                "merchant_category": "fintech", "amount": 520_000,
                                "transaction_timestamp": "2026-02-23 03:05:00"},
            },
            {
                "label": "4.  Medium risk — transport (Bolt), mobile channel",
                "transaction": {"fraud_explainability_trace": "mobile_channel_risk",
                                "merchant_category": "transport", "amount": 85_000,
                                "transaction_timestamp": "2026-02-22 23:45:00"},
            },
        ]
        level_colours_menu = [C.BRIGHT_GREEN, C.ORANGE, C.BRIGHT_RED, C.BRIGHT_YELLOW]
        for p, lc in zip(presets, level_colours_menu):
            print(f"  {lc}{p['label']}{C.RESET}")
        print(f"  {C.DIM}0.  Back to menu{C.RESET}\n")

        while True:
            try:
                choice = input(f"  {C.BRIGHT_CYAN}Select (0–{len(presets)}):{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if choice == "0" or choice.lower() == "back":
                break
            try:
                idx = int(choice) - 1
                if not 0 <= idx < len(presets):
                    print(f"  {C.RED}Enter 0–{len(presets)}.{C.RESET}")
                    continue
            except ValueError:
                print(f"  {C.RED}Please enter a number.{C.RESET}")
                continue

            txn   = presets[idx]["transaction"]
            label_txt = presets[idx]["label"].split(".", 1)[1].strip()
            print(f"\n  {C.DIM}Analysing: {label_txt}…{C.RESET}\n")

            start   = time.time()
            result  = await self.engine.calculate_fraud_risk(txn)
            elapsed = time.time() - start

            score      = result["total_risk_score"]
            level      = result["risk_level"]
            bd         = result["risk_breakdown"]
            action     = result["recommended_action"]
            block      = result["should_block"]
            challenge  = result["requires_challenge"]
            explanation= result.get("policy_explanation", "")

            rc = RISK_COLOURS.get(level, C.WHITE)

            print(f"  {C.DIM}{'─' * 62}{C.RESET}")
            print(f"  {label('Risk Score')}  {risk_score_bar(score)}")
            print(f"  {label('Risk Level')}  {rc}{C.BOLD}{level}{C.RESET}")
            print(f"  {label('Breakdown')}"
                  f"  flags {C.ORANGE}{bd['flag_score']}{C.RESET}"
                  f"  merchant {C.CORAL}{bd['merchant_risk']}{C.RESET}"
                  f"  timing {C.YELLOW}{bd['timing_risk']}{C.RESET}")
            print(f"  {label('Action')}  {C.BRIGHT_YELLOW}{action}{C.RESET}")
            block_s = f"{C.BRIGHT_RED}{C.BOLD}YES — freeze account{C.RESET}" if block else f"{C.DIM}No{C.RESET}"
            chal_s  = f"{C.ORANGE}YES{C.RESET}" if challenge else f"{C.DIM}No{C.RESET}"
            print(f"  {label('Block?')}  {block_s}   {C.DIM}Challenge:{C.RESET}  {chal_s}")
            if explanation:
                print(f"  {label('Policy')}  {C.DIM}{explanation[:200]}…{C.RESET}")
            print(f"  {elapsed_str(elapsed)}")
            print()

    async def interactive_trajectory(self) -> None:
        """
        Interactive Trajectory Agent demo.

        Collects the full customer behavioral profile and runs BOTH:
          - validate_product_recommendation()  (eligibility gate)
          - recommend_product()                (proactive suggestion w/ EMI + DSR)
        """
        section("INTERACTIVE — Trajectory Agent", C.MAGENTA)
        print(f"  {C.DIM}Enter a full customer profile derived from transaction history.{C.RESET}")
        print(f"  {C.DIM}The engine validates eligibility AND provides a proactive{C.RESET}")
        print(f"  {C.DIM}recommendation with EMI and DSR calculation.{C.RESET}\n")

        products = ["Car Loan", "Investment Plan", "Personal Loan", "Student Loan", "Trust Fund"]
        for i, p in enumerate(products, 1):
            pc = PRODUCT_COLOURS.get(p, C.CYAN)
            print(f"  {pc}{i}. {p}{C.RESET}")
        print(f"  {C.DIM}0. Back{C.RESET}\n")

        while True:
            try:
                p_choice = input(
                    f"  {C.BRIGHT_MAGENTA}Select product to validate (0–{len(products)}):{C.RESET} "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                break
            if p_choice == "0" or p_choice.lower() == "back":
                break
            try:
                p_idx = int(p_choice) - 1
                if not 0 <= p_idx < len(products):
                    print(f"  {C.RED}Invalid. Enter 0–{len(products)}.{C.RESET}")
                    continue
                product = products[p_idx]
            except ValueError:
                print(f"  {C.RED}Please enter a number.{C.RESET}")
                continue

            print(f"\n  {C.DIM}Enter customer data (press Enter for defaults):{C.RESET}")
            try:
                def _inp(prompt, default):
                    v = input(f"  {C.SKY}{prompt}{C.RESET} [{C.DIM}{default}{C.RESET}]: ").strip()
                    return v if v else str(default)

                loan_score      = float(_inp("Loan_signal_score (0.0–1.0)", "0.80"))
                monthly_inflow  = float(_inp("Monthly inflow (N)", "500000"))
                salary_str      = _inp("Salary detected? (y/n)", "y").lower()
                salary_detected = salary_str != "n"
                uber_tracker    = int(  _inp("Uber/Bolt trips in 90 days", "5"))
                age             = int(  _inp("Customer age", "30"))
                account_type    = _inp("Account type (savings/solo/current)", "savings")
                current_balance = float(_inp("Current balance (N)", "200000"))
                desired_str     = _inp("Desired loan amount (N, 0=auto)", "0")
                desired_amount  = float(desired_str)

            except (EOFError, KeyboardInterrupt, ValueError) as e:
                print(f"  {C.RED}Input error: {e}. Using defaults.{C.RESET}")
                loan_score, monthly_inflow, salary_detected = 0.80, 500_000.0, True
                uber_tracker, age, account_type             = 5, 30, "savings"
                current_balance, desired_amount             = 200_000.0, 0.0

            customer: Dict[str, Any] = {
                "Loan_signal_score": loan_score,
                "monthly_inflow":    monthly_inflow,
                "salary_detected":   salary_detected,
                "uber_tracker":      uber_tracker,
                "age":               age,
                "account_type":      account_type,
                "current_balance":   current_balance,
            }
            if desired_amount > 0:
                customer["desired_loan_amount"] = desired_amount

            print()
            # ── VALIDATION ────────────────────────────────────────────────────
            start      = time.time()
            val        = await self.engine.validate_product_recommendation(customer, product)
            elapsed    = time.time() - start

            eligible    = val["is_eligible"]
            recommend   = val["recommendation"]
            met         = val["met_criteria"]
            unmet       = val["unmet_criteria"]
            confidence  = val["confidence"]
            score_range = val.get("score_range")
            policy_b    = val.get("policy_basis", "")

            r_lo, r_hi  = (score_range if score_range else (0.0, 1.0))
            pc          = PRODUCT_COLOURS.get(product, C.CYAN)

            sub_section(f"VALIDATION — {product}", pc)
            print(f"  {label('Score range')}  {score_gradient_bar(loan_score, r_lo, r_hi)}")
            print(f"  {label('Result')}  {result_badge(recommend, eligible)}")
            print(f"  {label('Confidence')}  {confidence_bar(confidence)}")
            for m in met:
                print(bullet_ok(m))
            for u in unmet:
                print(bullet_fail(u))
            if policy_b:
                print(f"  {label('Policy basis')}  {C.DIM}{policy_b[:200]}…{C.RESET}")
            print(f"  {elapsed_str(elapsed)}")

            # ── RECOMMENDATION ─────────────────────────────────────────────────
            sub_section("RECOMMENDATION — behavioral profile", C.SKY)
            rec       = await self.recommender.recommend(customer)
            primary   = rec["primary_product"]
            r_met     = rec["met_criteria"]
            r_unmet   = rec["unmet_criteria"]
            emi       = rec["monthly_emi"]
            tenure    = rec["tenure_months"]
            dsr_ratio = rec["dsr_ratio"]
            dsr_warn  = rec["dsr_warning"]
            all_q     = rec["all_qualifying"]
            r_range   = rec.get("score_range")

            if primary:
                rpc     = PRODUCT_COLOURS.get(primary, C.CYAN)
                p_range = (f"{r_range[0]:.2f}–{r_range[1]:.2f}" if r_range else "N/A")
                print(f"  {label('Primary')}  {rpc}{C.BOLD}{primary}{C.RESET}"
                      f"  {C.DIM}range {p_range}  conf {rec['confidence']}{C.RESET}")
                if emi > 0:
                    dsr_warn_txt = (
                        f"  {C.BRIGHT_RED}{C.BOLD}⚠  EXCEEDS 33.3% — credit officer review{C.RESET}"
                        if dsr_warn else ""
                    )
                    print(f"  {label('Monthly EMI')}  {C.BOLD}{naira(emi)}{C.RESET}"
                          f"  {C.DIM}over{C.RESET} {C.GOLD}{tenure} months{C.RESET}")
                    print(f"  {label('DSR')}  {dsr_bar(dsr_ratio)}{dsr_warn_txt}")
                else:
                    print(f"  {label('EMI / DSR')}  {C.DIM}N/A (investment or wealth product){C.RESET}")

                if all_q and len(all_q) > 1:
                    all_coloured = [f"{PRODUCT_COLOURS.get(p, C.CYAN)}{p}{C.RESET}" for p in all_q]
                    print(f"  {label('All qualify')}  {', '.join(all_coloured)}")
                for m in r_met:
                    print(bullet_ok(m))
                for u in r_unmet:
                    print(bullet_note(u))
            else:
                print(f"  {C.BRIGHT_YELLOW}⚠  No product qualifies for this profile.{C.RESET}")
                for r in rec.get("reasoning", []):
                    print(bullet_note(r))
            print()

    async def interactive_policy(self) -> None:
        """Interactive Policy Agent demo."""
        section("INTERACTIVE — Policy Agent", C.TEAL)
        print(f"  {C.DIM}Ask any question about Sentinel Bank policies.{C.RESET}")
        print(f"  {C.DIM}Type 'back' to return to the menu.{C.RESET}\n")

        samples = [
            "What is the SLA for transaction disputes?",
            "How is fraud risk calculated?",
            "Which merchant categories have the highest risk?",
            "What are the eligibility requirements for a car loan?",
            "What is the Debt Service Ratio cap for loans?",
            "What interest rate applies to a student loan?",
        ]
        print(f"  {C.TEAL}Sample questions:{C.RESET}")
        for s in samples:
            print(f"    {C.DIM}•  {s}{C.RESET}")
        print()

        while True:
            try:
                question = input(f"  {C.BRIGHT_CYAN}Your question:{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not question or question.lower() == "back":
                break

            print()
            start   = time.time()
            result  = await self.engine.query(question)
            elapsed = time.time() - start

            answer     = result.get("answer") or "No answer found."
            confidence = result.get("confidence", 0.0)
            sources    = result.get("sources",    [])
            grounded   = result.get("grounded",   False)
            chunks     = result.get("chunks_used", 0)
            source_str = sources[0]["source"] if sources else "None"

            grnd_colour = C.BRIGHT_GREEN if grounded else C.BRIGHT_RED
            grnd_icon   = "✔" if grounded else "✘"

            print(f"  {C.DIM}{'─' * 62}{C.RESET}")
            print(f"  {C.GOLD}{C.BOLD}Answer:{C.RESET}")
            words, line = answer.split(), "  "
            for w in words:
                if len(line) + len(w) + 1 > 72:
                    print(line)
                    line = "    " + w
                else:
                    line = line + (" " if line.strip() else "") + w
            if line.strip():
                print(line)
            print()
            print(f"  {label('Confidence')}  {confidence_bar(confidence)}")
            print(f"  {label('Grounded')}  {grnd_colour}{grnd_icon}  {grounded}{C.RESET}"
                  f"  {C.DIM}Source:{C.RESET}  {C.SKY}{source_str}{C.RESET}"
                  f"  {C.DIM}Chunks: {chunks}{C.RESET}")
            print(f"  {elapsed_str(elapsed)}")
            print()

    # =========================================================================
    # MAIN MENU
    # =========================================================================

    async def main_menu(self) -> None:
        """Show interactive main menu."""
        while True:
            section("SENTINEL BANK — AGENT DEMO MENU", C.GOLD)
            print(f"  {C.BLUE}{C.BOLD}  1  {C.RESET}  Run Automated Test Suite {C.DIM}(all agents){C.RESET}")
            print(f"  {C.BLUE}{C.BOLD}  2  {C.RESET}  Interactive Dispatcher Demo  {C.DIM}(complaint routing){C.RESET}")
            print(f"  {C.CORAL}{C.BOLD}  3  {C.RESET}  Interactive Sentinel Demo    {C.DIM}(fraud risk scoring){C.RESET}")
            print(f"  {C.MAGENTA}{C.BOLD}  4  {C.RESET}  Interactive Trajectory Demo  {C.DIM}(eligibility + recommendation){C.RESET}")
            print(f"  {C.TEAL}{C.BOLD}  5  {C.RESET}  Interactive Policy Demo      {C.DIM}(general queries){C.RESET}")
            print(f"  {C.DIM}  0    Exit{C.RESET}")
            print()

            try:
                choice = input(f"  {C.GOLD}{C.BOLD}Select option:{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                break

            if choice == "0":
                print(f"\n  {C.DIM}Exiting. Goodbye.{C.RESET}\n")
                break
            elif choice == "1":
                await self.run_all_tests()
            elif choice == "2":
                await self.interactive_dispatcher()
            elif choice == "3":
                await self.interactive_sentinel()
            elif choice == "4":
                await self.interactive_trajectory()
            elif choice == "5":
                await self.interactive_policy()
            else:
                print(f"  {C.RED}Invalid choice. Enter 0–5.{C.RESET}\n")


# =============================================================================
# Entry Point
# =============================================================================

async def main() -> None:
    """Initialize and launch the interactive demo / test runner."""
    tester = AgentTester()
    try:
        await tester.initialize()
    except Exception as e:
        print(f"\n{C.BRIGHT_RED}[ERROR] Failed to initialize RAG engine:{C.RESET}  {e}")
        print(f"{C.DIM}Make sure ingest_documents.py has been run first.{C.RESET}\n")
        sys.exit(1)

    if "--auto" in sys.argv:
        await tester.run_all_tests()
    else:
        await tester.main_menu()


if __name__ == "__main__":
    asyncio.run(main())