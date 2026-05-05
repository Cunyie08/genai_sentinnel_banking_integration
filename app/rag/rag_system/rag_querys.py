"""
RAG Query Engine — Production Version  (rag_querys.py)
========================================================

Intelligent query interface for Sentinel Bank AI agents.

Provides:
  • General policy queries with synthesized answers
  • Dispatcher Agent: complaint routing with ≥85% confidence
  • Sentinel Agent: fraud risk scoring with policy explanation
  • Trajectory Agent: product eligibility validation

Architecture:
  Agent
    ↓
  RAGQueryEngine.query() or agent-specific method
    ↓
  RetrievalEngine.search() — semantic search + re-ranking
    ↓
  _synthesize_answer() — best-evidence extraction
    ↓
  Structured response dict

Fixes in this version (v6 — betting support):
  1. _synthesize_answer: return moved outside chunk loop (v3 fix)
  2. detect_complaint_category: two-pass keyword+RAG routing (v3 fix)
  3. DEPT_KEYWORDS: corrected keyword lists (v4 fix)
       - TSU: removed "transaction" (matched any complaint with "transactions")
       - DCS: removed bare "app" (matched "applied", "application" as false positive)
       - AOD: "restriction" → "restrict" (catches "restricted", "restricting")
       - CLS: removed bare "credit"; added "car loan", "personal loan", "applied for a loan"
       - COC: "pos" → "pos terminal"; "blocked" moved to "card blocked" (prevents AOD overlap)
       - FRM: "stolen" → "stolen funds" (card stolen stays in COC)
  4. _synthesize_answer: divider-line filter (v4 fix)
       - Paragraphs composed mostly of ─ ═ - = _ characters are skipped
       - Prevents section-separator lines from scoring as best answer
  5. _synthesize_answer: divider line stripping (v4 fix)
       - Leading/trailing separator lines stripped from returned paragraph
       - Ensures policy basis previews show content, not header decorations
  6. query(): logger.info → logger.debug (v5 fix)
       - Per-query log was firing on every internal RAG call, including those
         triggered by detect_complaint_category() and calculate_fraud_risk().
         Demoted to DEBUG so it is available when needed but silent in production.
  7. validate_product_recommendation(): Student Loan hard age gate (v5 fix)
       - Aligned with recommendation_engine.py v2.5: age > 35 now returns
         NOT_ELIGIBLE for Student Loan regardless of Loan_signal_score.
  8. validate_product_recommendation(): ₦ symbol alignment (v5 fix)
       - All naira references now use ₦ to match recommendation_engine.py v2.5.
  9. v6 — BETTING SUPPORT (this version):
       - Fallback MERCHANT_RISK dict now includes "betting": 25.
         Without this, transactions from BetKing and other betting platforms
         scored 0 merchant risk because the import fallback never knew about
         the new category. The RAG policy text was re-ingested (FRM-002 v1.1)
         but calculate_fraud_risk() reads from the constant, not from RAG —
         so the constant MUST include "betting" regardless of RAG state.
       - calculate_fraud_risk() now accepts and scores four additional
         contextual signals sent by MerchantCheckout.jsx and BettingScreen.jsx:
           is_new_merchant  (bool) : +25 if amount > 100k, else +10
           is_late_night    (bool) : +20 if passed explicitly (fallback to
                                     timestamp parsing which already existed)
           is_unlicensed    (bool) : +10 for grey-market betting operators
           multi_platform   (bool) : +20 for multi-platform betting velocity
         These mirror the FRM-002 v1.1 Heightened Alert Conditions exactly.
       - DEPT_KEYWORDS: "betting" keyword cluster added to FRM so that
         betting-related fraud complaints route correctly.
       - Fallback MERCHANT_RISK dict made exhaustive (all 10 categories).

Author: AI Engineer 2
Date: February 2026
"""

import asyncio
import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from .retrieval import RetrievalEngine
from .chromadb_config import initialize_chromadb

# Import shared policy constants (single source of truth)
try:
    from app.rag.knowledge_base.generate_policies import (
        MERCHANT_RISK,
        FLAG_WEIGHTS,
        EXPECTED_SLA,
        DEPT_NAMES,
        RISK_THRESHOLDS,
        PRODUCT_CLASSES,
        LOAN_SIGNAL_SCORE_RANGES,
    )
except ImportError:
    # Fallback defaults — reached if generate_policies.py is not on path.
    # CRITICAL: This dict MUST stay in sync with MERCHANT_RISK in
    # generate_policies.py. Every time a new merchant category is added
    # to generate_policies.py, add it here too — otherwise the fallback
    # path silently scores that category as 0 (the bug that caused betting
    # transactions to show 0% risk before v6).
    logging.warning("Could not import policy constants — using hardcoded defaults")
    MERCHANT_RISK: Dict[str, int] = {
        "fintech":     25,   # Highest — primary fraud exit channel
        "betting":     25,   # Highest — high chargeback & fraud exit risk (v6)
        "transport":   15,   # Card-testing indicator (Uber/Bolt)
        "education":   15,   # Social engineering scam cover
        "healthcare":  15,   # Emergency scam payments
        "telecoms":     5,   # Airtime resale at high volume
        "supermarket":  0,   # Routine essential spending
        "restaurants":  0,   # Routine food spending
        "fuel":         0,   # Routine predictable amounts
        "utilities":    0,   # Scheduled bill payments
    }
    FLAG_WEIGHTS: Dict[str, int] = {
        "mobile_channel_risk": 15,
        "high_amount_spike":   25,
        "multiple_failures":   20,
        "normal_pattern":       0,
    }
    EXPECTED_SLA: Dict[str, int] = {
        "TSU": 48,
        "COC": 48,
        "FRM": 24,
        "DCS": 72,
        "AOD": 72,
        "CLS": 96,
    }
    DEPT_NAMES: Dict[str, str] = {
        "TSU": "Transaction Services Unit",
        "COC": "Card Operations Center",
        "FRM": "Fraud Risk Management",
        "DCS": "Digital Channels Support",
        "AOD": "Account Operations Department",
        "CLS": "Credit & Loan Services",
    }
    RISK_THRESHOLDS: Dict[str, tuple] = {
        "LOW":      (0,  30),
        "MEDIUM":   (31, 60),
        "HIGH":     (61, 85),
        "CRITICAL": (86, 100),
    }
    PRODUCT_CLASSES: List[str] = [
        "Student Loan",
        "Car Loan",
        "Investment Plan",
        "Trust Fund",
        "Personal Loan",
    ]
    LOAN_SIGNAL_SCORE_RANGES: Dict[str, tuple] = {
        "Student Loan":    (0.80, 0.98),
        "Car Loan":        (0.75, 0.95),
        "Investment Plan": (0.70, 0.90),
        "Personal Loan":   (0.70, 0.92),
        "Trust Fund":      (0.65, 0.85),
    }

