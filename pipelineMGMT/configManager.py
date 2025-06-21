"""
Manager for the workflow configurations.
"""

from pipelineMGMT.parser import WorkflowParser

class ConfigManager:
    """Manager for workflow configurations."""

    def __init__(self, workflows_dir="workflows"):
        """Initialize the config manager."""
        self.workflows_dir = workflows_dir

    def load_workflow_configs(self):
        """Load all workflow configurations from the workflows directory."""
        return WorkflowParser.load_all_workflow_configs(self.workflows_dir)

    def get_workflow_config(self, name):
        """Get a specific workflow configuration by name."""
        configs = self.load_workflow_configs()
        return next((config for config in configs if config.get("name") == name), None)
    