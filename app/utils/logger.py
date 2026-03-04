# This file contains the central logging for Sentinnel bank
# To responsibly write structured reasoning logs (audit/evaluation purposes)

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional


# Create a class that handles strutured logging of agents decisions


class BaseLogger:
    LOG_DIR = "app/logs"

    @classmethod
    def _ensure_log_dir(cls):
        os.makedirs(cls.LOG_DIR, exist_ok=True)

    @classmethod
    def _write(cls, filename: str, data: Dict[str, Any]):
        cls._ensure_log_dir()
        path = os.path.join(cls.LOG_DIR, filename)

        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")


class ReasoningLogger(BaseLogger):
    Log_File = "reasoning.log"

    @classmethod  #
    # Write a reasoning log entry
    def log(cls, agent_name: str, payload: Dict[str, Any]) -> None:
        """
        Args: agent_name: Agent producing the log
        Returns: Decision data to be logged
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "payload": payload,
        }
        cls._write(cls.Log_File, log_entry)


# System Logger (Orchestrator / Errors / Timing)


class SystemLogger(BaseLogger):
    sys_log_File = "system.log"

    @classmethod
    def log_event(
        cls,
        event_type: str,
        message: str,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        sys_log_entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "event_type": event_type,
            "message": message,
            "metadata": metadata or {},
        }
        cls._write(cls.sys_log_File, sys_log_entry)
