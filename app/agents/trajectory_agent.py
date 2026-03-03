
# TRAJECTORY AGENT 


from typing import Dict, Any
import asyncio

from google import genai
from app.agents.abstract_agent import BaseAgent
from app.data.dataset_loader import DatasetLoader
from app.data.repository import BankRepository
from app.rag.rag_system.recommend_product import RecommendationEngine
from app.rag.rag_system.rag_querys import RAGQueryEngine
from app.utils.logger import ReasoningLogger, SystemLogger
from app.rag.rag_system.chromadb_config import initialize_chromadb
from app.rag.rag_system.rag_querys import create_engine
from app.utils.llm_client import LLMClient
from openai import AsyncOpenAI
from app.prompts.trajectory_prompt import Trajectory_System_Prompt
from openai import RateLimitError
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
from app.utils.schemas import TrajectoryResponse
import traceback

class TrajectoryAgent(BaseAgent):

    """
    Trajectory Agent — Product Recommendation & Eligibility Engine

    
    1. Deterministic recommendation (RecommendationEngine)
    2. Policy validation (RAG)
    3. LLM explanation layer (non-overriding)
    4. Structured governance-safe output

    The LLM NEVER overrides eligibility decisions.
    """
    # Initialize the agent
    def __init__(
        self,
        repo: BankRepository,
        rag_engine: RAGQueryEngine,
        openai_llm: LLMClient,
        gemini_llm: LLMClient,
    ):
        super().__init__()

        # Use injected dependencies ONLY
        self.repo = repo
        self.rag_engine = rag_engine
        self.recommender = RecommendationEngine()
        self.openai_llm = openai_llm
        self.gemini_llm = gemini_llm

 
    # Main execution
    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:

        customer_id = payload.get("customer_id")
        if not customer_id:
            raise ValueError("customer_id is required.")
        
        SystemLogger.log_event(
            event_type="TrajectoryAgent_started",
            message="TrajectoryAgent execution started",
            metadata={"customer_id": customer_id}
        )

      
        # Fetch customer profile
        profile = self.repo.get_customer_profile(customer_id)

        # Fetch transactions
        transactions = self.repo.get_customer_transactions(customer_id)
    
        try:

            if profile is None:
                raise ValueError(f"Customer {customer_id}not found.")
            
            SystemLogger.log_event(
                event_type="TrajectoryAgent_data_fetched",
                message="Retrieved customer profile and transactions",
                metadata={"customer_id": customer_id}
            )

            # Extract Loan_signal_score from transactions (pre-assigned per product)
            if not transactions.empty:
                loan_signal_score = float(transactions.iloc[0]["Loan_signal_score"])
            else:
                loan_signal_score = 0.0

            # Compute behavioral signals: Monthly inflow = total credits
            if transactions.empty:
                monthly_inflow = 0.0
            else:
                credits = transactions[transactions["transaction_type"] == "credit"]
                monthly_inflow = float(credits["amount"].sum())

            # Salary proxy
            salary_detected = bool(
                transactions["merchant_category"]
                .str.contains("salary", case=False, na=False)
                .any()
            )

            # Uber frequency
            uber_tracker = int(
                transactions[
                    transactions["merchant_name"].isin(["Uber", "Bolt", "LagRide"])
                ].shape[0]
            )

            # Prepare policy input

            policy_input = {
                "Loan_signal_score":loan_signal_score,
                "monthly_inflow": monthly_inflow,
                "salary_detected": salary_detected,
                "uber_tracker": uber_tracker,
                "age": int(profile.get("age", 0)),
                "account_type": profile.get("account_type", "savings"),
                "current_balance": float(profile.get("current_balance", 0.0)),
            }


            # Proactive Recommendation (Policy Engine)

            recommendation = await self.recommender.recommend(policy_input)

            SystemLogger.log_event(
                event_type="Product_recommendation_made",
                message="Primary product recommendation made",
                metadata={"primary_product": recommendation["primary_product"], "confidence": recommendation["confidence"]}
            )

            # If no product qualifies, return immediately
            if not recommendation["primary_product"]:
                SystemLogger.log_event(
                    event_type="No_product_qualified",
                    message="No product qualified for recommendation",
                    metadata={"customer_id": customer_id}
                )

                recommendation["agent"] = "TrajectoryAgent"
                recommendation["validation"] = None
                return recommendation

            primary_product  = recommendation["primary_product"]

            # Validate With RAG (Grounding Layer)
            validation = await self.rag_engine.validate_product_recommendation(
                    customer_data=policy_input,
                    recommended_product=primary_product,
                )
            
            SystemLogger.log_event(
                event_type="RAG_validation_completed",
                message="Trajectory RAG validation completed",
                metadata={"is_eligible": validation["is_eligible"]}
            )


            explanation_payload = f"""
    Customer ID: {customer_id}
    Primary Product: {primary_product}
    Loan_signal_score: {policy_input['Loan_signal_score']}
    Score Range: {recommendation['score_range']}

    Monthly Inflow: {monthly_inflow}
    Salary Detected: {salary_detected}
    Age: {policy_input['age']}
    Account Type: {policy_input['account_type']}
    Current Balance: {policy_input['current_balance']}

    Monthly EMI: {recommendation['monthly_emi']}
    Tenure: {recommendation['tenure_months']}
    DSR Ratio: {recommendation['dsr_ratio']}
    DSR Warning: {recommendation['dsr_warning']}

    Eligibility Decision: {recommendation['is_eligible']}

    Provide an audit-ready explanation aligned with PRS-001 policy.
    """

            try:
                llm_response = await self.openai_llm.generate(
                    system_prompt=Trajectory_System_Prompt,
                    user_input=explanation_payload,
                )

                SystemLogger.log_event(
                    event_type="LLM_explanation_completed",
                    message="LLM explanation generated",
                )

            except RateLimitError:
                llm_response = await self.gemini_llm.generate(
                    system_prompt=Trajectory_System_Prompt,
                    user_input=explanation_payload,
                )

            structured = llm_response.model_dump()

            explanation= (
                f"{structured['explanation']}\n\n"
                f"Risk Summary:\n{structured['risk_summary']}\n\n"
                f"Governance:\n{structured['governance_note']}"
            )

                
            # Logging
            ReasoningLogger.log(
                agent_name="TrajectoryAgent",
                payload=structured
            )

            # Final system log for audit traceability
            SystemLogger.log_event(
                event_type="TrajectoryAgent_completed",
                message="TrajectoryAgent execution completed",
                metadata={"primary_product": recommendation["primary_product"]
                }
            )

            return {
                "agent": "TrajectoryAgent",
                "customer_id": customer_id,
                "primary_product": primary_product,
                "all_qualifying_products": recommendation["all_qualifying"],
                "monthly_emi": recommendation["monthly_emi"],
                "tenure_months": recommendation["tenure_months"],
                "dsr_ratio": recommendation["dsr_ratio"],
                "dsr_warning": recommendation["dsr_warning"],
                "is_eligible": recommendation["is_eligible"],
                "confidence": recommendation["confidence"],
                "policy_validation": validation,
                "reasoning": (
                    f"Policy Validation:\n{validation.get('policy_basis', '')}\n\n"
                    f"LLM Explanation:\n{explanation}"
                ),
            }
        except Exception as e:
            SystemLogger.log_event(
                event_type="TrajectoryAgent_failed",
                message=str(e),
                metadata={"customer_id": customer_id, "error_trace": traceback.format_exc()}
            )
            raise


# Demo

if __name__ == "__main__":

    async def main():
        # Infrastructure Setup (Same as Orchestrator)

        dataset_loader = DatasetLoader()
        repo = BankRepository(dataset_loader)

        rag_engine = await create_engine()
        
        openai_llm = LLMClient(
        client= AsyncOpenAI(api_key=OPENAI_API_KEY),
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
        gemini_llm=gemini_llm
        )

        # Pick first customer from dataset
        customer_id = agent.repo.dataset_loader.customers.iloc[0]["customer_id"]

        result = await agent.run({
            "customer_id": customer_id
        })

        print("\n=== TRAJECTORY OUTPUT ===")
        print(result)


if __name__ == "__main__":
    asyncio.run(main())