# =============================================================================
# Logging
# =============================================================================

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Department Routing Tables
# =============================================================================

DEPT_KEYWORDS: Dict[str, List[str]] = {
    # Transaction Services Unit — payment / transfer failures
    "TSU": [
        "transfer", "sent money", "payment", "not received", "beneficiary",
        "reversal", "remittance", "funds", "wire", "neft", "rtgs",
        "not credited", "pending transfer", "money transfer", "bank transfer",
        "i sent", "debit alert", "wrong account", "failed transfer",
    ],
    # Card Operations Center — card & ATM issues
    "COC": [
        "card", "atm", "declined", "swallowed", "pin",
        "contactless", "chip", "debit card", "credit card", "card not working",
        "card expired", "card stolen", "pos terminal", "card replacement",
        "card blocked",
    ],
    # Fraud Risk Management — unauthorized / compromised account
    # v6: added betting-specific fraud patterns
    "FRM": [
        "fraud", "unauthorized", "hacked", "scam", "suspicious",
        "unknown transaction", "i did not", "i didn't",
        "not authorised", "not authorized", "fraudulent", "phishing",
        "identity theft", "account compromised", "stolen funds",
        "betting fraud", "casino fraud", "gambling scam",
        "did not make this bet", "did not fund this wallet",
    ],
    # Digital Channels Support — mobile/internet banking access
    "DCS": [
        "mobile app", "banking app", "sentinel app", "login", "mobile banking",
        "internet banking", "otp", "password", "online banking", "cannot log in",
        "app not working", "digital banking", "ussd", "2fa",
    ],
    # Account Operations Department — account-level restrictions / KYC
    "AOD": [
        "account", "kyc", "bvn", "upgrade", "restrict", "limit",
        "tier", "account blocked", "account frozen", "verification",
        "open account", "close account", "dormant", "reactivate",
        "account issue", "account problem", "cannot transact",
    ],
    # Credit & Loan Services — loan products and credit
    "CLS": [
        "loan", "repayment", "overdraft", "interest", "borrow", "mortgage",
        "loan application", "car loan", "personal loan", "loan status",
        "loan request", "credit score", "loan balance", "loan statement",
        "applied for a loan",
    ],
}

# Department name → code (for text matching in retrieved answers)
DEPT_NAME_TO_CODE: Dict[str, str] = {
    name.upper(): code
    for code, name in DEPT_NAMES.items()
}
DEPT_NAME_TO_CODE.update({
    "TRANSACTION SERVICES UNIT": "TSU",
    "CARD OPERATIONS CENTER":    "COC",
    "CARD OPERATIONS CENTRE":    "COC",
    "FRAUD RISK MANAGEMENT":     "FRM",
    "DIGITAL CHANNELS SUPPORT":  "DCS",
    "ACCOUNT OPERATIONS":        "AOD",
    "CREDIT & LOAN SERVICES":    "CLS",
    "CREDIT AND LOAN SERVICES":  "CLS",
    "TSU": "TSU", "COC": "COC", "FRM": "FRM",
    "DCS": "DCS", "AOD": "AOD", "CLS": "CLS",
})

# =============================================================================
# Betting platform classification (FRM-002 v1.1)
# =============================================================================
# Licensed NLRC operators — base +25 risk weight only.
# Unlicensed/grey-market operators — base +25 + additional +10 surcharge.

LICENSED_BETTING_OPERATORS: set = {
    "bet9ja", "sportybet", "betway", "bangbet", "nairabet",
    "betking", "msport", "betland", "merrybet",
}
UNLICENSED_BETTING_OPERATORS: set = {
    "1xbet", "parimatch", "betwinner", "22bet", "melbet",
}


# =============================================================================
# RAG Query Engine
# =============================================================================

