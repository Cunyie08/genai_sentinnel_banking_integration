# """
# Sentinel Bank - Simple Agent Demo
# ===================================
# Runs Dispatcher, Sentinel, and Trajectory agents against real DB rows.

# Usage:
#     python -m main
#     python main.py
# """

# import asyncio
# from sqlalchemy import text
# from app.core.orchestrator import Orchestrator
# from app.data.db_connections import get_async_session


# async def main():

#     # Boot orchestrator (DB + RAG + agents) 
#     orchestrator = Orchestrator()
#     await orchestrator.initialize()

#     engine = orchestrator.engine

#     # Fetch real IDs from the database 
#     async with get_async_session(engine) as session:
#         complaint_row = (await session.execute(
#             text("SELECT complaint_id FROM complaints LIMIT 1 OFFSET 250")
#         )).fetchone()

#         transaction_row = (await session.execute(
#             text("SELECT transaction_id FROM transactions LIMIT 1 OFFSET 250")
#         )).fetchone()

#         customer_row = (await session.execute(
#             text("SELECT customer_id FROM customers LIMIT 1 OFFSET 2033")
#         )).fetchone()

#     complaint_id   = complaint_row[0]
#     transaction_id = transaction_row[0]
#     customer_id    = customer_row[0]

#     print(f"\nComplaint ID   : {complaint_id}")
#     print(f"Transaction ID : {transaction_id}")
#     print(f"Customer ID    : {customer_id}")

#     # DISPATCHER 
#     result1 = await orchestrator.handle_request({
#         "type":         "complaint",
#         "complaint_id": complaint_id,
#     })
#     print("\n=== DISPATCHER OUTPUT ===")
#     print(result1)

#     # SENTINEL 
#     result2 = await orchestrator.handle_request({
#         "type":           "transaction",
#         "transaction_id": transaction_id,
#     })
#     print("\n=== SENTINEL OUTPUT ===")
#     print(result2)

#     # TRAJECTORY 
#     result3 = await orchestrator.handle_request({
#         "type":        "recommendation",
#         "customer_id": customer_id,
#     })
#     print("\n=== TRAJECTORY OUTPUT ===")
#     print(result3)


# if __name__ == "__main__":
#     asyncio.run(main())


"""
Sentinel Bank - Orchestrator Demo
==================================
Runs Dispatcher, Sentinel, and Trajectory agents against live DB rows.

Usage:
    python -m main
    python main.py
"""

import asyncio
import time
import os

import pandas as pd

from app.core.orchestrator import Orchestrator
from app.data.dataset_loader import _resolve_data_dir
from app.data.db_connections import get_async_session
from sqlalchemy import text as _text


# =============================================================================
# Terminal Colors
# =============================================================================

class C:
    RESET  = "\033[0m";  BOLD  = "\033[1m";  DIM    = "\033[2m"
    ITALIC = "\033[3m";  RED   = "\033[91m"; GREEN  = "\033[92m"
    YELLOW = "\033[93m"; BLUE  = "\033[94m"; MAGENTA= "\033[95m"
    CYAN   = "\033[96m"; WHITE = "\033[97m"

    BRIGHT_RED    = "\033[91;1m"; BRIGHT_GREEN  = "\033[92;1m"
    BRIGHT_YELLOW = "\033[93;1m"; BRIGHT_BLUE   = "\033[94;1m"
    BRIGHT_MAGENTA= "\033[95;1m"; BRIGHT_CYAN   = "\033[96;1m"
    BRIGHT_WHITE  = "\033[97;1m"

    ORANGE = "\033[38;5;208m"; PURPLE = "\033[38;5;135m"
    TEAL   = "\033[38;5;37m";  PINK   = "\033[38;5;213m"
    GOLD   = "\033[38;5;220m"; LIME   = "\033[38;5;118m"
    CORAL  = "\033[38;5;203m"; SKY    = "\033[38;5;117m"
    INDIGO = "\033[38;5;99m"

    BG_RED    = "\033[41m"; BG_GREEN  = "\033[42m"; BG_YELLOW = "\033[43m"
    BG_BLUE   = "\033[44m"; BG_DARK   = "\033[40m"; BG_ORANGE = "\033[48;5;208m"

    @staticmethod
    def green(s):  return f"{C.GREEN}{s}{C.RESET}"
    @staticmethod
    def red(s):    return f"{C.RED}{s}{C.RESET}"
    @staticmethod
    def yellow(s): return f"{C.YELLOW}{s}{C.RESET}"
    @staticmethod
    def cyan(s):   return f"{C.CYAN}{s}{C.RESET}"
    @staticmethod
    def bold(s):   return f"{C.BOLD}{s}{C.RESET}"
    @staticmethod
    def dim(s):    return f"{C.DIM}{s}{C.RESET}"
    @staticmethod
    def gold(s):   return f"{C.GOLD}{s}{C.RESET}"
    @staticmethod
    def orange(s): return f"{C.ORANGE}{s}{C.RESET}"
    @staticmethod
    def teal(s):   return f"{C.TEAL}{s}{C.RESET}"


