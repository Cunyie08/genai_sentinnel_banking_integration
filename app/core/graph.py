# This file contains the Agent routing graph for Sentinnel banking - Who should act next?

"""
This module defines how agents are connected and how the task flow.
"""

# Create a class for the Orchestration logic to determine which agents should handle the next task based on the dispatcher's output
class AgentGraph:

    # Define the map that links the corresponding department to each agent

    def __init__(self): # initialize the routing map

        # Mapping between department labels and agent identifiers
        self.routing_table = {
                "complaint": "DispatcherAgent",   
                "transaction": "SentinelAgent",   
                "recommendation": "TrajectoryAgent" 
        }

    # Define the agent to handle the next request

    def get_next_agent(self, request_decision: dict) -> str | None: # returns a string instead of an agent object for easy replacement of agents and cleaner orchestraion logic.
        
        """ 
        Args: 
            dispatch_decision is the output from the DispatcherAgent, expected to contain a department key

        Returns:
            A string with the Name of the agent to handle the next task    
            
        """  
        # Extract the department from the dispatcher ouput
        department = request_decision.get("department")

        # Search for the agent responsible for this department
        if department is not None:
            next_agent = self.routing_table.get(department)
        else:
            next_agent = None
        
        return next_agent



