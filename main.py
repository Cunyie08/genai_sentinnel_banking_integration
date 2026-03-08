from app.core.orchestrator import Orchestrator
import asyncio


# Complaint Routing
async def main():
        orchestrator = Orchestrator()
        await orchestrator.initialize()
        
        complaint_id = (
            orchestrator.repo.dataset_loader.complaints
            .iloc[250]["complaint_id"]
        )

        complaint_request = {
            "type": "complaint",
            "department": "complaint",
            "complaint_id": complaint_id,
            "agent": "DispatcherAgent" 
        }

        result1 = await orchestrator.handle_request(complaint_request)
        print("\n=== DISPATCHER OUTPUT ===")
        print(result1)

        # Fraud Detection

        transaction_id = (
            orchestrator.repo.dataset_loader.transactions
            .iloc[250]["transaction_id"]
        )

        transaction_request = {
            "type": "transaction",
            "department": "transaction",
            "transaction_id": transaction_id,
            "agent": "SentinelAgent"
        }

        result2 = await orchestrator.handle_request(transaction_request)
        print("\n=== SENTINEL OUTPUT ===")
        print(result2)

        
        # Product Recommendation

        recommendation_id = (
            orchestrator.repo.dataset_loader.transactions
            .iloc[250]["customer_id"]
        )

        recommendation_request = {
            "type": "recommendation",
            "department": "recommendation",
            "customer_id": recommendation_id,
            "agent": "TrajectoryAgent"
        }

        result3 = await orchestrator.handle_request(recommendation_request)
        print("\n=== TRAJECTORY OUTPUT ===")
        print(result3)


if __name__ == "__main__":
    asyncio.run(main())

# """
# Sentinel Bank — Orchestrator Demo
# ==================================
# Runs Dispatcher, Sentinel, and Trajectory agents against live dataset rows
# with rich terminal output matching the test_agents demo style.

# Usage (from project root):
#     python -m app.main
#     python main.py
# """

# import asyncio
# import time

# from app.core.orchestrator import Orchestrator


# # =============================================================================
# # Terminal Colors — Extended Palette
# # =============================================================================

# class C:
#     """ANSI color codes for terminal output."""
#     RESET       = "\033[0m"
#     BOLD        = "\033[1m"
#     DIM         = "\033[2m"
#     ITALIC      = "\033[3m"

#     RED         = "\033[91m"
#     GREEN       = "\033[92m"
#     YELLOW      = "\033[93m"
#     BLUE        = "\033[94m"
#     MAGENTA     = "\033[95m"
#     CYAN        = "\033[96m"
#     WHITE       = "\033[97m"

#     BRIGHT_RED    = "\033[91;1m"
#     BRIGHT_GREEN  = "\033[92;1m"
#     BRIGHT_YELLOW = "\033[93;1m"
#     BRIGHT_BLUE   = "\033[94;1m"
#     BRIGHT_MAGENTA= "\033[95;1m"
#     BRIGHT_CYAN   = "\033[96;1m"
#     BRIGHT_WHITE  = "\033[97;1m"

#     ORANGE  = "\033[38;5;208m"
#     PURPLE  = "\033[38;5;135m"
#     TEAL    = "\033[38;5;37m"
#     PINK    = "\033[38;5;213m"
#     GOLD    = "\033[38;5;220m"
#     LIME    = "\033[38;5;118m"
#     CORAL   = "\033[38;5;203m"
#     SKY     = "\033[38;5;117m"
#     INDIGO  = "\033[38;5;99m"

#     BG_RED    = "\033[41m"
#     BG_GREEN  = "\033[42m"
#     BG_YELLOW = "\033[43m"
#     BG_BLUE   = "\033[44m"
#     BG_DARK   = "\033[40m"
#     BG_ORANGE = "\033[48;5;208m"

