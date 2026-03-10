"""
Sentinnel Bank - Sentinnel Agent

Responsibilities:
    - Accept a transaction_id from the Orchestrator
    - Fetch the transaction record from the database via BankRepository
    - Run RAG-grounded deterministic fraud scoring
    - Run ML model for anomaly probability
    - Escalate risk tier if ML signals strong anomaly
    - Apply card-channel mandatory challenge override (ATM / POS)
    - Fetch last 5 transactions for historical context (via repository)
    - Enrich with LLM audit explanation (OpenAI → Gemini fallback)
    - Return a structured result dict

Integration contract (what Orchestrator provides):
    repo       : BankRepository - async DB gateway (shared)
    rag_engine : RAGQueryEngine - vector search (shared)
    openai_llm : LLMClient[FraudResponse] - primary LLM
    gemini_llm : LLMClient[FraudResponse] - fallback LLM

The agent NEVER re-creates these — it uses exactly what is injected.

Standalone usage (dev/debug only):
    python -m app.agents.sentinel_agent
"""

import asyncio
import logging
import traceback
import pandas as pd
from typing import Any, Dict, Optional
from openai import RateLimitError
from app.agents.abstract_agent import BaseAgent
from app.data.db_connections import get_engine, get_async_session
from app.data.dataset_loader import DatasetLoader
from Backend.models import Transaction
from app.data.repository import BankRepository
from app.ml.fraud_model import MLScorer
from app.prompts.sentinel_prompt import Sentinel_System_Prompt
from app.rag.rag_system.rag_querys import RAGQueryEngine, create_engine
from app.utils.llm_client import LLMClient
from app.utils.logger import ReasoningLogger, SystemLogger
from app.utils.schemas import FraudResponse
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
from typing import List

# Card channels that always require a push-to-app biometric challenge
_CARD_CHANNELS  = {"pos", "atm"}

# Ride-hailing merchants tracked for behavioral context
_RIDE_MERCHANTS = {"Uber", "Bolt", "LagRide"}


