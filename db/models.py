"""
Database models for the workflow management system.
"""
import sqlite3
import json
import uuid
from datetime import datetime
import os
import threading
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List


class StepType(Enum):
    AUTOMATED = "automated"
    MANUAL = "manual"


class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_INPUT = "waiting_input"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class WorkflowStep:
    """Individual workflow step configuration and state"""
    name: str
    step_type: StepType
    conditions: Dict[str, Any]  # Parameter conditions to trigger this step
    instructions: str
    mcp_server_config: Optional[Dict[str, Any]] = None  # For automated steps
    status: StepStatus = StepStatus.PENDING
    result: Optional[str] = None
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    
    @classmethod
    def from_config(cls, config):
        step_type = StepType.MANUAL if config["type"] == "manual" else StepType.AUTOMATED
        
        return WorkflowStep(
            name=config["id"],
            step_type=step_type,
            conditions=config.get("conditions", {}),
            instructions=config.get("instructions", ""),
            mcp_server_config=config.get("action")
        )


class Database:
    """SQLite database manager for workflow entities."""

    def __init__(self, db_path="workflows.db"):
        """Initialize the database connection."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.initialize()

    def initialize(self):
        """Initialize the database and create tables if they don't exist."""
        # Create the database directory if it doesn't exist
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        # Connect to the database with check_same_thread=False to allow usage across threads
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        # Enable foreign keys
        self.conn.execute("PRAGMA foreign_keys = ON")
        # Use Row as row factory to get dict-like rows
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()
        # Add a lock for thread safety
        self.lock = threading.RLock()

        # Create workflow_entities table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflow_entities (
            id TEXT PRIMARY KEY,
            name TEXT UNIQUE,
            config_name TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            context TEXT NOT NULL,
            steps TEXT NOT NULL,
            is_cancelled INTEGER NOT NULL DEFAULT 0,
            cancelled_at TEXT,
            logs TEXT NOT NULL
        )
        ''')

        # Create workflow_configs table
        self.cursor.execute('''
        CREATE TABLE IF NOT EXISTS workflow_configs (
            name TEXT PRIMARY KEY,
            description TEXT,
            context TEXT NOT NULL,
            steps TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        ''')

        self.conn.commit()

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager enter method."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit method."""
        self.close()


class WorkflowEntity:
    """Model for workflow entity."""

    def __init__(self, db, id=None, name=None, config_name=None, description=None,
                 context=None, steps=None, is_cancelled=False, cancelled_at=None,
                 logs=None, created_at=None, updated_at=None):
        """Initialize a workflow entity."""
        self.db = db
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.config_name = config_name
        self.description = description
        self.context = context or {}
        self.steps = steps or []  # List of WorkflowStep objects
        self.is_cancelled = is_cancelled
        self.cancelled_at = cancelled_at
        self.logs = logs or []
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or self.created_at

    def save(self):
        """Save the workflow entity to the database."""
        self.updated_at = datetime.utcnow().isoformat()

        # print(f"Saving workflow entity: {str(self)}")
        
        # Convert steps to a serializable format
        serialized_steps = []
        for step in self.steps:
            step_dict = {
                "name": step.name,
                "step_type": step.step_type.value,
                "conditions": step.conditions,
                "instructions": step.instructions,
                "mcp_server_config": step.mcp_server_config,
                "status": step.status.value,
                "result": step.result,
                "error": step.error,
                "started_at": step.started_at,
                "completed_at": step.completed_at
            }
            serialized_steps.append(step_dict)
        
        # print(f"Serialized steps: {json.dumps(serialized_steps, indent=2)}")
        # Use the lock to ensure thread safety
        with self.db.lock:
            self.db.cursor.execute('''
            INSERT OR REPLACE INTO workflow_entities (
                id, name, config_name, description, created_at, updated_at,
                context, steps, is_cancelled, cancelled_at, logs
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                self.id,
                self.name,
                self.config_name,
                self.description,
                self.created_at,
                self.updated_at,
                json.dumps(self.context),
                json.dumps(serialized_steps),
                1 if self.is_cancelled else 0,
                self.cancelled_at,
                json.dumps(self.logs)
            ))
            
            self.db.conn.commit()
        return self

    def add_log(self, message, level="INFO"):
        """Add a log entry to the workflow entity."""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "message": message
        }
        self.logs.append(log_entry)
        return self

    def cancel(self, reason=None):
        """Cancel the workflow."""
        self.is_cancelled = True
        self.cancelled_at = datetime.utcnow().isoformat()
        self.add_log(f"Workflow cancelled. Reason: {reason}", "WARNING")
        return self

    def update_context(self, context):
        """Update workflow context."""
        self.context.update(context)
        self.updated_at = datetime.utcnow().isoformat()
        self.add_log(f"context updated: {context}", "INFO")
        return self

    def complete_step(self, step_or_step_id):
        """Mark a step as completed."""
        if isinstance(step_or_step_id, str):
            step = next((s for s in self.steps if s.name == step_or_step_id), None)
        else:
            step = step_or_step_id
            
        if step:
            step.status = StepStatus.COMPLETED
            step.completed_at = datetime.utcnow().isoformat()
            self.add_log(f"Step completed: {step.name}", "INFO")
            self.save()
        return self

    def fail_step(self, step_or_step_id, error=None):
        """Mark a step as failed."""
        if isinstance(step_or_step_id, str):
            step = next((s for s in self.steps if s.name == step_or_step_id), None)
        else:
            step = step_or_step_id
            
        if step:
            step.status = StepStatus.FAILED
            step.error = error
            self.add_log(f"Step failed: {step.name} - {error}", "ERROR")
        return self

    def start_step(self, step_or_step_id):
        """Start executing a step."""
        if isinstance(step_or_step_id, str):
            step = next((s for s in self.steps if s.name == step_or_step_id), None)
        else:
            step = step_or_step_id
            
        if step:
            # Reset any currently running steps
            # for s in self.steps:
            #     if s.status == StepStatus.RUNNING:
            #         s.status = StepStatus.PENDING
            
            step.status = StepStatus.RUNNING
            step.started_at = datetime.utcnow().isoformat()
            self.add_log(f"Step started: {step.name}", "INFO")
        return self

    def add_step(self, step):
        """Add a new step to the workflow."""
        self.steps.append(step)
        self.add_log(f"Step added: {step.name}", "INFO")
        return self

    def get_step(self, step_id):
        """Get a step by ID."""
        return next((s for s in self.steps if s.name == step_id), None)

    def get_steps_by_status(self, status):
        """Get all steps with the given status."""
        return [s for s in self.steps if s.status == status]

    def get_current_step(self):
        """Get the currently running step, if any."""
        running_steps = [step for step in self.steps if step.status == StepStatus.RUNNING]
        return running_steps[0] if running_steps else None
    
    def get_first_step(self):
        """Get the first step in the workflow."""
        if not self.steps:
            print("No steps in the workflow.")
        return self.steps[0] if self.steps else None

    def get_next_pending_step(self):
        """Get the next pending step, if any."""
        pending_steps = [step for step in self.steps if step.status == StepStatus.PENDING]
        return pending_steps[0] if pending_steps else None

    def to_dict(self):
        """Convert the workflow entity to a dictionary."""
        # Convert steps to a serializable format
        serialized_steps = []
        for step in self.steps:
            step_dict = {
                "name": step.name,
                "type": step.step_type.value,
                "status": step.status.value,
                "instructions": step.instructions,
                "result": step.result,
                "error": step.error,
                "started_at": step.started_at,
                "completed_at": step.completed_at
            }
            serialized_steps.append(step_dict)
        
        return {
            "id": self.id,
            "name": self.name,
            "config_name": self.config_name,
            "description": self.description,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "context": self.context,
            "steps": serialized_steps,
            "is_cancelled": self.is_cancelled,
            "cancelled_at": self.cancelled_at,
            "logs": self.logs
        }

    @classmethod
    def from_row(cls, db, row):
        """Create a workflow entity from a database row."""
        if not row:
            return None
        
        # Deserialize steps
        steps = []

        # steps_data = row["steps"]
        # print("Steps data: " + steps_data)
        # print("Steps in the row: " + row["steps"])
        # print("steps" in row)
        if "steps" in row.keys() and row["steps"]:
            steps_data = json.loads(row["steps"])
            for step_data in steps_data:
                # print(f"Deserializing step data: {str(step_data)}")
                step = WorkflowStep(
                    name=step_data["name"],
                    step_type=StepType(step_data["step_type"]),
                    conditions=step_data["conditions"],
                    instructions=step_data["instructions"],
                    mcp_server_config=step_data.get("mcp_server_config"),
                    status=StepStatus(step_data["status"]),
                    result=step_data.get("result"),
                    error=step_data.get("error"),
                    started_at=step_data.get("started_at"),
                    completed_at=step_data.get("completed_at")
                )

                # print(f"Deserialized step: {step.name}")
                steps.append(step)
        # print("row:" + str(row))
        # print("steps in the row:" + row["steps"])
        # print(f"Deserialized steps: {steps}")
        
        return cls(
            db=db,
            id=row["id"],
            name=row["name"],
            config_name=row["config_name"],
            description=row["description"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            context=json.loads(row["context"]),
            steps=steps,
            is_cancelled=bool(row["is_cancelled"]),
            cancelled_at=row["cancelled_at"],
            logs=json.loads(row["logs"])
        )

    @classmethod
    def get_by_id(cls, db, workflow_id):
        """Get a workflow entity by ID."""
        with db.lock:
            db.cursor.execute(
                "SELECT * FROM workflow_entities WHERE id = ?", (workflow_id,)
            )
            row = db.cursor.fetchone()
            # print(f"Retrieved row: {dict(row)}")
        return cls.from_row(db, row)

    @classmethod
    def get_by_name(cls, db, name):
        """Get a workflow entity by name."""
        with db.lock:
            db.cursor.execute(
                "SELECT * FROM workflow_entities WHERE name = ?", (name,)
            )
            row = db.cursor.fetchone()
        return cls.from_row(db, row)

    @classmethod
    def get_by_description(cls, db, description):
        """Get a workflow entity by description."""
        with db.lock:
            db.cursor.execute(
                "SELECT * FROM workflow_entities WHERE description LIKE ?", (f"%{description}%",)
            )
            row = db.cursor.fetchone()
        return cls.from_row(db, row)

    @classmethod
    def list_all(cls, db, filters=None):
        """List all workflow entities with optional filters."""
        query = "SELECT * FROM workflow_entities"
        params = []
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if key in ["id", "name", "config_name"]:
                    conditions.append(f"{key} = ?")
                    params.append(value)
                elif key == "description":
                    conditions.append("description LIKE ?")
                    params.append(f"%{value}%")
                elif key == "is_cancelled":
                    conditions.append("is_cancelled = ?")
                    params.append(1 if value else 0)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        with db.lock:
            db.cursor.execute(query, params)
            rows = db.cursor.fetchall()
        return [cls.from_row(db, row) for row in rows]
