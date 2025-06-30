"""
Database manager for the workflow management system.
"""
from db.models import WorkflowEntity 
from db.database import Database
from db.workflowStep import WorkflowStep

class DatabaseManager:
    """Manager for database operations."""

    def __init__(self, db_path="workflows.db"):
        """Initialize the database manager."""
        self.db_path = db_path
        self.db = Database(db_path)

    def close(self):
        """Close the database connection."""
        self.db.close()

    def __enter__(self):
        """Context manager enter method."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit method."""
        self.close()

    # Workflow Entity Operations

    def create_workflow_entity(self, config, name="Sample name"):
        """Create a new pipeline (workflow entity)."""

        if not config:
            raise ValueError(f"Workflow configuration '{config}' not found")
        
        context = config.get("context", {})
        steps = []
        
        for step_config in config["steps"]:
            step = WorkflowStep.from_config(step_config)
            steps.append(step)
            print(step.name)

        entity = WorkflowEntity(
            db=self.db,
            name=name,
            config_name=config["name"],
            description=config["description"],
            context=config["context"],
            steps=steps
        )
        
        entity.add_log(f"Workflow '{name}' based on '{config["name"]}' created")
        entity.save()
        return entity
    
    def set_step_status(self, pipelineId, stepId, status):
        #TODO: check if step is eligible to be run
        pipeline = self.get_workflow_entity(pipelineId)
        if not pipeline:
            raise ValueError(f"Workflow entity '{pipelineId}' not found")
        
        step = None

        if stepId is None:
            step = pipeline.steps[0] if my_list else None
        else:
            step = pipeline.get_step(stepId)
        if not step:
            raise ValueError(f"Step '{step}' not found in workflow entity '{pipelineId}'")
        
        stepStatus = status
        step.status = stepStatus
        pipeline.save()

    def get_workflow_entity(self, identifier):
        """Get a workflow entity by ID, name, or description."""
        # Try to get by ID
        entity = WorkflowEntity.get_by_id(self.db, identifier)
        if entity:
            return entity

        # Try to get by name
        entity = WorkflowEntity.get_by_name(self.db, identifier)
        if entity:
            return entity

        # Try to get by description
        entity = WorkflowEntity.get_by_description(self.db, identifier)
        return entity

    def list_workflow_entities(self, filters=None):
        """List all workflow entities with optional filters."""
        return WorkflowEntity.list_all(self.db, filters)