class SentinelAgent(BaseAgent):
    """
    Fraud risk assessment agent.

    Pipeline per request:
        1. Resolve transaction (DB fetch OR live payload)
        2. Deterministic RAG fraud scoring
        3. ML anomaly probability
        4. Risk tier escalation if ML > 0.85  (LOW to MEDIUM only)
        5. Card-channel mandatory challenge override (ATM / POS)
        6. Historical context  (last 5 txns via repository, skipped for live)
        7. LLM audit explanation  (OpenAI → Gemini fallback)
        8. Assemble + return structured result

    Args:
        repo:       Async BankRepository — injected by Orchestrator.
        rag_engine: RAGQueryEngine           — injected by Orchestrator.
        openai_llm: LLMClient[FraudResponse] — primary, injected by Orchestrator.
        gemini_llm: LLMClient[FraudResponse] — fallback, injected by Orchestrator.
    """

    def __init__(
        self,
        repo:       BankRepository,
        rag_engine: RAGQueryEngine,
        openai_llm: LLMClient,
        gemini_llm: LLMClient,
    ) -> None:
        # Accept injected dependencies — never re-create them here
        self.repo       = repo
        self.rag_engine = rag_engine
        self.openai_llm = openai_llm
        self.gemini_llm = gemini_llm

        # MLScorer is stateless and cheap to build here
        # It uses the repository
        self.ml_scorer = MLScorer()


    # Main entry point

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full fraud assessment pipeline for a transaction.

        Payload modes:
            DB mode:
                {"transaction_id": "some-uuid"}
                → fetches transaction from database

            Live mode (demo / real-time):
                {
                    "amount": 15000,
                    "channel": "pos",
                    "merchant_name": "Shoprite",
                    "merchant_category": "retail",
                    "transaction_status": "pending",
                    "transaction_timestamp": "2025-01-01T12:00:00",
                    "customer_id": "optional-for-history",
                    ...
                }
                -> scores the payload directly, no DB fetch

        Returns:
            Structured fraud result dict.
        """
        transaction_id: Optional[str] = payload.get("transaction_id")
        is_live = _is_live_payload(payload)

        SystemLogger.log_event(
            event_type="sentinel_started",
            message="SentinelAgent started",
            metadata={
                "transaction_id": transaction_id,
                "mode": "live" if is_live else "db",
            },
        )

        try:
            # Validate + fetch transaction from DB (async)
            if is_live:
                # Use payload directly — demo/real-time path
                transaction = payload
                transaction_id = transaction_id or "live"
                all_transactions = []

                SystemLogger.log_event(
                    event_type="live_transaction_received",
                    message="Processing live transaction payload",
                    metadata={
                        "amount":   transaction.get("amount"),
                        "channel":  transaction.get("channel"),
                        "merchant": transaction.get("merchant_name"),
                    },
                )

            else:
                # Fetch from database — normal agent pipeline path
                if not transaction_id:
                    raise ValueError(
                        "Payload must contain 'transaction_id' "
                        "or a full live transaction (amount + channel)."
                    )

                transaction = await self.repo.get_transaction(transaction_id)

                if transaction is None:
                    raise ValueError(
                        f"Transaction '{transaction_id}' not found in database."
                    )

                SystemLogger.log_event(
                    event_type="transaction_fetched",
                    message="Transaction fetched from database",
                    metadata={
                        "transaction_id": transaction_id,
                        "amount":         transaction.get("amount"),
                        "channel":        transaction.get("channel"),
                        "merchant":       transaction.get("merchant_name"),
                        "status":         transaction.get("transaction_status"),
                    },
                )

                # Fetch history for context (DB mode only)
                customer_id = transaction.get("customer_id")
                all_transactions = (
                    await self.repo.get_customer_transactions(customer_id)
                    if customer_id else []
                )

            # RAG deterministic fraud scoring
            fraud_result = await self.rag_engine.calculate_fraud_risk(transaction)

            SystemLogger.log_event(
                event_type="rag_fraud_scoring_completed",
                message="RAG fraud policy scoring completed",
                metadata={
                    "transaction_id": transaction_id,
                    "risk_level":     fraud_result["risk_level"],
                    "total_score":    fraud_result["total_risk_score"],
                },
            )

            # Capture RAG decision-authoritative, LLM must not override
            rag_decision = {
                "total_risk_score":   fraud_result["total_risk_score"],
                "risk_level":         fraud_result["risk_level"],
                "recommended_action": fraud_result["recommended_action"],
                "requires_challenge": fraud_result["requires_challenge"],
                "should_block":       fraud_result["should_block"],
                "confidence":         fraud_result["confidence"],
                "risk_breakdown":     fraud_result["risk_breakdown"],
                "policy_explanation": fraud_result["policy_explanation"],
            }

            # # Fetch transaction history via repository
            # customer_id = transaction.get("customer_id")
            # if customer_id:
            #     all_transactions = await self.repo.get_customer_transactions(customer_id)
            #     # Ensure we represent history as DataFrame for the builder
            #     history_df = pd.DataFrame(all_transactions) if all_transactions else pd.DataFrame()
            # else:
            #     all_transactions = []
            #     history_df = pd.DataFrame()

            # ML anomaly probability
            ml_probability = self.ml_scorer.predict(transaction)
            rag_decision["ml_probability"] = round(ml_probability, 3)

            SystemLogger.log_event(
                event_type="ml_scoring_completed",
                message="ML fraud probability computed",
                metadata={"ml_probability": rag_decision["ml_probability"]},
            )

            # Risk escalation: LOW → MEDIUM if ML strongly flags
            if ml_probability > 0.85 and rag_decision["risk_level"] == "LOW":
                rag_decision["risk_level"]         = "MEDIUM"
                rag_decision["recommended_action"] = (
                    "Escalated to MEDIUM — ML anomaly signal exceeds 0.85 threshold"
                )
                SystemLogger.log_event(
                    event_type="risk_escalated",
                    message="Risk tier escalated LOW → MEDIUM via ML signal",
                    metadata={"ml_probability": ml_probability},
                )

            # Card-channel mandatory challenge override
            if transaction.get("channel") in _CARD_CHANNELS:
                rag_decision["requires_challenge"] = True
                rag_decision["recommended_action"] = (
                    "Mandatory push-to-app biometric challenge "
                    "(card channel policy override)"
                )

            # Historical context formatting for LLM
            history_context = _format_history_context(
                customer_id=transaction.get("customer_id"),
                current_transaction_id=transaction_id,
                history_data=all_transactions,
            )
            # LLM audit explanation 
            llm_input  = self._build_explanation_prompt(
                transaction, rag_decision, history_context
            )
            llm_result = await self._call_llm_with_fallback(llm_input)

            # Assemble final result 
            result = self._build_result(
                transaction_id = transaction_id,
                transaction    = transaction,
                rag_decision   = rag_decision,
                llm_result     = llm_result,
            )

            ReasoningLogger.log(agent_name="SentinelAgent", payload=result)

            SystemLogger.log_event(
                event_type="sentinel_completed",
                message="SentinelAgent execution completed",
                metadata={
                    "risk_level":   result["risk_level"],
                    "should_block": result["should_block"],
                    "mode":         "live" if is_live else "db",
                },
            )

            return result

        except Exception as e:
            SystemLogger.log_event(
                event_type="sentinel_failed",
                message=str(e),
                metadata={
                    "transaction_id": transaction_id,
                    "trace":          traceback.format_exc(),
                },
            )
            raise e

    
    # Private helpers

    def _build_explanation_prompt(
        self,
        transaction:     Dict[str, Any],
        rag_decision:    Dict[str, Any],
        history_context: str,
    ) -> str:
        return (
            f"Transaction Details:\n"
            f"  ID          : {transaction.get('transaction_id', 'live')}\n"
            f"  Amount      : ₦{transaction.get('amount', 0):,.2f}\n"
            f"  Channel     : {transaction.get('channel')}\n"
            f"  Merchant    : {transaction.get('merchant_name')} "
            f"({transaction.get('merchant_category')})\n"
            f"  Status      : {transaction.get('transaction_status')}\n"
            f"  Timestamp   : {transaction.get('transaction_timestamp')}\n"
            f"  Fraud Flags : {transaction.get('fraud_explainability_trace', 'N/A')}\n\n"
            f"Risk Assessment:\n"
            f"  Risk Level  : {rag_decision['risk_level']}\n"
            f"  Total Score : {rag_decision['total_risk_score']}\n"
            f"  ML Prob     : {rag_decision.get('ml_probability', 'N/A')}\n"
            f"  Action      : {rag_decision['recommended_action']}\n"
            f"  Block?      : {rag_decision['should_block']}\n\n"
            f"{history_context}\n\n"
            f"Provide a clear, audit-ready explanation of this fraud assessment, "
            f"referencing the transaction behaviour against historical patterns."
        )

    async def _call_llm_with_fallback(self, user_input: str) -> FraudResponse:
        if self.openai_llm:
            try:
                result = await self.openai_llm.generate(
                    system_prompt=Sentinel_System_Prompt,
                    user_input=user_input,
                )
                if isinstance(result, FraudResponse):
                    return result
            except RateLimitError:
                SystemLogger.log_event(
                    event_type="llm_fallback",
                    message="OpenAI rate limit — falling back to Gemini",
                )

        result = await self.gemini_llm.generate(
            system_prompt=Sentinel_System_Prompt,
            user_input=user_input,
        )
        if isinstance(result, FraudResponse):
            return result
        raise ValueError("Neither LLM returned a valid FraudResponse")

    def _build_result(
        self,
        transaction_id: str,
        transaction:    Dict[str, Any],
        rag_decision:   Dict[str, Any],
        llm_result:     FraudResponse,
    ) -> Dict[str, Any]:
        result = llm_result.model_dump()

        # RAG + ML decisions are authoritative
        result["total_risk_score"]   = rag_decision["total_risk_score"]
        result["risk_level"]         = rag_decision["risk_level"]
        result["recommended_action"] = rag_decision["recommended_action"]
        result["requires_challenge"] = rag_decision["requires_challenge"]
        result["should_block"]       = rag_decision["should_block"]
        result["confidence"]         = rag_decision["confidence"]
        result["risk_breakdown"]     = rag_decision["risk_breakdown"]
        result["ml_probability"]     = rag_decision.get("ml_probability")

        # Combine policy explanation + LLM narrative
        result["policy_explanation"] = (
            f"Policy Basis:\n{rag_decision['policy_explanation']}\n\n"
            f"LLM Explanation:\n{result.get('policy_explanation', '')}"
        )

        # Transaction context (for audit trail)
        result["transaction_id"]             = transaction_id
        result["amount"]                     = transaction.get("amount")
        result["channel"]                    = transaction.get("channel")
        result["merchant_category"]          = transaction.get("merchant_category")
        result["merchant_name"]              = transaction.get("merchant_name")
        result["transaction_status"]         = transaction.get("transaction_status")
        result["transaction_timestamp"]      = transaction.get("transaction_timestamp")
        result["fraud_explainability_trace"] = transaction.get("fraud_explainability_trace")
        result["agent"]                      = "SentinelAgent"

        return result

# Module-level helpers (no self, also usable outside the class)

def _is_live_payload(payload: Dict[str, Any]) -> bool:
    """
    Returns True if the payload is a full live transaction dict
    (has amount + channel) rather than just a transaction_id pointer.
    """
    return "amount" in payload and "channel" in payload


def _format_history_context(
    customer_id:            Optional[str],
    current_transaction_id: Optional[str],
    history_data:           List[Dict[str, Any]],
) -> str:
    """Format last-5-transactions list into an LLM-readable context string."""
    if not customer_id:
        return "No customer ID available, historical context unavailable."

    history = [
        t for t in history_data
        if t.get("transaction_id") != current_transaction_id
    ][:5]

    if not history:
        return (
            "No prior transaction history found for this customer. "
            "IMPORTANT: Do not penalise this transaction solely due "
            "to lack of history (cold-start customer)."
        )

    lines = ["Customer's Last 5 Transactions:"]
    for t in history:
        lines.append(
            f"  • {t.get('transaction_timestamp')}  "
            f"₦{t.get('amount', 0):,.2f}  "
            f"via {t.get('channel')}  "
            f"at {t.get('merchant_name')}  "
            f"({t.get('transaction_status')})"
        )
    return "\n".join(lines)


# Standalone entry point (dev / debug only)

async def _main() -> None:
    """
    Standalone runner for direct agent testing without the full Orchestrator.
    Mirrors the exact async DB stack used in production.
    """
    from openai import AsyncOpenAI
    from google import genai
    from sqlalchemy import select
    from Backend.models import Transaction

    # Bootstrap infrastructure 
    engine = get_engine()

    loader = DatasetLoader(engine)
    await loader.seed()

    repo = BankRepository(engine)

    health = await repo.health_check()
    print(f"[Dev] DB health: {health}")

    rag_engine = await create_engine()

    openai_llm = LLMClient(
        client=AsyncOpenAI(api_key=OPENAI_API_KEY),
        model_name="gpt-4o",
        response_schema=FraudResponse,
    )
    gemini_llm = LLMClient(
        client=genai.Client(api_key=GEMINI_API_KEY),
        model_name="gemini-2.0-flash",
        response_schema=FraudResponse,
    )

    agent = SentinelAgent(
        repo=repo,
        rag_engine=rag_engine,
        openai_llm=openai_llm,
        gemini_llm=gemini_llm,
    )

    # Fetch a real transaction_id from the database 
    async with get_async_session(engine) as session:
        row = await session.execute(
            select(Transaction.transaction_id).limit(1).offset(9)
        )
        transaction_id = row.scalar()

    print(f"[Dev] Testing with transaction_id: {transaction_id}")

    result = await agent.run({"transaction_id": transaction_id})
 
    _print_result(result)

    # Live mode (demo)
    print("\n[Dev] Live mode — simulated demo transaction")
    live_payload = {
        "amount":               75000.00,
        "channel":              "pos",
        "merchant_name":        "Shoprite Lekki",
        "merchant_category":    "retail",
        "transaction_status":   "pending",
        "transaction_timestamp": "2025-06-01T14:32:00",
        "customer_id":          None,   # no history for demo
    }
    result = await agent.run(live_payload)
    _print_result(result)


def _print_result(result: Dict[str, Any]) -> None:
    print("\n=== SENTINEL OUTPUT ===")
    for k, v in result.items():
        if k != "policy_explanation":
            print(f"  {k:<30}: {v}")
    print(f"\n  policy_explanation:\n{result.get('policy_explanation', '')}")


if __name__ == "__main__":
    asyncio.run(_main())




# # This contains the Fraud/risk assessment

# from typing import Dict, Any
# import pandas as pd
# import numpy as np
# from app.agents.abstract_agent import BaseAgent
# from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
# from app.utils.logger import ReasoningLogger, SystemLogger
# from app.utils.schemas import FraudResponse
# from app.utils.llm_client import LLMClient
# from openai import RateLimitError, AsyncOpenAI
# from google import genai
# from app.prompts.sentinel_prompt import Sentinel_System_Prompt
# from app.rag.rag_system.rag_querys import RAGQueryEngine
# from app.rag.rag_system.chromadb_config import initialize_chromadb
# import asyncio
# from app.database.dataset_loader import DatasetLoader
# from app.data.repository import BankRepository
# from app.ml.fraud_model import MLScorer
# from app.rag.rag_system.rag_querys import create_engine
# import traceback


# # Create a class that assess fraud/risk and explains why transaction was flagged


# class SentinelAgent(BaseAgent):
#     """
#     SentinelAgent performs fraud assessment using:
#     1. Deterministic risk scoring (RAG policy engine)
#     2. Business policy overrides (card channels)
#     3. LLM explanation overlay
#     4. Structured schema response
#     """

