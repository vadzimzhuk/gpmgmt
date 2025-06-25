"""
Database class.
"""
import sqlite3
# import json
# import uuid
# from datetime import datetime
import os
import threading
# from enum import Enum
# from dataclasses import dataclass
# from typing import Dict, Any, Optional, List
# from db.workflowStep import WorkflowStep, StepType, StepStatus

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
            status TEXT NOT NULL DEFAULT 'PENDING',
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
        # self.cursor.execute('''
        # CREATE TABLE IF NOT EXISTS workflow_configs (
        #     name TEXT PRIMARY KEY,
        #     description TEXT,
        #     context TEXT NOT NULL,
        #     steps TEXT NOT NULL,
        #     created_at TEXT NOT NULL,
        #     updated_at TEXT NOT NULL
        # )
        # ''')

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