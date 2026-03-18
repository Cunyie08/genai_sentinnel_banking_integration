"""
Sentinnel Bank - Dispatcher Agent

Responsibilities:
    - Accept a complaint_id from the Orchestrator
    - Fetch the complaint record from the database via SentinelRepository
    - Run RAG-grounded routing (department + priority + SLA)
    - Enrich routing decision with an LLM-generated audit explanation
    - Fall back from OpenAI -> Gemini on rate-limit errors
    - Return a structured result dict (never raises - re-raises to Orchestrator)

Integration contract (what Orchestrator provides):
    repo       : SentinelRepository  - async DB gateway (shared instance)
    rag_engine : RAGQueryEngine      - vector search (shared instance)
    openai_llm : LLMClient[RoutingResponse] - primary LLM
    gemini_llm : LLMClient[RoutingResponse] - fallback LLM

The agent NEVER re-creates these - it uses exactly what is injected.

Standalone usage (dev/debug only):
    python -m app.agents.dispatcher_agent
"""


import asyncio
import traceback
from typing import Any, Dict, Optional

from openai import RateLimitError

from app.agents.abstract_agent import BaseAgent
from app.data.db_connections import get_engine
from app.data.dataset_loader import DatasetLoader
from app.data.repository import BankRepository
from app.prompts.dispatcher_prompt import Dispatcher_System_Prompt
from app.rag.rag_system.rag_querys import RAGQueryEngine, create_engine
from app.utils.llm_client import LLMClient
from app.utils.logger import ReasoningLogger, SystemLogger
from app.utils.schemas import RoutingResponse
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY


class DispatcherAgent(BaseAgent):
    """
    Routes customer complaints to the correct department using a
    RAG-grounded policy engine + LLM explanation layer.

    Args:
        repo:       Async BankRepository - injected by Orchestrator.
        rag_engine: RAGQueryEngine           - injected by Orchestrator.
        openai_llm: LLMClient[RoutingResponse] - primary, injected by Orchestrator.
        gemini_llm: LLMClient[RoutingResponse] - fallback, injected by Orchestrator.
    """

    def __init__(
        self,
        repo:       BankRepository,
        rag_engine: RAGQueryEngine,
        openai_llm: LLMClient,
        gemini_llm: LLMClient,
    ) -> None:
        # Accept injected dependencies - never re-create them here
        self.repo       = repo
        self.rag_engine = rag_engine
        self.openai_llm = openai_llm
        self.gemini_llm = gemini_llm


    # Main entry point

    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a complaint routing request end-to-end.

        Args:
        Supports two input modes:

        Mode A: Live frontend input (demo / production intake):
            {
                "complaint_text": "My card was charged twice at Shoprite",
                "customer_id":    "optional-uuid",       # optional
                "channel":        "web",                  # optional
            }

        Mode B: Database lookup (batch processing / orchestrator):
            {
                "complaint_id": "CMP-000001"
            }

        If both are provided, complaint_text takes priority (live mode).

        Returns:
            Structured routing result dict with department, priority,
            SLA, confidence, RAG reasoning, and LLM explanation.

        Raises:
            ValueError  if complaint_id is missing or complaint not found.
            Exception   re-raised to Orchestrator after logging.
        """
        complaint_id:   Optional[str] = payload.get("complaint_id")
        complaint_text: Optional[str] = payload.get("complaint_text", "").strip()

        # Determine input mode
        is_live_input = bool(complaint_text)

        SystemLogger.log_event(
            event_type="dispatcher_started",
            message="DispatcherAgent started",
            metadata={
                "mode":         "live_input" if is_live_input else "db_lookup",
                "complaint_id": complaint_id,
                "has_text":     is_live_input,
            },
        )


        try:
            # Validate input 
            if is_live_input:
                # Mode A: frontend provided complaint text directly
                # Build a synthetic complaint_record from the payload
                complaint_record = {
                    "complaint_text":    complaint_text,
                    "customer_id":       payload.get("customer_id"),
                    "complaint_channel": payload.get("channel", "web"),
                    "sentiment":         None,   # not pre-computed for live input
                    "linked_transaction": None,
                    "department_code":   None,
                    "priority_level":    None,
                }
                complaint_id = complaint_id or "LIVE"

                SystemLogger.log_event(
                    event_type="live_complaint_received",
                    message="Processing live complaint text from frontend",
                    metadata={
                        "customer_id": complaint_record["customer_id"],
                        "channel":     complaint_record["complaint_channel"],
                        "text_length": len(complaint_text),
                    },
                )

            else:
                # Mode B: fetch complaint record from database by ID
                if not complaint_id:
                    raise ValueError(
                        "Provide either 'complaint_text' (live input) "
                        "or 'complaint_id' (database lookup)."
                    )

                complaint_record = await self.repo.get_complaint(complaint_id)

                if complaint_record is None:
                    raise ValueError(
                        f"Complaint '{complaint_id}' not found in database."
                    )

                complaint_text = complaint_record["complaint_text"]

                SystemLogger.log_event(
                    event_type="complaint_fetched",
                    message="Fetched complaint from database",
                    metadata={
                        "complaint_id": complaint_id,
                        "department":   complaint_record.get("department_code"),
                        "priority":     complaint_record.get("priority_level"),
                        "sentiment":    complaint_record.get("sentiment"),
                    },
                )

            # RAG-grounded routing 
            routing = await self.rag_engine.detect_complaint_category(complaint_text)

            SystemLogger.log_event(
                event_type="rag_routing_completed",
                message="Policy-based routing completed",
                metadata={
                    "department_code": routing["department_code"],
                    "priority_level":  routing["priority_level"],
                    "confidence":      routing["confidence"],
                },
            )

            # Capture RAG decision - this is the ground truth, LLM must not override it
            rag_decision = {
                "department_code": routing["department_code"],
                "department_name": routing["department_name"],
                "priority_level":  routing["priority_level"],
                "sla_hours":       routing["sla_hours"],
                "confidence":      routing["confidence"],
                "routing_method":  routing["routing_method"],
                "keyword_matches": routing["keyword_matches"],
                "reasoning":       routing["reasoning"],
            }

            # LLM audit explanation (OpenAI -> Gemini fallback) 
            llm_input = self._build_explanation_prompt(complaint_text, rag_decision)
            llm_result = await self._call_llm_with_fallback(llm_input)

            # Assemble final result 
            result = self._build_result(
                complaint_id     = complaint_id,
                complaint_record = complaint_record,
                rag_decision     = rag_decision,
                llm_result       = llm_result,
            )

            ReasoningLogger.log(agent_name="DispatcherAgent", payload=result)

            SystemLogger.log_event(
                event_type="dispatcher_completed",
                message="DispatcherAgent execution completed",
                metadata={
                    "department": result["department_name"],
                    "priority":   result["priority_level"],
                },
            )

            return result

        except Exception as exc:
            SystemLogger.log_event(
                event_type="dispatcher_failed",
                message=str(exc),
                metadata={
                    "complaint_id": complaint_id,
                    "trace":        traceback.format_exc(),
                },
            )
            raise

    # Private helpers

    def _build_explanation_prompt(
        self,
        complaint_text: str,
        rag_decision:   Dict[str, Any],
    ) -> str:
        """Build the LLM input payload for the explanation layer."""
        return (
            f"Complaint:\n{complaint_text}\n\n"
            f"Routing Decision:\n"
            f"  Department Code : {rag_decision['department_code']}\n"
            f"  Department Name : {rag_decision['department_name']}\n"
            f"  Priority        : {rag_decision['priority_level']}\n"
            f"  SLA Hours       : {rag_decision['sla_hours']}\n"
            f"  Confidence      : {rag_decision['confidence']:.2%}\n\n"
            f"Provide a clear, audit-ready explanation of why this complaint "
            f"was routed to this department, referencing the policy basis."
        )

    async def _call_llm_with_fallback(self, user_input: str) -> RoutingResponse:
        """
        Call OpenAI primary. On RateLimitError fall back to Gemini.
        Returns a RoutingResponse Pydantic object.
        """
        if self.openai_llm:
            try:
                response = await self.openai_llm.generate(
                    system_prompt=Dispatcher_System_Prompt,
                    user_input=user_input,
                )
                return self._ensure_routing_response(response)
            except RateLimitError:
                SystemLogger.log_event(
                    event_type="llm_fallback",
                    message="OpenAI rate limit hit - falling back to Gemini",
                )

        response = await self.gemini_llm.generate(
            system_prompt=Dispatcher_System_Prompt,
            user_input=user_input,
        )
        return self._ensure_routing_response(response)

    def _ensure_routing_response(self, response: Any) -> RoutingResponse:
        """
        Convert response to RoutingResponse if needed.
        Handles Pydantic models, dicts, and already-instantiated RoutingResponse objects.
        """
        if isinstance(response, RoutingResponse):
            return response
        if isinstance(response, dict):
            return RoutingResponse(**response)
        if hasattr(response, 'model_dump') and callable(response.model_dump):
            data = response.model_dump()
            if isinstance(data, dict):
                return RoutingResponse(**data)
        if hasattr(response, '__dict__'):
            return RoutingResponse(**response.__dict__)
        raise ValueError(f"Cannot convert response of type {type(response)} to RoutingResponse")

    def _build_result(
        self,
        complaint_id:     str,
        complaint_record: Dict[str, Any],
        rag_decision:     Dict[str, Any],
        llm_result:       RoutingResponse,
    ) -> Dict[str, Any]:
        """
        Merge RAG decision + complaint context + LLM explanation into the
        final result dict.

        RAG values are always authoritative, LLM cannot override
        department_code, priority, SLA, or confidence.

        Works identically for both live input and DB-fetched complaints.
        """
        result = llm_result.model_dump()

        # RAG decision is authoritative - overwrite any LLM values
        result["department_code"] = rag_decision["department_code"]
        result["department_name"] = rag_decision["department_name"]
        result["priority_level"]  = rag_decision["priority_level"]
        result["sla_hours"]       = rag_decision["sla_hours"]
        result["confidence"]      = rag_decision["confidence"]
        result["routing_method"]  = rag_decision["routing_method"]
        result["keyword_matches"] = rag_decision["keyword_matches"]

        # Combine RAG policy reasoning + LLM narrative explanation
        result["reasoning"] = (
            f"Policy Basis:\n{rag_decision['reasoning']}\n\n"
            f"Explanation:\n{result.get('reasoning', '')}"
        )

        # Complaint context (identical fields regardless of input mode)
        result["complaint_id"]       = complaint_id
        result["complaint_text"]     = complaint_record["complaint_text"]
        result["customer_id"]        = complaint_record.get("customer_id")
        result["sentiment"]          = complaint_record.get("sentiment")
        result["complaint_channel"]  = complaint_record.get("complaint_channel")
        result["linked_transaction"] = complaint_record.get("linked_transaction")
        result["agent"]              = "DispatcherAgent"

        return result


# Standalone entry point

async def _main() -> None:
    """
    Standalone runner for direct agent testing without the full Orchestrator.
    Uses the same async DB stack so behaviour is identical to production.
    """
    from openai import AsyncOpenAI
    from google import genai

    # Bootstrap infrastructure (mirrors Orchestrator.initialize()) 
    engine = get_engine()

    loader = DatasetLoader(engine)
    await loader.seed()

    repo = BankRepository(engine)

    health = await repo.health_check()
    print(f"[Dev] DB health: {health}")

    rag_engine = await create_engine()

    openai_llm = LLMClient(
        client=AsyncOpenAI(api_key=OPENAI_API_KEY),
        model_name="gpt-4o",
        response_schema=RoutingResponse,
    )
    gemini_llm = LLMClient(
        client=genai.Client(api_key=GEMINI_API_KEY),
        model_name="gemini-2.0-flash",
        response_schema=RoutingResponse,
    )

    agent = DispatcherAgent(
        repo=repo,
        rag_engine=rag_engine,
        openai_llm=openai_llm,
        gemini_llm=gemini_llm,
    )

    # Fetch a real complaint_id from the database
    health = await repo.health_check()
    print(f"[Dev] Complaints in DB: {health['complaints']}")

    # Use the repository to get a sample complaint_id
    from sqlalchemy import select, text
    from app.data.db_connections import get_async_session
    from Backend.models import Complaint

    async with get_async_session(engine) as session:
        result = await session.execute(
            select(Complaint.complaint_id).limit(1).offset(25)
        )
        complaint_id = result.scalar()

    print(f"[Dev] Testing with complaint_id: {complaint_id}")

    result = await agent.run({"complaint_id": complaint_id})

    print("\n=== DISPATCHER OUTPUT ===")
    for k, v in result.items():
        if k not in ("reasoning", "complaint_text"):
            print(f"  {k:<22}: {v}")
    print(f"\n  reasoning:\n{result.get('reasoning', '')}")


if __name__ == "__main__":
    asyncio.run(_main())




# from typing import Dict, Any
# from openai import AsyncOpenAI
# from google import genai
# from openai import RateLimitError
# from app.agents.abstract_agent import BaseAgent
# from app.prompts.dispatcher_prompt import Dispatcher_System_Prompt
# from app.utils.logger import ReasoningLogger, SystemLogger
# from app.utils.schemas import RoutingResponse
# import asyncio
# from app.rag.rag_system.rag_querys import RAGQueryEngine
# from app.rag.rag_system.chromadb_config import initialize_chromadb
# from app.utils.llm_client import LLMClient
# from app.settings import OPENAI_API_KEY, GEMINI_API_KEY
# from app.data.dataset_loader import DatasetLoader
# from app.data.repository import BankRepository
# from app.rag.rag_system.rag_querys import create_engine
# import traceback
# from dotenv import load_dotenv


# load_dotenv()

# class DispatcherAgent(BaseAgent):

#     def __init__(self, repo, rag_engine, openai_llm, gemini_llm):
#         self.repo = repo
#         self.rag_engine = rag_engine
#         self.openai_llm = openai_llm
#         self.gemini_llm = gemini_llm

#         # Initialize the RAG
#         self.client, self.config = initialize_chromadb()
#         self.rag_engine = RAGQueryEngine(self.client, self.config)

#         # Initialize the Dataset repository
#         self.repo = repo

#         # OpenAI LLM (Explanation Layer)
#         if OPENAI_API_KEY:
#             self.openai_llm = LLMClient(
#                 client=AsyncOpenAI(api_key=OPENAI_API_KEY),
#                 model_name="gpt-4o",
#                 response_schema=RoutingResponse,
#             )
#         else:
#             self.openai_llm = None
#             print("DispatcherAgent: OPENAI_API_KEY missing. OpenAI features disabled.")

#         # Gemini for fallback
#         self.gemini_llm = LLMClient(
#             client=genai.Client(api_key=GEMINI_API_KEY),
#             model_name="gemini-2.0-flash",
#             response_schema=RoutingResponse,
#         )
#         if not GEMINI_API_KEY:
#             raise ValueError("GEMINI_API_KEY is not set.")

#     async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
#         complaint_id: str | None = payload.get("complaint_id")

#         SystemLogger.log_event(
#             event_type="DispatcherAgent_started",
#             message="DispatcherAgent started processing complaint_id",
#             metadata={"complaint_id": complaint_id}
#         )
    
#         try:
#             # Validate before calling the repository
#             if complaint_id is None:
#                 raise ValueError("complaint_id is required for DispatcherAgent.")

#             complaint_record = self.repo.get_complaints(complaint_id)
#             complaint_text = complaint_record["complaint_text"]

#             SystemLogger.log_event(
#                 event_type="Complaint_fetched", 
#                 message="Fetched complaint text for complaint_id",
#                 metadata={"complaint_id": complaint_id}
#             )

#             # Call RAG for policy-grounded routing
#             routing = await self.rag_engine.detect_complaint_category(
#                 complaint_text

#                 )
            
#             SystemLogger.log_event(
#                 event_type="RAG_routing_completed",
#                 message=f"Policy-based routing completed for complaint_id: {complaint_id}",
#                 metadata={"department_code": routing["department_code"], "priority_level": routing["priority_level"]}
#             )

#             # Build base routing from the RAG engine 

#             base_result = {
#                 "department_code": routing["department_code"],
#                 "department_name": routing["department_name"],
#                 "priority_level": routing["priority_level"],
#                 "sla_hours": routing["sla_hours"],
#                 "confidence": routing["confidence"],
#                 "routing_method": routing["routing_method"],
#                 "keyword_matches": routing["keyword_matches"],
#                 "reasoning": routing["reasoning"],
#             }

#             # LLM explanation/formatting
#             explanation_payload = f"""
#             Complaint: {complaint_text}
            
