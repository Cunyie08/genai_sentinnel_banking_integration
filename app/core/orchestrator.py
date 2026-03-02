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
from app.utils.logger import ReasoningLogger, SystemLogger
from openai import AsyncOpenAI
from google import genai
import traceback
from app.utils.llm_client import LLMClient
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
from app.utils.logger import ReasoningLogger
from app.utils.schemas import RoutingResponse, TrajectoryResponse, FraudResponse
from app.core.graph import AgentGraph
from app.evaluation.metrics import Metrics


# Central coordinator class for agent execution
class Orchestrator: 
    """
    Sentinel Bank Multi-Agent Orchestrator

    Responsibilities:
        - Initialize shared system components
        - Route incoming requests to correct agent
        - Return structured unified response
        - Handle errors safely
    """
 
    # Initialize the agents and routing graph
    def __init__(self):
      
        # Load dataset once
        self.dataset_loader = DatasetLoader()

        # Initialize repository layer
        self.repo = BankRepository(self.dataset_loader)

        # Initialize the Graph for routing
        self.graph = AgentGraph()

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
        
        # Initialize LLm Clients for Sentinel Agent Only
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")

        self.openai_llm = LLMClient(
            client=AsyncOpenAI(api_key=OPENAI_API_KEY),
            model_name="gpt-4o",
            response_schema=FraudResponse,
        )

        self.gemini_llm = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=FraudResponse,
        )

        # Initialize LLm Clients for Trajectory Agent Only
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set.")

        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set.")

        self.openai_llm = LLMClient(
            client=AsyncOpenAI(api_key=OPENAI_API_KEY),
            model_name="gpt-4o",
            response_schema=TrajectoryResponse,
        )

        self.gemini_llm = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=TrajectoryResponse,
        )

        self.dispatcher = DispatcherAgent(self.repo,self.rag, openai_llm=self.openai_llm,gemini_llm=self.gemini_llm)
        self.sentinel = SentinelAgent(repo=self.repo, rag_engine=self.rag, openai_llm=self.openai_llm,gemini_llm=self.gemini_llm)
        self.trajectory = TrajectoryAgent(repo=self.repo, rag_engine=self.rag, openai_llm=self.openai_llm,gemini_llm=self.gemini_llm)

        self._initialized = True

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
        if not self._initialized:
            raise RuntimeError(
                "Orchestrator not initialized. Call await initialize() first."
            )

        if not request or "type" not in request:
            return {
                "status": "error",
                "message": "Request must include a 'type' field.",
            }


        agent_name = self.graph.get_next_agent(request)
        try: 
            if agent_name == "DispatcherAgent":
                result = await self.dispatcher.run(request)
                return {**result, **Metrics.evaluate_triage(result)}

            elif agent_name == "SentinelAgent":
                result = await self.sentinel.run(request)
                return {**result, **Metrics.evaluate_fraud(result)} 

            elif agent_name == "TrajectoryAgent":
                result = await self.trajectory.run(request)
                return {**result, **Metrics.evaluate_product_recommendation(result)}

            else:
                return {
                    "error": f"Unknown agent name: {agent_name}",
                    "supported_agents": ["DispatcherAgent","SentinelAgent","TrajectoryAgent"]
                }
        except Exception as e:
            # Production-safe error response
            return {
                "status": "error",
                "message": str(e),
                "trace": traceback.format_exc(),
                "agent": agent_name,
            }


       
