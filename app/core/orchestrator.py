# This file contains the System's Brain (Orchestrator) for Sentinnel Bank

"""
This coordinates the agent execution using AgentGraph
"""
from typing import Dict, Any, Optional
from app.rag.rag_system.rag_querys import create_engine as create_rag_engine
from app.data.db_connections import get_engine
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


class Orchestrator:
    """
    Central coordinator for all Sentinel Bank agents.

    Lifecycle:
        1. __init__()      - synchronous, sets up placeholders only
        2. initialize()    - async, bootstraps DB + RAG + agents
        3. handle_request() - async, routes + executes + evaluates

    Never call handle_request() before awaiting initialize().
    """

    def __init__(self) -> None:
        # Placeholders (populated in initialize()) 
        self._initialized: bool = False

        self.engine:      Optional[Any] = None
        self.repo:        Optional[BankRepository] = None
        self.rag:         Optional[Any] = None

        self.dispatcher:  Optional[DispatcherAgent]  = None
        self.sentinel:    Optional[SentinelAgent]    = None
        self.trajectory:  Optional[TrajectoryAgent]  = None

        # Graph is stateless - safe to build synchronously
        self.graph = AgentGraph()


    # Initialization

    async def initialize(self) -> None:
        """
        Bootstrap all async components. Must be awaited once before
        calling handle_request().

        Order:
            1. Validate API keys (fail fast - no point going further)
            2. Create DB engine + async repository
            3. Seed database from CSVs (idempotent - skips if already seeded)
            4. Initialize RAG engine
            5. Build one LLM client pair per agent (each with correct schema)
            6. Instantiate agents with their dependencies
        """
        # API key guard 
        self._validate_api_keys()

        # Database + repository 
        self.engine = get_engine()
        self.repo   = BankRepository(self.engine)

        # Seed database (idempotent - safe to call on every startup)
        loader = DatasetLoader(self.engine)
        await loader.seed()

        # Confirm tables are populated
        health = await self.repo.health_check()
        if not health["healthy"]:
            raise RuntimeError(
                f"Database health check failed after seeding: {health}"
            )

        SystemLogger.log_event(
            event_type="db_ready",
            message="Database seeded and healthy",
            metadata=health,
        )

        # RAG engine 
        self.rag = await create_rag_engine()

        SystemLogger.log_event(
            event_type="rag_ready",
            message="RAG engine initialized",
        )

        # LLM clients (one correctly-typed pair per agent) 
        self._build_agents()

        self._initialized = True

        SystemLogger.log_event(
            event_type="orchestrator_ready",
            message="Orchestrator initialized - all agents online",
            metadata={
                "agents": ["DispatcherAgent", "SentinelAgent", "TrajectoryAgent"],
                "db_rows": health,
            },
        )


    # Request handler
 

    async def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Route a request to the correct agent and return a unified response.

        Expected request shape:
            {
                "type":  "complaint" | "transaction" | "recommendation",
                ...payload fields expected by the target agent...
            }

        Returns:
            Merged dict of agent result + metrics + LLM evaluation +
            request_id + processing_time_seconds.

        Never raises; all exceptions are caught and returned as an
        error dict so callers always receive a structured response.
        """
        if not self._initialized:
            raise RuntimeError(
                "Orchestrator not initialized. "
                "Await orchestrator.initialize() before handling requests."
            )

        request_id = str(uuid.uuid4())
        start_time = time.time()

        # Basic request validation
        if not request or "type" not in request:
            SystemLogger.log_event(
                event_type="invalid_request",
                message="Request missing 'type' field",
                request_id=request_id,
                metadata={"request": request},
            )
            return {
                "status":     "error",
                "message":    "Request must include a 'type' field.",
                "request_id": request_id,
            }

        #  Route via AgentGraph 
        agent_name = self.graph.get_next_agent(request)

        SystemLogger.log_event(
            event_type="request_received",
            message=f"Routing to {agent_name}",
            request_id=request_id,
            metadata=request,
        )

        try:
            #  Agent execution 
            result, metrics = await self._dispatch(agent_name, request)

            #  Reasoning log 
            ReasoningLogger.log(
                agent_name=agent_name,
                payload=result,
                request_id=request_id,
            )

            #  LLM evaluation (judge) 
            llm_evaluation = LLMJudge.evaluate(
                agent_name=agent_name,
                result=result,
            )

            SystemLogger.log_event(
                event_type="llm_evaluation_completed",
                message="LLM evaluation executed",
                request_id=request_id,
                metadata=llm_evaluation,
            )

            #  Metrics log 
            SystemLogger.log_event(
                event_type="metrics_completed",
                message="Metrics evaluation executed",
                request_id=request_id,
                metadata=metrics,
            )

            duration = round(time.time() - start_time, 3)

            SystemLogger.log_event(
                event_type="request_completed",
                message="Request processed successfully",
                request_id=request_id,
                metadata={
                    "agent":            agent_name,
                    "duration_seconds": duration,
                },
            )

            return {
                **result,
                **metrics,
                **llm_evaluation,
                "request_id":              request_id,
                "processing_time_seconds": duration,
            }

        except Exception as exc:
            duration = round(time.time() - start_time, 3)

            SystemLogger.log_event(
                event_type="request_failed",
                message=str(exc),
                request_id=request_id,
                metadata={
                    "agent":            agent_name,
                    "duration_seconds": duration,
                },
            )

            return {
                "status":                  "error",
                "message":                 str(exc),
                "agent":                   agent_name,
                "request_id":              request_id,
                "processing_time_seconds": duration,
            }

# Helpers

    async def _dispatch(
        self,
        agent_name: str,
        request: Dict[str, Any],
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Execute the correct agent and compute its metrics.

        Returns:
            (result dict, metrics dict)

        Raises:
            ValueError if agent_name is not recognised.
        """
        if agent_name == "DispatcherAgent":
            result  = await self.dispatcher.run(request)
            result  = self._sanitize(result)          # ← add this
            metrics = Metrics.evaluate_triage(result)

        elif agent_name == "SentinelAgent":
            result  = await self.sentinel.run(request)
            result  = self._sanitize(result)          # ← add this
            metrics = Metrics.evaluate_fraud(result)

        elif agent_name == "TrajectoryAgent":
            result  = await self.trajectory.run(request)
            result  = self._sanitize(result)          # ← add this
            metrics = Metrics.evaluate_product_recommendation(result)

        else:
            raise ValueError(
                f"Unknown agent '{agent_name}'. "
                f"Supported: DispatcherAgent, SentinelAgent, TrajectoryAgent."
            )

        return result, metrics

    def _build_agents(self) -> None:
        """
        Instantiate one LLM client pair per agent, each bound to the
        correct response schema, then construct the three agents.

        This is the critical fix vs v1 - v1 reassigned self.openai_llm /
        self.gemini_llm three times so every agent received the
        TrajectoryResponse schema regardless of type.
        """

        # DispatcherAgent: RoutingResponse 
        dispatcher_openai = LLMClient(
            client=AsyncOpenAI(api_key=OPENAI_API_KEY),
            model_name="gpt-4o",
            response_schema=RoutingResponse,
        )
        dispatcher_gemini = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=RoutingResponse,
        )
        self.dispatcher = DispatcherAgent(
            repo=self.repo,
            rag_engine=self.rag,
            openai_llm=dispatcher_openai,
            gemini_llm=dispatcher_gemini,
        )

        # SentinelAgent: FraudResponse 
        sentinel_openai = LLMClient(
            client=AsyncOpenAI(api_key=OPENAI_API_KEY),
            model_name="gpt-4o",
            response_schema=FraudResponse,
        )
        sentinel_gemini = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=FraudResponse,
        )
        self.sentinel = SentinelAgent(
            repo=self.repo,
            rag_engine=self.rag,
            openai_llm=sentinel_openai,
            gemini_llm=sentinel_gemini,
        )

        #  TrajectoryAgent: TrajectoryResponse 
        trajectory_openai = LLMClient(
            client=AsyncOpenAI(api_key=OPENAI_API_KEY),
            model_name="gpt-4o",
            response_schema=TrajectoryResponse,
        )
        trajectory_gemini = LLMClient(
            client=genai.Client(api_key=GEMINI_API_KEY),
            model_name="gemini-2.5-flash",
            response_schema=TrajectoryResponse,
        )
        self.trajectory = TrajectoryAgent(
            repo=self.repo,
            rag_engine=self.rag,
            openai_llm=trajectory_openai,
            gemini_llm=trajectory_gemini,
        )

    @staticmethod
    def _validate_api_keys() -> None:
        """
        Raise ValueError early if any required API key is missing.
        Consolidates the three duplicate key-check blocks from v1.
        """
        missing = []
        if not OPENAI_API_KEY:
            missing.append("OPENAI_API_KEY")
        if not GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY")
        if missing:
            raise ValueError(
                f"Missing required API keys: {', '.join(missing)}. "
                "Set them in your .env file or environment."
            )
    @staticmethod
    def _sanitize(obj):
        """Recursively convert Decimal/datetime to JSON-safe types."""
        from decimal import Decimal
        from datetime import datetime, date
        if isinstance(obj, dict):
            return {k: Orchestrator._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [Orchestrator._sanitize(i) for i in obj]
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, date)):
            return str(obj)
        return obj



