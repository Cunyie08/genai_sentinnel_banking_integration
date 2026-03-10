# TRAJECTORY AGENT

"""
Sentinnel Bank — Trajectory Agent

Responsibilities:
    - Accept a customer_id from the Orchestrator
    - Fetch the full behavioral profile from the database via BankRepository
      (Loan_signal_score, monthly_inflow, salary_detected, uber_tracker,
       account_type, current_balance, age — all pre-aggregated by repo)
    - Run the RecommendationEngine (proactive product suggestion)
    - Validate the recommendation via RAG policy engine
    - Enrich with LLM audit explanation (OpenAI → Gemini fallback)
    - Return a structured, governance-safe result dict

Integration contract (what Orchestrator provides):
    repo       : BankRepository - async DB gateway (shared)
    rag_engine : RAGQueryEngine - vector search (shared)
    openai_llm : LLMClient[TrajectoryResponse] - primary LLM
    gemini_llm : LLMClient[TrajectoryResponse] - fallback LLM

The agent NEVER re-creates these — it uses exactly what is injected.
The LLM NEVER overrides eligibility or product decisions.

Standalone usage (dev/debug only):
    python -m app.agents.trajectory_agent
"""

import asyncio
import traceback
from typing import Any, Dict, Optional

from openai import RateLimitError

from app.agents.abstract_agent import BaseAgent
from app.data.db_connections import get_engine, get_async_session
from app.data.dataset_loader import DatasetLoader
from Backend.models import Transaction
from app.data.repository import BankRepository
from app.prompts.trajectory_prompt import Trajectory_System_Prompt
from app.rag.rag_system.rag_querys import RAGQueryEngine, create_engine
from app.rag.rag_system.recommend_product import RecommendationEngine
from app.utils.llm_client import LLMClient
from app.utils.logger import ReasoningLogger, SystemLogger
from app.utils.schemas import TrajectoryResponse
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY


class TrajectoryAgent(BaseAgent):
    """
    Product recommendation and eligibility agent.

    Pipeline per request:
        1. Fetch pre-aggregated behavioral profile from DB  (async repository)
        2. Proactive product recommendation                 (RecommendationEngine)
        3. RAG policy validation                            (eligibility gate)
        4. LLM audit explanation                            (OpenAI → Gemini fallback)
        5. Assemble + return structured governance-safe result

    Args:
        repo:       Async BankRepository - injected by Orchestrator.
        rag_engine: RAGQueryEngine - injected by Orchestrator.
        openai_llm: LLMClient[TrajectoryResponse] - primary, injected by Orchestrator.
        gemini_llm: LLMClient[TrajectoryResponse] - fallback, injected by Orchestrator.
    """

    def __init__(
        self,
        repo:       BankRepository,
        rag_engine: RAGQueryEngine,
        openai_llm: LLMClient,
        gemini_llm: LLMClient,
    ) -> None:
        super().__init__()

        # Accept injected dependencies — never re-create them here
        self.repo       = repo
        self.rag_engine = rag_engine
        self.openai_llm = openai_llm
        self.gemini_llm = gemini_llm

        # RecommendationEngine is stateless — safe to build here
        self.recommender = RecommendationEngine()


    # Main entry point

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run the full product recommendation pipeline for a customer.

        Args:
            payload: Must contain "customer_id".
                     e.g. {"customer_id": "some-uuid", ...}

        Returns:
            Structured recommendation result dict with primary product,
            EMI, DSR, eligibility, RAG validation, and LLM explanation.

        Raises:
            ValueError  if customer_id is missing or customer not found.
            Exception   re-raised to Orchestrator after logging.
        """
        customer_id: Optional[str] = payload.get("customer_id")

        SystemLogger.log_event(
            event_type="trajectory_started",
            message="TrajectoryAgent started",
            metadata={"customer_id": customer_id},
        )

        try:
            # Validate input 
            if not customer_id:
                raise ValueError("customer_id is required for TrajectoryAgent.")

            # Fetch pre-aggregated behavioral profile from DB (async) 
            #
            # repo.get_customer_profile() returns all signals already computed:
            #   Loan_signal_score, monthly_inflow, monthly_outflow,
            #   salary_detected, uber_tracker, recommended_product,
            #   account_type, current_balance, age, transaction_count
            #
            # No DataFrames, no manual aggregation needed here.
            profile = await self.repo.get_customer_profile(customer_id)

            if profile is None:
                raise ValueError(
                    f"Customer '{customer_id}' not found in database."
                )

            SystemLogger.log_event(
                event_type="profile_fetched",
                message="Customer behavioral profile fetched from database",
                metadata={
                    "customer_id":       customer_id,
                    "transaction_count": profile.get("transaction_count", 0),
                    "loan_signal_score": profile.get("Loan_signal_score"),
                    "salary_detected":   profile.get("salary_detected"),
                    "uber_tracker":      profile.get("uber_tracker"),
                    "account_type":      profile.get("account_type"),
                },
            )

            # Build policy input from pre-aggregated profile 
            #
            # All signal fields come directly from the repository — no manual
            # DataFrame computation. The repository's get_customer_profile()
            # handles Loan_signal_score, monthly_inflow, salary_detected,
            # uber_tracker, account_type, and current_balance aggregation.
            policy_input = self._build_policy_input(profile)

            # Proactive product recommendation
            recommendation = await self.recommender.recommend(policy_input)

            SystemLogger.log_event(
                event_type="recommendation_made",
                message="Primary product recommendation computed",
                metadata={
                    "primary_product": recommendation.get("primary_product"),
                    "confidence":      recommendation.get("confidence"),
                    "all_qualifying":  recommendation.get("all_qualifying"),
                },
            )

            # If no product qualifies, return early — no LLM call needed
            if not recommendation.get("primary_product"):
                SystemLogger.log_event(
                    event_type="no_product_qualified",
                    message="No product qualified for this customer profile",
                    metadata={"customer_id": customer_id},
                )
                return {
                    "agent":               "TrajectoryAgent",
                    "customer_id":         customer_id,
                    "primary_product":     None,
                    "all_qualifying":      [],
                    "monthly_emi":         0,
                    "tenure_months":       0,
                    "dsr_ratio":           "N/A",
                    "dsr_warning":         False,
                    "is_eligible":         False,
                    "confidence":          recommendation.get("confidence", 0.0),
                    "policy_validation":   None,
                    "reasoning":           "No product qualified for this customer profile.",
                }

            primary_product = recommendation["primary_product"]

            # RAG policy validation (eligibility gate)
            validation = await self.rag_engine.validate_product_recommendation(
                customer_data=policy_input,
                recommended_product=primary_product,
            )

            SystemLogger.log_event(
                event_type="rag_validation_completed",
                message="RAG policy validation completed",
                metadata={
                    "primary_product": primary_product,
                    "is_eligible":     validation.get("is_eligible"),
                    "confidence":      validation.get("confidence"),
                },
            )

            # LLM audit explanation 
            llm_input  = self._build_explanation_prompt(
                customer_id, policy_input, recommendation, validation
            )
            llm_result = await self._call_llm_with_fallback(llm_input)

            # Assemble final result 
            result = self._build_result(
                customer_id    = customer_id,
                policy_input   = policy_input,
                recommendation = recommendation,
                validation     = validation,
                llm_result     = llm_result,
            )

            ReasoningLogger.log(agent_name="TrajectoryAgent", payload=result)

            SystemLogger.log_event(
                event_type="trajectory_completed",
                message="TrajectoryAgent execution completed",
                metadata={
                    "primary_product": result["primary_product"],
                    "is_eligible":     result["is_eligible"],
                },
            )

            return result

        except Exception as exc:
            SystemLogger.log_event(
                event_type="trajectory_failed",
                message=str(exc),
                metadata={
                    "customer_id": customer_id,
                    "trace":       traceback.format_exc(),
                },
            )
            raise


    # Private helpers

    def _build_policy_input(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the exact fields RecommendationEngine.recommend() and
        RAGQueryEngine.validate_product_recommendation() expect from the
        pre-aggregated customer profile returned by the repository.

        All signals are already computed by repo.get_customer_profile() —
        no DataFrame access or manual aggregation here.
        """
        return {
            "Loan_signal_score": float(profile.get("Loan_signal_score") or 0.0),
            "monthly_inflow":    float(profile.get("monthly_inflow")    or 0.0),
            "salary_detected":   bool( profile.get("salary_detected")   or False),
            "uber_tracker":      int(  profile.get("uber_tracker")      or 0),
            "age":               int(  profile.get("age")               or 0),
            "account_type":      str(  profile.get("account_type")      or "savings"),
            "current_balance":   float(profile.get("current_balance")   or 0.0),
        }

    def _build_explanation_prompt(
        self,
        customer_id:    str,
        policy_input:   Dict[str, Any],
        recommendation: Dict[str, Any],
        validation:     Dict[str, Any],
    ) -> str:
        """Build the LLM input for the product recommendation audit explanation."""
        return (
            f"Customer ID      : {customer_id}\n\n"
            f"Behavioral Profile:\n"
            f"  Loan Signal Score : {policy_input['Loan_signal_score']:.4f}\n"
            f"  Score Range       : {recommendation.get('score_range')}\n"
            f"  Monthly Inflow    : ₦{policy_input['monthly_inflow']:,.2f}\n"
            f"  Salary Detected   : {policy_input['salary_detected']}\n"
            f"  Uber/Bolt Trips   : {policy_input['uber_tracker']}\n"
            f"  Age               : {policy_input['age']}\n"
            f"  Account Type      : {policy_input['account_type']}\n"
            f"  Current Balance   : ₦{policy_input['current_balance']:,.2f}\n\n"
            f"Recommendation:\n"
            f"  Primary Product   : {recommendation.get('primary_product')}\n"
            f"  All Qualifying    : {recommendation.get('all_qualifying')}\n"
            f"  Monthly EMI       : ₦{recommendation.get('monthly_emi', 0):,.2f}\n"
            f"  Tenure            : {recommendation.get('tenure_months')} months\n"
            f"  DSR Ratio         : {recommendation.get('dsr_ratio')}\n"
            f"  DSR Warning       : {recommendation.get('dsr_warning')}\n"
            f"  Confidence        : {recommendation.get('confidence')}\n\n"
            f"RAG Policy Validation:\n"
            f"  Is Eligible       : {validation.get('is_eligible')}\n"
            f"  Recommendation    : {validation.get('recommendation')}\n"
            f"  Policy Basis      : {validation.get('policy_basis', '')}\n\n"
            f"Provide a clear, audit-ready explanation aligned with PRS-001 policy, "
            f"covering eligibility rationale, EMI affordability, and DSR compliance."
        )

    async def _call_llm_with_fallback(self, user_input: str) -> TrajectoryResponse:
        """
        Call OpenAI primary. On RateLimitError fall back to Gemini.
        Returns a TrajectoryResponse Pydantic object.
        """
        if self.openai_llm:
            try:
                result = await self.openai_llm.generate(
                    system_prompt=Trajectory_System_Prompt,
                    user_input=user_input,
                )
                if isinstance(result, TrajectoryResponse):
                    return result
                return TrajectoryResponse.model_validate(result)
            except RateLimitError:
                SystemLogger.log_event(
                    event_type="llm_fallback",
                    message="OpenAI rate limit hit — falling back to Gemini",
                )

        result = await self.gemini_llm.generate(
            system_prompt=Trajectory_System_Prompt,
            user_input=user_input,
        )
        if isinstance(result, TrajectoryResponse):
            return result
        return TrajectoryResponse.model_validate(result)

    def _build_result(
        self,
        customer_id:    str,
        policy_input:   Dict[str, Any],
        recommendation: Dict[str, Any],
        validation:     Dict[str, Any],
        llm_result:     TrajectoryResponse,
    ) -> Dict[str, Any]:
        """
        Merge recommendation engine output + RAG validation + LLM explanation
        into the final structured result dict.

        RecommendationEngine and RAG decisions are always authoritative.
        The LLM explanation is layered on top — it cannot override
        is_eligible, primary_product, EMI, DSR, or confidence.
        """
        structured = llm_result.model_dump()

        # Assemble LLM narrative from structured response fields
        llm_explanation = (
            f"{structured.get('explanation', '')}\n\n"
            f"Risk Summary:\n{structured.get('risk_summary', '')}\n\n"
            f"Governance:\n{structured.get('governance_note', '')}"
        )

        return {
            # Identity
            "agent":                   "TrajectoryAgent",
            "customer_id":             customer_id,

            # Recommendation engine (authoritative)
            "primary_product":         recommendation["primary_product"],
            "all_qualifying_products": recommendation.get("all_qualifying", []),
            "monthly_emi":             recommendation.get("monthly_emi", 0),
            "tenure_months":           recommendation.get("tenure_months", 0),
            "dsr_ratio":               recommendation.get("dsr_ratio", "N/A"),
            "dsr_warning":             recommendation.get("dsr_warning", False),
            "score_range":             recommendation.get("score_range"),
            "confidence":              recommendation.get("confidence", 0.0),
            "met_criteria":            recommendation.get("met_criteria", []),
            "unmet_criteria":          recommendation.get("unmet_criteria", []),

            # Eligibility (authoritative — from recommendation engine + RAG)
            "is_eligible":             recommendation.get("is_eligible", False),

            # RAG policy validation (full dict preserved for audit)
            "policy_validation":       validation,

            # Behavioral signals used (for audit traceability)
            "loan_signal_score":       policy_input["Loan_signal_score"],
            "monthly_inflow":          policy_input["monthly_inflow"],
            "salary_detected":         policy_input["salary_detected"],
            "uber_tracker":            policy_input["uber_tracker"],
            "account_type":            policy_input["account_type"],
            "current_balance":         policy_input["current_balance"],

            # LLM explanation (non-authoritative — narrative only)
            "reasoning": (
                f"Policy Validation:\n"
                f"{validation.get('policy_basis', '')}\n\n"
                f"LLM Explanation:\n{llm_explanation}"
            ),
        }



