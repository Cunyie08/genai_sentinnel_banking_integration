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
    from app.rag.rag_system.rag_querys import RAGQueryEngine
    from app.rag.rag_system.chromadb_config import initialize_chromadb
    from app.rag.knowledge_base.generate_policies import (
        EXPECTED_SLA, DEPT_NAMES, MERCHANT_RISK, FLAG_WEIGHTS,
        LOAN_SIGNAL_SCORE_RANGES,
    )
    from app.rag.rag_system.recommend_product import recommend_product
except ImportError:
    try:
        from .rag_querys import RAGQueryEngine
        from .chromadb_config import initialize_chromadb
        from app.rag.knowledge_base.generate_policies import (
            EXPECTED_SLA, DEPT_NAMES, MERCHANT_RISK, FLAG_WEIGHTS,
            LOAN_SIGNAL_SCORE_RANGES,
        )
        from recommend_product import recommend_product
    except ImportError as e:
        print(f"\n[ERROR] Could not import RAG system: {e}")
        print("Make sure you have run ingest_documents.py first.")
        print("Run from project root: python -m app.rag.rag_system.test_agents")
        sys.exit(1)


# =============================================================================
# Terminal Colors & Styles
# =============================================================================

class C:
    """ANSI color and style codes for terminal output."""
    RESET    = "\033[0m"
    BOLD     = "\033[1m"
    DIM      = "\033[2m"
    ITALIC   = "\033[3m"
    UNDERLINE= "\033[4m"

    # Foreground colors
    BLACK    = "\033[30m"
    RED      = "\033[91m"
    GREEN    = "\033[92m"
    YELLOW   = "\033[93m"
    BLUE     = "\033[94m"
    MAGENTA  = "\033[95m"
    CYAN     = "\033[96m"
    WHITE    = "\033[97m"
    ORANGE   = "\033[38;5;214m"
    PURPLE   = "\033[38;5;141m"
    TEAL     = "\033[38;5;80m"
    LIME     = "\033[38;5;154m"
    PINK     = "\033[38;5;213m"
    GOLD     = "\033[38;5;220m"
    CORAL    = "\033[38;5;203m"

    # Background colors
    BG_RED   = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_BLUE  = "\033[44m"
    BG_CYAN  = "\033[46m"
    BG_BLACK = "\033[40m"
    BG_DARK  = "\033[48;5;235m"
    BG_NAVY  = "\033[48;5;17m"

    @staticmethod
    def green(s):    return f"{C.GREEN}{s}{C.RESET}"
    @staticmethod
    def red(s):      return f"{C.RED}{s}{C.RESET}"
    @staticmethod
    def yellow(s):   return f"{C.YELLOW}{s}{C.RESET}"
    @staticmethod
    def cyan(s):     return f"{C.CYAN}{s}{C.RESET}"
    @staticmethod
    def blue(s):     return f"{C.BLUE}{s}{C.RESET}"
    @staticmethod
    def bold(s):     return f"{C.BOLD}{s}{C.RESET}"
    @staticmethod
    def magenta(s):  return f"{C.MAGENTA}{s}{C.RESET}"
    @staticmethod
    def dim(s):      return f"{C.DIM}{s}{C.RESET}"
    @staticmethod
    def orange(s):   return f"{C.ORANGE}{s}{C.RESET}"
    @staticmethod
    def gold(s):     return f"{C.GOLD}{s}{C.RESET}"
    @staticmethod
    def teal(s):     return f"{C.TEAL}{s}{C.RESET}"
    @staticmethod
    def lime(s):     return f"{C.LIME}{s}{C.RESET}"


# =============================================================================
# Visual Rendering Helpers
# =============================================================================

WIDTH = 72  # terminal width for all decorations


def confidence_bar(score: float, width: int = 28, label: bool = True) -> str:
    """
    Render a segmented, coloured confidence bar.
    Uses block chars for a crisp filled look.
    """
    filled  = int(score * width)
    empty   = width - filled

    if score >= 0.85:
        colour = C.LIME
        fill_ch = "█"
    elif score >= 0.65:
        colour = C.YELLOW
        fill_ch = "▓"
    elif score >= 0.45:
        colour = C.ORANGE
        fill_ch = "▒"
    else:
        colour = C.RED
        fill_ch = "░"

    bar = f"{colour}{fill_ch * filled}{C.DIM}{'░' * empty}{C.RESET}"
    pct = f"{colour}{C.BOLD}{score:.1%}{C.RESET}" if label else ""
    return f"{bar}  {pct}" if label else bar


def risk_score_bar(score: float, max_score: int = 100, width: int = 30) -> str:
    """
    Render a coloured risk score bar (0-100).
    More dramatic colouring for fraud risk display.
    """
    ratio  = score / max_score
    filled = int(ratio * width)
    empty  = width - filled

    if ratio >= 0.80:
        colour  = C.RED
        fill_ch = "█"
        bg_ch   = "▄"
    elif ratio >= 0.60:
        colour  = C.ORANGE
        fill_ch = "▓"
        bg_ch   = "░"
    elif ratio >= 0.35:
        colour  = C.YELLOW
        fill_ch = "▒"
        bg_ch   = "░"
    else:
        colour  = C.LIME
        fill_ch = "▒"
        bg_ch   = "░"

    bar = f"{colour}{fill_ch * filled}{C.DIM}{bg_ch * empty}{C.RESET}"
    return f"{bar}  {colour}{C.BOLD}{score:>3}/100{C.RESET}"


def score_gauge(value: float, low: float = 0.0, high: float = 1.0,
                width: int = 30) -> str:
    """
    Render a loan signal score gauge with min/max boundaries displayed.
    A triangle marker (▲) shows the current value's position.
    """
    norm   = (value - low) / (high - low) if high != low else 0
    pos    = int(norm * width)
    bar    = [C.DIM + "─" + C.RESET] * width
    if 0 <= pos < width:
        bar[pos] = f"{C.GOLD}{C.BOLD}▲{C.RESET}"

    return (f"{C.DIM}{low:.2f}{C.RESET} "
            + "".join(bar)
            + f" {C.DIM}{high:.2f}{C.RESET}")


