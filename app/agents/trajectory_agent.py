# ==========================================================
# TRAJECTORY AGENT — Clean Final Version
# ==========================================================

from typing import Dict, Any
import asyncio

from app.agents.abstract_agent import BaseAgent
from app.data.dataset_loader import DatasetLoader
from app.data.repository import BankRepository
from app.rag.rag_system.recommend_product import RecommendationEngine
from app.rag.rag_system.rag_querys import RAGQueryEngine
from app.rag.rag_system.chromadb_config import initialize_chromadb
from app.rag.rag_system.rag_querys import create_engine


class TrajectoryAgent(BaseAgent):

    """
    Trajectory Agent performs the following: 
    
    1. Fetch customer financial data
    2. Compute behavioral signals
    3. Call deterministic recommendation engine (PRS-001)
    4. Validate recommendation using RAG grounding
    5. Return structured decision
    """
    # Initialize the agent
    def __init__(self, repo, rag_engine):
        self.repo = repo
        self.rag_engine = rag_engine

        # Dataset + repository
        self.dataset_loader = DatasetLoader()
        self.repo = BankRepository(self.dataset_loader)

        # RAG Engine (for validation grounding)
        client, config = initialize_chromadb()
        self.rag_engine = RAGQueryEngine(client, config)
        self.recommender= RecommendationEngine()



    # Main execution
    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:

        customer_id = payload.get("customer_id")
        if not customer_id:
            raise ValueError("customer_id is required.")

      
        # Fetch customer profile
        profile = self.repo.get_customer_profile(customer_id)
        if profile is None:
            raise ValueError("Customer not found.")

        # Fetch transactions
        transactions = self.repo.get_customer_transactions(customer_id)

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
            "Loan_signal_score": float(profile.get("Loan_signal_score", 0.0)),
            "monthly_inflow": monthly_inflow,
            "salary_detected": salary_detected,
            "uber_tracker": uber_tracker,
            "age": int(profile.get("age", 0)),
            "account_type": profile.get("account_type", "savings"),
            "current_balance": float(profile.get("current_balance", 0.0)),
        }

      

        # Proactive Recommendation (Policy Engine)

        recommendation = self.recommender.recommend(policy_input)

        # If no product qualifies, return immediately
        if not recommendation["primary_product"]:
            recommendation["agent"] = "TrajectoryAgent"
            recommendation["validation"] = None
            return recommendation

        primary_product  = recommendation["primary_product"]

        # Validate With RAG (Grounding Layer)
        if primary_product:

            validation = await self.rag_engine.validate_product_recommendation(
                customer_data=policy_input,
                recommended_product=primary_product,
            )

            recommendation["validation"] = validation

        recommendation["agent"] ="TrajectoryAgent"

        return recommendation


# Demo
async def main():
    # Infrastructure Setup (Same as Orchestrator)

    dataset_loader = DatasetLoader()
    repo = BankRepository(dataset_loader)

    rag_engine = await create_engine()


    agent = TrajectoryAgent(
        repo=repo,
        rag_engine=rag_engine
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