#     @staticmethod
#     def green(s):   return f"{C.GREEN}{s}{C.RESET}"
#     @staticmethod
#     def red(s):     return f"{C.RED}{s}{C.RESET}"
#     @staticmethod
#     def yellow(s):  return f"{C.YELLOW}{s}{C.RESET}"
#     @staticmethod
#     def cyan(s):    return f"{C.CYAN}{s}{C.RESET}"
#     @staticmethod
#     def bold(s):    return f"{C.BOLD}{s}{C.RESET}"
#     @staticmethod
#     def dim(s):     return f"{C.DIM}{s}{C.RESET}"
#     @staticmethod
#     def gold(s):    return f"{C.GOLD}{s}{C.RESET}"
#     @staticmethod
#     def orange(s):  return f"{C.ORANGE}{s}{C.RESET}"
#     @staticmethod
#     def teal(s):    return f"{C.TEAL}{s}{C.RESET}"


# # =============================================================================
# # Rendering helpers
# # =============================================================================

# RISK_COLOURS = {
#     "CRITICAL": C.BRIGHT_RED,
#     "HIGH":     C.ORANGE,
#     "MEDIUM":   C.BRIGHT_YELLOW,
#     "LOW":      C.BRIGHT_GREEN,
# }

# PRIORITY_COLOURS = {
#     "Critical": C.BRIGHT_RED,
#     "High":     C.ORANGE,
#     "Medium":   C.BRIGHT_CYAN,
#     "Low":      C.BRIGHT_GREEN,
# }

# DEPT_COLOURS = {
#     "FRM": C.BRIGHT_RED,
#     "TSU": C.ORANGE,
#     "COC": C.YELLOW,
#     "DCS": C.SKY,
#     "AOD": C.CYAN,
#     "CLS": C.TEAL,
# }

# PRODUCT_COLOURS = {
#     "Car Loan":        C.ORANGE,
#     "Personal Loan":   C.BRIGHT_CYAN,
#     "Student Loan":    C.LIME,
#     "Investment Plan": C.GOLD,
#     "Trust Fund":      C.PURPLE,
# }


# def confidence_bar(score: float, width: int = 25) -> str:
#     filled = int(score * width)
#     empty  = width - filled
#     if score >= 0.90:
#         fc = pc = C.BRIGHT_GREEN
#     elif score >= 0.75:
#         fc = pc = C.LIME
#     elif score >= 0.60:
#         fc = pc = C.BRIGHT_YELLOW
#     elif score >= 0.40:
#         fc = pc = C.ORANGE
#     else:
#         fc = pc = C.BRIGHT_RED
#     bar = f"{fc}{'█' * filled}{C.RESET}{C.DIM}{'░' * empty}{C.RESET}"
#     return f"{bar}  {pc}{C.BOLD}{score:.1%}{C.RESET}"


# def risk_score_bar(score: int, width: int = 20) -> str:
#     proportion = score / 100.0
#     filled     = int(proportion * width)
#     empty      = width - filled
#     if score >= 75:
#         colour = C.BRIGHT_RED
#     elif score >= 50:
#         colour = C.ORANGE
#     elif score >= 30:
#         colour = C.BRIGHT_YELLOW
#     else:
#         colour = C.BRIGHT_GREEN
#     bar = f"{colour}{'█' * filled}{C.RESET}{C.DIM}{'░' * empty}{C.RESET}"
#     return f"{bar}  {colour}{C.BOLD}{score}/100{C.RESET}"


# def dsr_bar(ratio_str: str, width: int = 20) -> str:
#     try:
#         val = float(str(ratio_str).strip("%")) / 100.0
#     except (ValueError, AttributeError):
#         return str(ratio_str)
#     cap        = 0.333
#     proportion = min(1.0, val / cap)
#     filled     = int(proportion * width)
#     empty      = width - filled
#     if val > cap:
#         fc = pc = C.BRIGHT_RED
#     elif val >= 0.25:
#         fc = pc = C.ORANGE
#     else:
#         fc = pc = C.BRIGHT_GREEN
#     bar = f"{fc}{'█' * filled}{C.RESET}{C.DIM}{'░' * empty}{C.RESET}"
#     return f"{bar}  {pc}{C.BOLD}{ratio_str}{C.RESET}  {C.DIM}/ {cap:.0%} cap{C.RESET}"