#     # Initialize the agent
#     def __init__(
#         self,
#         repo: BankRepository,
#         rag_engine: RAGQueryEngine,
#         openai_llm: LLMClient,
#         gemini_llm: LLMClient,
#     ):

#         self.repo = repo
#         self.rag_engine = rag_engine
#         self.openai_llm = openai_llm
#         self.gemini_llm = gemini_llm

#         # Repository abstracts dataset access
#         self.repo = repo

#         # Initialize the RAG engine for fraud scoring + policy explanation grounding
#         self.client, self.config = initialize_chromadb()
#         self.rag_engine = RAGQueryEngine(self.client, self.config)

#         # Initialize the MLScorer
#         self.ml_scorer = MLScorer(self.repo.dataset_loader)

#         # Initialize OpenAI client only if key is set
#         if OPENAI_API_KEY:
#             self.openai_llm = LLMClient(
#                 client=AsyncOpenAI(api_key=OPENAI_API_KEY),
#                 model_name="gpt-4o",
#                 response_schema=FraudResponse,
#             )
#         # Fallback
#         self.gemini_llm = LLMClient(
#             client=genai.Client(api_key=GEMINI_API_KEY),
#             model_name="gemini-2.0-flash",
#             response_schema=FraudResponse,
#         )

#     # Fraud assessment flow
#     async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
#         """
#         Performs fraud detection and enforcement logic.