def pass_fail(ok: bool, verbose: bool = True) -> str:
    if ok:
        badge = f"{C.BG_GREEN}{C.BLACK}{C.BOLD}  PASS  {C.RESET}"
    else:
        badge = f"{C.BG_RED}{C.WHITE}{C.BOLD}  FAIL  {C.RESET}"
    return badge


def mini_tag(text: str, colour: str = C.CYAN) -> str:
    """Small inline tag like [HIGH] [CRITICAL]."""
    return f"{colour}{C.BOLD}[{text}]{C.RESET}"


def spinner_line(msg: str) -> None:
    """Print a styled loading line."""
    print(f"  {C.DIM}⟳  {msg}{C.RESET}")


def naira(amount: float) -> str:
    return f"₦{amount:,.0f}"


def elapsed_tag(seconds: float) -> str:
    if seconds < 1.0:
        return f"{C.DIM}({seconds * 1000:.0f}ms){C.RESET}"
    return f"{C.DIM}({seconds:.2f}s){C.RESET}"


# =============================================================================
# Section / Block Decorators
# =============================================================================

SECTION_STYLES = {
    "dispatcher": {
        "colour":  C.BLUE,
        "accent":  C.TEAL,
        "icon":    "⇄",
        "border":  "═",
        "corner":  "╔╗╚╝║",
    },
    "sentinel": {
        "colour":  C.RED,
        "accent":  C.ORANGE,
        "icon":    "⚠",
        "border":  "═",
        "corner":  "╔╗╚╝║",
    },
    "trajectory": {
        "colour":  C.MAGENTA,
        "accent":  C.PURPLE,
        "icon":    "◈",
        "border":  "═",
        "corner":  "╔╗╚╝║",
    },
    "policy": {
        "colour":  C.CYAN,
        "accent":  C.TEAL,
        "icon":    "§",
        "border":  "═",
        "corner":  "╔╗╚╝║",
    },
    "default": {
        "colour":  C.WHITE,
        "accent":  C.CYAN,
        "icon":    "◆",
        "border":  "═",
        "corner":  "╔╗╚╝║",
    },
}


def section(title: str, style_key: str = "default") -> None:
    """
    Print a bold, decorated section header with icon and double-line border.
    """
    s       = SECTION_STYLES.get(style_key, SECTION_STYLES["default"])
    col     = s["colour"]
    acc     = s["accent"]
    icon    = s["icon"]
    brdr    = s["border"]
    crnrs   = s["corner"]  # ╔╗╚╝║

    inner_w = WIDTH - 2
    label   = f"  {icon}  {title}  {icon}  "
    pad_tot = inner_w - len(label)
    pad_l   = pad_tot // 2
    pad_r   = pad_tot - pad_l
    top_row = f"{col}{crnrs[0]}{brdr * inner_w}{crnrs[1]}{C.RESET}"
    mid_row = (f"{col}{crnrs[4]}{acc}{brdr * pad_l}"
               f"{C.BOLD}{C.WHITE}{label}{C.RESET}"
               f"{acc}{brdr * pad_r}{col}{crnrs[4]}{C.RESET}")
    bot_row = f"{col}{crnrs[2]}{brdr * inner_w}{crnrs[3]}{C.RESET}"

    print(f"\n{top_row}")
    print(mid_row)
    print(f"{bot_row}\n")


def divider(colour: str = C.DIM, char: str = "─") -> None:
    """Thin dividing line."""
    print(f"  {colour}{char * (WIDTH - 4)}{C.RESET}")


def sub_header(title: str, colour: str = C.CYAN) -> None:
    """Small sub-section label."""
    print(f"\n  {colour}{'▸'} {C.BOLD}{title}{C.RESET}")


def bullet_ok(text: str) -> None:
    print(f"  {C.LIME}✔  {C.RESET}{text}")


def bullet_fail(text: str) -> None:
    print(f"  {C.RED}✘  {C.RESET}{text}")


def bullet_info(text: str) -> None:
    print(f"  {C.DIM}◦  {text}{C.RESET}")


def key_val(key: str, value: str, key_colour: str = C.CYAN,
            val_colour: str = C.WHITE) -> None:
    k = f"{key_colour}{C.BOLD}{key:<14}{C.RESET}"
    v = f"{val_colour}{value}{C.RESET}"
    print(f"  {k}  {v}")


def priority_badge(priority: str) -> str:
    colours = {
        "Critical": f"{C.BG_RED}{C.WHITE}{C.BOLD}  CRITICAL  {C.RESET}",
        "High":     f"{C.ORANGE}{C.BOLD}[ HIGH ]    {C.RESET}",
        "Medium":   f"{C.YELLOW}{C.BOLD}[ MEDIUM ]  {C.RESET}",
        "Low":      f"{C.TEAL}{C.BOLD}[ LOW ]     {C.RESET}",
    }
    return colours.get(priority, f"[ {priority} ]")


def risk_level_badge(level: str) -> str:
    badges = {
        "CRITICAL": f"{C.BG_RED}{C.WHITE}{C.BOLD}  !! CRITICAL !!  {C.RESET}",
        "HIGH":     f"{C.RED}{C.BOLD}[ ▲ HIGH ]      {C.RESET}",
        "MEDIUM":   f"{C.YELLOW}{C.BOLD}[ ~ MEDIUM ]    {C.RESET}",
        "LOW":      f"{C.LIME}{C.BOLD}[ ✔ LOW ]       {C.RESET}",
    }
    return badges.get(level, f"[ {level} ]")