# def score_gradient_bar(score: float, lo: float, hi: float, width: int = 20) -> str:
#     norm   = max(0.0, min(1.0, (score - lo) / (hi - lo))) if hi != lo else 1.0
#     filled = int(norm * width)
#     empty  = width - filled
#     colour = C.BRIGHT_GREEN if norm >= 0.5 else C.ORANGE
#     bar    = f"{colour}{'▓' * filled}{C.RESET}{C.DIM}{'░' * empty}{C.RESET}"
#     return f"{bar}  {colour}{C.BOLD}{score:.2f}{C.RESET}  {C.DIM}[{lo:.2f}–{hi:.2f}]{C.RESET}"


# def naira(amount: float) -> str:
#     return f"{C.GOLD}₦{C.RESET}{C.BOLD}{amount:,.0f}{C.RESET}"


# def elapsed_str(seconds: float) -> str:
#     if seconds < 1.0:
#         return f"{C.TEAL}{seconds * 1000:.0f}ms{C.RESET}"
#     return f"{C.TEAL}{seconds:.2f}s{C.RESET}"


# def lbl(text: str, colour: str = C.CYAN) -> str:
#     return f"{colour}{C.BOLD}{text:<18}{C.RESET}"


# def bullet_ok(text: str)   -> str:
#     return f"  {C.BRIGHT_GREEN}✔{C.RESET}  {text}"


# def bullet_fail(text: str) -> str:
#     return f"  {C.BRIGHT_RED}✘{C.RESET}  {text}"


# def bullet_note(text: str) -> str:
#     return f"  {C.DIM}◦{C.RESET}  {C.DIM}{text}{C.RESET}"


# def section(title: str, colour: str = C.CYAN) -> None:
#     width = 70
#     pad   = max(0, (width - len(title) - 4) // 2)
#     print(f"\n{colour}{'═' * width}{C.RESET}")
#     print(f"{colour}╠{'═' * pad}  {C.BOLD}{C.WHITE}{title}{C.RESET}{colour}  {'═' * pad}╣{C.RESET}")
#     print(f"{colour}{'═' * width}{C.RESET}\n")


# def sub_section(title: str, colour: str = C.DIM) -> None:
#     width = 60
#     pad   = max(0, (width - len(title) - 2) // 2)
#     print(f"  {colour}{'─' * pad} {C.BOLD}{title}{C.RESET}{colour} {'─' * pad}{C.RESET}")


# def result_badge(text: str, ok: bool) -> str:
#     bg = C.BG_GREEN if ok else C.BG_RED
#     fg = "\033[30m" if ok else C.WHITE
#     return f"{bg}{fg}{C.BOLD} {text} {C.RESET}"


# def pass_fail(ok: bool) -> str:
#     if ok:
#         return f"{C.BG_GREEN}\033[30m{C.BOLD}  PASS  {C.RESET}"
#     return f"{C.BG_RED}{C.WHITE}{C.BOLD}  FAIL  {C.RESET}"


# # =============================================================================
# # Output renderers
# # =============================================================================

# def print_dispatcher_result(result: dict, elapsed: float) -> None:
#     """Pretty-print Dispatcher Agent output."""
#     dept      = result.get("department_code", "N/A")
#     dept_name = result.get("department_name", "Unknown")
#     priority  = result.get("priority_level", "N/A")
#     sla       = result.get("sla_hours", "N/A")
#     conf      = result.get("confidence", 0.0)
#     method    = result.get("routing_method", "N/A")
#     keywords  = result.get("keyword_matches", [])
#     reasoning = result.get("reasoning", "")
#     complaint = result.get("complaint_text", "")