# =============================================================================
# Colour maps
# =============================================================================

RISK_COLOURS = {
    "CRITICAL": C.BRIGHT_RED,
    "HIGH":     C.ORANGE,
    "MEDIUM":   C.BRIGHT_YELLOW,
    "LOW":      C.BRIGHT_GREEN,
}

PRIORITY_COLOURS = {
    "Critical": C.BRIGHT_RED,
    "High":     C.ORANGE,
    "Medium":   C.BRIGHT_CYAN,
    "Low":      C.BRIGHT_GREEN,
}

DEPT_COLOURS = {
    "FRM": C.BRIGHT_RED,
    "TSU": C.ORANGE,
    "COC": C.YELLOW,
    "DCS": C.SKY,
    "AOD": C.CYAN,
    "CLS": C.TEAL,
}

PRODUCT_COLOURS = {
    "Car Loan":        C.ORANGE,
    "Personal Loan":   C.BRIGHT_CYAN,
    "Student Loan":    C.LIME,
    "Investment Plan": C.GOLD,
    "Trust Fund":      C.PURPLE,
}


# =============================================================================
# Visual helpers
# =============================================================================

def confidence_bar(score: float, width: int = 25) -> str:
    try:
        score = float(score or 0)
    except (ValueError, TypeError):
        score = 0.0
    filled = int(score * width)
    empty  = width - filled
    if score >= 0.90:   fc = pc = C.BRIGHT_GREEN
    elif score >= 0.75: fc = pc = C.LIME
    elif score >= 0.60: fc = pc = C.BRIGHT_YELLOW
    elif score >= 0.40: fc = pc = C.ORANGE
    else:               fc = pc = C.BRIGHT_RED
    bar = f"{fc}{'█' * filled}{C.RESET}{C.DIM}{'░' * empty}{C.RESET}"
    return f"{bar}  {pc}{C.BOLD}{score:.1%}{C.RESET}"


def risk_score_bar(score, width: int = 20) -> str:
    score = int(score or 0)
    proportion = score / 100.0
    filled = int(proportion * width)
    empty  = width - filled
    if score >= 75:   colour = C.BRIGHT_RED
    elif score >= 50: colour = C.ORANGE
    elif score >= 30: colour = C.BRIGHT_YELLOW
    else:             colour = C.BRIGHT_GREEN
    bar = f"{colour}{'█' * filled}{C.RESET}{C.DIM}{'░' * empty}{C.RESET}"
    return f"{bar}  {colour}{C.BOLD}{score}/100{C.RESET}"