# Standalone entry point (dev / debug only)

async def _main() -> None:
    """
    Standalone runner for direct agent testing without the full Orchestrator.
    Mirrors the exact async DB stack used in production.
    """
    from openai import AsyncOpenAI
    from google import genai
    from sqlalchemy import select

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
        response_schema=TrajectoryResponse,
    )
    gemini_llm = LLMClient(
        client=genai.Client(api_key=GEMINI_API_KEY),
        model_name="gemini-2.5-flash",
        response_schema=TrajectoryResponse,
    )

    agent = TrajectoryAgent(
        repo=repo,
        rag_engine=rag_engine,
        openai_llm=openai_llm,
        gemini_llm=gemini_llm,
    )

    # Fetch a real customer_id from the database
    from Backend.models import Customer
    async with get_async_session(engine) as session:
        result = await session.execute(
            select(Customer.customer_id).limit(1).offset(0)
        )
        customer_id = result.scalar()

    print(f"[Dev] Testing with customer_id: {customer_id}")

    result = await agent.run({"customer_id": customer_id})

    print("\n=== TRAJECTORY OUTPUT ===")
    for k, v in result.items():
        if k != "reasoning":
            print(f"  {k:<28}: {v}")
    print(f"\n  reasoning:\n{result.get('reasoning', '')}")