#     dc = DEPT_COLOURS.get(dept, C.CYAN)
#     pc = PRIORITY_COLOURS.get(priority, C.WHITE)

#     if complaint:
#         print(f"  {C.DIM}Complaint  :{C.RESET}  {C.ITALIC}{complaint[:120]}{C.RESET}")

#     print(f"  {C.DIM}{'─' * 62}{C.RESET}")
#     print(f"  {lbl('Department')}  {dc}{C.BOLD}{dept} — {dept_name}{C.RESET}")
#     print(f"  {lbl('Priority')}  {pc}{C.BOLD}{priority}{C.RESET}"
#           f"  {C.DIM}|{C.RESET}  SLA {C.GOLD}{C.BOLD}{sla}h{C.RESET}")
#     print(f"  {lbl('Confidence')}  {confidence_bar(conf)}")
#     print(f"  {lbl('Method')}  {C.TEAL}{method}{C.RESET}"
#           f"  {C.DIM}|  Keywords:{C.RESET}  {C.SKY}{keywords[:5]}{C.RESET}")
#     if reasoning:
#         print(f"  {lbl('Policy basis')}  {C.DIM}{str(reasoning)[:200]}{C.RESET}")
#     print(f"  {lbl('Response time')}  {elapsed_str(elapsed)}")
#     print()


# def print_sentinel_result(result: dict, elapsed: float) -> None:
#     """Pretty-print Sentinel Agent fraud risk output."""
#     score     = result.get("total_risk_score", 0)
#     level     = result.get("risk_level", "N/A")
#     bd        = result.get("risk_breakdown", {})
#     action    = result.get("recommended_action", "N/A")
#     block     = result.get("should_block", False)
#     challenge = result.get("requires_challenge", False)
#     conf      = result.get("confidence", 0.0)
#     expl      = result.get("policy_explanation", "")

#     # Transaction summary fields (if available)
#     merchant  = result.get("merchant_category", "")
#     amount    = result.get("amount", 0)
#     timestamp = result.get("transaction_timestamp", "")
#     flags     = result.get("fraud_explainability_trace", "")

#     rc = RISK_COLOURS.get(level, C.WHITE)

#     if merchant or amount:
#         print(f"  {C.DIM}Transaction:{C.RESET}"
#               + (f"  {naira(amount)}" if amount else "")
#               + (f"  {C.DIM}merchant{C.RESET} {C.TEAL}{merchant}{C.RESET}" if merchant else "")
#               + (f"  {C.DIM}at{C.RESET} {C.DIM}{timestamp}{C.RESET}" if timestamp else "")
#               + (f"  {C.DIM}flags:{C.RESET} {C.ORANGE}{flags}{C.RESET}" if flags else ""))

#     print(f"  {C.DIM}{'─' * 62}{C.RESET}")
#     print(f"  {lbl('Risk Score')}  {risk_score_bar(score)}")
#     print(f"  {lbl('Risk Level')}  {rc}{C.BOLD}{level}{C.RESET}")

#     f_score = bd.get("flag_score", 0)
#     m_risk  = bd.get("merchant_risk", 0)
#     t_risk  = bd.get("timing_risk", 0)
#     print(f"  {lbl('Breakdown')}"
#           f"  flags {C.ORANGE}{f_score:>3}{C.RESET}"
#           f"  merchant {C.CORAL}{m_risk:>3}{C.RESET}"
#           f"  timing {C.YELLOW}{t_risk:>3}{C.RESET}")

#     print(f"  {lbl('Action')}  {C.BRIGHT_YELLOW}{action}{C.RESET}")
#     block_s = (f"{C.BRIGHT_RED}{C.BOLD}YES — freeze account{C.RESET}"
#                if block else f"{C.DIM}No{C.RESET}")
#     chal_s  = f"{C.ORANGE}YES{C.RESET}" if challenge else f"{C.DIM}No{C.RESET}"
#     print(f"  {lbl('Block?')}  {block_s}   {C.DIM}Challenge:{C.RESET}  {chal_s}")
#     print(f"  {lbl('Confidence')}  {confidence_bar(conf)}")
#     if expl:
#         print(f"  {lbl('Policy basis')}  {C.DIM}{str(expl)[:200]}{C.RESET}")
#     print(f"  {lbl('Response time')}  {elapsed_str(elapsed)}")
#     print()