def dsr_bar(ratio_str: str, width: int = 20) -> str:
    try:
        val = float(str(ratio_str).strip("%")) / 100.0
    except (ValueError, AttributeError):
        return str(ratio_str)
    cap        = 0.333
    proportion = min(1.0, val / cap)
    filled     = int(proportion * width)
    empty      = width - filled
    if val > cap:     fc = pc = C.BRIGHT_RED
    elif val >= 0.25: fc = pc = C.ORANGE
    else:             fc = pc = C.BRIGHT_GREEN
    bar = f"{fc}{'█' * filled}{C.RESET}{C.DIM}{'░' * empty}{C.RESET}"
    return f"{bar}  {pc}{C.BOLD}{ratio_str}{C.RESET}  {C.DIM}/ {cap:.0%} cap{C.RESET}"


def score_gradient_bar(score: float, lo: float, hi: float, width: int = 20) -> str:
    score  = float(score or 0)
    norm   = max(0.0, min(1.0, (score - lo) / (hi - lo))) if hi != lo else 1.0
    filled = int(norm * width)
    empty  = width - filled
    colour = C.BRIGHT_GREEN if norm >= 0.5 else C.ORANGE
    bar    = f"{colour}{'▓' * filled}{C.RESET}{C.DIM}{'░' * empty}{C.RESET}"
    return f"{bar}  {colour}{C.BOLD}{score:.4f}{C.RESET}  {C.DIM}[{lo:.2f}–{hi:.2f}]{C.RESET}"


def naira(amount) -> str:
    try:    amount = float(amount or 0)
    except: amount = 0.0
    return f"{C.GOLD}₦{C.RESET}{C.BOLD}{amount:,.0f}{C.RESET}"


def elapsed_str(seconds: float) -> str:
    if seconds < 1.0:
        return f"{C.TEAL}{seconds * 1000:.0f}ms{C.RESET}"
    return f"{C.TEAL}{seconds:.2f}s{C.RESET}"


def lbl(text: str, colour: str = C.CYAN) -> str:
    return f"{colour}{C.BOLD}{text:<22}{C.RESET}"


def bullet_ok(text: str)   -> str: return f"  {C.BRIGHT_GREEN}✔{C.RESET}  {text}"
def bullet_fail(text: str) -> str: return f"  {C.BRIGHT_RED}✘{C.RESET}  {text}"
def bullet_note(text: str) -> str: return f"  {C.DIM}◦{C.RESET}  {C.DIM}{text}{C.RESET}"


