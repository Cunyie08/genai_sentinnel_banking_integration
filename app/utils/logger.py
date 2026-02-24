import json
import os
from datetime import datetime


class ReasoningLogger:
    @staticmethod
    def log(agent_name: str, payload: dict):
        """Logs the reasoning process of an agent to the console and potentially a file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {"timestamp": timestamp, "agent": agent_name, "data": payload}

        # Simple console log for now
        print(f"\n[REASONING LOG - {timestamp}] {agent_name}")
        print(json.dumps(payload, indent=2))
        print("-" * 40)

        # Optional: Save to file
        log_dir = os.path.join(os.getcwd(), "app", "logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

        log_file = os.path.join(log_dir, "reasoning.log")
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