# def print_trajectory_result(result: dict, elapsed: float) -> None:
#     """Pretty-print Trajectory Agent recommendation output."""
#     # ── Validation section ────────────────────────────────────────────────────
#     validation = result.get("validation", {})
#     if validation:
#         product    = validation.get("product", result.get("recommended_product", "N/A"))
#         eligible   = validation.get("is_eligible", False)
#         recommend  = validation.get("recommendation", "N/A")
#         met        = validation.get("met_criteria", [])
#         unmet      = validation.get("unmet_criteria", [])
#         conf       = validation.get("confidence", 0.0)
#         score_range= validation.get("score_range")
#         policy_b   = validation.get("policy_basis", "")
#         loan_score = result.get("Loan_signal_score", 0.0)

#         pc = PRODUCT_COLOURS.get(product, C.CYAN)
#         sub_section(f"① VALIDATION — {product}", pc)

#         r_lo, r_hi = score_range if score_range else (0.0, 1.0)
#         print(f"  {lbl('Score range')}  {score_gradient_bar(loan_score, r_lo, r_hi)}")
#         print(f"  {lbl('Eligibility')}  {result_badge(recommend, eligible)}")
#         print(f"  {lbl('Confidence')}  {confidence_bar(conf)}")
#         for m in met:
#             print(bullet_ok(m))
#         for u in unmet:
#             print(bullet_fail(u))
#         if policy_b:
#             print(f"  {lbl('Policy basis')}  {C.DIM}{str(policy_b)[:200]}{C.RESET}")

#     # ── Recommendation section ────────────────────────────────────────────────
#     recommendation = result.get("recommendation", {})
#     if recommendation:
#         primary   = recommendation.get("primary_product")
#         r_met     = recommendation.get("met_criteria", [])
#         r_unmet   = recommendation.get("unmet_criteria", [])
#         r_conf    = recommendation.get("confidence", 0.0)
#         emi       = recommendation.get("monthly_emi", 0)
#         tenure    = recommendation.get("tenure_months", 0)
#         dsr_ratio = recommendation.get("dsr_ratio", "N/A")
#         dsr_warn  = recommendation.get("dsr_warning", False)
#         all_q     = recommendation.get("all_qualifying", [])
#         r_range   = recommendation.get("score_range")

#         sub_section("② RECOMMENDATION — behavioral profile", C.SKY)

#         if primary:
#             rpc     = PRODUCT_COLOURS.get(primary, C.CYAN)
#             p_range = (f"{r_range[0]:.2f}–{r_range[1]:.2f}" if r_range else "N/A")
#             print(f"  {lbl('Recommended')}  {rpc}{C.BOLD}{primary}{C.RESET}"
#                   f"  {C.DIM}range {p_range}  conf {r_conf}{C.RESET}")

#             if emi and emi > 0:
#                 dsr_warn_txt = (
#                     f"  {C.BRIGHT_RED}{C.BOLD}⚠  EXCEEDS 33.3% CBN CAP — credit officer review{C.RESET}"
#                     if dsr_warn else ""
#                 )
#                 print(f"  {lbl('Monthly EMI')}  {C.BOLD}{naira(emi)}{C.RESET}"
#                       f"  {C.DIM}over{C.RESET}  {C.GOLD}{tenure} months{C.RESET}")
#                 print(f"  {lbl('DSR')}  {dsr_bar(str(dsr_ratio))}{dsr_warn_txt}")
#             else:
#                 print(f"  {lbl('EMI / DSR')}  {C.DIM}N/A (investment or wealth product){C.RESET}")

