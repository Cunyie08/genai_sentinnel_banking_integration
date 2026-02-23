# This contains the Fraud/risk assessment

# KAFKA to be integrated
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

# Create a class that assess fraud/risk and explains why transaction was flagged

class SentinelAgent(BaseAgent):
    # Initialize the agent
    def __init__(self):
        super().__init__(name="SentinelAgent")

    
        # Initialize the RAG engine
        self.client, self.config = initialize_chromadb()
        self.rag_engine = RAGQueryEngine(self.client, self.config)
    
        self.openai_llm = LLMClient(
                client=AsyncOpenAI(api_key=OPENAI_API_KEY),
                model_name="gpt-4o",
                response_schema=FraudResponse
            )

        self.gemini_llm = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=FraudResponse
        )
    
    # Perform basic fraud assessment
    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:

        """
        Args: Dispatcher output
        
        Returns: Fraud Assessment result
        """
        # Deterministic fraud engine
        fraud_result = await self.rag_engine.calculate_fraud_risk(input_data)

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

        # Explanation
        explanation_payload = f"""
            Transaction:
            {input_data}

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
        except RateLimitError:
                print("OpenAI rate limited. Falling back to Gemini...")

                llm_response = await self.gemini_llm.generate(
                system_prompt=Sentinel_System_Prompt,
                user_input=explanation_payload
                )

        result = llm_response.model_dump()

        # Preserve deterministic fraud engine decisions
        result["total_risk_score"] = base_result["total_risk_score"]
        result["risk_level"] = base_result["risk_level"]
        result["recommended_action"] = base_result["recommended_action"]
        result["requires_challenge"] = base_result["requires_challenge"]
        result["should_block"] = base_result["should_block"]
        result["confidence"] = base_result["confidence"]
        result["risk_breakdown"] = base_result["risk_breakdown"]

        # Merge reasoning safely
        result["policy_explanation"] = (
            f"Policy Basis:\n{base_result['reasoning']}\n\n"
            f"Explanation:\n{result.get('reasoning', '')}"
        )

        result["agent"] = self.name

        ReasoningLogger.log(
            agent_name=self.name,
            payload=result
        )

        return result

async def main():
    client, config = initialize_chromadb()
    rag_engine = RAGQueryEngine(client, config)

    transaction = {
        "fraud_explainability_trace": "mobile_channel_risk,high_amount_spike",
        "amount": 450000,
        "merchant_category": "fintech",
        "transaction_timestamp": "2024-01-15 02:30:00"
    }

    result = await rag_engine.calculate_fraud_risk(transaction)

    print("\n=== SENTINEL OUTPUT ===")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())