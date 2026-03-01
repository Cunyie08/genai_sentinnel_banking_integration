from typing import Dict, Any
from openai import AsyncOpenAI
from google import genai
from openai import RateLimitError
from app.agents.abstract_agent import BaseAgent
from app.prompts.dispatcher_prompt import Dispatcher_System_Prompt
from app.utils.logger import ReasoningLogger
from app.utils.schemas import RoutingResponse
import asyncio
from app.rag.rag_system.rag_querys import RAGQueryEngine
from app.rag.rag_system.chromadb_config import initialize_chromadb
from app.utils.llm_client import LLMClient
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
from app.data.dataset_loader import DatasetLoader
from app.data.repository import BankRepository
from app.rag.rag_system.rag_querys import create_engine



class DispatcherAgent(BaseAgent):

    def __init__(self, repo, rag_engine, openai_llm, gemini_llm):
        self.repo = repo
        self.rag_engine = rag_engine
        self.openai_llm = openai_llm
        self.gemini_llm = gemini_llm

        # Initialize the RAG
        self.client, self.config = initialize_chromadb()
        self.rag_engine = RAGQueryEngine(self.client, self.config)

        # Initialize the Dataset repository
        self.repo = repo

        # OpenAI LLM (Explanation Layer)
        self.openai_llm = LLMClient(
            client=AsyncOpenAI(api_key=OPENAI_API_KEY),
            model_name="gpt-4o",
            response_schema=RoutingResponse
        )
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")
        
        # Gemini for fallback
        self.gemini_llm = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=RoutingResponse
        )
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")


    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        complaint_id: str | None = payload.get("complaint_id")


        # Validate before calling the repository
        if complaint_id is None:
            raise ValueError("complaint_id is required for DispatcherAgent.")

        complaint_record = self.repo.get_complaints(complaint_id)
        complaint_text = complaint_record["complaint_text"]

        # Call RAG for policy-grounded routing
        routing = await self.rag_engine.detect_complaint_category(
            complaint_text

            )
        
        # Build base routing from the RAG engine 

        base_result = {
            "department_code": routing["department_code"],
            "department_name": routing["department_name"],
            "priority_level": routing["priority_level"],
            "sla_hours": routing["sla_hours"],
            "confidence": routing["confidence"],
            "routing_method": routing["routing_method"],
            "keyword_matches": routing["keyword_matches"],
            "reasoning": routing["reasoning"],
        }

        # LLM explanation/formatting
        explanation_payload = f"""
        Complaint: {complaint_text}
        
        Routing Decision:
        Department Code: {base_result['department_code']}
        Department Name: {base_result['department_name']}
        Priority: {base_result['priority_level']}
        SLA Hours: {base_result['sla_hours']}

        Provide a clear audit-ready explanation
        """
        
        try:
            llm_response = await self.openai_llm.generate(
            system_prompt=Dispatcher_System_Prompt,
            user_input=explanation_payload
        )


        except RateLimitError:
            print("OpenAI rate limited. Falling back to Gemini...")

            llm_response = await self.gemini_llm.generate(
                system_prompt=Dispatcher_System_Prompt,
                user_input=explanation_payload
            )

        result = llm_response.model_dump()

        # Preservig RAG decision integrity
        result['department_code'] = base_result['department_code']
        result['department_name'] = base_result['department_name']
        result['priority_level'] = base_result['priority_level']
        result['routing_method'] = base_result['routing_method']
        result['keyword_matches'] = base_result['keyword_matches']
        result['sla_hours'] = base_result['sla_hours']
        result['confidence'] = base_result['confidence']

        # Preservig RAG decision integrity + add LLM explanation layer
        result['reasoning'] = (
              f"Policy Basis:\n{base_result['reasoning']}\n\n"
              f"Explanation: \n{result.get('reasoning', '')}") # To extracting grounded policy, LLM explanation and audit traceability
        
        result['agent'] = "DispatcherAgent"


        # Logging
        ReasoningLogger.log(
            agent_name="DispatcherAgent",
            payload=result
        )

        return result

async def main():

    # Infrastructure Setup (Same as Orchestrator)

    dataset_loader = DatasetLoader()
    await dataset_loader.load()
    repo = BankRepository(dataset_loader)

    rag_engine = await create_engine()

    openai_llm = LLMClient(
        client=AsyncOpenAI(api_key=OPENAI_API_KEY),
        model_name="gpt-4o",
        response_schema=RoutingResponse
    )

    gemini_llm = LLMClient(
        client=genai.Client(api_key=GEMINI_API_KEY),
        model_name="gemini-2.5-flash",
        response_schema=RoutingResponse
    )

    agent = DispatcherAgent(
        repo=repo,
        rag_engine=rag_engine,
        openai_llm=openai_llm,
        gemini_llm=gemini_llm,
        )

    # Get a real complaint ID from dataset
    complaint_id = agent.repo.dataset_loader.complaints.iloc[25]["complaint_id"]

    result = await agent.run({
        "complaint_id": complaint_id
    })

    print("\n=== DISPATCHER OUTPUT ===")
    print(result)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())