#             if all_q and len(all_q) > 1:
#                 all_coloured = [f"{PRODUCT_COLOURS.get(p, C.CYAN)}{p}{C.RESET}" for p in all_q]
#                 print(f"  {lbl('All qualifying')}  {', '.join(all_coloured)}")

#             for m in r_met:
#                 print(bullet_ok(m))
#             for u in r_unmet:
#                 print(bullet_note(u))
#         else:
#             score = result.get("Loan_signal_score", 0.0)
#             print(f"  {C.BRIGHT_YELLOW}⚠  No product qualifies —"
#                   f" Loan_signal_score {C.BOLD}{score:.2f}{C.RESET}"
#                   f"{C.BRIGHT_YELLOW} is below all product floors{C.RESET}")
#             for r in recommendation.get("reasoning", []):
#                 print(bullet_note(r))

#     # ── Customer profile summary (if no nested keys, render flat result) ──────
#     if not validation and not recommendation:
#         # Fallback: render whatever the agent returned
#         for k, v in result.items():
#             print(f"  {lbl(str(k)[:18])}  {C.DIM}{str(v)[:80]}{C.RESET}")

#     print(f"  {lbl('Response time')}  {elapsed_str(elapsed)}")
#     print()


# # =============================================================================
# # Configuration
# # =============================================================================

# ROW_START = 1    # inclusive
# ROW_END   = 10   # inclusive  →  indices 1 … 10


# # =============================================================================
# # Per-row runner
# # =============================================================================

# async def run_row(orchestrator: Orchestrator, idx: int) -> dict:
#     """
#     Run all three agents for dataset row `idx`.

#     Returns a summary dict:
#         {
#             "idx":          int,
#             "dispatcher":   "ok" | "skip",
#             "sentinel":     "ok" | "skip",
#             "trajectory":   "ok" | "skip",
#             "errors":       [str, ...],
#             "total_elapsed": float,
#         }
#     """
#     summary = {
#         "idx":           idx,
#         "dispatcher":    "skip",
#         "sentinel":      "skip",
#         "trajectory":    "skip",
#         "errors":        [],
#         "total_elapsed": 0.0,
#     }
#     row_start = time.time()

#     complaints   = orchestrator.repo.dataset_loader.complaints
#     transactions = orchestrator.repo.dataset_loader.transactions

#     # ── Row header ────────────────────────────────────────────────────────────
#     print(f"\n{C.INDIGO}{'▓' * 70}{C.RESET}")
#     print(f"{C.INDIGO}▓{C.RESET}  "
#           f"{C.GOLD}{C.BOLD}  Row {idx:>3} / {ROW_END}  "
#           f"{C.DIM}({ROW_END - ROW_START + 1} rows total){C.RESET}"
#           f"  {C.INDIGO}▓{C.RESET}")
#     print(f"{C.INDIGO}{'▓' * 70}{C.RESET}")

#     # =========================================================================
#     # 1. DISPATCHER
#     # =========================================================================
#     section("DISPATCHER AGENT — Complaint Routing", C.BLUE)
#     try:
#         complaint_id = complaints.iloc[idx]["complaint_id"]
#         print(f"  {lbl('Row / ID')}  {C.DIM}idx {idx}{C.RESET}  {C.SKY}{complaint_id}{C.RESET}")

#         start   = time.time()
#         result1 = await orchestrator.handle_request({
#             "type":         "complaint",
#             "department":   "complaint",
#             "complaint_id": complaint_id,
#             "agent":        "DispatcherAgent",
#         })
#         print_dispatcher_result(result1, time.time() - start)
#         summary["dispatcher"] = "ok"

#     except Exception as exc:
#         msg = f"[Row {idx}] Dispatcher: {exc}"
#         summary["errors"].append(msg)
#         print(f"  {C.BRIGHT_RED}✘  SKIPPED — {exc}{C.RESET}\n")