class RAGQueryEngine:
    """
    Intelligent query engine for Sentinel Bank policy documents.

    Answers questions using retrieved policy chunks with semantic search
    and keyword-boosted re-ranking.

    Agent methods:
      detect_complaint_category()       → Dispatcher Agent
      calculate_fraud_risk()            → Sentinel Agent
      validate_product_recommendation() → Trajectory Agent
    """

    def __init__(self, chromadb_client, chromadb_config):
        self.retrieval = RetrievalEngine(chromadb_client, chromadb_config)
        logger.info("RAG Query Engine initialized")

    # =========================================================================
    # Core Query Method
    # =========================================================================

    async def query(
        self,
        question:   str,
        agent:      Optional[str] = None,
        collection: str           = "all",
        top_k:      int           = 7,
    ) -> Dict[str, Any]:
        """
        Answer a question using policy documents.

        Args:
            question:   Query text
            agent:      Optional agent filter (Dispatcher|Sentinel|Trajectory|Customer)
            collection: "all" | "policies" | "faqs"
            top_k:      Chunks to retrieve

        Returns:
            Dict:
              answer            — synthesized best-match paragraph
              sources           — list of source dicts with source, section, similarity
              confidence        — weighted float 0–1
              confidence_label  — "Very High" | "High" | "Medium" | "Low"
              grounded          — True if retrieved from knowledge base
              chunks_used       — number of chunks retrieved
        """
        logger.debug(f"Query: {question[:80]}...")

        retrieval_result = await self.retrieval.search(
            query      = question,
            agent      = agent,
            collection = collection,
            top_k      = top_k,
        )

        if retrieval_result["total_found"] == 0:
            return {
                "answer":      None,
                "sources":     [],
                "confidence":  0.0,
                "grounded":    False,
                "chunks_used": 0,
                "message":     "No relevant information found in knowledge base.",
            }

        chunks     = retrieval_result["chunks"]
        answer     = self._synthesize_answer(question, chunks)
        sources    = [
            {
                "source":     c["source"],
                "section":    c["section"],
                "similarity": c["similarity"],
            }
            for c in chunks
        ]
        confidence = retrieval_result.get("confidence", 0.0)

        return {
            "answer":           answer,
            "sources":          sources,
            "confidence":       confidence,
            "confidence_label": retrieval_result.get("confidence_label", ""),
            "grounded":         True,
            "chunks_used":      len(chunks),
        }

    # =========================================================================
    # Answer Synthesis
    # =========================================================================

    def _synthesize_answer(self, question: str, chunks: List[Dict]) -> str:
        """
        Extract the single best-evidence paragraph from retrieved chunks.
        """
        if not chunks:
            return "No answer found in the knowledge base."

        question_lower = question.lower()
        question_words = set(w.lower() for w in question.split() if len(w) >= 4)

        priority_keywords: List[str] = []

        if any(k in question_lower for k in ("sla", "hours", "time", "deadline")):
            priority_keywords += ["sla", "hours", "within", "resolution", "days"]

        if any(k in question_lower for k in ("department", "unit", "route", "routing")):
            priority_keywords += ["department", "unit", "responsible", "handles"]

        if any(k in question_lower for k in ("risk", "score", "fraud", "flag")):
            priority_keywords += ["risk", "score", "threshold", "flag", "points"]

        if any(k in question_lower for k in ("eligib", "criteria", "qualify")):
            priority_keywords += ["eligible", "eligibility", "criteria", "minimum"]

        if any(k in question_lower for k in ("merchant", "category", "betting")):
            priority_keywords += ["merchant", "category", "risk", "weight", "betting"]

        EXAMPLE_SKIP_PATTERNS = re.compile(
            r"^(examples?|sample|illustration|e\.g\.)",
            re.IGNORECASE,
        )
        DIVIDER_PATTERN = re.compile(r"^[\─═\-=_\s]{10,}$", re.MULTILINE)
        SLA_TERMS  = {"hour", "sla", "within", "resolution", "deadline", "days", "timeframe"}
        DEPT_TERMS = set(DEPT_NAMES.values()) | set(DEPT_NAMES.keys())

        best_para  = None
        best_score = -999.0

        for chunk in chunks:
            content    = chunk.get("content", "")
            similarity = chunk.get("similarity", 0.0)
            paragraphs = content.split("\n\n")

            for para in paragraphs:
                para_stripped = para.strip()

                if len(para_stripped) < 40:
                    continue

                if EXAMPLE_SKIP_PATTERNS.match(para_stripped[:20]):
                    continue

                non_divider_chars = re.sub(r"[\─═\-=_\s│┼┤├┬┴┐┌└┘]", "", para_stripped)
                if len(non_divider_chars) < 15:
                    continue

                para_lower = para_stripped.lower()
                score      = similarity * 10.0

                for word in question_words:
                    if word in para_lower:
                        score += 5.0

                for kw in priority_keywords:
                    if kw in para_lower:
                        score += 5.0

                if any(t in para_lower for t in SLA_TERMS):
                    score += 8.0

                if any(c.isdigit() for c in para_stripped):
                    score += 5.0

                for dept in DEPT_TERMS:
                    if dept.lower() in para_lower:
                        score += 4.0
                        break

                if score > best_score:
                    best_score = score
                    best_para  = para_stripped

        if best_para:
            cleaned_lines = []
            for line in best_para.split("\n"):
                stripped = line.strip()
                non_div  = re.sub(r"[\─═\-=_\s│┼┤├┬┴┐┌└┘]", "", stripped)
                if len(non_div) >= 5:
                    cleaned_lines.append(line)
                elif cleaned_lines:
                    cleaned_lines.append(line)
            clean_para = "\n".join(cleaned_lines).strip()
            return clean_para if clean_para else best_para

        return chunks[0]["content"][:500]

    # =========================================================================
    # DISPATCHER AGENT
    # =========================================================================

    async def detect_complaint_category(
        self,
        complaint_text: str,
    ) -> Dict[str, Any]:
        """
        Route a customer complaint to the correct department.

        Strategy (two-pass):
          Pass 1: Keyword routing via DEPT_KEYWORDS table
          Pass 2: RAG retrieval using expanded query
        """
        complaint_lower = complaint_text.lower()

        # ── Pass 1: Keyword routing ────────────────────────────────────────
        keyword_dept    = None
        keyword_score   = 0
        keyword_matched: List[str] = []

        for dept_code, keywords in DEPT_KEYWORDS.items():
            matches = [kw for kw in keywords if kw in complaint_lower]
            if len(matches) > keyword_score:
                keyword_score   = len(matches)
                keyword_dept    = dept_code
                keyword_matched = matches

        # ── Pass 2: RAG retrieval ──────────────────────────────────────────
        expanded_query = self._build_routing_query(complaint_text, keyword_dept)

        rag_result = await self.query(
            question   = expanded_query,
            agent      = "Dispatcher",
            collection = "policies",
            top_k      = 7,
        )

        if rag_result["grounded"]:
            rag_dept = self._extract_department(
                answer  = rag_result.get("answer", ""),
                sources = rag_result.get("sources", []),
                chunks  = rag_result.get("chunks_used", 0),
            )
        else:
            rag_dept = None

        # Decision logic
        if keyword_dept == "FRM" or rag_dept == "FRM":
            final_dept     = "FRM"
            routing_method = "keyword+rag"
        elif keyword_score >= 2:
            final_dept     = keyword_dept
            routing_method = "keyword+rag" if rag_dept else "keyword"
        elif rag_dept and rag_dept != "TSU":
            final_dept     = rag_dept
            routing_method = "rag"
        elif keyword_dept:
            final_dept     = keyword_dept
            routing_method = "keyword"
        else:
            final_dept     = "TSU"
            routing_method = "default"

        # Confidence calculation
        keyword_confidence = min(0.97, 0.82 + keyword_score * 0.05)
        rag_confidence     = rag_result.get("confidence", 0.0)
        agreement_bonus    = 0.05 if (keyword_dept and rag_dept and
                                       keyword_dept == rag_dept) else 0.0

        if keyword_score >= 2 and rag_result["grounded"]:
            confidence = min(0.99, (keyword_confidence + rag_confidence) / 2
                            + agreement_bonus)
        elif keyword_score >= 2:
            confidence = keyword_confidence
        elif keyword_score == 1 and rag_result["grounded"]:
            single_kw_floor = 0.65
            confidence = min(0.99, (single_kw_floor + rag_confidence) / 2
                            + agreement_bonus)
        elif rag_result["grounded"]:
            confidence = rag_confidence
        else:
            confidence = 0.60

        if rag_result.get("answer"):
            reasoning = rag_result["answer"]
        else:
            dept_name = DEPT_NAMES.get(final_dept, final_dept)
            reasoning = (
                f"Complaint routed to {dept_name} ({final_dept}) based on "
                f"keyword signals: {', '.join(keyword_matched[:3])}."
            )

        priority  = self._determine_priority(complaint_text, final_dept)
        sla_hours = EXPECTED_SLA.get(final_dept, 48)

        return {
            "department_code":  final_dept,
            "department_name":  DEPT_NAMES.get(final_dept, final_dept),
            "priority_level":   priority,
            "sla_hours":        sla_hours,
            "confidence":       round(confidence, 3),
            "reasoning":        reasoning[:500],
            "routing_method":   routing_method,
            "keyword_matches":  keyword_matched,
        }

    def _build_routing_query(
        self,
        complaint:    str,
        keyword_dept: Optional[str],
    ) -> str:
        dept_context = {
            "TSU": "transaction payment transfer department routing",
            "COC": "card ATM blocked declined department routing",
            "FRM": "fraud unauthorized suspicious department routing",
            "DCS": "digital app mobile banking login department routing",
            "AOD": "account KYC restriction limit department routing",
            "CLS": "loan credit repayment department routing",
        }
        context = dept_context.get(keyword_dept, "complaint routing department") \
            if keyword_dept else "complaint routing department policy"
        return f"{context} — {complaint}"

    def _extract_department(
        self,
        answer:  str,
        sources: List[Dict],
        chunks:  Any,
    ) -> Optional[str]:
        if answer:
            text_upper = answer.upper()
            for name, code in DEPT_NAME_TO_CODE.items():
                if name in text_upper:
                    return code
        for src in sources:
            combined = (
                str(src.get("source",  "")).upper() + " " +
                str(src.get("section", "")).upper()
            )
            for name, code in DEPT_NAME_TO_CODE.items():
                if name in combined:
                    return code
        return None

    def _determine_priority(self, complaint: str, dept: str) -> str:
        text_lower = complaint.lower()

        if dept == "FRM":
            return "Critical"

        if any(w in text_lower for w in (
            "fraud", "unauthorized", "hacked", "stolen", "scam"
        )):
            return "Critical"

        if any(w in text_lower for w in (
            "declined", "swallowed", "blocked", "failed", "rejected",
            "not received", "missing"
        )):
            return "High"

        if any(w in text_lower for w in (
            "statement", "balance", "enquiry", "information", "update"
        )):
            return "Low"

        return "Medium"

    # =========================================================================
    # SENTINEL AGENT — calculate_fraud_risk()
    # =========================================================================

    async def calculate_fraud_risk(
        self,
        transaction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate fraud risk score for a transaction.

        Scoring components (all capped at 100 total):

          1. FLAG_WEIGHTS    — from fraud_explainability_trace field
             mobile_channel_risk  : +15
             high_amount_spike    : +25
             multiple_failures    : +20
             normal_pattern       :  +0

          2. MERCHANT_RISK   — from merchant_category field (MERCHANT_RISK dict)
             fintech / betting    : +25  ← v6: betting now included
             transport/education/healthcare : +15
             telecoms             :  +5
             supermarket/restaurants/fuel/utilities : 0

          3. TIMING_RISK     — computed from transaction_timestamp or is_late_night flag
             Late night (00:00–04:59 WAT) + amount >= ₦100,000 : +20

          4. CONTEXTUAL_RISK — optional fields sent by frontend (v6 additions)
             is_new_merchant (bool):
               amount > ₦100,000 → +25 (FRM-002 "Large Single Transaction" rule)
               amount <= ₦100,000 → +10 (FRM-002 "First Transaction" rule)
             is_unlicensed (bool):
               betting operator is grey-market (1xBet, Parimatch, etc.) → +10
             multi_platform (bool):
               2+ different betting platforms in 60 minutes → +20
             merchant_name (str):
               Auto-detect unlicensed if merchant_name matches UNLICENSED set
               and is_unlicensed is not explicitly passed

        Args:
            transaction: Transaction dict. Supported keys:
                fraud_explainability_trace : str   — comma-separated flags
                merchant_category          : str   — e.g. "betting"
                merchant_name              : str   — e.g. "BetKing"
                amount                     : float — transaction amount in NGN
                transaction_timestamp      : str   — ISO datetime (optional)
                is_new_merchant            : bool  — first txn to this merchant
                is_late_night              : bool  — override timestamp check
                is_unlicensed              : bool  — grey-market operator flag
                multi_platform             : bool  — multi-platform velocity flag

        Returns:
            Dict:
              total_risk_score   : int  0–100
              risk_level         : "LOW" | "MEDIUM" | "HIGH" | "CRITICAL"
              risk_breakdown     : dict of named component scores
              recommended_action : human-readable action string
              requires_challenge : bool — push-to-app needed
              should_block       : bool — immediate block required
              policy_explanation : RAG-grounded explanation text
              confidence         : retrieval confidence (0–1)
        """
        risk_breakdown = {
            "flag_score":       0,
            "merchant_risk":    0,
            "timing_risk":      0,
            "new_merchant_risk": 0,
            "unlicensed_risk":  0,
            "multi_platform_risk": 0,
        }

        # ── 1. Fraud flag weights ──────────────────────────────────────────
        trace = str(transaction.get("fraud_explainability_trace", "normal_pattern"))
        for flag in trace.split(","):
            flag = flag.strip()
            risk_breakdown["flag_score"] += FLAG_WEIGHTS.get(flag, 0)

        # ── 2. Merchant category risk ──────────────────────────────────────
        # MERCHANT_RISK is the single source of truth — if the import succeeded
        # it came from generate_policies.py (which now includes "betting": 25).
        # If the import failed, the fallback dict above also includes "betting": 25.
        # Either way, a betting transaction will ALWAYS receive +25 here.
        merchant_cat = str(transaction.get("merchant_category", "")).lower().strip()
        risk_breakdown["merchant_risk"] = MERCHANT_RISK.get(merchant_cat, 0)

        # ── 3. Timing risk ─────────────────────────────────────────────────
        amount      = float(transaction.get("amount", 0))
        is_late     = bool(transaction.get("is_late_night", False))

        if not is_late:
            # Fall back to parsing the timestamp if is_late_night not passed explicitly
            timestamp = transaction.get("transaction_timestamp", "")
            if timestamp:
                try:
                    ts_clean = str(timestamp).replace(" ", "T")
                    dt       = datetime.fromisoformat(ts_clean)
                    if 0 <= dt.hour < 5:
                        is_late = True
                except Exception:
                    pass

        if is_late and amount >= 100_000:
            risk_breakdown["timing_risk"] = 20

        # ── 4. New merchant risk (FRM-002 Section 2 velocity rules) ────────
        # MerchantCheckout.jsx sends is_new_merchant=True for BetKing because
        # it is the first transaction ever from this account to that merchant.
        is_new_merchant = bool(transaction.get("is_new_merchant", False))
        if is_new_merchant:
            if amount > 100_000:
                # "Large Single Transaction with New Merchant" rule: +25
                risk_breakdown["new_merchant_risk"] = 25
            else:
                # "First Transaction with New Merchant" rule: +10
                risk_breakdown["new_merchant_risk"] = 10

        # ── 5. Unlicensed operator surcharge (FRM-002 betting section) ─────
        # Explicitly passed by frontend, or auto-detected from merchant_name.
        is_unlicensed = bool(transaction.get("is_unlicensed", False))
        if not is_unlicensed:
            merchant_name = str(transaction.get("merchant_name", "")).lower().strip()
            if merchant_name in UNLICENSED_BETTING_OPERATORS:
                is_unlicensed = True
        if is_unlicensed and merchant_cat == "betting":
            risk_breakdown["unlicensed_risk"] = 10

        # ── 6. Multi-platform betting velocity (FRM-002 Section 2) ────────
        multi_platform = bool(transaction.get("multi_platform", False))
        if multi_platform and merchant_cat == "betting":
            risk_breakdown["multi_platform_risk"] = 20

        # ── Total (capped at 100) ──────────────────────────────────────────
        total = min(sum(risk_breakdown.values()), 100)

        # ── Risk level from RISK_THRESHOLDS ────────────────────────────────
        risk_level = "LOW"
        for level, (low, high) in RISK_THRESHOLDS.items():
            if low <= total <= high:
                risk_level = level
                break

        # ── Action mapping ─────────────────────────────────────────────────
        ACTIONS = {
            "CRITICAL": ("BLOCK immediately and freeze account",                False, True),
            "HIGH":     ("Mandatory push-to-app biometric challenge required",  True,  False),
            "MEDIUM":   ("Step-up OTP authentication required",                 True,  False),
            "LOW":      ("Process with standard SMS alert",                     False, False),
        }
        action, requires_challenge, should_block = ACTIONS.get(
            risk_level, ("Process with standard SMS alert", False, False)
        )

        # ── RAG explanation ────────────────────────────────────────────────
        # Rich query so the embedding model retrieves relevant FRM-002 chunks
        # regardless of risk level (the old short query scored ~0% for LOW).
        flags_str  = str(transaction.get("fraud_explainability_trace", "normal_pattern"))
        amount_str = f"N{amount:,.0f}" if amount > 0 else "unknown amount"

        sentinel_query = (
            f"fraud risk assessment {risk_level} risk level "
            f"total score {total} points "
            f"flag score {risk_breakdown['flag_score']} "
            f"merchant risk {risk_breakdown['merchant_risk']} "
            f"timing risk {risk_breakdown['timing_risk']} "
            f"new merchant risk {risk_breakdown['new_merchant_risk']} "
            f"fraud flags {flags_str} "
            f"merchant category {merchant_cat} "
            f"transaction amount {amount_str} "
            f"recommended action SLA policy FRM fraud scoring threshold "
            f"betting platform risk FRM-002"
        )

        explanation = await self.query(
            question   = sentinel_query,
            agent      = "Sentinel",
            collection = "policies",
            top_k      = 5,
        )

        return {
            "total_risk_score":      total,
            "risk_level":            risk_level,
            "risk_breakdown":        risk_breakdown,
            "recommended_action":    action,
            "requires_challenge":    requires_challenge,
            "should_block":          should_block,
            "policy_explanation":    explanation.get("answer", ""),
            "confidence":            explanation.get("confidence", 0.0),
        }

    # =========================================================================
    # TRAJECTORY AGENT
    # =========================================================================

    async def validate_product_recommendation(
        self,
        customer_data:       Dict[str, Any],
        recommended_product: str,
    ) -> Dict[str, Any]:
        """
        Validate whether a customer is eligible for a recommended product.

        Hybrid Architecture:
          Primary:  RAG-grounded policy validation
          Fallback: Deterministic score-based validation (fail-open)

        Guarantees:
          - System always returns a decision (no blocking)
          - Student Loan age rule (18–35) is ALWAYS enforced

        Args:
            customer_data: Dict with:
                Loan_signal_score : float
                monthly_inflow    : float
                salary_detected   : bool
                age               : int
            recommended_product: one of PRODUCT_CLASSES

        Returns:
            Dict:
                is_eligible      : bool
                met_criteria     : list of passed criteria strings
                unmet_criteria   : list of failed criteria strings
                recommendation   : "APPROVED" | "NOT_ELIGIBLE" | "CANNOT_VALIDATE"
                score_range      : (floor, ceiling) for the product
                policy_basis     : RAG-grounded policy text
                confidence       : retrieval confidence
                validation_mode  : "RAG" | "FALLBACK"
        """

        # ── Step 1: Query policy via RAG ──────────────────────────────────
        policy = await self.query(
            question=(
                f"What are the eligibility criteria and minimum requirements "
                f"for the {recommended_product} product?"
            ),
            agent      = "Trajectory",
            collection = "policies",
            top_k      = 5,
        )

        # ── Extract customer data ─────────────────────────────────────────
        loan_score      = float(customer_data.get("Loan_signal_score", 0.0))
        monthly_inflow  = float(customer_data.get("monthly_inflow", 0.0))
        salary_detected = bool(customer_data.get("salary_detected", False))
        age             = int(customer_data.get("age", 0))

        # ── Score range lookup ────────────────────────────────────────────
        score_range = LOAN_SIGNAL_SCORE_RANGES.get(recommended_product)

        # ── FALLBACK MODE (RAG unavailable) ──────────────────────────────
        if not policy.get("grounded", False):

            if score_range:
                floor, ceiling = score_range

                if recommended_product == "Student Loan":
                    if age > 35:
                        return {
                            "is_eligible":     False,
                            "met_criteria":    [],
                            "unmet_criteria":  [
                                f"Age {age} exceeds Student Loan maximum age of 35"
                            ],
                            "recommendation":  "NOT_ELIGIBLE",
                            "score_range":     score_range,
                            "policy_basis":    "Score-based fallback (RAG unavailable)",
                            "confidence":      0.75,
                            "validation_mode": "FALLBACK",
                        }
                    elif age > 0 and age < 18:
                        return {
                            "is_eligible":     False,
                            "met_criteria":    [],
                            "unmet_criteria":  [
                                f"Age {age} below Student Loan minimum age of 18"
                            ],
                            "recommendation":  "NOT_ELIGIBLE",
                            "score_range":     score_range,
                            "policy_basis":    "Score-based fallback (RAG unavailable)",
                            "confidence":      0.75,
                            "validation_mode": "FALLBACK",
                        }

                is_eligible = loan_score >= floor

                return {
                    "is_eligible":     is_eligible,
                    "met_criteria":    [
                        f"Loan_signal_score {loan_score:.2f} >= {floor:.2f} "
                        f"{recommended_product} floor "
                        f"(range {floor:.2f}-{ceiling:.2f})"
                    ] if is_eligible else [],
                    "unmet_criteria":  [] if is_eligible else [
                        f"Loan_signal_score {loan_score:.2f} below {floor:.2f} "
                        f"{recommended_product} floor "
                        f"(range {floor:.2f}-{ceiling:.2f})"
                    ],
                    "recommendation":  "APPROVED" if is_eligible else "NOT_ELIGIBLE",
                    "score_range":     score_range,
                    "policy_basis":    "Score-based fallback (RAG unavailable)",
                    "confidence":      0.75,
                    "validation_mode": "FALLBACK",
                }

            return {
                "is_eligible":     False,
                "met_criteria":    [],
                "unmet_criteria":  [
                    f"Unknown product '{recommended_product}'. "
                    f"Valid products: {', '.join(PRODUCT_CLASSES)}"
                ],
                "recommendation":  "CANNOT_VALIDATE",
                "score_range":     None,
                "policy_basis":    "Fallback failed: unknown product",
                "confidence":      0.0,
                "validation_mode": "FALLBACK",
            }

        # ── RAG MODE ──────────────────────────────────────────────────────
        if score_range is None:
            return {
                "is_eligible":     False,
                "met_criteria":    [],
                "unmet_criteria":  [
                    f"Unknown product '{recommended_product}'. "
                    f"Valid products: {', '.join(PRODUCT_CLASSES)}"
                ],
                "recommendation":  "CANNOT_VALIDATE",
                "score_range":     None,
                "policy_basis":    policy.get("answer", "")[:400],
                "confidence":      policy.get("confidence", 0.0),
                "validation_mode": "RAG",
            }

        floor, ceiling = score_range
        met:   List[str] = []
        unmet: List[str] = []

        if recommended_product == "Car Loan":
            if loan_score >= floor:
                met.append(f"Loan signal score {loan_score:.2f} >= {floor:.2f}")
            else:
                unmet.append(f"Loan signal score {loan_score:.2f} below {floor:.2f}")
            if salary_detected:
                met.append("Salary inflow detected")
            if monthly_inflow >= 500_000:
                met.append(f"Monthly inflow ₦{monthly_inflow:,.0f} ≥ ₦500,000")

        elif recommended_product == "Investment Plan":
            if loan_score >= floor:
                met.append(f"Loan signal score {loan_score:.2f} >= {floor:.2f}")
            else:
                unmet.append(f"Loan signal score {loan_score:.2f} below {floor:.2f}")
            if monthly_inflow >= 2_000_000:
                met.append("High-value investment candidate")

        elif recommended_product == "Personal Loan":
            if loan_score >= floor:
                met.append(f"Loan signal score {loan_score:.2f} >= {floor:.2f}")
            else:
                unmet.append(f"Loan signal score {loan_score:.2f} below {floor:.2f}")
            if salary_detected:
                met.append("Salary inflow detected")
            else:
                met.append("No salary pattern detected")

        elif recommended_product == "Student Loan":
            if age > 35:
                unmet.append(f"Age {age} exceeds Student Loan maximum age of 35")
            elif age > 0 and age < 18:
                unmet.append(f"Age {age} below Student Loan minimum age of 18")
            else:
                if loan_score >= floor:
                    met.append(f"Loan signal score {loan_score:.2f} >= {floor:.2f}")
                else:
                    unmet.append(f"Loan signal score {loan_score:.2f} below {floor:.2f}")

        elif recommended_product == "Trust Fund":
            if loan_score >= floor:
                met.append(f"Loan signal score {loan_score:.2f} >= {floor:.2f}")
            else:
                unmet.append(f"Loan signal score {loan_score:.2f} below {floor:.2f}")
            if monthly_inflow >= 1_000_000:
                met.append("High-net-worth indicator")

        else:
            unmet.append(f"Unrecognized product '{recommended_product}'")

        is_eligible = len(unmet) == 0

        return {
            "is_eligible":     is_eligible,
            "met_criteria":    met,
            "unmet_criteria":  unmet,
            "recommendation":  "APPROVED" if is_eligible else "NOT_ELIGIBLE",
            "score_range":     score_range,
            "policy_basis":    policy.get("answer", "")[:400],
            "confidence":      policy.get("confidence", 0.0),
            "validation_mode": "RAG",
        }


# =============================================================================
# Convenience Factory
# =============================================================================

async def create_engine() -> RAGQueryEngine:
    """
    Create a ready-to-use RAG query engine with default settings.

    Returns:
        RAGQueryEngine instance

    Example:
        engine = await create_engine()
        result = await engine.query("What is the SLA for TSU?")
    """
    client, config = initialize_chromadb()
    return RAGQueryEngine(client, config)


# =============================================================================
# Full System Demo
# =============================================================================

async def full_demo():
    """
    Run a full demonstration of all four agent capabilities.

    Validates:
      - General policy queries with confidence > 85%
      - Dispatcher routing with correct department
      - Sentinel fraud risk scoring (including betting)
      - Trajectory product eligibility
    """
    engine = await create_engine()

    print("\n" + "=" * 70)
    print(" " * 20 + "SENTINEL BANK RAG SYSTEM DEMO")
    print("=" * 70 + "\n")

    # ── 1. General Policy Query ────────────────────────────────────────────
    print("━" * 50)
    print("1. GENERAL QUERY — SLA Policy")
    print("━" * 50)

    question = "What is the SLA for transaction disputes?"
    result   = await engine.query(question)

    print(f"  Question   : {question}")
    print(f"  Answer     : {result['answer'][:200] if result['answer'] else 'None'}...")
    print(f"  Confidence : {result['confidence']:.1%}")
    print(f"  Source     : {result['sources'][0]['source'] if result['sources'] else 'None'}")
    print(f"  Grounded   : {result['grounded']}")
    print()

    # ── 2. Dispatcher — Transfer complaint ────────────────────────────────
    print("━" * 50)
    print("2. DISPATCHER AGENT — Transfer complaint")
    print("━" * 50)

    complaint = "I transferred money to a friend, but he hasn't received it yet."
    routing   = await engine.detect_complaint_category(complaint)

    print(f"  Complaint       : {complaint}")
    print(f"  Department      : {routing['department_code']} — {routing['department_name']}")
    print(f"  Priority        : {routing['priority_level']}")
    print(f"  SLA Hours       : {routing['sla_hours']}h")
    print(f"  Confidence      : {routing['confidence']:.1%}")
    print(f"  Routing Method  : {routing['routing_method']}")
    print(f"  Keyword Matches : {routing['keyword_matches']}")
    print(f"  Reasoning       : {routing['reasoning'][:150]}...")
    print()

    # ── 3. Dispatcher — Fraud complaint ───────────────────────────────────
    print("━" * 50)
    print("3. DISPATCHER AGENT — Fraud complaint")
    print("━" * 50)

    complaint2 = "I see an unauthorized transaction of ₦250,000 on my account I did not make."
    routing2   = await engine.detect_complaint_category(complaint2)

    print(f"  Complaint  : {complaint2}")
    print(f"  Department : {routing2['department_code']} — {routing2['department_name']}")
    print(f"  Priority   : {routing2['priority_level']}")
    print(f"  SLA Hours  : {routing2['sla_hours']}h")
    print(f"  Confidence : {routing2['confidence']:.1%}")
    print()

    # ── 4. Sentinel — BetKing checkout scenario ───────────────────────────
    print("━" * 50)
    print("4. SENTINEL AGENT — BetKing ₦250,000 at 02:14 AM (MerchantCheckout)")
    print("━" * 50)

    betking_txn = {
        "fraud_explainability_trace": "normal_pattern",
        "merchant_category":          "betting",
        "merchant_name":              "BetKing",
        "amount":                     250_000,
        "transaction_timestamp":      "2026-02-22 02:14:00",
        "is_new_merchant":            True,    # First BetKing transaction
        "is_late_night":              True,    # Explicit flag from frontend
        "is_unlicensed":              False,   # BetKing is NLRC licensed
        "multi_platform":             False,
    }
    betking_fraud = await engine.calculate_fraud_risk(betking_txn)

    print(f"  Merchant     : {betking_txn['merchant_name']} ({betking_txn['merchant_category']})")
    print(f"  Amount       : ₦{betking_txn['amount']:,}")
    print(f"  Time         : 02:14 AM (late night)")
    print(f"  New Merchant : Yes")
    print()
    print(f"  Score Breakdown:")
    for component, pts in betking_fraud["risk_breakdown"].items():
        if pts > 0:
            print(f"    {component:<25}: +{pts}")
    print(f"  ─────────────────────────────────────")
    print(f"  Total Risk Score : {betking_fraud['total_risk_score']}/100")
    print(f"  Risk Level       : {betking_fraud['risk_level']}")
    print(f"  Action           : {betking_fraud['recommended_action']}")
    print(f"  Block?           : {betking_fraud['should_block']}")
    print(f"  Challenge?       : {betking_fraud['requires_challenge']}")
    print()

    # Expected breakdown:
    #   flag_score          :  0  (normal_pattern)
    #   merchant_risk       : 25  (betting Tier 1)
    #   timing_risk         : 20  (02:14 AM + ₦250k >= ₦100k)
    #   new_merchant_risk   : 25  (first txn + ₦250k > ₦100k)
    #   unlicensed_risk     :  0
    #   multi_platform_risk :  0
    #   Total               : 70  → HIGH → push-to-app challenge

    # ── 5. Sentinel — 1xBet unlicensed scenario ───────────────────────────
    print("━" * 50)
    print("5. SENTINEL AGENT — 1xBet ₦150,000 (unlicensed operator)")
    print("━" * 50)

    onex_txn = {
        "fraud_explainability_trace": "mobile_channel_risk",
        "merchant_category":          "betting",
        "merchant_name":              "1xbet",
        "amount":                     150_000,
        "transaction_timestamp":      "2026-02-22 14:30:00",
        "is_new_merchant":            True,
        "is_late_night":              False,
        "multi_platform":             False,
    }
    onex_fraud = await engine.calculate_fraud_risk(onex_txn)

    print(f"  Merchant     : 1xBet ({onex_txn['merchant_category']})")
    print(f"  Amount       : ₦{onex_txn['amount']:,}")
    print(f"  Flags        : {onex_txn['fraud_explainability_trace']}")
    print()
    print(f"  Score Breakdown:")
    for component, pts in onex_fraud["risk_breakdown"].items():
        if pts > 0:
            print(f"    {component:<25}: +{pts}")
    print(f"  ─────────────────────────────────────")
    print(f"  Total Risk Score : {onex_fraud['total_risk_score']}/100")
    print(f"  Risk Level       : {onex_fraud['risk_level']}")
    print(f"  Action           : {onex_fraud['recommended_action']}")
    print()

    # Expected:
    #   flag_score          : 15  (mobile_channel_risk)
    #   merchant_risk       : 25  (betting)
    #   timing_risk         :  0  (14:30 WAT — daytime)
    #   new_merchant_risk   : 25  (first txn + ₦150k > ₦100k)
    #   unlicensed_risk     : 10  (1xbet auto-detected)
    #   multi_platform_risk :  0
    #   Total               : 75  → HIGH → push-to-app challenge

    # ── 6. Sentinel — fintech high risk (existing test) ───────────────────
    print("━" * 50)
    print("6. SENTINEL AGENT — Fintech fraud (existing scenario)")
    print("━" * 50)

    fintech_txn = {
        "fraud_explainability_trace": "high_amount_spike,mobile_channel_risk",
        "merchant_category":          "fintech",
        "amount":                     450_000,
        "transaction_timestamp":      "2026-02-22 02:15:00",
    }
    fintech_fraud = await engine.calculate_fraud_risk(fintech_txn)

    print(f"  Amount       : ₦{fintech_txn['amount']:,}")
    print(f"  Flags        : {fintech_txn['fraud_explainability_trace']}")
    print(f"  Risk Score   : {fintech_fraud['total_risk_score']}/100")
    print(f"  Risk Level   : {fintech_fraud['risk_level']}")
    print(f"  Breakdown    : {fintech_fraud['risk_breakdown']}")
    print(f"  Action       : {fintech_fraud['recommended_action']}")
    print()

    # ── 7. Trajectory — Product Eligibility ──────────────────────────────
    print("━" * 50)
    print("7. TRAJECTORY AGENT — Product Eligibility (5 products)")
    print("━" * 50)

    demo_cases = [
        ("Car Loan",        0.82, 600_000,   True,  30, "APPROVED"),
        ("Investment Plan", 0.78, 2_500_000, True,  40, "APPROVED"),
        ("Personal Loan",   0.71, 450_000,   True,  28, "APPROVED"),
        ("Student Loan",    0.88, 80_000,    False, 21, "APPROVED"),
        ("Student Loan",    0.88, 9_900_000, True,  63, "NOT_ELIGIBLE"),
        ("Trust Fund",      0.73, 1_200_000, True,  45, "APPROVED"),
        ("Car Loan",        0.60, 300_000,   False, 25, "NOT_ELIGIBLE"),
        ("Trust Fund",      0.50, 500_000,   False, 35, "NOT_ELIGIBLE"),
    ]

    for product, score, inflow, salary, age, expected in demo_cases:
        customer = {
            "Loan_signal_score": score,
            "monthly_inflow":    inflow,
            "salary_detected":   salary,
            "age":               age,
        }
        result      = await engine.validate_product_recommendation(customer, product)
        floor, ceil = result.get("score_range") or (0, 0)
        status      = "PASS" if result["recommendation"] == expected else "FAIL"
        print(f"  [{status}] {product:<18}  age={age}  "
              f"score={score:.2f} (range {floor:.2f}-{ceil:.2f})  "
              f"-> {result['recommendation']}")
        for m in result["met_criteria"]:
            print(f"           + {m}")
        for u in result["unmet_criteria"]:
            print(f"           - {u}")
        print()

    print("\n" + "=" * 70)
    print("Demo complete.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(full_demo())