def section(title: str, colour: str = C.CYAN) -> None:
    width = 70
    pad   = max(0, (width - len(title) - 4) // 2)
    print(f"\n{colour}{'═' * width}{C.RESET}")
    print(f"{colour}╠{'═' * pad}  {C.BOLD}{C.WHITE}{title}{C.RESET}{colour}  {'═' * pad}╣{C.RESET}")
    print(f"{colour}{'═' * width}{C.RESET}\n")


def sub_section(title: str, colour: str = C.DIM) -> None:
    width = 60
    pad   = max(0, (width - len(title) - 2) // 2)
    print(f"  {colour}{'─' * pad} {C.BOLD}{title}{C.RESET}{colour} {'─' * pad}{C.RESET}")


def result_badge(text: str, ok: bool) -> str:
    bg = C.BG_GREEN if ok else C.BG_RED
    fg = "\033[30m" if ok else C.WHITE
    return f"{bg}{fg}{C.BOLD} {text} {C.RESET}"


# =============================================================================
# Output renderers
# =============================================================================

def print_dispatcher_result(result: dict, elapsed: float) -> None:
    dept      = result.get("department_code",  "N/A")
    dept_name = result.get("department_name",  "Unknown")
    priority  = result.get("priority_level",   "N/A")
    sla       = result.get("sla_hours",        "N/A")
    conf      = float(result.get("confidence", 0.0) or 0.0)
    method    = result.get("routing_method",   "N/A")
    keywords  = result.get("keyword_matches",  [])
    reasoning = result.get("reasoning",        "")
    complaint = result.get("complaint_text",   "")
    sentiment = result.get("sentiment",        "")

    dc = DEPT_COLOURS.get(dept, C.CYAN)
    pc = PRIORITY_COLOURS.get(priority, C.WHITE)

    if complaint:
        print(f"  {C.DIM}Complaint  :{C.RESET}  {C.ITALIC}{str(complaint)[:120]}{C.RESET}")
    if sentiment:
        print(f"  {C.DIM}Sentiment  :{C.RESET}  {C.DIM}{sentiment}{C.RESET}")

    print(f"  {C.DIM}{'─' * 64}{C.RESET}")
    print(f"  {lbl('Department')}  {dc}{C.BOLD}{dept} - {dept_name}{C.RESET}")
    print(f"  {lbl('Priority')}  {pc}{C.BOLD}{priority}{C.RESET}"
          f"  {C.DIM}|{C.RESET}  SLA {C.GOLD}{C.BOLD}{sla}h{C.RESET}")
    print(f"  {lbl('Confidence')}  {confidence_bar(conf)}")
    print(f"  {lbl('Method')}  {C.TEAL}{method}{C.RESET}"
          f"  {C.DIM}|  Keywords:{C.RESET}  {C.SKY}{list(keywords)[:5]}{C.RESET}")
    if reasoning:
        print(f"  {lbl('Policy basis')}  {C.DIM}{str(reasoning)[:200]}{C.RESET}")
    print(f"  {lbl('Response time')}  {elapsed_str(elapsed)}")
    print()


def print_sentinel_result(result: dict, elapsed: float) -> None:
    score     = result.get("total_risk_score",   0)
    level     = result.get("risk_level",          "N/A")
    bd        = result.get("risk_breakdown",       {}) or {}
    action    = result.get("recommended_action",  "N/A")
    block     = result.get("should_block",         False)
    challenge = result.get("requires_challenge",   False)
    conf      = float(result.get("confidence",    0.0) or 0.0)
    expl      = result.get("policy_explanation",  "")
    ml_prob   = result.get("ml_probability")

    merchant   = result.get("merchant_category",         "")
    merch_name = result.get("merchant_name",              "")
    amount     = result.get("amount",                     0)
    timestamp  = result.get("transaction_timestamp",      "")
    flags      = result.get("fraud_explainability_trace", "")
    channel    = result.get("channel",                    "")

    rc = RISK_COLOURS.get(str(level).upper(), C.WHITE)

    if merchant or amount:
        print(f"  {C.DIM}Transaction :{C.RESET}"
              + (f"  {naira(amount)}" if amount else "")
              + (f"  {C.DIM}via{C.RESET} {C.TEAL}{channel}{C.RESET}" if channel else "")
              + (f"  {C.DIM}at{C.RESET} {C.TEAL}{merch_name} ({merchant}){C.RESET}" if merchant else "")
              + (f"  {C.DIM}@{C.RESET} {C.DIM}{str(timestamp)[:16]}{C.RESET}" if timestamp else ""))
    if flags:
        print(f"  {C.DIM}Fraud flags :{C.RESET}  {C.ORANGE}{str(flags)[:100]}{C.RESET}")

    print(f"  {C.DIM}{'─' * 64}{C.RESET}")
    print(f"  {lbl('Risk Score')}  {risk_score_bar(score)}")
    print(f"  {lbl('Risk Level')}  {rc}{C.BOLD}{level}{C.RESET}")

    f_score = bd.get("flag_score",    0)
    m_risk  = bd.get("merchant_risk", 0)
    t_risk  = bd.get("timing_risk",   0)
    print(f"  {lbl('Breakdown')}"
          f"  flags {C.ORANGE}{f_score:>3}{C.RESET}"
          f"  merchant {C.CORAL}{m_risk:>3}{C.RESET}"
          f"  timing {C.YELLOW}{t_risk:>3}{C.RESET}")

    if ml_prob is not None:
        print(f"  {lbl('ML Probability')}  {confidence_bar(float(ml_prob))}")

    print(f"  {lbl('Action')}  {C.BRIGHT_YELLOW}{action}{C.RESET}")
    block_s = (f"{C.BRIGHT_RED}{C.BOLD}YES - freeze account{C.RESET}"
               if block else f"{C.DIM}No{C.RESET}")
    chal_s  = f"{C.ORANGE}YES{C.RESET}" if challenge else f"{C.DIM}No{C.RESET}"
    print(f"  {lbl('Block?')}  {block_s}   {C.DIM}Challenge:{C.RESET}  {chal_s}")
    print(f"  {lbl('Confidence')}  {confidence_bar(conf)}")
    if expl:
        print(f"  {lbl('Policy basis')}  {C.DIM}{str(expl)[:200]}{C.RESET}")
    print(f"  {lbl('Response time')}  {elapsed_str(elapsed)}")
    print()


def print_trajectory_result(result: dict, elapsed: float) -> None:
    if result.get("status") == "error":
        print(f"  {C.BRIGHT_RED}✘  Agent error:{C.RESET}  {result.get('message', 'unknown')}")
        print(f"  {lbl('Response time')}  {elapsed_str(elapsed)}")
        print()
        return

    primary    = result.get("primary_product")
    all_q      = result.get("all_qualifying_products", []) or []
    emi        = result.get("monthly_emi",    0)
    tenure     = result.get("tenure_months",  0)
    dsr_ratio  = result.get("dsr_ratio",      "N/A")
    dsr_warn   = result.get("dsr_warning",    False)
    score_range= result.get("score_range")
    # confidence can be "High"/"Medium"/"Low" string or a float
    _conf_raw  = result.get("confidence", 0.0)
    _conf_map  = {"High": 0.90, "Medium": 0.65, "Low": 0.35}
    if isinstance(_conf_raw, str):
        conf = _conf_map.get(_conf_raw, 0.5)
    else:
        conf = float(_conf_raw or 0.0)
    met        = result.get("met_criteria",   []) or []
    unmet      = result.get("unmet_criteria", []) or []
    eligible   = result.get("is_eligible",    False)
    loan_score = float(result.get("loan_signal_score", 0.0) or 0.0)
    inflow     = result.get("monthly_inflow", 0.0)
    salary     = result.get("salary_detected", False)
    uber       = result.get("uber_tracker",   0)
    acct_type  = result.get("account_type",   "")
    balance    = result.get("current_balance", 0.0)
    reasoning  = result.get("reasoning",      "")

    policy_val    = result.get("policy_validation") or {}
    rag_eligible  = policy_val.get("is_eligible",   eligible)
    rag_recommend = policy_val.get("recommendation", "")
    rag_policy_b  = policy_val.get("policy_basis",   "")

    sub_section("① BEHAVIORAL PROFILE", C.SKY)
    r_lo, r_hi = score_range if score_range else (0.0, 1.0)
    print(f"  {lbl('Loan Signal Score')}  {score_gradient_bar(loan_score, r_lo, r_hi)}")
    print(f"  {lbl('Monthly Inflow')}  {naira(inflow)}"
          f"  {C.DIM}salary={C.RESET}{C.BRIGHT_GREEN if salary else C.DIM}{'✔' if salary else '✘'}{C.RESET}"
          f"  {C.DIM}uber/bolt trips={C.RESET} {C.GOLD}{uber}{C.RESET}")
    print(f"  {lbl('Account Type')}  {C.TEAL}{acct_type}{C.RESET}"
          f"  {C.DIM}balance{C.RESET} {naira(balance)}")

    sub_section("② RECOMMENDATION", C.ORANGE)
    if primary:
        rpc = PRODUCT_COLOURS.get(primary, C.CYAN)
        print(f"  {lbl('Primary Product')}  {rpc}{C.BOLD}{primary}{C.RESET}")
        print(f"  {lbl('Eligibility')}  {result_badge('ELIGIBLE' if eligible else 'NOT ELIGIBLE', eligible)}")
        print(f"  {lbl('Confidence')}  {confidence_bar(conf)}")

        if all_q and len(all_q) > 1:
            coloured = [f"{PRODUCT_COLOURS.get(p, C.CYAN)}{p}{C.RESET}" for p in all_q]
            print(f"  {lbl('All qualifying')}  {', '.join(coloured)}")

        if emi and float(emi or 0) > 0:
            dsr_warn_txt = (
                f"  {C.BRIGHT_RED}{C.BOLD}⚠  EXCEEDS 33.3% CBN CAP{C.RESET}"
                if dsr_warn else ""
            )
            print(f"  {lbl('Monthly EMI')}  {C.BOLD}{naira(emi)}{C.RESET}"
                  f"  {C.DIM}over{C.RESET}  {C.GOLD}{tenure} months{C.RESET}")
            print(f"  {lbl('DSR')}  {dsr_bar(str(dsr_ratio))}{dsr_warn_txt}")
        else:
            print(f"  {lbl('EMI / DSR')}  {C.DIM}N/A (investment or wealth product){C.RESET}")

        for m in met:
            print(bullet_ok(str(m)))
        for u in unmet:
            print(bullet_note(str(u)))
    else:
        print(f"  {C.BRIGHT_YELLOW}⚠  No product qualifies - "
              f"Loan_signal_score {C.BOLD}{loan_score:.4f}{C.RESET}"
              f"{C.BRIGHT_YELLOW} below all product floors{C.RESET}")

    if policy_val:
        sub_section("③ RAG POLICY VALIDATION", C.MAGENTA)
        print(f"  {lbl('RAG Eligibility')}  "
              f"{result_badge('ELIGIBLE' if rag_eligible else 'NOT ELIGIBLE', rag_eligible)}")
        if rag_recommend:
            print(f"  {lbl('RAG Decision')}  {C.DIM}{str(rag_recommend)[:120]}{C.RESET}")
        if rag_policy_b:
            print(f"  {lbl('Policy basis')}  {C.DIM}{str(rag_policy_b)[:200]}{C.RESET}")

    if reasoning:
        print(f"  {lbl('Reasoning')}  {C.DIM}{str(reasoning)[:200]}{C.RESET}")

    print(f"  {lbl('Response time')}  {elapsed_str(elapsed)}")
    print()


# =============================================================================
# Configuration  — change these to test different rows
# =============================================================================

NUM_ROWS   = 5    # how many rows to run
ROW_OFFSET = 250  # skip this many rows (250 = start at row 251, same as original script)


# =============================================================================
# Per-row runner
# =============================================================================

async def run_row(
    orchestrator:   Orchestrator,
    complaint_id:   str,
    transaction_id: str,
    customer_id:    str,
    row_num:        int,
) -> dict:
    summary = {
        "idx":           row_num,
        "dispatcher":    "skip",
        "sentinel":      "skip",
        "trajectory":    "skip",
        "errors":        [],
        "total_elapsed": 0.0,
    }
    row_start = time.time()

    print(f"\n{C.INDIGO}{'▓' * 70}{C.RESET}")
    print(f"{C.INDIGO}▓{C.RESET}  "
          f"{C.GOLD}{C.BOLD}  Row {row_num:>4} / {NUM_ROWS}  "
          f"{C.DIM}(offset {ROW_OFFSET}){C.RESET}"
          f"  {C.INDIGO}▓{C.RESET}")
    print(f"{C.INDIGO}{'▓' * 70}{C.RESET}")

    # DISPATCHER 
    section("DISPATCHER AGENT - Complaint Routing", C.BLUE)
    try:
        print(f"  {lbl('Row / ID')}  {C.DIM}row {row_num}{C.RESET}  {C.SKY}{complaint_id}{C.RESET}")
        start   = time.time()
        result1 = await orchestrator.handle_request({
            "type":         "complaint",
            "complaint_id": complaint_id,
        })
        print_dispatcher_result(result1, time.time() - start)
        summary["dispatcher"] = "ok"
    except Exception as exc:
        summary["errors"].append(f"[Row {row_num}] Dispatcher: {exc}")
        print(f"  {C.BRIGHT_RED}✘  SKIPPED - {exc}{C.RESET}\n")

    # SENTINEL 
    section("SENTINEL AGENT - Fraud Risk Scoring", C.CORAL)
    try:
        print(f"  {lbl('Row / ID')}  {C.DIM}row {row_num}{C.RESET}  {C.SKY}{transaction_id}{C.RESET}")
        start   = time.time()
        result2 = await orchestrator.handle_request({
            "type":           "transaction",
            "transaction_id": transaction_id,
        })
        print_sentinel_result(result2, time.time() - start)
        summary["sentinel"] = "ok"
    except Exception as exc:
        summary["errors"].append(f"[Row {row_num}] Sentinel: {exc}")
        print(f"  {C.BRIGHT_RED}✘  SKIPPED - {exc}{C.RESET}\n")

    # TRAJECTORY 
    section("TRAJECTORY AGENT - Eligibility + Recommendation", C.MAGENTA)
    try:
        print(f"  {lbl('Row / ID')}  {C.DIM}row {row_num}{C.RESET}  {C.SKY}{customer_id}{C.RESET}")
        start   = time.time()
        result3 = await orchestrator.handle_request({
            "type":        "recommendation",
            "customer_id": customer_id,
        })
        print_trajectory_result(result3, time.time() - start)
        summary["trajectory"] = "ok"
    except Exception as exc:
        summary["errors"].append(f"[Row {row_num}] Trajectory: {exc}")
        print(f"  {C.BRIGHT_RED}✘  SKIPPED - {exc}{C.RESET}\n")

    summary["total_elapsed"] = time.time() - row_start
    return summary


# =============================================================================
# Final summary
# =============================================================================

def print_final_summary(summaries: list, grand_elapsed: float) -> None:
    section("MULTI-ROW RUN SUMMARY", C.GOLD)

    total = len(summaries)
    ok_d = ok_s = ok_t = skip_d = skip_s = skip_t = 0
    all_errors = []

    for s in summaries:
        if s["dispatcher"] == "ok": ok_d   += 1
        else:                        skip_d += 1
        if s["sentinel"]   == "ok": ok_s   += 1
        else:                        skip_s += 1
        if s["trajectory"] == "ok": ok_t   += 1
        else:                        skip_t += 1
        all_errors.extend(s["errors"])

    def agent_row(name, colour, ok, skip):
        rate   = ok / total if total else 0
        bar    = confidence_bar(rate, width=20)
        status = (
            f"{C.BG_GREEN}\033[30m{C.BOLD}  ALL OK  {C.RESET}"
            if skip == 0
            else f"{C.BG_ORANGE}{C.WHITE}{C.BOLD}  {skip} SKIPPED  {C.RESET}"
        )
        print(f"  {colour}{C.BOLD}{name:<12}{C.RESET}  "
              f"{C.BRIGHT_GREEN}{ok}{C.RESET}{C.DIM}/{total} ok{C.RESET}  "
              f"{bar}  {status}")

    agent_row("Dispatcher",  C.BLUE,    ok_d, skip_d)
    agent_row("Sentinel",    C.CORAL,   ok_s, skip_s)
    agent_row("Trajectory",  C.MAGENTA, ok_t, skip_t)

    print()
    total_calls  = total * 3
    total_ok     = ok_d + ok_s + ok_t
    overall_rate = total_ok / total_calls if total_calls else 0
    print(f"  {C.BOLD}Rows tested  :{C.RESET}  {C.BOLD}{total}{C.RESET}"
          f"  {C.DIM}(offset {ROW_OFFSET}, {NUM_ROWS} rows){C.RESET}")
    print(f"  {C.BOLD}Agent calls  :{C.RESET}  {C.BOLD}{total_ok}/{total_calls}{C.RESET} succeeded")
    print(f"  {C.BOLD}Overall rate :{C.RESET}  {confidence_bar(overall_rate, width=30)}")
    print(f"  {C.BOLD}Total time   :{C.RESET}  {elapsed_str(grand_elapsed)}")

    if all_errors:
        print(f"\n  {C.BRIGHT_RED}{C.BOLD}Errors / skipped rows:{C.RESET}")
        for err in all_errors:
            print(f"    {C.RED}✘{C.RESET}  {C.DIM}{err}{C.RESET}")
    else:
        print(f"\n  {C.BG_GREEN}\033[30m{C.BOLD}  ✔  ALL AGENT CALLS SUCCEEDED  {C.RESET}")
    print()


# =============================================================================
# Main
# =============================================================================

async def main() -> None:
    print(f"\n{C.INDIGO}{'▓' * 70}{C.RESET}")
    print(f"{C.INDIGO}▓{C.RESET}  "
          f"{C.GOLD}{C.BOLD}{'Sentinel Bank - Orchestrator Multi-Row Run':^64}{C.RESET}"
          f"  {C.INDIGO}▓{C.RESET}")
    print(f"{C.INDIGO}▓{C.RESET}  "
          f"{C.DIM}{'Rows 1 → ' + str(NUM_ROWS) + '  |  3 agents per row  |  skip on error':^64}{C.RESET}"
          f"  {C.INDIGO}▓{C.RESET}")
    print(f"{C.INDIGO}{'▓' * 70}{C.RESET}\n")

    # Initialize orchestrator
    print(f"  {C.DIM}Initializing orchestrator …{C.RESET}")
    init_start   = time.time()
    orchestrator = Orchestrator()
    await orchestrator.initialize()
    print(f"  {C.BRIGHT_GREEN}✔  Orchestrator ready{C.RESET}  {elapsed_str(time.time() - init_start)}")

    # Fetch IDs from DB (guarantees they exist)
    print(f"  {C.DIM}Fetching row IDs from database …{C.RESET}")
    engine = orchestrator.engine
    async with get_async_session(engine) as session:
        c_rows = (await session.execute(
            _text(f"SELECT complaint_id FROM complaints LIMIT {NUM_ROWS} OFFSET {ROW_OFFSET}")
        )).fetchall()
        t_rows = (await session.execute(
            _text(f"SELECT transaction_id, customer_id FROM transactions LIMIT {NUM_ROWS} OFFSET {ROW_OFFSET}")
        )).fetchall()

    complaint_ids   = [r[0] for r in c_rows]
    transaction_ids = [r[0] for r in t_rows]
    customer_ids    = [r[1] for r in t_rows]

    print(f"  {C.BRIGHT_GREEN}✔  IDs loaded from DB{C.RESET}"
          f"  {C.DIM}complaints={len(complaint_ids)}"
          f"  transactions={len(transaction_ids)}"
          f"  customers={len(set(customer_ids))}{C.RESET}\n")

    # Run loop
    summaries   = []
    grand_start = time.time()

    for idx in range(NUM_ROWS):
        row_summary = await run_row(
            orchestrator,
            complaint_ids[idx],
            transaction_ids[idx],
            customer_ids[idx],   # real customer from DB — no hardcoded override
            idx + 1,
        )
        summaries.append(row_summary)

        d_icon = f"{C.BRIGHT_GREEN}✔{C.RESET}" if row_summary["dispatcher"] == "ok" else f"{C.RED}✘{C.RESET}"
        s_icon = f"{C.BRIGHT_GREEN}✔{C.RESET}" if row_summary["sentinel"]   == "ok" else f"{C.RED}✘{C.RESET}"
        t_icon = f"{C.BRIGHT_GREEN}✔{C.RESET}" if row_summary["trajectory"] == "ok" else f"{C.RED}✘{C.RESET}"
        print(
            f"  {C.DIM}Row {idx+1:>4} done{C.RESET}  "
            f"{C.BLUE}D{C.RESET}{d_icon}  "
            f"{C.CORAL}S{C.RESET}{s_icon}  "
            f"{C.MAGENTA}T{C.RESET}{t_icon}  "
            f"{elapsed_str(row_summary['total_elapsed'])}"
        )

    print_final_summary(summaries, time.time() - grand_start)


if __name__ == "__main__":
    asyncio.run(main())