def eligibility_badge(eligible: bool, recommendation: str) -> str:
    if eligible:
        return f"{C.BG_GREEN}{C.BLACK}{C.BOLD}  ✔ APPROVED  {C.RESET}"
    return f"{C.BG_RED}{C.WHITE}{C.BOLD}  ✘ NOT ELIGIBLE  {C.RESET}"


def dept_badge(dept_code: str) -> str:
    dept_colours = {
        "FRM": C.RED, "TSU": C.BLUE, "COC": C.YELLOW,
        "DCS": C.CYAN, "AOD": C.ORANGE, "CLS": C.TEAL,
    }
    col = dept_colours.get(dept_code, C.WHITE)
    return f"{col}{C.BOLD}[ {dept_code} ]{C.RESET}"


def progress_header(current: int, total: int,
                    label: str, colour: str = C.CYAN) -> None:
    """Show test N/M progress with mini bar."""
    ratio   = current / total if total else 0
    bar_w   = 16
    filled  = int(ratio * bar_w)
    bar     = f"{colour}{'▪' * filled}{C.DIM}{'·' * (bar_w - filled)}{C.RESET}"
    print(f"\n  {bar}  {colour}{C.BOLD}Test {current}/{total}{C.RESET}"
          f"  {C.WHITE}{label}{C.RESET}")


def summary_table_row(suite: str, passed: int, total: int,
                      colour: str = C.WHITE) -> None:
    rate    = passed / total if total else 0
    bar     = confidence_bar(rate, width=22, label=False)
    pct_str = f"{rate:.0%}"
    status  = (f"{C.LIME}{C.BOLD}✔ ALL PASS{C.RESET}"
               if passed == total else f"{C.RED}{C.BOLD}✘ {total - passed} FAILED{C.RESET}")
    print(f"  {colour}{C.BOLD}{suite:<14}{C.RESET}"
          f"  {passed}/{total}  {bar}  {pct_str:>5}  {status}")


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
# Banner
# =============================================================================

def print_banner() -> None:
    lines = [
        f"{C.CYAN}{'═' * WIDTH}{C.RESET}",
        f"{C.CYAN}║{C.RESET}{C.BOLD}{C.WHITE}{'  ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     ':^{WIDTH-2}}{C.RESET}{C.CYAN}║{C.RESET}",
        f"{C.CYAN}║{C.RESET}{C.TEAL}{'  SENTINEL BANK  ·  RAG AGENT DEMO & TEST SUITE  ·  v2.2':^{WIDTH-2}}{C.RESET}{C.CYAN}║{C.RESET}",
        f"{C.CYAN}║{C.RESET}{C.DIM}{'  Dispatcher  ·  Sentinel (Fraud)  ·  Trajectory  ·  Policy':^{WIDTH-2}}{C.RESET}{C.CYAN}║{C.RESET}",
        f"{C.CYAN}{'═' * WIDTH}{C.RESET}",
    ]
    print()
    for line in lines:
        print(line)
    print()


# =============================================================================
# Main Tester Class
# =============================================================================