if __name__ == "__main__":
    asyncio.run(_main())


# from typing import Dict, Any
# import asyncio

# from google import genai
# from app.agents.abstract_agent import BaseAgent
# from app.database.dataset_loader import DatasetLoader
# from app.data.repository import BankRepository
# from app.rag.rag_system.recommend_product import RecommendationEngine
# from app.rag.rag_system.rag_querys import RAGQueryEngine
# from app.utils.logger import ReasoningLogger, SystemLogger
# from app.rag.rag_system.chromadb_config import initialize_chromadb
# from app.rag.rag_system.rag_querys import create_engine
# from app.utils.llm_client import LLMClient
# from openai import AsyncOpenAI
# from app.prompts.trajectory_prompt import Trajectory_System_Prompt
# from openai import RateLimitError
# from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
# from app.utils.schemas import TrajectoryResponse
# import traceback

# class TrajectoryAgent(BaseAgent):
#     """
#     Trajectory Agent — Product Recommendation & Eligibility Engine


#     1. Deterministic recommendation (RecommendationEngine)
#     2. Policy validation (RAG)
#     3. LLM explanation layer (non-overriding)
#     4. Structured governance-safe output

#     The LLM NEVER overrides eligibility decisions.
#     """

#     # Initialize the agent
#     def __init__(
#         self,
#         repo: BankRepository,
#         rag_engine: RAGQueryEngine,
#         openai_llm: LLMClient,
#         gemini_llm: LLMClient,
#     ):
#         super().__init__()