#     # =========================================================================
#     # 2. SENTINEL
#     # =========================================================================
#     section("SENTINEL AGENT — Fraud Risk Scoring", C.CORAL)
#     try:
#         transaction_id = transactions.iloc[idx]["transaction_id"]
#         print(f"  {lbl('Row / ID')}  {C.DIM}idx {idx}{C.RESET}  {C.SKY}{transaction_id}{C.RESET}")

#         start   = time.time()
#         result2 = await orchestrator.handle_request({
#             "type":           "transaction",
#             "department":     "transaction",
#             "transaction_id": transaction_id,
#             "agent":          "SentinelAgent",
#         })
#         print_sentinel_result(result2, time.time() - start)
#         summary["sentinel"] = "ok"

#     except Exception as exc:
#         msg = f"[Row {idx}] Sentinel: {exc}"
#         summary["errors"].append(msg)
#         print(f"  {C.BRIGHT_RED}✘  SKIPPED — {exc}{C.RESET}\n")

#     # =========================================================================
#     # 3. TRAJECTORY
#     # =========================================================================
#     section("TRAJECTORY AGENT — Eligibility + Recommendation", C.MAGENTA)
#     try:
#         customer_id = transactions.iloc[idx]["customer_id"]
#         print(f"  {lbl('Row / ID')}  {C.DIM}idx {idx}{C.RESET}  {C.SKY}{customer_id}{C.RESET}")

#         start   = time.time()
#         result3 = await orchestrator.handle_request({
#             "type":        "recommendation",
#             "department":  "recommendation",
#             "customer_id": customer_id,
#             "agent":       "TrajectoryAgent",
#         })
#         print_trajectory_result(result3, time.time() - start)
#         summary["trajectory"] = "ok"

#     except Exception as exc:
#         msg = f"[Row {idx}] Trajectory: {exc}"
#         summary["errors"].append(msg)
#         print(f"  {C.BRIGHT_RED}✘  SKIPPED — {exc}{C.RESET}\n")

#     summary["total_elapsed"] = time.time() - row_start
#     return summary


# # =============================================================================
# # Final summary table
# # =============================================================================

# def print_final_summary(summaries: list, grand_elapsed: float) -> None:
#     """Print a compact pass/skip/error table across all rows."""
#     section("MULTI-ROW RUN SUMMARY", C.GOLD)

#     total      = len(summaries)
#     ok_d = ok_s = ok_t = 0
#     skip_d = skip_s = skip_t = 0
#     all_errors = []

#     for s in summaries:
#         if s["dispatcher"]  == "ok": ok_d   += 1
#         else:                         skip_d += 1
#         if s["sentinel"]    == "ok": ok_s   += 1
#         else:                         skip_s += 1
#         if s["trajectory"]  == "ok": ok_t   += 1
#         else:                         skip_t += 1
#         all_errors.extend(s["errors"])

#     def agent_row(name: str, colour: str, ok: int, skip: int) -> None:
#         rate = ok / total if total else 0
#         bar  = confidence_bar(rate, width=20)
#         status = (
#             f"{C.BG_GREEN}\033[30m{C.BOLD}  ALL OK  {C.RESET}"
#             if skip == 0
#             else f"{C.BG_ORANGE}{C.WHITE}{C.BOLD}  {skip} SKIPPED  {C.RESET}"
#         )
#         print(f"  {colour}{C.BOLD}{name:<12}{C.RESET}  "
#               f"{C.BRIGHT_GREEN}{ok}{C.RESET}{C.DIM}/{total} ok{C.RESET}  "
#               f"{bar}  {status}")

#     agent_row("Dispatcher",  C.BLUE,    ok_d, skip_d)
#     agent_row("Sentinel",    C.CORAL,   ok_s, skip_s)
#     agent_row("Trajectory",  C.MAGENTA, ok_t, skip_t)