#             Routing Decision:
#             Department Code: {base_result['department_code']}
#             Department Name: {base_result['department_name']}
#             Priority: {base_result['priority_level']}
#             SLA Hours: {base_result['sla_hours']}

#             Provide a clear audit-ready explanation
#             """

#             try:
#                 llm_response = await self.openai_llm.generate(
#                 system_prompt=Dispatcher_System_Prompt,
#                 user_input=explanation_payload
#             )


#             except RateLimitError:
#                 print("OpenAI rate limited. Falling back to Gemini...")
#                 SystemLogger.log_event(
#                     event_type="LLM_fallbacks",
#                     message="OpenAI rate limit exceeded. Falling back to Gemini."
#                 )

#                 llm_response = await self.gemini_llm.generate(
#                     system_prompt=Dispatcher_System_Prompt,
#                     user_input=explanation_payload
#                 )

#             SystemLogger.log_event(
#                 event_type="LLM_explanation_completed",
#                 message="LLM explanation generated"
#             )

#             result = llm_response.model_dump()

#             # Preservig RAG decision integrity
#             result['department_code'] = base_result['department_code']
#             result['department_name'] = base_result['department_name']
#             result['priority_level'] = base_result['priority_level']
#             result['routing_method'] = base_result['routing_method']
#             result['keyword_matches'] = base_result['keyword_matches']
#             result['sla_hours'] = base_result['sla_hours']
#             result['confidence'] = base_result['confidence']