#         # Use injected dependencies ONLY
#         self.repo = repo
#         self.rag_engine = rag_engine
#         self.recommender = RecommendationEngine()
#         self.openai_llm = openai_llm
#         self.gemini_llm = gemini_llm

#     # Main execution
#     async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:

#         customer_id = payload.get("customer_id")
#         if not customer_id:
#             raise ValueError("customer_id is required.")
        
#         SystemLogger.log_event(
#             event_type="TrajectoryAgent_started",
#             message="TrajectoryAgent execution started",
#             metadata={"customer_id": customer_id}
#         )

#         # Fetch customer profile
#         profile = await self.repo.get_customer_profile(customer_id)

#         # Fetch transactions
#         transactions = await self.repo.get_customer_transactions(customer_id)
    
#         try:

#             if profile is None:
#                 raise ValueError(f"Customer {customer_id}not found.")
            
#             SystemLogger.log_event(
#                 event_type="TrajectoryAgent_data_fetched",
#                 message="Retrieved customer profile and transactions",
#                 metadata={"customer_id": customer_id}
#             )

#             # Extract Loan_signal_score from transactions (pre-assigned per product)
#             if not transactions.empty:
#                 loan_signal_score = float(transactions.iloc[0]["Loan_signal_score"])
#             else:
#                 loan_signal_score = 0.0
#             # Compute behavioral signals: Monthly inflow = total credits
#             if transactions.empty:
#                 monthly_inflow = 0.0
#             else:
#                 credits = transactions[transactions["transaction_type"] == "credit"]
#                 monthly_inflow = float(credits["amount"].sum())

#             # Salary proxy
#             salary_detected = bool(
#                 transactions["merchant_category"]
#                 .str.contains("salary", case=False, na=False)
#                 .any()
#             )

#             # Uber frequency
#             uber_tracker = int(
#                 transactions[
#                     transactions["merchant_name"].isin(["Uber", "Bolt", "LagRide"])
#                 ].shape[0]
#             )

#             # Prepare policy input

#             policy_input = {
#             "Loan_signal_score":loan_signal_score,
#             "monthly_inflow": monthly_inflow,
#             "salary_detected": salary_detected,
#             "uber_tracker": uber_tracker,
#             "age": int(profile.get("age", 0)),
#             "account_type": profile.get("account_type", "savings"),
#             "current_balance": float(profile.get("current_balance", 0.0)),
#             }


#             # Proactive Recommendation (Policy Engine)

#             recommendation = await self.recommender.recommend(policy_input)

#             SystemLogger.log_event(
#                 event_type="Product_recommendation_made",
#                 message="Primary product recommendation made",
#                 metadata={"primary_product": recommendation["primary_product"], "confidence": recommendation["confidence"]}
#             )

#             # If no product qualifies, return immediately
#             if not recommendation["primary_product"]:
#                 SystemLogger.log_event(
#                     event_type="No_product_qualified",
#                     message="No product qualified for recommendation",
#                     metadata={"customer_id": customer_id}
#                 )

#                 recommendation["agent"] = "TrajectoryAgent"
#                 recommendation["validation"] = None
#                 return recommendation

#             primary_product  = recommendation["primary_product"]

#             # Validate With RAG (Grounding Layer)
#             validation = await self.rag_engine.validate_product_recommendation(
#                     customer_data=policy_input,
#                     recommended_product=primary_product,
#                 )
            
#             SystemLogger.log_event(
#                 event_type="RAG_validation_completed",
#                 message="Trajectory RAG validation completed",
#                 metadata={"is_eligible": validation["is_eligible"]}
#             )


