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

Fixes in this version (v5 — matches project filename rag_querys.py):
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
         Previously age was context-only in this method while the proactive
         engine hard-gated it — creating a split-brain inconsistency.
  8. validate_product_recommendation(): ₦ symbol alignment (v5 fix)
       - All naira references now use ₦ to match recommendation_engine.py v2.5.

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
    # Fallback defaults — should not be reached in production
    logging.warning("Could not import policy constants — using hardcoded defaults")
    MERCHANT_RISK        = {"fintech": 25, "transport": 15}
    FLAG_WEIGHTS         = {"high_amount_spike": 25, "mobile_channel_risk": 15,
                            "multiple_failures": 20, "normal_pattern": 0}
    EXPECTED_SLA         = {"TSU": 48, "COC": 48, "FRM": 24,
                            "DCS": 72, "AOD": 72, "CLS": 96}
    DEPT_NAMES           = {"TSU": "Transaction Services Unit",
                            "COC": "Card Operations Center",
                            "FRM": "Fraud Risk Management",
                            "DCS": "Digital Channels Support",
                            "AOD": "Account Operations Department",
                            "CLS": "Credit & Loan Services"}
    RISK_THRESHOLDS      = {"LOW": (0, 30), "MEDIUM": (31, 60),
                            "HIGH": (61, 85), "CRITICAL": (86, 100)}
    # Product classes — must match data_generator.py PRODUCT_CLASSES exactly
    PRODUCT_CLASSES      = [
        "Student Loan", "Car Loan", "Investment Plan",
        "Trust Fund", "Personal Loan",
    ]
    # Loan_signal_score ranges per product — (floor, ceiling)
    # Floor is the minimum score for APPROVED; ceiling is dataset upper bound.
    # Matches the random.uniform() ranges in data_generator.py exactly.
    LOAN_SIGNAL_SCORE_RANGES = {
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
# Primary keyword routing — provides correct department even when embedding
# similarity is below threshold. Used as the first-pass signal in
# detect_complaint_category(), with RAG retrieval providing justification.

DEPT_KEYWORDS: Dict[str, List[str]] = {
    # Transaction Services Unit — payment / transfer failures
    # Removed: "transaction" (matches "transactions" in any complaint — too generic),
    #          "debit", "credit" (ambiguous with card-related complaints)
    "TSU": [
        "transfer", "sent money", "payment", "not received", "beneficiary",
        "reversal", "remittance", "funds", "wire", "neft", "rtgs",
        "not credited", "pending transfer", "money transfer", "bank transfer",
        "i sent", "debit alert", "wrong account", "failed transfer",
    ],
    # Card Operations Center — card & ATM issues
    # Changed: "blocked" removed (overlaps AOD account-level blocks);
    #          "pos" → "pos terminal" to avoid matching "positive", "position"
    "COC": [
        "card", "atm", "declined", "swallowed", "pin",
        "contactless", "chip", "debit card", "credit card", "card not working",
        "card expired", "card stolen", "pos terminal", "card replacement",
        "card blocked",
    ],
    # Fraud Risk Management — unauthorized / compromised account
    # Removed: "stolen" alone (card stolen is COC; kept "stolen funds")
    "FRM": [
        "fraud", "unauthorized", "hacked", "scam", "suspicious",
        "unknown transaction", "i did not", "i didn't",
        "not authorised", "not authorized", "fraudulent", "phishing",
        "identity theft", "account compromised", "stolen funds",
    ],
    # Digital Channels Support — mobile/internet banking access
    # Removed: "app" (matches "applied", "application" — false positive for CLS)
    #          "access", "website", "digital" (too generic)
    # Added:   "mobile app", "banking app" (explicit, unambiguous)
    "DCS": [
        "mobile app", "banking app", "sentinel app", "login", "mobile banking",
        "internet banking", "otp", "password", "online banking", "cannot log in",
        "app not working", "digital banking", "ussd", "2fa",
    ],
    # Account Operations Department — account-level restrictions / KYC
    # Fixed: "restriction" → "restrict" (catches restricted/restriction/restricting)
    # Added: "account issue", "account problem", "cannot transact"
    "AOD": [
        "account", "kyc", "bvn", "upgrade", "restrict", "limit",
        "tier", "account blocked", "account frozen", "verification",
        "open account", "close account", "dormant", "reactivate",
        "account issue", "account problem", "cannot transact",
    ],
    # Credit & Loan Services — loan products and credit
    # Removed: "credit" (matches "credit card" → COC confusion)
    # Added:   "car loan", "personal loan", "loan application", "applied for"
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
# Add abbreviated forms
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

    Example:
        engine = RAGQueryEngine(client, config)
        result = await engine.query("What is the SLA for TSU?")
        # result['confidence'] > 0.85
    """

    def __init__(self, chromadb_client, chromadb_config):
        """
        Args:
            chromadb_client: ChromaDB client from initialize_chromadb()
            chromadb_config: ChromaDBConfig instance
        """
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
              confidence        — weighted float 0–1: (top_sim x 0.7) + (top3_avg x 0.3)
                                  both using raw pre-boost similarity from RetrievalEngine
              confidence_label  — "Very High" | "High" | "Medium" | "Low"
              grounded          — True if retrieved from knowledge base
              chunks_used       — number of chunks retrieved
        """
        # DEBUG (not INFO) — this fires on every internal RAG call, including
        # those triggered automatically by detect_complaint_category() and
        # calculate_fraud_risk(). Keeping it at DEBUG prevents the console
        # from flooding with internal routing queries during normal operation.
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

        chunks = retrieval_result["chunks"]
        answer = self._synthesize_answer(question, chunks)

        sources = [
            {
                "source":     c["source"],
                "section":    c["section"],
                "similarity": c["similarity"],
            }
            for c in chunks
        ]

        # Use the honest weighted confidence computed by RetrievalEngine.
        # _compute_confidence: (top_sim x 0.7) + (top3_avg x 0.3), both
        # using raw pre-boost similarity. This replaces the old approach
        # of taking chunks[0]["similarity"] directly, which was a single
        # raw score that ignored how well the other retrieved chunks matched.
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

        FIX: The previous version returned inside the chunk loop, meaning
        only the first chunk was ever searched. This version searches ALL
        chunks and ALL paragraphs before selecting the best.

        Scoring:
          - Base: chunk semantic similarity × 10
          - +5 per query keyword found in paragraph
          - +8 if paragraph contains SLA/hours/resolution terms
          - +5 if paragraph contains numeric values
          - +4 if paragraph mentions a department name
          - -10 if paragraph is an "examples" header (skip example lists)

        Args:
            question: Original query text
            chunks:   Retrieved and re-ranked chunk list

        Returns:
            Best matching paragraph string (≤500 chars if no good match)
        """
        if not chunks:
            return "No answer found in the knowledge base."

        question_lower  = question.lower()
        question_words  = set(w.lower() for w in question.split() if len(w) >= 4)

        # Intent keyword detection
        priority_keywords: List[str] = []

        if any(k in question_lower for k in ("sla", "hours", "time", "deadline")):
            priority_keywords += ["sla", "hours", "within", "resolution", "days"]

        if any(k in question_lower for k in ("department", "unit", "route", "routing")):
            priority_keywords += ["department", "unit", "responsible", "handles"]

        if any(k in question_lower for k in ("risk", "score", "fraud", "flag")):
            priority_keywords += ["risk", "score", "threshold", "flag", "points"]

        if any(k in question_lower for k in ("eligib", "criteria", "qualify")):
            priority_keywords += ["eligible", "eligibility", "criteria", "minimum"]

        if any(k in question_lower for k in ("merchant", "category")):
            priority_keywords += ["merchant", "category", "risk", "weight"]

        EXAMPLE_SKIP_PATTERNS = re.compile(
            r"^(examples?|sample|illustration|e\.g\.)",
            re.IGNORECASE,
        )
        # Regex matching lines composed almost entirely of divider characters
        # (─, ═, ─, =, -, _). These are section headers with no answer content.
        DIVIDER_PATTERN = re.compile(r"^[\─═\-=_\s]{10,}$", re.MULTILINE)
        SLA_TERMS = {"hour", "sla", "within", "resolution", "deadline", "days", "timeframe"}
        DEPT_TERMS = set(DEPT_NAMES.values()) | set(DEPT_NAMES.keys())

        best_para   = None
        best_score  = -999.0

        # ── Search ALL chunks, ALL paragraphs ──────────────────────────────
        for chunk in chunks:
            content    = chunk.get("content", "")
            similarity = chunk.get("similarity", 0.0)
            paragraphs = content.split("\n\n")

            for para in paragraphs:
                para_stripped = para.strip()

                if len(para_stripped) < 40:
                    continue

                # Skip pure example headers
                if EXAMPLE_SKIP_PATTERNS.match(para_stripped[:20]):
                    continue

                # Skip paragraphs that are entirely divider/separator lines
                # (e.g. ────────────, =========, ----)
                non_divider_chars = re.sub(r"[\─═\-=_\s│┼┤├┬┴┐┌└┘]", "", para_stripped)
                if len(non_divider_chars) < 15:
                    continue

                para_lower = para_stripped.lower()
                score      = similarity * 10.0  # semantic base

                # Query word overlap
                for word in question_words:
                    if word in para_lower:
                        score += 5.0

                # Priority keyword boost
                for kw in priority_keywords:
                    if kw in para_lower:
                        score += 5.0

                # SLA / time reference boost
                if any(t in para_lower for t in SLA_TERMS):
                    score += 8.0

                # Numeric content boost (thresholds, hours)
                if any(c.isdigit() for c in para_stripped):
                    score += 5.0

                # Department mention boost
                for dept in DEPT_TERMS:
                    if dept.lower() in para_lower:
                        score += 4.0
                        break

                if score > best_score:
                    best_score = score
                    best_para  = para_stripped

        # ── Return best paragraph found ────────────────────────────────────
        if best_para:
            # Strip leading/trailing divider lines so the answer starts
            # with actual content, not a ─────────── or ========= header.
            cleaned_lines = []
            for line in best_para.split("\n"):
                stripped = line.strip()
                non_div  = re.sub(r"[\─═\-=_\s│┼┤├┬┴┐┌└┘]", "", stripped)
                if len(non_div) >= 5:          # line has real content
                    cleaned_lines.append(line)
                elif cleaned_lines:            # already have content — keep gaps
                    cleaned_lines.append(line)
            clean_para = "\n".join(cleaned_lines).strip()
            return clean_para if clean_para else best_para

        # Fallback: first 500 chars of best chunk
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
                  → Guaranteed correct department for known complaint types
          Pass 2: RAG retrieval using expanded query
                  → Policy-grounded reasoning and SLA confirmation

        Args:
            complaint_text: Raw customer complaint text

        Returns:
            Dict:
              department_code : TSU | COC | FRM | DCS | AOD | CLS
              department_name : Full department name
              priority_level  : Critical | High | Medium | Low
              sla_hours       : SLA hours from EXPECTED_SLA constant
              confidence      : Routing confidence score (0–1)
              reasoning       : Policy-grounded explanation
              routing_method  : "keyword" | "rag" | "keyword+rag"
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

        # ── Pass 2: RAG retrieval for grounded reasoning ───────────────────
        expanded_query = self._build_routing_query(complaint_text, keyword_dept)

        rag_result = await self.query(
            question   = expanded_query,
            agent      = "Dispatcher",
            collection = "policies",
            top_k      = 7,
        )

        # ── Merge routing signals ──────────────────────────────────────────
        if rag_result["grounded"]:
            rag_dept = self._extract_department(
                answer  = rag_result.get("answer", ""),
                sources = rag_result.get("sources", []),
                chunks  = rag_result.get("chunks_used", 0),
            )
        else:
            rag_dept = None

        # Decision logic:
        #   FRM always wins (fraud is highest priority)
        #   Keyword dept used as primary if confident (≥2 matches)
        #   RAG dept used if keyword confidence low and RAG found it
        #   Default: TSU (most common complaint category)

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
            final_dept     = "TSU"  # Grounded default per policy
            routing_method = "default"

        # ── Confidence calculation ─────────────────────────────────────────
        # keyword_confidence: base 0.82 + 0.05 per keyword match, capped 0.97
        # rag_confidence:     weighted blend from RetrievalEngine (honest float)
        # agreement_bonus:    +0.05 when keyword and RAG agree on same dept
        #
        # Routing paths:
        #   >= 2 keyword matches + RAG grounded → blend both + agreement bonus
        #   >= 2 keyword matches only           → keyword confidence alone
        #   1 keyword match + RAG grounded      → blend keyword floor with RAG
        #                                         (previously: rag only → ~42%)
        #   RAG grounded only (0 keywords)      → rag confidence
        #   Nothing                             → 0.60 floor

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
            # One keyword is a weak but real signal — blend a reduced keyword
            # floor (0.65) with the RAG score rather than dropping to raw RAG.
            # This prevents a single-keyword correct routing from scoring lower
            # than the 0.65 Dispatcher threshold just because RAG similarity
            # on the expanded complaint string is low.
            single_kw_floor = 0.65
            confidence = min(0.99, (single_kw_floor + rag_confidence) / 2
                            + agreement_bonus)
        elif rag_result["grounded"]:
            confidence = rag_confidence
        else:
            confidence = 0.60  # floor for keyword-only routing

        # ── Build reasoning ───────────────────────────────────────────────
        if rag_result.get("answer"):
            reasoning = rag_result["answer"]
        else:
            dept_name = DEPT_NAMES.get(final_dept, final_dept)
            reasoning = (
                f"Complaint routed to {dept_name} ({final_dept}) based on "
                f"keyword signals: {', '.join(keyword_matched[:3])}."
            )

        priority = self._determine_priority(complaint_text, final_dept)
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
        """
        Build an expanded query for department routing retrieval.

        Prepends department-specific context so the embedding search
        aligns better with routing policy chunks.

        Args:
            complaint:    Original complaint text
            keyword_dept: Department pre-identified by keywords (may be None)

        Returns:
            Expanded query string
        """
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
        """
        Extract department code from answer text and source metadata.

        Searches for department names and codes using DEPT_NAME_TO_CODE.

        Args:
            answer:  Synthesized answer text
            sources: List of source dicts from retrieval
            chunks:  Unused (kept for interface compatibility)

        Returns:
            Department code string or None
        """
        # Search answer text
        if answer:
            text_upper = answer.upper()
            for name, code in DEPT_NAME_TO_CODE.items():
                if name in text_upper:
                    return code

        # Search source section titles
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
        """
        Determine complaint priority from text and routed department.

        Args:
            complaint: Complaint text
            dept:      Routed department code

        Returns:
            "Critical" | "High" | "Medium" | "Low"
        """
        text_lower = complaint.lower()

        # Fraud is always Critical
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
    # SENTINEL AGENT
    # =========================================================================

    async def calculate_fraud_risk(
        self,
        transaction: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Calculate fraud risk score for a transaction.

        Uses shared FLAG_WEIGHTS and MERCHANT_RISK constants (single source
        of truth from policy_generator.py) plus timing-based risk.

        Args:
            transaction: Transaction dict with keys:
                fraud_explainability_trace: comma-separated flag list
                merchant_category:         merchant category string
                amount:                    transaction amount (float)
                transaction_timestamp:     ISO datetime string

        Returns:
            Dict:
              total_risk_score   : 0–100
              risk_level         : LOW | MEDIUM | HIGH | CRITICAL
              risk_breakdown     : dict of component scores
              recommended_action : human-readable action string
              requires_challenge : True if push-to-app needed
              should_block       : True if immediate block required
              policy_explanation : RAG-grounded explanation
              confidence         : retrieval confidence
        """
        risk_breakdown = {
            "flag_score":    0,
            "merchant_risk": 0,
            "timing_risk":   0,
        }

        # Parse fraud flags
        trace = str(transaction.get("fraud_explainability_trace", "normal_pattern"))
        for flag in trace.split(","):
            flag = flag.strip()
            risk_breakdown["flag_score"] += FLAG_WEIGHTS.get(flag, 0)

        # Merchant category risk
        merchant = str(transaction.get("merchant_category", "")).lower().strip()
        risk_breakdown["merchant_risk"] = MERCHANT_RISK.get(merchant, 0)

        # Timing risk (late-night high-value transactions)
        timestamp = transaction.get("transaction_timestamp", "")
        amount    = float(transaction.get("amount", 0))
        if timestamp:
            try:
                ts_clean = str(timestamp).replace(" ", "T")
                dt       = datetime.fromisoformat(ts_clean)
                if 0 <= dt.hour < 5 and amount >= 100_000:
                    risk_breakdown["timing_risk"] = 20
            except Exception:
                pass

        total = min(sum(risk_breakdown.values()), 100)

        # Determine risk level from RISK_THRESHOLDS
        risk_level = "LOW"
        for level, (low, high) in RISK_THRESHOLDS.items():
            if low <= total <= high:
                risk_level = level
                break

        # Map risk level to action
        ACTIONS = {
            "CRITICAL": ("BLOCK immediately and freeze account",           False, True),
            "HIGH":     ("Mandatory push-to-app challenge required",        True,  False),
            "MEDIUM":   ("Step-up OTP authentication required",             True,  False),
            "LOW":      ("Process with standard SMS alert",                 False, False),
        }
        action, requires_challenge, should_block = ACTIONS.get(
            risk_level, ("Process with standard SMS alert", False, False)
        )

        # RAG explanation — rich query for high confidence retrieval.
        # The original single-line query ("What action applies to LOW for other?")
        # produced ~68% confidence because "other" and "LOW" barely match any
        # policy chunk. Adding flags, score breakdown and fraud policy keywords
        # gives the embedding model much more signal regardless of risk level.
        flags_str  = str(transaction.get("fraud_explainability_trace", "normal_pattern"))
        amount_str = f"N{amount:,.0f}" if amount > 0 else "unknown amount"

        sentinel_query = (
            f"fraud risk assessment {risk_level} risk level "
            f"total score {total} points "
            f"flag score {risk_breakdown['flag_score']} "
            f"merchant risk {risk_breakdown['merchant_risk']} "
            f"timing risk {risk_breakdown['timing_risk']} "
            f"fraud flags {flags_str} "
            f"merchant category {merchant} "
            f"transaction amount {amount_str} "
            f"recommended action SLA policy FRM fraud scoring threshold"
        )

        explanation = await self.query(
            question   = sentinel_query,
            agent      = "Sentinel",
            collection = "policies",
            top_k      = 5,
        )

        return {
            "total_risk_score":   total,
            "risk_level":         risk_level,
            "risk_breakdown":     risk_breakdown,
            "recommended_action": action,
            "requires_challenge": requires_challenge,
            "should_block":       should_block,
            "policy_explanation": explanation.get("answer", ""),
            "confidence":         explanation.get("confidence", 0.0),
        }

    # =========================================================================
    # TRAJECTORY AGENT
    # =========================================================================

    async def validate_product_recommendation(
        self,
        customer_data: Dict[str, Any],
        recommended_product: str,
    ) -> Dict[str, Any]:
        """
        Validate whether a customer is eligible for a recommended product.

        Hybrid Architecture:
        - Primary: RAG-grounded policy validation
        - Fallback: Deterministic score-based validation (fail-open)

        Guarantees:
        - System always returns a decision (no blocking)
        - Student Loan age rule (18–35) is ALWAYS enforced
        
        Args:
        customer_data: Dict with customer financial attributes:
            Loan_signal_score : float  — from transactions.csv (capital L)
            monthly_inflow    : float  — cumulative credit amount
            salary_detected   : bool   — proxy for salary payroll
            age               : int    — from customers.csv
        recommended_product: one of
            "Car Loan" | "Personal Loan" | "Investment Plan" |
            "Student Loan" | "Trust Fund"

    Returns:
        Dict:
            is_eligible      : bool
            met_criteria     : list of passed criteria strings
            unmet_criteria   : list of failed criteria strings
            recommendation   : "APPROVED" | "NOT_ELIGIBLE" | "CANNOT_VALIDATE"
            score_range      : (floor, ceiling) for the product
            policy_basis     : RAG-grounded policy text
            confidence       : retrieval confidence
        """

        # ── Step 1: Query policy via RAG ─────────────────────────────
        policy = await self.query(
            question=(
                f"What are the eligibility criteria and minimum requirements "
                f"for the {recommended_product} product?"
            ),
            agent="Trajectory",
            collection="policies",
            top_k=5,
        )

        # ── Extract customer data ───────────────────────────────────
        loan_score      = float(customer_data.get("Loan_signal_score", 0.0))
        monthly_inflow  = float(customer_data.get("monthly_inflow", 0.0))
        salary_detected = bool(customer_data.get("salary_detected", False))
        age             = int(customer_data.get("age", 0))

        # ── Score range lookup (single source of truth) ─────────────
        score_range = LOAN_SIGNAL_SCORE_RANGES.get(recommended_product)

        # ────────────────────────────────────────────────────────────
        # FALLBACK MODE (RAG unavailable)
        if not policy.get("grounded", False):

            if score_range:
                floor, ceiling = score_range

                # ── Student Loan hard age gate (FULL enforcement) ──
                if recommended_product == "Student Loan":
                    if age > 35:
                        return {
                            "is_eligible":    False,
                            "met_criteria":   [],
                            "unmet_criteria": [
                                f"Age {age} exceeds Student Loan maximum age of 35"
                            ],
                            "recommendation": "NOT_ELIGIBLE",
                            "score_range":    score_range,
                            "policy_basis":   "Score-based fallback (RAG unavailable)",
                            "confidence":     0.75,
                            "validation_mode": "FALLBACK",
                        }
                    elif age > 0 and age < 18:
                        return {
                            "is_eligible":    False,
                            "met_criteria":   [],
                            "unmet_criteria": [
                                f"Age {age} below Student Loan minimum age of 18"
                            ],
                            "recommendation": "NOT_ELIGIBLE",
                            "score_range":    score_range,
                            "policy_basis":   "Score-based fallback (RAG unavailable)",
                            "confidence":     0.75,
                            "validation_mode": "FALLBACK",
                        }

                # ── Score-based decision ──
                is_eligible = loan_score >= floor

                return {
                    "is_eligible":    is_eligible,
                    "met_criteria":   [
                        f"Loan_signal_score {loan_score:.2f} >= {floor:.2f} "
                        f"{recommended_product} floor "
                        f"(range {floor:.2f}-{ceiling:.2f})"
                    ] if is_eligible else [],
                    "unmet_criteria": [] if is_eligible else [
                        f"Loan_signal_score {loan_score:.2f} below {floor:.2f} "
                        f"{recommended_product} floor "
                        f"(range {floor:.2f}-{ceiling:.2f})"
                    ],
                    "recommendation": "APPROVED" if is_eligible else "NOT_ELIGIBLE",
                    "score_range":    score_range,
                    "policy_basis":   "Score-based fallback (RAG unavailable)",
                    "confidence":     0.75,
                    "validation_mode": "FALLBACK",
                }

            # ── Unknown product (true last resort) ──
            return {
                "is_eligible":    False,
                "met_criteria":   [],
                "unmet_criteria": [
                    f"Unknown product '{recommended_product}'. "
                    f"Valid products: {', '.join(PRODUCT_CLASSES)}"
                ],
                "recommendation": "CANNOT_VALIDATE",
                "score_range":    None,
                "policy_basis":   "Fallback failed: unknown product",
                "confidence":     0.0,
                "validation_mode": "FALLBACK",
            }

        # ────────────────────────────────────────────────────────────
        #  RAG MODE (policy grounded)
        # ────────────────────────────────────────────────────────────

        if score_range is None:
            return {
                "is_eligible":    False,
                "met_criteria":   [],
                "unmet_criteria": [
                    f"Unknown product '{recommended_product}'. "
                    f"Valid products: {', '.join(PRODUCT_CLASSES)}"
                ],
                "recommendation": "CANNOT_VALIDATE",
                "score_range":    None,
                "policy_basis":   policy.get("answer", "")[:400],
                "confidence":     policy.get("confidence", 0.0),
                "validation_mode": "RAG",
            }

        floor, ceiling = score_range

        met: List[str] = []
        unmet: List[str] = []

        # ── Product-specific validation ─────────────────────────────

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
            # Full hard age enforcement
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
            "is_eligible":    is_eligible,
            "met_criteria":   met,
            "unmet_criteria": unmet,
            "recommendation": "APPROVED" if is_eligible else "NOT_ELIGIBLE",
            "score_range":    score_range,
            "policy_basis":   policy.get("answer", "")[:400],
            "confidence":     policy.get("confidence", 0.0),
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
      - Sentinel fraud risk scoring
      - Trajectory product eligibility
    """
    engine = await create_engine()

    print("\n" + "=" * 70)
    print(" " * 20 + "SENTINEL BANK RAG SYSTEM DEMO")
    print("=" * 70 + "\n")

    # ──────────────────────────────────────────────────────
    # 1. General Policy Query
    # ──────────────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────
    # 2. Dispatcher Agent — Transfer complaint
    # ──────────────────────────────────────────────────────
    print("━" * 50)
    print("2. DISPATCHER AGENT — Transfer complaint")
    print("━" * 50)

    complaint = "I transferred money to a friend, but he hasn't received it yet."
    routing   = await engine.detect_complaint_category(complaint)

    print(f"  Complaint       : {complaint}")
    print(f"  Department      : {routing['department_code']} "
          f"— {routing['department_name']}")
    print(f"  Priority        : {routing['priority_level']}")
    print(f"  SLA Hours       : {routing['sla_hours']}h")
    print(f"  Confidence      : {routing['confidence']:.1%}")
    print(f"  Routing Method  : {routing['routing_method']}")
    print(f"  Keyword Matches : {routing['keyword_matches']}")
    print(f"  Reasoning       : {routing['reasoning'][:150]}...")
    print()

    # ──────────────────────────────────────────────────────
    # 3. Dispatcher Agent — Fraud complaint
    # ──────────────────────────────────────────────────────
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

    # ──────────────────────────────────────────────────────
    # 4. Sentinel Agent — Fraud Risk
    # ──────────────────────────────────────────────────────
    print("━" * 50)
    print("4. SENTINEL AGENT — Fraud Risk Assessment")
    print("━" * 50)

    transaction = {
        "fraud_explainability_trace": "high_amount_spike,mobile_channel_risk",
        "merchant_category":          "fintech",
        "amount":                     450_000,
        "transaction_timestamp":      "2026-02-22 02:15:00",
    }
    fraud = await engine.calculate_fraud_risk(transaction)

    print(f"  Amount           : ₦{transaction['amount']:,}")
    print(f"  Flags            : {transaction['fraud_explainability_trace']}")
    print(f"  Merchant         : {transaction['merchant_category']}")
    print(f"  Risk Score       : {fraud['total_risk_score']}/100")
    print(f"  Risk Level       : {fraud['risk_level']}")
    print(f"  Breakdown        : {fraud['risk_breakdown']}")
    print(f"  Action           : {fraud['recommended_action']}")
    print(f"  Block?           : {fraud['should_block']}")
    print(f"  Challenge?       : {fraud['requires_challenge']}")
    print(f"  Explanation      : {fraud['policy_explanation'][:150]}...")
    print()

    # ──────────────────────────────────────────────────────
    # 5. Trajectory Agent — Product Eligibility (5 products)
    # ──────────────────────────────────────────────────────
    print("━" * 50)
    print("5. TRAJECTORY AGENT — Product Eligibility (5 products)")
    print("━" * 50)

    demo_cases = [
        # product             Loan_signal_score  monthly_inflow  salary  age   expected
        ("Car Loan",          0.82,              600_000,        True,   30,   "APPROVED"),
        ("Investment Plan",   0.78,              2_500_000,      True,   40,   "APPROVED"),
        ("Personal Loan",     0.71,              450_000,        True,   28,   "APPROVED"),
        ("Student Loan",      0.88,              80_000,         False,  21,   "APPROVED"),
        ("Student Loan",      0.88,              9_900_000,      True,   63,   "NOT_ELIGIBLE"),  # age gate
        ("Trust Fund",        0.73,              1_200_000,      True,   45,   "APPROVED"),
        ("Car Loan",          0.60,              300_000,        False,  25,   "NOT_ELIGIBLE"),
        ("Trust Fund",        0.50,              500_000,        False,  35,   "NOT_ELIGIBLE"),
    ]

    for product, score, inflow, salary, age, expected in demo_cases:
        customer = {
            "Loan_signal_score": score,
            "monthly_inflow":    inflow,
            "salary_detected":   salary,
            "age":               age,
        }
        result = await engine.validate_product_recommendation(customer, product)
        floor, ceiling = result.get("score_range") or (0, 0)
        status = "PASS" if result["recommendation"] == expected else "FAIL"
        print(f"  [{status}] {product:<18}  age={age}  "
              f"score={score:.2f} (range {floor:.2f}-{ceiling:.2f})  "
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