class AgentTester:
    """Runs automated tests and interactive demos for all four agents."""

    def __init__(self) -> None:
        self.engine:  Optional[RAGQueryEngine] = None
        self.results: List[Dict]               = []

    # -------------------------------------------------------------------------
    # Initialization
    # -------------------------------------------------------------------------

    async def initialize(self) -> None:
        print_banner()

        print(f"  {C.DIM}Initializing ChromaDB and loading embedding model...{C.RESET}")
        start = time.time()

        client, config = initialize_chromadb()
        self.engine    = RAGQueryEngine(client, config)

        elapsed = time.time() - start
        print(f"  {C.LIME}✔  Engine ready  {elapsed_tag(elapsed)}{C.RESET}")

        stats = self.engine.retrieval.get_collection_stats()
        print()
        print(f"  {C.CYAN}{'─'*40}{C.RESET}")
        print(f"  {C.CYAN}{C.BOLD}Collection Stats{C.RESET}")
        print(f"  {C.CYAN}{'─'*40}{C.RESET}")
        key_val("Policy chunks", str(stats["policies"]), C.TEAL)
        key_val("FAQ chunks",    str(stats["faqs"]),     C.TEAL)
        key_val("Total chunks",  str(stats["total"]),    C.LIME)
        print()

    # =========================================================================
    # DISPATCHER TESTS
    # =========================================================================

    async def run_dispatcher_tests(self) -> int:
        section("DISPATCHER AGENT  —  Complaint Routing", "dispatcher")

        passed = 0
        for i, tc in enumerate(DISPATCHER_CASES, 1):
            progress_header(i, len(DISPATCHER_CASES), tc["name"], C.BLUE)
            print(f"  {C.DIM}Complaint: {tc['complaint']}{C.RESET}")

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

            divider()
            print(f"  {dept_badge(dept)}  {C.BOLD}{dept_name}{C.RESET}"
                  f"  {C.DIM}(expected: {tc['expected_dept']}){C.RESET}"
                  f"  {pass_fail(dept_ok)}")
            print(f"  {priority_badge(priority)}  SLA: {C.BOLD}{sla}h{C.RESET}")
            print()
            print(f"  {'Confidence':<14}  {confidence_bar(confidence)}")
            print(f"  {C.DIM}{'Method':<14}  {method}  |  Keywords: {keywords[:4]}{C.RESET}")
            print(f"  {C.DIM}{'Time':<14}  {elapsed_tag(elapsed)}{C.RESET}")
            print(f"\n  Overall   →  {pass_fail(ok)}")
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
        section("SENTINEL AGENT  —  Fraud Risk Scoring", "sentinel")

        passed = 0
        for i, tc in enumerate(SENTINEL_CASES, 1):
            txn = tc["transaction"]
            progress_header(i, len(SENTINEL_CASES), tc["name"], C.RED)
            flags_str = txn["fraud_explainability_trace"]
            print(f"  {C.DIM}Amount: {naira(txn['amount'])}"
                  f"  |  Merchant: {txn['merchant_category']}"
                  f"  |  Time: {txn['transaction_timestamp'].split()[1]}{C.RESET}")
            print(f"  {C.DIM}Flags : {flags_str}{C.RESET}")

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

            divider()

            # Risk score bar
            print(f"\n  {'Risk Score':<14}  {risk_score_bar(score)}")
            print(f"  {'Risk Level':<14}  {risk_level_badge(level)}"
                  f"  {C.DIM}(expected: {tc['expected_level']}){C.RESET}"
                  f"  {pass_fail(level_ok)}")

            # Breakdown sub-bars
            print()
            sub_header("Score Breakdown", C.ORANGE)
            bd_items = [
                ("Flags",    breakdown.get("flag_score",     0), 40, C.RED),
                ("Merchant", breakdown.get("merchant_risk",  0), 30, C.ORANGE),
                ("Timing",   breakdown.get("timing_risk",    0), 20, C.YELLOW),
            ]
            for bd_label, bd_val, bd_max, bd_col in bd_items:
                bd_ratio  = bd_val / bd_max if bd_max else 0
                bd_filled = int(bd_ratio * 20)
                bd_bar    = f"{bd_col}{'▪' * bd_filled}{C.DIM}{'·' * (20 - bd_filled)}{C.RESET}"
                print(f"    {C.DIM}{bd_label:<10}{C.RESET}  {bd_bar}  "
                      f"{bd_col}{bd_val}/{bd_max}{C.RESET}")

            print()
            block_str    = f"{C.RED}{C.BOLD}BLOCK NOW{C.RESET}" if block else f"{C.LIME}No block{C.RESET}"
            chall_str    = f"{C.YELLOW}Challenge required{C.RESET}" if challenge else f"{C.DIM}No challenge{C.RESET}"
            print(f"  {'Action':<14}  {C.YELLOW}{action}{C.RESET}")
            print(f"  {'Block?':<14}  {block_str}  |  {chall_str}")
            print(f"  {'Confidence':<14}  {confidence_bar(confidence)}")

            if result.get("policy_explanation"):
                expl = result["policy_explanation"][:130]
                print(f"\n  {C.DIM}Policy: {expl}...{C.RESET}")

            print(f"  {C.DIM}Time: {elapsed_tag(elapsed)}{C.RESET}")
            print(f"\n  Overall   →  {pass_fail(ok)}")
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
        section("TRAJECTORY AGENT  —  Eligibility + Recommendation", "trajectory")

        passed = 0
        for i, tc in enumerate(TRAJECTORY_CASES, 1):
            cd      = tc["customer_data"]
            product = tc["product"]

            score   = cd.get("Loan_signal_score", 0)
            inflow  = cd.get("monthly_inflow", 0)
            age     = cd.get("age", "N/A")
            uber    = cd.get("uber_tracker", 0)
            salary  = cd.get("salary_detected", False)
            acct    = cd.get("account_type", "savings")
            balance = cd.get("current_balance", 0)
            desired = cd.get("desired_loan_amount", 0)

            progress_header(i, len(TRAJECTORY_CASES), tc["name"], C.MAGENTA)

            # Profile summary panel
            divider(C.MAGENTA, "─")
            sub_header("Customer Profile", C.MAGENTA)
            print(f"    {C.CYAN}Age{C.RESET}          {age}   "
                  f"{C.CYAN}Account{C.RESET}  {acct.upper()}")
            print(f"    {C.CYAN}Inflow{C.RESET}       {naira(inflow):<16}  "
                  f"{C.CYAN}Balance{C.RESET}  {naira(balance)}")
            salary_str = f"{C.LIME}✔ Yes{C.RESET}" if salary else f"{C.DIM}✘ No{C.RESET}"
            uber_str    = f"{uber} "
            uber_stars  = (f"{C.TEAL}{'●' * min(uber, 15)}{C.RESET}" if uber > 0
                           else f"{C.DIM}no trips{C.RESET}")
            print(f"    {C.CYAN}Salary{C.RESET}       {salary_str:<24}  "
                  f"{C.CYAN}Uber trips{C.RESET}  {uber_str}{uber_stars}")
            if desired > 0:
                print(f"    {C.CYAN}Desired loan{C.RESET}  {naira(desired)}")

            # Score gauge
            print()
            print(f"    {C.CYAN}Signal score{C.RESET}  "
                  + score_gauge(score, 0.0, 1.0, width=32)
                  + f"  {C.GOLD}{C.BOLD}{score:.2f}{C.RESET}")

            # ── VALIDATION ───────────────────────────────────────────────────
            sub_header(f"[1]  VALIDATION  ←  {product}", C.PURPLE)
            v_start   = time.time()
            val       = await self.engine.validate_product_recommendation(cd, product)
            v_elapsed = time.time() - v_start

            eligible   = val["is_eligible"]
            recommend  = val["recommendation"]
            met        = val["met_criteria"]
            unmet      = val["unmet_criteria"]
            confidence = val["confidence"]
            score_range= val.get("score_range")
            policy     = val.get("policy_basis", "")

            val_ok     = recommend == tc["expected_result"]
            range_str  = (f"{score_range[0]:.2f} → {score_range[1]:.2f}"
                          if score_range else "N/A")

            print(f"\n    Result      {eligibility_badge(eligible, recommend)}"
                  f"  {C.DIM}(expected: {tc['expected_result']}){C.RESET}"
                  f"  {pass_fail(val_ok)}")
            print(f"    Score range {C.DIM}{range_str}{C.RESET}")
            print(f"    Confidence  {confidence_bar(confidence, width=22)}")
            print(f"    {elapsed_tag(v_elapsed)}")

            for m in met:
                print(f"    {C.LIME}✔{C.RESET}  {m}")
            for u in unmet:
                print(f"    {C.RED}✘{C.RESET}  {u}")
            if policy:
                print(f"\n    {C.DIM}Policy: {policy[:120]}...{C.RESET}")

            # ── RECOMMENDATION ────────────────────────────────────────────────
            sub_header("[2]  RECOMMENDATION  —  behavioral profile", C.PURPLE)
            r_start    = time.time()
            rec_result = recommend_product(cd)
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
                p_range = (f"{r_range[0]:.2f} → {r_range[1]:.2f}" if r_range else "N/A")
                print(f"\n    {C.LIME}{C.BOLD}▶  {primary}{C.RESET}"
                      f"  {C.DIM}(range {p_range}  confidence: {r_conf}){C.RESET}")

                if emi > 0:
                    dsr_col = C.RED if dsr_warn else C.LIME
                    dsr_note = (" ⚠ EXCEEDS CBN 33.3% CAP — refer to credit officer"
                                if dsr_warn else "  ✔ within CBN 33.3% cap")
                    # EMI visual bar
                    dsr_val  = float(str(dsr_ratio).replace("%", "")) / 100
                    emi_bar  = confidence_bar(min(dsr_val, 1.0), width=20, label=False)
                    print(f"    {'Monthly EMI':<14}  {C.BOLD}{naira(emi)}{C.RESET}"
                          f"  over {tenure} months")
                    print(f"    {'DSR':<14}  {dsr_col}{dsr_ratio}{C.RESET}"
                          f"  {emi_bar}  {dsr_col}{dsr_note}{C.RESET}")
                else:
                    print(f"    {'EMI / DSR':<14}  {C.DIM}N/A  (investment / wealth product){C.RESET}")

                if all_q and len(all_q) > 1:
                    products_str = "  ".join(
                        f"{C.TEAL}[{p}]{C.RESET}" for p in all_q
                    )
                    print(f"    {'Qualifying':<14}  {products_str}")

                for m in r_met:
                    print(f"    {C.LIME}+{C.RESET}  {m}")
                for u in r_unmet:
                    print(f"    {C.DIM}~  {u}{C.RESET}")

            else:
                print(f"\n    {C.YELLOW}⚠  No product qualifies — "
                      f"score {score:.2f} is below all product floors{C.RESET}")
                for r in rec_result.get("reasoning", []):
                    print(f"    {C.DIM}  {r}{C.RESET}")

            print(f"    {elapsed_tag(r_elapsed)}")

            ok = val_ok
            if ok:
                passed += 1

            print(f"\n  Overall   →  {pass_fail(ok)}")
            print()

            self.results.append({
                "suite":      "Trajectory",
                "name":       tc["name"],
                "passed":     ok,
                "confidence": confidence,
            })

        return passed

    # =========================================================================
    # POLICY TESTS
    # =========================================================================

    async def run_policy_tests(self) -> int:
        section("POLICY AGENT  —  General Knowledge Queries", "policy")

        passed = 0
        for i, tc in enumerate(POLICY_CASES, 1):
            progress_header(i, len(POLICY_CASES), tc["name"], C.CYAN)
            print(f"  {C.DIM}Q: {tc['question']}{C.RESET}")

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

            source_str = sources[0]["source"] if sources else "None"

            divider()
            print(f"  {'Confidence':<14}  {confidence_bar(confidence)}")

            grounded_str = (f"{C.LIME}✔ Grounded{C.RESET}"
                            if grounded else f"{C.RED}✘ Not grounded{C.RESET}")
            print(f"  {'Source':<14}  {source_str}  |  {grounded_str}")

            # Keyword hits as tags
            hits_display = "  ".join(
                f"{C.LIME}[{kw}]{C.RESET}" for kw in keyword_hits
            ) or f"{C.RED}none{C.RESET}"
            missed = [kw for kw in tc["keywords"] if kw not in answer_lower]
            miss_display = "  ".join(
                f"{C.DIM}[{kw}]{C.RESET}" for kw in missed
            )
            print(f"  {'Keywords':<14}  Hit: {hits_display}"
                  + (f"  Miss: {miss_display}" if missed else ""))

            # Answer preview — wrapped
            if answer:
                preview = answer[:220].replace("\n", " ")
                print()
                print(f"  {C.DIM}Answer preview:{C.RESET}")
                words = preview.split()
                line  = "  "
                for w in words:
                    if len(line) + len(w) + 1 > WIDTH - 2:
                        print(f"  {C.DIM}{line.strip()}{C.RESET}")
                        line = "    " + w
                    else:
                        line = line + (" " if line.strip() else "") + w
                if line.strip():
                    print(f"  {C.DIM}{line.strip()}...{C.RESET}")

            print(f"\n  {elapsed_tag(elapsed)}")
            print(f"  Overall   →  {pass_fail(ok)}")
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
        self.results.clear()
        total_start = time.time()

        d_pass = await self.run_dispatcher_tests()
        s_pass = await self.run_sentinel_tests()
        t_pass = await self.run_trajectory_tests()
        p_pass = await self.run_policy_tests()

        # ── Final Summary ─────────────────────────────────────────────────────
        section("FINAL  RESULTS", "default")

        suites = [
            ("Dispatcher", len(DISPATCHER_CASES), d_pass, C.BLUE),
            ("Sentinel",   len(SENTINEL_CASES),   s_pass, C.RED),
            ("Trajectory", len(TRAJECTORY_CASES), t_pass, C.MAGENTA),
            ("Policy",     len(POLICY_CASES),      p_pass, C.CYAN),
        ]

        total_tests  = sum(n for _, n, _, _ in suites)
        total_passed = sum(p for _, _, p, _ in suites)

        print(f"  {C.DIM}{'Agent Suite':<14}  {'P/T':<6}  {'Confidence bar':<34}  {'%':>5}  {'Status'}{C.RESET}")
        divider(C.DIM)

        for suite, total, p, col in suites:
            summary_table_row(suite, p, total, col)

        divider(C.DIM)

        overall_rate = total_passed / total_tests if total_tests else 0
        elapsed      = time.time() - total_start

        print(f"\n  {C.WHITE}{C.BOLD}{'Overall':<14}{C.RESET}  "
              f"{total_passed}/{total_tests}  "
              f"{confidence_bar(overall_rate, width=22)}  "
              f"{overall_rate:.0%}")
        print(f"  {C.DIM}Total time: {elapsed:.1f}s{C.RESET}")

        # Per-suite average RAG confidence
        print()
        sub_header("Average RAG Confidence by Suite", C.TEAL)
        by_suite: Dict[str, List[float]] = {}
        for r in self.results:
            by_suite.setdefault(r["suite"], []).append(r["confidence"])
        for suite_name, col in [(s, c) for s, _, _, c in suites]:
            scores = by_suite.get(suite_name, [])
            avg = sum(scores) / len(scores) if scores else 0
            print(f"    {col}{suite_name:<14}{C.RESET}  {confidence_bar(avg, width=22)}")

        print()
        if total_passed == total_tests:
            print(f"  {C.BG_GREEN}{C.BLACK}{C.BOLD}  ✔  ALL {total_tests} TESTS PASSED — AGENTS OPERATING CORRECTLY  {C.RESET}\n")
        else:
            failed = [r for r in self.results if not r["passed"]]
            print(f"  {C.BG_RED}{C.WHITE}{C.BOLD}  ✘  {len(failed)} TEST(S) FAILED — REVIEW ABOVE  {C.RESET}")
            print()
            for f in failed:
                print(f"    {C.RED}✘{C.RESET}  [{f['suite']}]  {f['name']}")
            print()

    # =========================================================================
    # INTERACTIVE DEMOS
    # =========================================================================

    async def interactive_dispatcher(self) -> None:
        section("INTERACTIVE  —  Dispatcher Agent", "dispatcher")
        print(f"  {C.DIM}Type a customer complaint and the Dispatcher Agent will route it.{C.RESET}")
        print(f"  {C.DIM}Type {C.WHITE}'back'{C.DIM} to return to the menu.{C.RESET}\n")
        samples = [
            "I transferred N50,000 to my cousin yesterday but it hasn't arrived",
            "My debit card was blocked after I tried to use it at a POS terminal",
            "Someone made an unauthorized transaction on my account last night",
            "The Sentinel Bank mobile app won't let me log in",
        ]
        print(f"  {C.TEAL}Sample complaints:{C.RESET}")
        for s in samples:
            print(f"    {C.DIM}▸ {s}{C.RESET}")
        print()

        while True:
            try:
                complaint = input(f"  {C.CYAN}▶  Complaint:{C.RESET} ").strip()
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

            divider(C.BLUE)
            print(f"  {dept_badge(dept)}  {C.BOLD}{dept_name}{C.RESET}")
            print(f"  {priority_badge(priority)}  SLA: {C.BOLD}{sla}h{C.RESET}")
            print()
            print(f"  {'Confidence':<14}  {confidence_bar(conf)}")
            print(f"  {C.DIM}{'Method':<14}  {method}  |  Keywords: {keywords[:5]}{C.RESET}")
            if reasoning:
                print(f"\n  {C.DIM}Policy basis: {reasoning[:220]}...{C.RESET}")
            print(f"  {elapsed_tag(elapsed)}")
            print()

    async def interactive_sentinel(self) -> None:
        section("INTERACTIVE  —  Sentinel Agent", "sentinel")
        print(f"  {C.DIM}Select a sample transaction to analyse.{C.RESET}\n")

        presets = [
            {
                "label": "Low risk  — grocery, daytime, small amount",
                "transaction": {
                    "fraud_explainability_trace": "normal_pattern",
                    "merchant_category": "grocery", "amount": 4_800,
                    "transaction_timestamp": "2026-02-22 11:20:00",
                },
            },
            {
                "label": "High risk  — fintech, 2am, ₦450K",
                "transaction": {
                    "fraud_explainability_trace": "high_amount_spike,mobile_channel_risk",
                    "merchant_category": "fintech", "amount": 450_000,
                    "transaction_timestamp": "2026-02-22 02:15:00",
                },
            },
            {
                "label": "Critical  — multiple failures, 3am, ₦520K",
                "transaction": {
                    "fraud_explainability_trace": "multiple_failures,high_amount_spike",
                    "merchant_category": "fintech", "amount": 520_000,
                    "transaction_timestamp": "2026-02-23 03:05:00",
                },
            },
            {
                "label": "Medium risk  — transport (Bolt), mobile channel",
                "transaction": {
                    "fraud_explainability_trace": "mobile_channel_risk",
                    "merchant_category": "transport", "amount": 85_000,
                    "transaction_timestamp": "2026-02-22 23:45:00",
                },
            },
        ]

        for idx, p in enumerate(presets, 1):
            risk_icons = {1: f"{C.LIME}✔", 2: f"{C.ORANGE}▲", 3: f"{C.RED}!!", 4: f"{C.YELLOW}~"}
            icon = risk_icons.get(idx, "·")
            print(f"  {icon}{C.RESET}  {C.CYAN}{idx}.{C.RESET}  {p['label']}")
        print(f"  {C.DIM}   0.  Back to menu{C.RESET}\n")

        while True:
            try:
                choice = input(f"  {C.CYAN}▶  Select (0-{len(presets)}):{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if choice == "0" or choice.lower() == "back":
                break
            try:
                idx = int(choice) - 1
                if not 0 <= idx < len(presets):
                    print(f"  {C.RED}Enter 0-{len(presets)}.{C.RESET}")
                    continue
            except ValueError:
                print(f"  {C.RED}Please enter a number.{C.RESET}")
                continue

            txn   = presets[idx]["transaction"]
            label = presets[idx]["label"]
            print(f"\n  {C.DIM}Analysing: {label}...{C.RESET}\n")

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

            divider(C.RED)
            print(f"\n  {'Risk Score':<14}  {risk_score_bar(score)}")
            print(f"  {'Risk Level':<14}  {risk_level_badge(level)}")

            print()
            sub_header("Breakdown", C.ORANGE)
            for bd_label, bd_val, bd_max, bd_col in [
                ("Flags",    bd.get("flag_score",    0), 40, C.RED),
                ("Merchant", bd.get("merchant_risk", 0), 30, C.ORANGE),
                ("Timing",   bd.get("timing_risk",   0), 20, C.YELLOW),
            ]:
                bd_ratio  = bd_val / bd_max if bd_max else 0
                bd_filled = int(bd_ratio * 18)
                bd_bar    = f"{bd_col}{'▪' * bd_filled}{C.DIM}{'·' * (18 - bd_filled)}{C.RESET}"
                print(f"    {C.DIM}{bd_label:<10}{C.RESET}  {bd_bar}  {bd_col}{bd_val}/{bd_max}{C.RESET}")

            print()
            print(f"  {'Action':<14}  {C.YELLOW}{action}{C.RESET}")
            block_str = (f"{C.BG_RED}{C.WHITE}{C.BOLD}  FREEZE ACCOUNT  {C.RESET}"
                         if block else f"{C.LIME}No block{C.RESET}")
            chall_str = (f"{C.YELLOW}Challenge required{C.RESET}"
                         if challenge else f"{C.DIM}No challenge{C.RESET}")
            print(f"  {'Block?':<14}  {block_str}  {chall_str}")
            if explanation:
                print(f"\n  {C.DIM}Policy: {explanation[:220]}...{C.RESET}")
            print(f"  {elapsed_tag(elapsed)}")
            print()

    async def interactive_trajectory(self) -> None:
        section("INTERACTIVE  —  Trajectory Agent", "trajectory")
        print(f"  {C.DIM}Enter a full customer profile derived from transaction history.{C.RESET}")
        print(f"  {C.DIM}Validates eligibility AND provides a proactive recommendation{C.RESET}")
        print(f"  {C.DIM}with EMI, DSR, and behavioral reasoning.{C.RESET}\n")

        products = ["Car Loan", "Investment Plan", "Personal Loan", "Student Loan", "Trust Fund"]
        for i, p in enumerate(products, 1):
            print(f"  {C.MAGENTA}{i}.{C.RESET}  {p}")
        print(f"  {C.DIM}0.  Back{C.RESET}\n")

        while True:
            try:
                p_choice = input(
                    f"  {C.MAGENTA}▶  Select product to validate (0-{len(products)}):{C.RESET} "
                ).strip()
            except (EOFError, KeyboardInterrupt):
                break
            if p_choice == "0" or p_choice.lower() == "back":
                break
            try:
                p_idx = int(p_choice) - 1
                if not 0 <= p_idx < len(products):
                    print(f"  {C.RED}Invalid. Enter 0-{len(products)}.{C.RESET}")
                    continue
                product = products[p_idx]
            except ValueError:
                print(f"  {C.RED}Please enter a number.{C.RESET}")
                continue

            print(f"\n  {C.DIM}Enter customer data (press Enter for defaults):{C.RESET}")
            try:
                def _inp(prompt, default):
                    v = input(f"  {C.DIM}{prompt}{C.RESET} [{C.CYAN}{default}{C.RESET}]: ").strip()
                    return v if v else str(default)

                loan_score     = float(_inp("Loan_signal_score (0.0-1.0)", "0.80"))
                monthly_inflow = float(_inp("Monthly inflow (₦)", "500000"))
                salary_str     = _inp("Salary detected? (y/n)", "y").lower()
                salary_detected= salary_str != "n"
                uber_tracker   = int(  _inp("Uber/Bolt trips in 90 days", "5"))
                age            = int(  _inp("Customer age", "30"))
                account_type   = _inp("Account type (savings/solo/current)", "savings")
                current_balance= float(_inp("Current balance (₦)", "200000"))
                desired_str    = _inp("Desired loan amount (₦, 0=auto)", "0")
                desired_amount = float(desired_str)

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

            # Gauge display
            print(f"  Signal score  " + score_gauge(loan_score, 0.0, 1.0, 32)
                  + f"  {C.GOLD}{C.BOLD}{loan_score:.2f}{C.RESET}")
            print()

            # ── VALIDATION ──────────────────────────────────────────────────
            sub_header(f"VALIDATION  ←  {product}", C.PURPLE)
            start   = time.time()
            val     = await self.engine.validate_product_recommendation(customer, product)
            elapsed = time.time() - start

            eligible   = val["is_eligible"]
            recommend  = val["recommendation"]
            met        = val["met_criteria"]
            unmet      = val["unmet_criteria"]
            confidence = val["confidence"]
            score_range= val.get("score_range")
            policy     = val.get("policy_basis", "")

            range_str  = (f"{score_range[0]:.2f} → {score_range[1]:.2f}"
                          if score_range else "N/A")

            print(f"\n  {eligibility_badge(eligible, recommend)}"
                  f"  Score range: {C.DIM}{range_str}{C.RESET}")
            print(f"  {'Confidence':<14}  {confidence_bar(confidence)}")
            for m in met:
                print(f"  {C.LIME}✔{C.RESET}  {m}")
            for u in unmet:
                print(f"  {C.RED}✘{C.RESET}  {u}")
            if policy:
                print(f"\n  {C.DIM}Policy: {policy[:220]}...{C.RESET}")
            print(f"  {elapsed_tag(elapsed)}")

            # ── RECOMMENDATION ───────────────────────────────────────────────
            print()
            sub_header("RECOMMENDATION  —  behavioral profile", C.PURPLE)
            rec        = recommend_product(customer)
            primary    = rec["primary_product"]
            r_met      = rec["met_criteria"]
            r_unmet    = rec["unmet_criteria"]
            emi        = rec["monthly_emi"]
            tenure     = rec["tenure_months"]
            dsr_ratio  = rec["dsr_ratio"]
            dsr_warn   = rec["dsr_warning"]
            all_q      = rec["all_qualifying"]
            r_range    = rec.get("score_range")

            if primary:
                p_range = (f"{r_range[0]:.2f} → {r_range[1]:.2f}" if r_range else "N/A")
                print(f"\n  {C.LIME}{C.BOLD}▶  {primary}{C.RESET}"
                      f"  {C.DIM}(range {p_range}  confidence: {rec['confidence']}){C.RESET}")
                if emi > 0:
                    dsr_col  = C.RED if dsr_warn else C.LIME
                    dsr_note = (" ⚠ EXCEEDS CBN cap — credit officer review"
                                if dsr_warn else "  ✔ within CBN 33.3% cap")
                    dsr_val  = float(str(dsr_ratio).replace("%", "")) / 100
                    print(f"  {'Monthly EMI':<14}  {C.BOLD}{naira(emi)}{C.RESET}  over {tenure} months")
                    print(f"  {'DSR':<14}  {dsr_col}{dsr_ratio}{C.RESET}"
                          + f"  {confidence_bar(min(dsr_val, 1.0), width=18, label=False)}"
                          + f"  {dsr_col}{dsr_note}{C.RESET}")
                else:
                    print(f"  {'EMI / DSR':<14}  {C.DIM}N/A  (investment / wealth product){C.RESET}")
                if all_q and len(all_q) > 1:
                    print(f"  {'Qualifying':<14}  "
                          + "  ".join(f"{C.TEAL}[{p}]{C.RESET}" for p in all_q))
                for m in r_met:
                    print(f"  {C.LIME}+{C.RESET}  {m}")
                for u in r_unmet:
                    print(f"  {C.DIM}~  {u}{C.RESET}")
            else:
                print(f"\n  {C.YELLOW}⚠  No product qualifies for this profile.{C.RESET}")
                for r in rec.get("reasoning", []):
                    print(f"  {C.DIM}  {r}{C.RESET}")
            print()

    async def interactive_policy(self) -> None:
        section("INTERACTIVE  —  Policy Agent", "policy")
        print(f"  {C.DIM}Ask any question about Sentinel Bank policies.{C.RESET}")
        print(f"  {C.DIM}Type {C.WHITE}'back'{C.DIM} to return to the menu.{C.RESET}\n")

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
            print(f"    {C.DIM}▸ {s}{C.RESET}")
        print()

        while True:
            try:
                question = input(f"  {C.CYAN}▶  Question:{C.RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not question or question.lower() == "back":
                break

            print()
            start   = time.time()
            result  = await self.engine.query(question)
            elapsed = time.time() - start

            answer    = result.get("answer") or "No answer found."
            confidence= result.get("confidence", 0.0)
            sources   = result.get("sources",    [])
            grounded  = result.get("grounded",   False)
            chunks    = result.get("chunks_used", 0)
            source_str= sources[0]["source"] if sources else "None"

            divider(C.CYAN)
            print(f"  {'Confidence':<14}  {confidence_bar(confidence)}")
            grnd = f"{C.LIME}✔ Grounded{C.RESET}" if grounded else f"{C.RED}✘ Not grounded{C.RESET}"
            print(f"  {'Source':<14}  {source_str}  |  Chunks: {chunks}  |  {grnd}")
            print()

            # Word-wrapped answer
            print(f"  {C.TEAL}{C.BOLD}Answer:{C.RESET}")
            words = answer.split()
            line  = "  "
            for w in words:
                if len(line) + len(w) + 1 > WIDTH:
                    print(f"  {line.strip()}")
                    line = "    " + w
                else:
                    line = line + (" " if line.strip() else "") + w
            if line.strip():
                print(f"  {line.strip()}")

            print(f"\n  {elapsed_tag(elapsed)}")
            print()

    # =========================================================================
    # MAIN MENU
    # =========================================================================

    async def main_menu(self) -> None:
        while True:
            section("SENTINEL BANK  —  AGENT DEMO MENU", "default")

            menu_items = [
                ("1", "Run Automated Test Suite  (all agents)",   C.WHITE),
                ("2", "Interactive Dispatcher    (complaint routing)", C.BLUE),
                ("3", "Interactive Sentinel      (fraud risk scoring)",  C.RED),
                ("4", "Interactive Trajectory    (eligibility + recommendation)", C.MAGENTA),
                ("5", "Interactive Policy        (general queries)", C.CYAN),
                ("0", "Exit",                                      C.DIM),
            ]

            for key, label, col in menu_items:
                print(f"  {col}{C.BOLD}{key}{C.RESET}  {label}")
            print()

            try:
                choice = input(f"  {C.WHITE}{C.BOLD}▶  Select option:{C.RESET} ").strip()
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
                print(f"  {C.RED}Invalid choice. Enter 0-5.{C.RESET}\n")


# =============================================================================
# Entry Point
# =============================================================================

async def main() -> None:
    tester = AgentTester()
    try:
        await tester.initialize()
    except Exception as e:
        print(f"\n{C.RED}[ERROR] Failed to initialize RAG engine:{C.RESET} {e}")
        print(f"{C.DIM}Make sure ingest_documents.py has been run first.{C.RESET}\n")
        sys.exit(1)

    if "--auto" in sys.argv:
        await tester.run_all_tests()
    else:
        await tester.main_menu()


if __name__ == "__main__":
    asyncio.run(main())