#         Steps:
#         1. Fetch transaction
#         2. Run deterministic fraud scoring
#         3. Run ML model → get fraud_probability (0–1)
#         4. Attach fraud_probability to output
#         5. If ML probability is very high → increase risk by 1 tier
#         6. Apply card override
#         7. Add LLM explanation overlay
#         8. Log decision
#         """
#         # Validate transaction payload
#         if not payload:
#             raise ValueError("Transaction payload is required.")

#         try:
#             # If a transaction_id is passed and it's not a live test payload from app.py, try fetching it.
#             # Otherwise, we use the payload itself as the transaction dictionary.
#             transaction_id = payload.get("transaction_id")

#             SystemLogger.log_event(
#             event_type="SentinelAgent_started",
#             message="SentinelAgent exceution started",
#             metadata={"transaction_id": transaction_id}
#             )

#             # Determine if this is a live incoming transaction or an existing one
#             # Checking for necessary keys to consider it a "full" transaction object
#             if "amount" in payload and "account_number" in payload:
#                 transaction = payload
#                 print("Processing live transaction payload:", transaction)
#             else:
#                 if not transaction_id:
#                     raise ValueError("transaction_id is required if full transaction payload is not provided.")
#                 # Fetch transaction from the repository
#                 transaction = self.repo.get_transactions(transaction_id)
#                 print("Transaction ID:", transaction_id)
#                 print("Transaction fetched:", transaction)

