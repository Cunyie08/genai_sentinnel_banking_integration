# In this file contains the abstract base agent that defines the common interface for all the agents

from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseAgent(ABC): # Parent class for all agents in sentinnel bank
    """
    Enforces a unified async interface to ensure the orchestrator can call all agents consistently.
    """
    ""
    @abstractmethod
    async def run(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute agent logic.

        Args:
            payload: structured dictionary

        Returns:
            structured response dictionary
        """
        pass