# # Central coordinator class for agent execution
# class Orchestrator: 
#     """
#     Sentinel Bank Multi-Agent Orchestrator

#     Responsibilities:
#         - Initialize shared system components
#         - Route incoming requests to correct agent
#         - Return structured unified response
#         - Handle errors safely
#     """
 
#     # Initialize the agents and routing graph
#     def __init__(self):
      
#         # Load dataset once
#         self.dataset_loader = DatasetLoader()

#         # Initialize repository layer
#         self.repo = BankRepository(self.dataset_loader)

#         # Initialize the Graph for routing
#         self.graph = AgentGraph()

#         # Initialize the agents
#     async def initialize(self):
#         """
#          Initialize async components (RAG engine).
#          Must be called before handling requests.
#          """

#         # Load dataset from DB into memory
#         # await self.dataset_loader.load()
        
#         # Initialize RAG Engine
#         self.rag = await create_engine()

#         # Initialize LLm Clients for Dispatcher Agent Only
#         if not OPENAI_API_KEY:
#             raise ValueError("OPENAI_API_KEY is not set.")

#         if not GEMINI_API_KEY:
#             raise ValueError("GEMINI_API_KEY is not set.")

#         self.openai_llm = LLMClient(
#             client=AsyncOpenAI(api_key=OPENAI_API_KEY),
#             model_name="gpt-4o",
#             response_schema=RoutingResponse,
#         )

