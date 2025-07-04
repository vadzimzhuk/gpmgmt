"""
Database models for the workflow step.
"""
# import sqlite3
# import json
# import uuid
# from datetime import datetime
# import os
# import threading
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class WorkflowStep:
    """Individual workflow step configuration and state"""
    name: str
    instructions: str
    mcp_server_config: Optional[Dict[str, Any]] = None 
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    
    @classmethod
    def from_config(cls, config):
        
        return WorkflowStep(
            name=config["id"],
            instructions=config.get("instructions", ""),
            mcp_server_config=config.get("action")
        )
    
    def to_dict(self):
        """Convert the step to a dictionary for serialization."""
        return {
            "name": self.name,
            "instructions": self.instructions,
            "mcp_server_config": self.mcp_server_config,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at,
            "completed_at": self.completed_at
        }