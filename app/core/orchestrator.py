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
from app.utils.logger import ReasoningLogger, SystemLogger
from openai import AsyncOpenAI
from google import genai
import traceback
from app.utils.llm_client import LLMClient
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
from app.utils.schemas import RoutingResponse, TrajectoryResponse, FraudResponse
from app.core.graph import AgentGraph
from app.evaluation.metrics import Metrics
from app.evaluation.llm_evaluation import LLMJudge
import uuid
from datetime import datetime
import time



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
            "type": "complaint" | "transaction" | "recommendation",
            ...payload...
        }
        """

        if not self._initialized:
            raise RuntimeError(
                "Orchestrator not initialized. Call await initialize() first."
            )
        
        request_id = str(uuid.uuid4())  # Unique ID for tracing this request through logs
        start_time = time.time()

        # Validate basic request

        if not request or "type" not in request:
            SystemLogger.log_event(
                event_type="invalid_request",
                message="Request received, no 'type' field.",
                request_id=request_id,
                metadata={"request": request},
            )
            return {
                "status": "error",
                "message": "Request must include a 'type' field.",
                "request_id": request.get("request_id"),
            }


        agent_name = self.graph.get_next_agent(request)

        try:
            # Request Received Log
            SystemLogger.log_event(
                event_type="Request_received",
                message=f"Routing to {agent_name}",
                request_id=request_id,
                metadata=request
            )

            # Agent Execution
            if agent_name == "DispatcherAgent":
                result = await self.dispatcher.run(request)
                metrics= Metrics.evaluate_triage(result)              

            elif agent_name == "SentinelAgent":
                result = await self.sentinel.run(request)
                metrics= Metrics.evaluate_fraud(result)  

            elif agent_name == "TrajectoryAgent":
                result = await self.trajectory.run(request)
                metrics= Metrics.evaluate_product_recommendation(result)  
                        

            else:
                SystemLogger.log_event(
                event_type="Unknown_Agent",
                message=f"Unknown agent name: {agent_name}",
                request_id=request_id
                    )
               
                return {
                    "status": "error",
                    "error": f"Unknown agent name: {agent_name}",
                    "supported_agents": [
                        "DispatcherAgent",
                        "SentinelAgent",
                        "TrajectoryAgent"
                    ],
                    "request_id": request_id,
                }

                # Reasoning Log
            ReasoningLogger.log(
                agent_name=agent_name,
                payload=result,
                request_id=request_id
            )


            # LLM Evaluation
            llm_evaluation = LLMJudge.evaluate(
                agent_name=agent_name,
                result=result
            )

            SystemLogger.log_event(
                event_type="LLM_evaluation completed",
                message="LLM evaluation executed",
                request_id=request_id,
                metadata=llm_evaluation
            )

            # Metrics log
            SystemLogger.log_event(
                event_type="Metrics_completed",
                message="Metrics evaluation executed",
                request_id=request_id,
                metadata=metrics
            )

            duration = round(time.time() - start_time, 3)

            SystemLogger.log_event(
                event_type="Request_completed",
                message="Request processed successfully",
                request_id=request_id,
                metadata={
                    "agent": agent_name,
                    "duration_seconds": duration
                }
            )

            return {
                **result,
                **metrics,
                **llm_evaluation,
                "request_id": request_id,
                "processing_time_seconds": duration
            }


        except Exception as e:
            # Production-safe error response
            return {
                "status": "error",
                "message": str(e),
                "agent": agent_name,
                "request_id": request_id
            }
    


       
