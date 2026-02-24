from typing import Dict, Any
from openai import AsyncOpenAI
from google import genai
from openai import RateLimitError
from app.agents.abstract_agent import BaseAgent
from app.prompts.dispatcher_prompt import Dispatcher_System_Prompt
from app.utils.logger import ReasoningLogger
from app.utils.schemas import RoutingResponse
from app.utils.llm_client import LLMClient
import asyncio
from app.settings import OPENAI_API_KEY, GEMINI_API_KEY


class DispatcherAgent(BaseAgent):

    def __init__(self):
        super().__init__(name="DispatcherAgent")
        self.openai_llm = None
        self.gemini_llm = None

        if OPENAI_API_KEY:
            try:
                self.openai_llm = LLMClient(
                    client=AsyncOpenAI(api_key=OPENAI_API_KEY),
                    model_name="gpt-4o",
                    response_schema=RoutingResponse,
                )
            except Exception as e:
                print(f"Failed to initialize OpenAI Client: {e}")

        if GEMINI_API_KEY:
            try:
                self.gemini_llm = LLMClient(
                    client=genai.Client(api_key=GEMINI_API_KEY),
                    model_name="gemini-2.0-flash",
                    response_schema=RoutingResponse,
                )
            except Exception as e:
                print(f"Failed to initialize Gemini Client: {e}")

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        complaint_text: str = input_data.get("complaint_text", "").lower()

        # 1. Check if we have any AI keys. If not, use Simulation Mode.
        if not self.openai_llm and not self.gemini_llm:
            print("⚠️ [SIMULATION MODE] No AI providers initialized. Using keywords.")
            return self._run_simulation(complaint_text)

        # 2. Try OpenAI first (if initialized)
        if self.openai_llm:
            try:
                llm_response = await self.openai_llm.generate(
                    system_prompt=Dispatcher_System_Prompt, user_input=complaint_text
                )
                return self._finalize_response(llm_response)
            except Exception as e:
                print(f"OpenAI error: {e}. Trying Gemini...")

        # 3. Try Gemini fallback (if initialized)
        if self.gemini_llm:
            try:
                llm_response = await self.gemini_llm.generate(
                    system_prompt=Dispatcher_System_Prompt, user_input=complaint_text
                )
                return self._finalize_response(llm_response)
            except Exception as e:
                print(f"Gemini error: {e}.")

        # 4. Final Fallback if AI fails or isn't available
        return self._run_simulation(complaint_text)

    def _finalize_response(self, llm_response) -> Dict[str, Any]:
        result = llm_response.model_dump()
        result["agent"] = self.name
        ReasoningLogger.log(agent_name=self.name, payload=result)
        return result

    def _run_simulation(self, complaint_text: str) -> Dict[str, Any]:
        # Simple keyword logic for testing
        if any(
            word in complaint_text for word in ["transfer", "money", "sent", "receive"]
        ):
            dept, code = "Transactions", "TRX-001"
        elif any(
            word in complaint_text for word in ["login", "password", "reset", "account"]
        ):
            dept, code = "Account Services", "ACC-002"
        elif any(
            word in complaint_text
            for word in ["scam", "fraud", "stolen", "unrecognized"]
        ):
            dept, code = "Security & Fraud", "SEC-003"
        else:
            dept, code = "General Support", "GEN-000"

        result = {
            "department": dept,
            "department_code": code,
            "priority": "High" if "urgent" in complaint_text else "Medium",
            "sentiment": (
                "Frustrated"
                if any(x in complaint_text for x in ["bad", "poor", "why"])
                else "Neutral"
            ),
            "agent": self.name + " (Simulated)",
        }
        ReasoningLogger.log(agent_name=self.name, payload=result)
        return result


async def main():
    dispatcher = DispatcherAgent()
    complaint_text = """I transferred money to a friend of mine who in turn
    complained that he hasn't been credited. Please look into this"""
    result = await dispatcher.run(input_data={"complaint_text": complaint_text})
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