#             SystemLogger.log_event(
#                 event_type="Transaction_data_fetched",
#                 message="Transaction retrieved",
#                 metadata={"transaction_id": transaction_id, 
#                           "amount": transaction.get("amount"),
#                           "channel": transaction.get("channel")}
#             )

#             # Deterministic fraud scoring engine
#             fraud_result = await self.rag_engine.calculate_fraud_risk(transaction)

#             SystemLogger.log_event(
#                 event_type="RAG_fraud_scoring_completed",
#                 message="RAG-based fraud policy validation completed",
#                 metadata={"transaction_id": transaction_id, "risk_level": fraud_result["risk_level"]}
#             )

            
#             # Extract structured result
#             base_result = {
#             "total_risk_score": fraud_result["total_risk_score"],
#             "risk_level": fraud_result["risk_level"],
#             "recommended_action": fraud_result["recommended_action"],
#             "requires_challenge": fraud_result["requires_challenge"],
#             "should_block": fraud_result["should_block"],
#             "confidence": fraud_result["confidence"],
#             "risk_breakdown": fraud_result["risk_breakdown"],
#             "policy_explanation": fraud_result["policy_explanation"]
#             }

#             # ML Fraud Probability 
#             ml_probability = self.ml_scorer.predict(transaction)

#             base_result["ml_probability"] = round(ml_probability, 3)

