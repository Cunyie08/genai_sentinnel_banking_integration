# This file contains the System's Brain (Orchestrator) for Sentinnel Bank

"""
This coordinates the agent execution using AgentGraph
"""
from typing import Dict, Any
from app.rag.rag_system.rag_querys import create_engine
from app.data.dataset_loader import DatasetLoader
from app.data.repository import BankRepository
from app.agents.dispatcher_agent import DispatcherAgent
from app.agents.sentinel_agent import SentinelAgent
from app.agents.trajectory_agent import TrajectoryAgent
from app.core.graph import AgentGraph
from app.utils.logger import ReasoningLogger
from openai import AsyncOpenAI
from google import genai
from app.utils.llm_client import LLMClient
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
from app.utils.logger import ReasoningLogger
from app.utils.schemas import RoutingResponse


# Central coordinator class for agent execution
class Orchestrator: 
    """
    Sentinel Bank Multi-Agent Orchestrator

    Responsibilities:
        - Initialize shared system components
        - Route incoming requests to correct agent
        - Return structured unified response
    """
 
    # Initialize the agents and routing graph
    def __init__(self):
      
        # Load dataset once
        self.dataset_loader = DatasetLoader()

        # Initialize repository layer
        self.repo = BankRepository(self.dataset_loader)
        
        # Initialize the agents
    async def initialize(self):
        """
         Initialize async components (RAG engine).
         Must be called before handling requests.
         """
        
        # Initialize RAG Engine
        self.rag = await create_engine()

        # Initialize LLm Clients for Dispatcher Agent Only
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")

        self.openai_llm = LLMClient(
            client=AsyncOpenAI(api_key=OPENAI_API_KEY),
            model_name="gpt-4o",
            response_schema=RoutingResponse,
        )

        self.gemini_llm = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=RoutingResponse,
        )
        

        self.dispatcher = DispatcherAgent(self.repo,self.rag, openai_llm=self.openai_llm,gemini_llm=self.gemini_llm)
        self.sentinel = SentinelAgent(repo=self.repo, rag_engine=self.rag)
        self.trajectory = TrajectoryAgent(repo=self.repo, rag_engine=self.rag)

    # Handle incoming customer complaint
    async def handle_request(self,request: Dict[str, Any]) -> Dict[str, Any]: # Raw complaint text -> final system response

        """
        Route request based on request_type.

        Expected request format:

        {
            "type": "complaints" | "transactions" | "recommendations",
            ...payload...
        }
        """
        if not request or "type" not in request:
            return {
                "error": "Request must include 'type' field."
            }

        request_type = request["type"]

        if request_type == "complaint":
            return await self.dispatcher.run(request)

        elif request_type == "transaction":
            return await self.sentinel.run(request["transaction_id"])

        elif request_type == "recommendations":
            return await self.trajectory.run(request["customer_id"])

        else:
            return {
                "error": f"Unknown request type: {request_type}",
                "supported_types": ["complaint","transaction","recommendation"]
            }


       