#             explanation_payload = f"""
#     Customer ID: {customer_id}
#     Primary Product: {primary_product}
#     Loan_signal_score: {policy_input['Loan_signal_score']}
#     Score Range: {recommendation['score_range']}

#     Monthly Inflow: {monthly_inflow}
#     Salary Detected: {salary_detected}
#     Age: {policy_input['age']}
#     Account Type: {policy_input['account_type']}
#     Current Balance: {policy_input['current_balance']}

#     Monthly EMI: {recommendation['monthly_emi']}
#     Tenure: {recommendation['tenure_months']}
#     DSR Ratio: {recommendation['dsr_ratio']}
#     DSR Warning: {recommendation['dsr_warning']}

#     Eligibility Decision: {recommendation['is_eligible']}

#     Provide an audit-ready explanation aligned with PRS-001 policy.
#     """

#             try:
#                 llm_response = await self.openai_llm.generate(
#                     system_prompt=Trajectory_System_Prompt,
#                     user_input=explanation_payload,
#                 )

#                 SystemLogger.log_event(
#                     event_type="LLM_explanation_completed",
#                     message="LLM explanation generated",
#                 )

#             except RateLimitError:
#                 llm_response = await self.gemini_llm.generate(
#                     system_prompt=Trajectory_System_Prompt,
#                     user_input=explanation_payload,
#                 )

#             structured = llm_response.model_dump()

#             explanation= (
#                 f"{structured['explanation']}\n\n"
#                 f"Risk Summary:\n{structured['risk_summary']}\n\n"
#                 f"Governance:\n{structured['governance_note']}"
#             )

                
#             # Logging
#             ReasoningLogger.log(
#                 agent_name="TrajectoryAgent",
#                 payload=structured
#             )

#             # Final system log for audit traceability
#             SystemLogger.log_event(
#                 event_type="TrajectoryAgent_completed",
#                 message="TrajectoryAgent execution completed",
#                 metadata={"primary_product": recommendation["primary_product"]
#                 }
#             )

#             return {
#                 "agent": "TrajectoryAgent",
#                 "customer_id": customer_id,
#                 "primary_product": primary_product,
#                 "all_qualifying_products": recommendation["all_qualifying"],
#                 "monthly_emi": recommendation["monthly_emi"],
#                 "tenure_months": recommendation["tenure_months"],
#                 "dsr_ratio": recommendation["dsr_ratio"],
#                 "dsr_warning": recommendation["dsr_warning"],
#                 "is_eligible": recommendation["is_eligible"],
#                 "confidence": recommendation["confidence"],
#                 "policy_validation": validation,
#                 "reasoning": (
#                     f"Policy Validation:\n{validation.get('policy_basis', '')}\n\n"
#                     f"LLM Explanation:\n{explanation}"
#                 ),
#             }
#         except Exception as e:
#             SystemLogger.log_event(
#                 event_type="TrajectoryAgent_failed",
#                 message=str(e),
#                 metadata={"customer_id": customer_id, "error_trace": traceback.format_exc()}
#             )
#             raise e

# # Demo

# if __name__ == "__main__":

#     async def main():
#         # Infrastructure Setup (Same as Orchestrator)

#         dataset_loader = DatasetLoader()
#         repo = BankRepository(dataset_loader)

#         rag_engine = await create_engine()

#         openai_llm = LLMClient(
#             client=AsyncOpenAI(api_key=OPENAI_API_KEY),
#             model_name="gpt-4o",
#             response_schema=TrajectoryResponse,
#         )

#         gemini_llm = LLMClient(
#             client=genai.Client(api_key=GEMINI_API_KEY),
#             model_name="gemini-2.5-flash",
#             response_schema=TrajectoryResponse,
#         )

#         agent = TrajectoryAgent(
#             repo=repo,
#             rag_engine=rag_engine,
#             openai_llm=openai_llm,
#             gemini_llm=gemini_llm,
#         )

#         # Pick first customer from dataset
#         customer_id = agent.repo.dataset_loader.customers.iloc[0]["customer_id"]

#         result = await agent.run({"customer_id": customer_id})

#         print("\n=== TRAJECTORY OUTPUT ===")
#         print(result)


# if __name__ == "__main__":
#     asyncio.run(main())