#             # Preservig RAG decision integrity + add LLM explanation layer
#             result['reasoning'] = (
#                 f"Policy Basis:\n{base_result['reasoning']}\n\n"
#                 f"Explanation: \n{result.get('reasoning', '')}") # To extracting grounded policy, LLM explanation and audit traceability
            
#             result['agent'] = "DispatcherAgent"


#             # Logging
#             ReasoningLogger.log(
#                 agent_name="DispatcherAgent",
#                 payload=result
#             )

#             SystemLogger.log_event(
#                 event_type="DispatcherAgent_completed",
#                 message="DispatcherAgent execution completed",
#                 metadata={"department": result['department_name'], "priority": result['priority_level']}
#             )

#             return result
        
#         except Exception as e:

#             SystemLogger.log_event(
#                 event_type="Agent_failed",
#                 message=str(e),
#                 metadata={"complaint_id": complaint_id,
#                           "trace": traceback.format_exc()}
#             )

#             raise



# async def main():

#     # Infrastructure Setup (Same as Orchestrator)

#     dataset_loader = DatasetLoader()
#     await dataset_loader.load()
#     repo = BankRepository(dataset_loader)

#     rag_engine = await create_engine()

#     openai_llm = LLMClient(
#         client=AsyncOpenAI(api_key=OPENAI_API_KEY),
#         model_name="gpt-4o",
#         response_schema=RoutingResponse,
#     )

#     gemini_llm = LLMClient(
#         client=genai.Client(api_key=GEMINI_API_KEY),
#         model_name="gemini-2.0-flash",
#         response_schema=RoutingResponse,
#     )

#     agent = DispatcherAgent(
#         repo=repo,
#         rag_engine=rag_engine,
#         openai_llm=openai_llm,
#         gemini_llm=gemini_llm,
#     )

#     # Get a real complaint ID from dataset
#     complaint_id = agent.repo.dataset_loader.complaints.iloc[25]["complaint_id"]

#     result = await agent.run({"complaint_id": complaint_id})

#     print("\n=== DISPATCHER OUTPUT ===")
#     print(result)


# if __name__ == "__main__":
#     import asyncio

#     asyncio.run(main())
