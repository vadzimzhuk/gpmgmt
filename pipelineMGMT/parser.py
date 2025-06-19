"""
Parser for workflow configuration files.
"""
import os
import pickle
import json
from datetime import datetime
import json

class WorkflowParser:
    """Parser for workflow JSON configuration files."""

    @staticmethod
    def parse_json_file(file_path):
        """Parse a .json workflow configuration file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Workflow file not found: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return config
        except Exception as e:
            raise ValueError(f"Error parsing workflow JSON file: {e}")

    @staticmethod
    def save_to_json_file(config, file_path):
        """Save a workflow configuration to a .json file."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            raise ValueError(f"Error saving workflow JSON file: {e}")

    @staticmethod
    def validate_workflow_config(config):
        """Validate a workflow configuration."""
        # Check required fields
        if not isinstance(config, dict):
            raise ValueError("Workflow configuration must be a dictionary")

        if "name" not in config:
            raise ValueError("Workflow configuration must have a name")

        if "context" not in config or not isinstance(config["context"], dict):
            raise ValueError("Workflow configuration must have context as a dictionary")

        if "steps" not in config or not isinstance(config["steps"], list):
            raise ValueError("Workflow configuration must have steps as a list")

        # Validate context
        for param_name, param_config in config["context"].items():
            if not isinstance(param_config, dict):
                raise ValueError(f"Parameter '{param_name}' configuration must be a dictionary")

            if "type" not in param_config:
                raise ValueError(f"Parameter '{param_name}' must have a type")

        # Validate steps
        step_ids = set()
        for i, step in enumerate(config["steps"]):
            if not isinstance(step, dict):
                raise ValueError(f"Step at index {i} must be a dictionary")

            if "id" not in step:
                raise ValueError(f"Step at index {i} must have an id")

            if step["id"] in step_ids:
                raise ValueError(f"Duplicate step id: {step['id']}")
            step_ids.add(step["id"])

            if "type" not in step:
                raise ValueError(f"Step '{step['id']}' must have a type")

            if step["type"] not in ["manual", "automated"]:
                raise ValueError(f"Step '{step['id']}' type must be 'manual' or 'automated'")

            if step["type"] == "manual" and "instructions" not in step:
                raise ValueError(f"Manual step '{step['id']}' must have instructions")

            if step["type"] == "automated":
                if "action" not in step:
                    raise ValueError(f"Automated step '{step['id']}' must have an action")

                if not isinstance(step["action"], dict):
                    raise ValueError(f"Step '{step['id']}' action must be a dictionary")

                action = step["action"]
                if "server" not in action:
                    raise ValueError(f"Step '{step['id']}' action must have a server")
                if "tool" not in action:
                    raise ValueError(f"Step '{step['id']}' action must have a tool")

        return True

    @staticmethod
    def load_all_workflow_configs(directory):
        """Load all workflow configurations from a directory."""
        configs = []
        if not os.path.exists(directory):
            return configs

        for filename in os.listdir(directory):
            if filename.endswith(".json"):
                file_path = os.path.join(directory, filename)
                try:
                    config = WorkflowParser.parse_json_file(file_path)
                    if WorkflowParser.validate_workflow_config(config):
                        configs.append(config)
                except Exception as e:
                    print(f"Error loading workflow config {filename}: {e}")
        
        return configs
