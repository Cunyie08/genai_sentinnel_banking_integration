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
    # # Initialize the agent
    # def __init__(self, name:str = "gpt-4o"): # string for human-readable identifier for the agent
    #     self.name: str = name

    # @abstractmethod # Catching errors early

    # # Execute the agent's logic
    # def run(self, input_data:Dict[str, Any]) -> Dict[str, Any]: # keys - strings, values - flexible
    
    #     """
    #     Args:
    #         input_data (Dict[str, Any]): For structured input payload

    #     Returns:
    #          Dict[str, Any]: The Agent decision 

    #     Raises:
    #         NotImplementedError: If not implemented by subclass
    #     """
    #     pass
    
