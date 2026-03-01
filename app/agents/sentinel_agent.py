# This contains the Fraud/risk assessment

from typing import Dict, Any
from app.agents.abstract_agent import BaseAgent
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
from app.utils.logger import ReasoningLogger
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

        # Repository abstracts dataset access
        self.repo = repo
    
        # Initialize the RAG engine for fraud scoring + policy explanation grounding
        self.client, self.config = initialize_chromadb()
        self.rag_engine = RAGQueryEngine(self.client, self.config)

        # Initialize the MLScorer
        self.ml_scorer = MLScorer(self.repo.dataset_loader)
    
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
        # Validate transaction payload
        if not payload:
            raise ValueError("Transaction payload is required.")

        # If a transaction_id is passed and it's not a live test payload from app.py, try fetching it.
        # Otherwise, we use the payload itself as the transaction dictionary.
        transaction_id = payload.get("transaction_id")
        
        # Determine if this is a live incoming transaction or an existing one
        # Checking for necessary keys to consider it a "full" transaction object
        if "amount" in payload and "account_number" in payload:
            transaction = payload
            print("Processing live transaction payload:", transaction)
        else:
            if not transaction_id:
                raise ValueError("transaction_id is required if full transaction payload is not provided.")
            # Fetch transaction from the repository
            transaction = self.repo.get_transactions(transaction_id)
            print("Transaction ID:", transaction_id)
            print("Transaction fetched:", transaction)

        # Deterministic fraud scoring engine
        fraud_result = await self.rag_engine.calculate_fraud_risk(transaction)

        
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

        # Card-Channel Mandatory Override 
        # All ATM / POS transactions must require push-to-app
        card_channels = ['pos', 'atm']

        if transaction.get('channel') in card_channels:
             base_result["requires_challenge"] = True
             base_result['recommended_action'] = "Mandatory push-to-app biometric challenge (Card channel policy override)"

        

        # Gather Historical Context
        account_num = transaction.get("account_number")
        if account_num:
            # Check how repository stores transactions. They store either `account_number` or `account_id`.
            # We filter the raw dataset loader dataframe directly to get past behavior for this specific account
            history_df = self.repo.dataset_loader.transactions

            filters = []
            if "account_number" in history_df.columns:
                filters.append(history_df["account_number"] == account_num)
            if "account_id" in history_df.columns and transaction.get("account_id"):
                filters.append(history_df["account_id"] == transaction.get("account_id"))

            if filters:
                # Combine filters with logical OR
                import pandas as pd
                import numpy as np
                combined_filter = np.logical_or.reduce(filters)
                history_df = history_df[combined_filter]
            else:
                history_df = history_df.head(0) # Empty dataframe if no matching columns
            # Remove the current transaction from history if it exists
            # (By comparing transaction_id if present)
            txn_id = transaction.get("transaction_id")
            if txn_id:
                history_df = history_df[history_df["transaction_id"] != txn_id]
            
            # Take last 5 transactions for context
            historical_txns = history_df.tail(5).to_dict('records')
        else:
            historical_txns = []

        history_context = ""
        if historical_txns:
            history_context = "User's Last 5 Transactions:\n"
            for t in historical_txns:
                history_context += f"- {t.get('transaction_timestamp')}: {t.get('amount')} via {t.get('channel')} (Status: {t.get('transaction_status')})\n"
        else:
            history_context = "User has NO prior transaction history (Cold Start). IMPORTANT: Do not automatically penalize this transaction or assume fraud strictly due to lack of history."


        # LLM Explanation
        explanation_payload = f"""
            Transaction:
            {transaction}

            Risk Level: {base_result['risk_level']}
            Total Score: {base_result['total_risk_score']}
            Action: {base_result['recommended_action']}
            
            Historical Context:
            {history_context}

            Provide a clear audit-ready explanation considering the transaction against their historical behavior.
            """
        
        try:
            llm_response = await self.openai_llm.generate(
            system_prompt=Sentinel_System_Prompt,
            user_input=explanation_payload
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

        return result


# Testing
async def main():
    # Infrastructure Setup (Same as Orchestrator)

    dataset_loader = DatasetLoader()
    await dataset_loader.load()
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

