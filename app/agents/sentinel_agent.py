# This contains the Fraud/risk assessment

from typing import Dict, Any
from app.agents.abstract_agent import BaseAgent
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
from app.utils.logger import ReasoningLogger, SystemLogger
from app.utils.schemas import FraudResponse
from app.utils.llm_client import LLMClient
from openai import RateLimitError, AsyncOpenAI
from google import genai
from app.prompts.sentinel_prompt import Sentinel_System_Prompt
from app.rag.rag_system.rag_querys import RAGQueryEngine
from app.rag.rag_system.chromadb_config import initialize_chromadb
import asyncio
from app.data.dataset_loader import DatasetLoader
from app.data.repository import BankRepository
from app.ml.fraud_model import MLScorer
from app.rag.rag_system.rag_querys import create_engine
import traceback


# Create a class that assess fraud/risk and explains why transaction was flagged

class SentinelAgent(BaseAgent):
    """
    SentinelAgent performs fraud assessment using:
    1. Deterministic risk scoring (RAG policy engine)
    2. Business policy overrides (card channels)
    3. LLM explanation overlay
    4. Structured schema response
    """

    # Initialize the agent
    def __init__(
        self,
        repo: BankRepository,
        rag_engine: RAGQueryEngine,
        openai_llm: LLMClient,
        gemini_llm: LLMClient,
    ):
       
        self.repo = repo
        self.rag_engine = rag_engine
        self.openai_llm = openai_llm
        self.gemini_llm = gemini_llm

        # Load the Dataset for the customers, accounts, transactions, complaints
        self.dataset_loader = DatasetLoader()

        # Repository abstracts dataset access
        self.repo = BankRepository(self.dataset_loader)
    
        # Initialize the RAG engine for fraud scoring + policy explanation grounding
        self.client, self.config = initialize_chromadb()
        self.rag_engine = RAGQueryEngine(self.client, self.config)

        # Initialize the MLScorer
        self.ml_scorer = MLScorer(self.dataset_loader)
    
        # Initialize OpenAI client
        self.openai_llm = LLMClient(
                client=AsyncOpenAI(api_key=OPENAI_API_KEY),
                model_name="gpt-4o",
                response_schema=FraudResponse
            )
        # Fallback

        self.gemini_llm = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=FraudResponse
        )
    
    # Fraud assessment flow
    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:

        """
        Performs fraud detection and enforcement logic.

        Steps:
        1. Fetch transaction
        2. Run deterministic fraud scoring
        3. Run ML model → get fraud_probability (0–1)
        4. Attach fraud_probability to output
        5. If ML probability is very high → increase risk by 1 tier
        6. Apply card override
        7. Add LLM explanation overlay
        8. Log decision
        """
        # Validate transaction
        transaction_id: str | None = payload.get("transaction_id")

        SystemLogger.log_event(
            event_type="SentinelAgent_started",
            message="SentinelAgent exceution started",
            metadata={"transaction_id": transaction_id}
        )

        try:
            if transaction_id is None:
                raise ValueError("transaction_id is required.")

            # Fetch transaction from the repository
            transaction = self.repo.get_transactions(transaction_id)
            print("Transaction ID:", transaction_id)
            print("Transaction fetched:", transaction)

            SystemLogger.log_event(
                event_type="Transaction_data_fetched",
                message="Transaction retrieved",
                metadata={"transaction_id": transaction_id, 
                          "amount": transaction.get("amount"),
                          "channel": transaction.get("channel")}
            )

            # Deterministic fraud scoring engine
            fraud_result = await self.rag_engine.calculate_fraud_risk(transaction)

            SystemLogger.log_event(
                event_type="RAG_fraud_scoring_completed",
                message="RAG-based fraud policy validation completed",
                metadata={"transaction_id": transaction_id, "risk_level": fraud_result["risk_level"]}
            )

            
            # Extract structured result
            base_result = {
            "total_risk_score": fraud_result["total_risk_score"],
            "risk_level": fraud_result["risk_level"],
            "recommended_action": fraud_result["recommended_action"],
            "requires_challenge": fraud_result["requires_challenge"],
            "should_block": fraud_result["should_block"],
            "confidence": fraud_result["confidence"],
            "risk_breakdown": fraud_result["risk_breakdown"],
            "policy_explanation": fraud_result["policy_explanation"]
            }

            # ML Fraud Probability 
            ml_probability = self.ml_scorer.predict(transaction)

            base_result["ml_probability"] = round(ml_probability, 3)

            # Only escalate LOW → MEDIUM if ML strongly indicates anomaly
            if ml_probability > 0.85 and base_result["risk_level"] == "LOW":
                base_result["risk_level"] = "MEDIUM"
                base_result["recommended_action"] = \
                            "Escalated to MEDIUM risk due to ML anomaly signal"
            
            SystemLogger.log_event(
                event_type="ML_scoring_completed",
                message="Fraud scoring computed",
                metadata={"ml_probability": base_result["ml_probability"]}
            )

            # Card-Channel Mandatory Override 
            # All ATM / POS transactions must require push-to-app
            card_channels = ['pos', 'atm']

            if transaction.get('channel') in card_channels:
                base_result["requires_challenge"] = True
                base_result['recommended_action'] = "Mandatory push-to-app biometric challenge (Card channel policy override)"

            

            # LLM Explanation
            explanation_payload = f"""
                Transaction:
                {transaction}

                Risk Level: {base_result['risk_level']}
                Total Score: {base_result['total_risk_score']}
                Action: {base_result['recommended_action']}

                Provide a clear audit-ready explanation.
                """
            
            try:
                llm_response = await self.openai_llm.generate(
                system_prompt=Sentinel_System_Prompt,
                user_input=explanation_payload
                )

                SystemLogger.log_event(
                    event_type="LLM_explanation_completed",
                    message="Sentinel LLM explanation generated"
                )

            except RateLimitError:
                    print("OpenAI rate limited. Falling back to Gemini...")

                    llm_response = await self.gemini_llm.generate(
                    system_prompt=Sentinel_System_Prompt,
                    user_input=explanation_payload
                    )

            # Extract structured LLM output
            result = llm_response.model_dump()

            # Preserve deterministic fraud engine decisions
            result["total_risk_score"] = base_result["total_risk_score"]
            result["risk_level"] = base_result["risk_level"]
            result["recommended_action"] = base_result["recommended_action"]
            result["requires_challenge"] = base_result["requires_challenge"]
            result["should_block"] = base_result["should_block"]
            result["confidence"] = base_result["confidence"]
            result["risk_breakdown"] = base_result["risk_breakdown"]

            # Merge policy_explanation safely with LLM Explanation
            result["policy_explanation"] = (
                f"Policy Basis:\n{base_result['policy_explanation']}\n\n"
                f"LLM Explanation:\n{result.get('policy_explanation', '')}"
            )

            # Tag the Agent
            result["agent"] = "SentinelAgent"

            # Log reasoning trace
            ReasoningLogger.log(
                agent_name="SentinelAgent",
                payload=result
            )

            SystemLogger.log_event(
                event_type="SentinelAgent_completed",
                message=f"SentinelAgent execution completed",
                metadata={"final_risk_level": result["risk_level"], "should_block": result["should_block"]}
            )

            return result
        except Exception as e:
            SystemLogger.log_event(
                event_type="SentinelAgent failed",
                message=str(e),
                metadata={"transaction_id": transaction_id, "traceback": traceback.format_exc()}
            )
            raise


# Testing
async def main():
    # Infrastructure Setup (Same as Orchestrator)

    dataset_loader = DatasetLoader()
    repo = BankRepository(dataset_loader)

    rag_engine = await create_engine()

    openai_llm = LLMClient(
    client= AsyncOpenAI(api_key=OPENAI_API_KEY),
    model_name="gpt-4o",
    response_schema=FraudResponse,
    )


    gemini_llm = LLMClient(     
    client=genai.Client(api_key=GEMINI_API_KEY),
    model_name="gemini-2.5-flash",
    response_schema=FraudResponse

    )

    agent = SentinelAgent(
    repo=repo,
    rag_engine=rag_engine,
    openai_llm=openai_llm,
    gemini_llm=gemini_llm
    )

    # Select a real transaction ID from the dataset
    transaction_id = agent.repo.dataset_loader.transactions.iloc[9]["transaction_id"]

    result = await agent.run({
        "transaction_id": transaction_id
    })
    print("\n=== SENTINEL OUTPUT ===")
    print(result)

if __name__ == "__main__":
     asyncio.run(main())

