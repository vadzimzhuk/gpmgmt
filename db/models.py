"""
Database models for the workflow management system.
"""
# import sqlite3
import json
import uuid
from datetime import datetime
# import os
# import threading
from enum import Enum
from dataclasses import dataclass
# from typing import Dict, Any, Optional, List
from db.workflowStep import WorkflowStep, StepType, StepStatus
# from db.database import Database

class WorkflowStatus(Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

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
        self.status = WorkflowStatus.CREATED
        self.context = context or {}
        self.steps = steps or []
        self.is_cancelled = is_cancelled
        self.cancelled_at = cancelled_at
        self.logs = logs or []
        self.created_at = created_at or datetime.utcnow().isoformat()
        self.updated_at = updated_at or self.created_at

    def save(self):
        """Save the workflow entity to the database."""
        self.updated_at = datetime.utcnow().isoformat()
        
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
    
    # ============== Business logic methods ================
    def complete(self):
        """Mark the workflow as completed."""
        self.status = WorkflowStatus.COMPLETED
        self.updated_at = datetime.utcnow().isoformat()
        self.add_log("Workflow completed successfully.", "INFO")
        self.save()
        return self

    def cancel(self, reason=None):
        """Cancel the workflow."""
        self.status = WorkflowStatus.CANCELLED
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

    # ============== Step management methods ================
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

    # ============= Step retrieval methods ================
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
        return self.steps[0] if self.steps else None

    def get_next_pending_step(self):
        """Get the next pending step, if any."""
        pending_steps = [step for step in self.steps if step.status == StepStatus.PENDING]
        return pending_steps[0] if pending_steps else None

    # ================== Class methods for database operations ==================
    @classmethod
    def from_row(cls, db, row):
        """Create a workflow entity from a database row."""
        if not row:
            return None
        
        steps = []

        if "steps" in row.keys() and row["steps"]:
            steps_data = json.loads(row["steps"])
            for step_data in steps_data:
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

                steps.append(step)
        
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