#         self.gemini_llm = LLMClient(
#             client=genai.Client(api_key=GEMINI_API_KEY),
#             model_name="gemini-2.5-flash",
#             response_schema=RoutingResponse,
#         )
        
#         # Initialize LLm Clients for Sentinel Agent Only
#         if not OPENAI_API_KEY:
#             raise ValueError("OPENAI_API_KEY is not set.")

#         if not GEMINI_API_KEY:
#             raise ValueError("GEMINI_API_KEY is not set.")

#         self.openai_llm = LLMClient(
#             client=AsyncOpenAI(api_key=OPENAI_API_KEY),
#             model_name="gpt-4o",
#             response_schema=FraudResponse,
#         )

#         self.gemini_llm = LLMClient(
#             client=genai.Client(api_key=GEMINI_API_KEY),
#             model_name="gemini-2.5-flash",
#             response_schema=FraudResponse,
#         )

#         # Initialize LLm Clients for Trajectory Agent Only
#         if not OPENAI_API_KEY:
#             raise ValueError("OPENAI_API_KEY is not set.")

#         if not GEMINI_API_KEY:
#             raise ValueError("GEMINI_API_KEY is not set.")

#         self.openai_llm = LLMClient(
#             client=AsyncOpenAI(api_key=OPENAI_API_KEY),
#             model_name="gpt-4o",
#             response_schema=TrajectoryResponse,
#         )

#         self.gemini_llm = LLMClient(
#             client=genai.Client(api_key=GEMINI_API_KEY),
#             model_name="gemini-2.5-flash",
#             response_schema=TrajectoryResponse,
#         )