#             # Only escalate LOW → MEDIUM if ML strongly indicates anomaly
#             if ml_probability > 0.85 and base_result["risk_level"] == "LOW":
#                 base_result["risk_level"] = "MEDIUM"
#                 base_result["recommended_action"] = \
#                             "Escalated to MEDIUM risk due to ML anomaly signal"
            
#             SystemLogger.log_event(
#                 event_type="ML_scoring_completed",
#                 message="Fraud scoring computed",
#                 metadata={"ml_probability": base_result["ml_probability"]}
#             )

#             # Card-Channel Mandatory Override 
#             # All ATM / POS transactions must require push-to-app
#             card_channels = ['pos', 'atm']

#             if transaction.get('channel') in card_channels:
#                 base_result["requires_challenge"] = True
#                 base_result['recommended_action'] = "Mandatory push-to-app biometric challenge (Card channel policy override)"

            

#             # Gather Historical Context
#             account_num = transaction.get("account_number")
#             if account_num:
#                 # Check how repository stores transactions. They store either `account_number` or `account_id`.
#                 # We filter the raw dataset loader dataframe directly to get past behavior for this specific account
#                 history_df = self.repo.dataset_loader.transactions

#                 filters = []
#                 if "account_number" in history_df.columns:
#                     filters.append(history_df["account_number"] == account_num)
#                 if "account_id" in history_df.columns and transaction.get("account_id"):
#                     filters.append(history_df["account_id"] == transaction.get("account_id"))

#                 if filters:
#                     # Combine filters with logical OR
#                     combined_filter = np.logical_or.reduce(filters)
#                     history_df = history_df[combined_filter]
#                 else:
#                     history_df = history_df.head(0) # Empty dataframe if no matching columns
#                 # Remove the current transaction from history if it exists
#                 # (By comparing transaction_id if present)
#                 txn_id = transaction.get("transaction_id")
#                 if txn_id:
#                     history_df = history_df[history_df["transaction_id"] != txn_id]

#                 # Take last 5 transactions for context
#                 historical_txns = history_df.tail(5).to_dict('records')
#             else:
#                 historical_txns = []