#     print()
#     total_calls  = total * 3
#     total_ok     = ok_d + ok_s + ok_t
#     overall_rate = total_ok / total_calls if total_calls else 0
#     print(f"  {C.BOLD}Rows tested  :{C.RESET}  {C.BOLD}{total}{C.RESET}"
#           f"  {C.DIM}(indices {ROW_START}–{ROW_END}){C.RESET}")
#     print(f"  {C.BOLD}Agent calls  :{C.RESET}  {C.BOLD}{total_ok}/{total_calls}{C.RESET} succeeded")
#     print(f"  {C.BOLD}Overall rate :{C.RESET}  {confidence_bar(overall_rate, width=30)}")
#     print(f"  {C.BOLD}Total time   :{C.RESET}  {elapsed_str(grand_elapsed)}")

#     if all_errors:
#         print(f"\n  {C.BRIGHT_RED}{C.BOLD}Errors / skipped rows:{C.RESET}")
#         for err in all_errors:
#             print(f"    {C.RED}✘{C.RESET}  {C.DIM}{err}{C.RESET}")
#     else:
#         print(f"\n  {C.BG_GREEN}\033[30m{C.BOLD}  ✔  ALL AGENT CALLS SUCCEEDED ACROSS ALL ROWS  {C.RESET}")

#     print()


# # =============================================================================
# # Main
# # =============================================================================

# async def main() -> None:
#     # ── Banner ────────────────────────────────────────────────────────────────
#     print(f"\n{C.INDIGO}{'▓' * 70}{C.RESET}")
#     print(f"{C.INDIGO}▓{C.RESET}  "
#           f"{C.GOLD}{C.BOLD}{'Sentinel Bank — Orchestrator Multi-Row Run':^64}{C.RESET}"
#           f"  {C.INDIGO}▓{C.RESET}")
#     print(f"{C.INDIGO}▓{C.RESET}  "
#           f"{C.DIM}{'Rows ' + str(ROW_START) + ' → ' + str(ROW_END) + '  |  3 agents per row  |  skip on error':^64}{C.RESET}"
#           f"  {C.INDIGO}▓{C.RESET}")
#     print(f"{C.INDIGO}{'▓' * 70}{C.RESET}\n")

#     # ── Initialize (once, outside the loop) ───────────────────────────────────
#     print(f"  {C.DIM}Initializing orchestrator …{C.RESET}")
#     init_start   = time.time()
#     orchestrator = Orchestrator()
#     await orchestrator.initialize()
#     print(f"  {C.BRIGHT_GREEN}✔  Ready{C.RESET}  {elapsed_str(time.time() - init_start)}\n")

#     # ── Multi-row loop ────────────────────────────────────────────────────────
#     summaries   = []
#     grand_start = time.time()

#     for idx in range(ROW_START, ROW_END + 1):
#         row_summary = await run_row(orchestrator, idx)
#         summaries.append(row_summary)

#         # Compact per-row status line printed after each row
#         d_icon = f"{C.BRIGHT_GREEN}✔{C.RESET}" if row_summary["dispatcher"] == "ok" else f"{C.RED}✘{C.RESET}"
#         s_icon = f"{C.BRIGHT_GREEN}✔{C.RESET}" if row_summary["sentinel"]   == "ok" else f"{C.RED}✘{C.RESET}"
#         t_icon = f"{C.BRIGHT_GREEN}✔{C.RESET}" if row_summary["trajectory"] == "ok" else f"{C.RED}✘{C.RESET}"
#         print(
#             f"  {C.DIM}Row {idx:>3} done{C.RESET}  "
#             f"{C.BLUE}D{C.RESET}{d_icon}  "
#             f"{C.CORAL}S{C.RESET}{s_icon}  "
#             f"{C.MAGENTA}T{C.RESET}{t_icon}  "
#             f"{elapsed_str(row_summary['total_elapsed'])}"
#         )

#     # ── Final summary ─────────────────────────────────────────────────────────
#     print_final_summary(summaries, time.time() - grand_start)


# if __name__ == "__main__":
#     asyncio.run(main())