#         self.dispatcher = DispatcherAgent(self.repo,self.rag, openai_llm=self.openai_llm,gemini_llm=self.gemini_llm)
#         self.sentinel = SentinelAgent(repo=self.repo, rag_engine=self.rag, openai_llm=self.openai_llm,gemini_llm=self.gemini_llm)
#         self.trajectory = TrajectoryAgent(repo=self.repo, rag_engine=self.rag, openai_llm=self.openai_llm,gemini_llm=self.gemini_llm)

#         self._initialized = True

#     # Handle incoming customer complaint
#     async def handle_request(self,request: Dict[str, Any]) -> Dict[str, Any]: # Raw complaint text -> final system response

#         """
#         Route request based on request_type.

#         Expected request format:

#         {
#             "type": "complaint" | "transaction" | "recommendation",
#             ...payload...
#         }
#         """

#         if not self._initialized:
#             raise RuntimeError(
#                 "Orchestrator not initialized. Call await initialize() first."
#             )
        
#         request_id = str(uuid.uuid4())  # Unique ID for tracing this request through logs
#         start_time = time.time()

#         # Validate basic request

#         if not request or "type" not in request:
#             SystemLogger.log_event(
#                 event_type="invalid_request",
#                 message="Request received, no 'type' field.",
#                 request_id=request_id,
#                 metadata={"request": request},
#             )
#             return {
#                 "status": "error",
#                 "message": "Request must include a 'type' field.",
#                 "request_id": request.get("request_id"),
#             }


#         agent_name = self.graph.get_next_agent(request)

#         try:
#             # Request Received Log
#             SystemLogger.log_event(
#                 event_type="Request_received",
#                 message=f"Routing to {agent_name}",
#                 request_id=request_id,
#                 metadata=request
#             )

#             # Agent Execution
#             if agent_name == "DispatcherAgent":
#                 result = await self.dispatcher.run(request)
#                 metrics= Metrics.evaluate_triage(result)              

#             elif agent_name == "SentinelAgent":
#                 result = await self.sentinel.run(request)
#                 metrics= Metrics.evaluate_fraud(result)  

#             elif agent_name == "TrajectoryAgent":
#                 result = await self.trajectory.run(request)
#                 metrics= Metrics.evaluate_product_recommendation(result)  
                        

#             else:
#                 SystemLogger.log_event(
#                 event_type="Unknown_Agent",
#                 message=f"Unknown agent name: {agent_name}",
#                 request_id=request_id
#                     )
               
#                 return {
#                     "status": "error",
#                     "error": f"Unknown agent name: {agent_name}",
#                     "supported_agents": [
#                         "DispatcherAgent",
#                         "SentinelAgent",
#                         "TrajectoryAgent"
#                     ],
#                     "request_id": request_id,
#                 }

#                 # Reasoning Log
#             ReasoningLogger.log(
#                 agent_name=agent_name,
#                 payload=result,
#                 request_id=request_id
#             )


#             # LLM Evaluation
#             llm_evaluation = LLMJudge.evaluate(
#                 agent_name=agent_name,
#                 result=result
#             )

#             SystemLogger.log_event(
#                 event_type="LLM_evaluation completed",
#                 message="LLM evaluation executed",
#                 request_id=request_id,
#                 metadata=llm_evaluation
#             )

#             # Metrics log
#             SystemLogger.log_event(
#                 event_type="Metrics_completed",
#                 message="Metrics evaluation executed",
#                 request_id=request_id,
#                 metadata=metrics
#             )

#             duration = round(time.time() - start_time, 3)

#             SystemLogger.log_event(
#                 event_type="Request_completed",
#                 message="Request processed successfully",
#                 request_id=request_id,
#                 metadata={
#                     "agent": agent_name,
#                     "duration_seconds": duration
#                 }
#             )

#             return {
#                 **result,
#                 **metrics,
#                 **llm_evaluation,
#                 "request_id": request_id,
#                 "processing_time_seconds": duration
#             }


#         except Exception as e:
#             # Production-safe error response
#             return {
#                 "status": "error",
#                 "message": str(e),
#                 "agent": agent_name,
#                 "request_id": request_id
#             }
    


       