#             history_context = ""
#             if historical_txns:
#                 history_context = "User's Last 5 Transactions:\n"
#                 for t in historical_txns:
#                     history_context += f"- {t.get('transaction_timestamp')}: {t.get('amount')} via {t.get('channel')} (Status: {t.get('transaction_status')})\n"
#             else:
#                 history_context = "User has NO prior transaction history (Cold Start). IMPORTANT: Do not automatically penalize this transaction or assume fraud strictly due to lack of history."


#             # LLM Explanation
#             explanation_payload = f"""
#                 Transaction:
#                 {transaction}

#                 Risk Level: {base_result['risk_level']}
#                 Total Score: {base_result['total_risk_score']}
#                 Action: {base_result['recommended_action']}

#                 Historical Context:
#                 {history_context}

#                 Provide a clear audit-ready explanation considering the transaction against their historical behavior.
#                 """

            
#             try:
#                 llm_response = await self.openai_llm.generate(
#                 system_prompt=Sentinel_System_Prompt,
#                 user_input=explanation_payload
#                 )
#             except Exception as e:
#                 print(f"OpenAI error: {e}. Falling back to Gemini...")
#                 llm_response = await self.gemini_llm.generate(
#                     system_prompt=Sentinel_System_Prompt,
#                     user_input=explanation_payload
#                     )

#                 SystemLogger.log_event(
#                     event_type="LLM_explanation_completed",
#                     message="Sentinel LLM explanation generated"
#                 )

#             # Extract structured LLM output
#             result = llm_response.model_dump()

#             # Preserve deterministic fraud engine decisions
#             result["total_risk_score"] = base_result["total_risk_score"]
#             result["risk_level"] = base_result["risk_level"]
#             result["recommended_action"] = base_result["recommended_action"]
#             result["requires_challenge"] = base_result["requires_challenge"]
#             result["should_block"] = base_result["should_block"]
#             result["confidence"] = base_result["confidence"]
#             result["risk_breakdown"] = base_result["risk_breakdown"]

#             # Merge policy_explanation safely with LLM Explanation
#             result["policy_explanation"] = (
#                 f"Policy Basis:\n{base_result['policy_explanation']}\n\n"
#                 f"LLM Explanation:\n{result.get('policy_explanation', '')}"
#             )

#             # Tag the Agent
#             result["agent"] = "SentinelAgent"

#             # Log reasoning trace
#             ReasoningLogger.log(
#                 agent_name="SentinelAgent",
#                 payload=result
#             )

#             SystemLogger.log_event(
#                 event_type="SentinelAgent_completed",
#                 message=f"SentinelAgent execution completed",
#                 metadata={"final_risk_level": result["risk_level"], "should_block": result["should_block"]}
#             )

#             return result
#         except Exception as e:

#             SystemLogger.log_event(
#                 event_type="SentinelAgent failed",
#                 message=str(e),
#                 metadata={"transaction_id": transaction_id, "traceback": traceback.format_exc()}
#             )
#             raise e


# # Testing
# async def main():
#     # Infrastructure Setup (Same as Orchestrator)

#     dataset_loader = DatasetLoader()
#     await dataset_loader.load()
#     repo = BankRepository(dataset_loader)

#     rag_engine = await create_engine()

#     openai_llm = LLMClient(
#         client=AsyncOpenAI(api_key=OPENAI_API_KEY),
#         model_name="gpt-4o",
#         response_schema=FraudResponse,
#     )


#     gemini_llm = LLMClient(     
#     client=genai.Client(api_key=GEMINI_API_KEY),
#     model_name="gemini-2.5-flash",
#     response_schema=FraudResponse

#     )

#     agent = SentinelAgent(
#         repo=repo, rag_engine=rag_engine, openai_llm=openai_llm, gemini_llm=gemini_llm
#     )

#     # Select a real transaction ID from the dataset
#     transaction_id = agent.repo.dataset_loader.transactions.iloc[9]["transaction_id"]

#     result = await agent.run({"transaction_id": transaction_id})
#     print("\n=== SENTINEL OUTPUT ===")
#     print(result)


# if __name__ == "__main__":
#     asyncio.run(main())
