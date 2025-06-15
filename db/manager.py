"""
Database manager for the workflow management system.
"""
from db.models import Database, WorkflowEntity, WorkflowConfig, WorkflowStep, StepType, StepStatus


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

    def create_workflow_entity(self, config, name="Sample name", parameters=None):
        """Create a new pipeline (workflow entity)."""
        # Get the workflow configuration
        # config = self.get_workflow_config(config_name)
        # print("Workflow creation: " + str(config))

        if not config:
            raise ValueError(f"Workflow configuration '{config}' not found")
        
        # Initialize parameters with defaults from config
        merged_parameters = {}
        for param_name, param_config in config["parameters"].items():
            if "default" in param_config:
                merged_parameters[param_name] = param_config["default"]

        # Override with provided parameters
        if parameters:
            merged_parameters.update(parameters)

        # Validate required parameters - should be moved to the launch pipeline method
        # for param_name, param_config in config.parameters.items():
        #     if param_config.get("required", False) and param_name not in merged_parameters:
        #         raise ValueError(f"Required parameter '{param_name}' is missing")

        # Create the workflow entity
        entity = WorkflowEntity(
            db=self.db,
            name=name,
            config_name=config["name"],
            description=config["description"],
            parameters=merged_parameters
        )

        print("Workflow entity created: " + str(entity))
        
        # Initialize steps from config
        for step_config in config["steps"]:
            # Check if step conditions match initial parameters
            if self._check_step_conditions(step_config, merged_parameters):
                # Create a WorkflowStep object
                step = self._create_workflow_step_from_config(step_config)
                entity.steps.append(step)
                
                # Set the first matching step as the current step
                if len(entity.steps) == 1:
                    entity.start_step(step)
        
        entity.add_log(f"Workflow '{name}' based on '{config["name"]}' created")
        entity.save()
        return entity
    
    def launch_workflow_entity(self, pipeline_id, parameters=None):
        """Launch an existing workflow entity."""
        entity = WorkflowEntity.get_by_id(self.db, pipeline_id)

        if not entity:
            print(f"Workflow entity with ID '{pipeline_id}' not found")
            print("Active workflows:")
            active_entities = WorkflowEntity.list_all(self.db)
            print(str(active_entities))
            raise ValueError(f"Workflow entity with ID '{pipeline_id}' not found")

        print(f"Launching workflow entity with ID: {pipeline_id}")

        # Update parameters if provided
        if parameters:
            entity.update_parameters(parameters)

        # Check if there are any pending steps to start - moved to executor
        # first_step = entity.get_first_step()
        # if first_step:
        #     entity.start_step(first_step)
        
        entity.save()
        return entity
    
        
    def _create_workflow_step_from_config(self, step_config):
        """Create a WorkflowStep object from a step configuration."""
        step_type = StepType.MANUAL if step_config["type"] == "manual" else StepType.AUTOMATED
        
        return WorkflowStep(
            name=step_config["id"],
            step_type=step_type,
            conditions=step_config.get("conditions", {}),
            instructions=step_config.get("instructions", ""),
            mcp_server_config=step_config.get("action")
        )

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

    def update_workflow_entity(self, identifier, parameters):
        """Update a workflow entity's parameters."""
        entity = self.get_workflow_entity(identifier)
        if not entity:
            raise ValueError(f"Workflow entity '{identifier}' not found")

        # Update parameters
        entity.update_parameters(parameters)

        # Get the workflow configuration
        config = self.get_workflow_config(entity.config_name)
        if not config:
            raise ValueError(f"Workflow configuration '{entity.config_name}' not found")

        # Get existing step names
        existing_step_names = [step.name for step in entity.steps]

        # Check for steps that should be triggered
        for step_config in config.steps:
            step_id = step_config["id"]
            if (step_id not in [s.name for s in entity.get_steps_by_status(StepStatus.COMPLETED)] and 
                step_id not in existing_step_names and
                self._check_step_conditions(step_config, entity.parameters)):
                # Create a new WorkflowStep object
                step = self._create_workflow_step_from_config(step_config)
                entity.steps.append(step)
                entity.add_log(f"Step '{step_id}' added to steps")

        # If no current step is set and there are pending steps, set the first one
        if not entity.get_current_step() and entity.get_steps_by_status(StepStatus.PENDING):
            # Find the first pending step
            first_pending_step = entity.get_steps_by_status(StepStatus.PENDING)[0]
            entity.start_step(first_pending_step)

        entity.save()
        return entity

    def execute_workflow_step(self, identifier, step_id=None):
        """Execute a workflow step."""
        entity = self.get_workflow_entity(identifier)
        if not entity:
            raise ValueError(f"Workflow entity '{identifier}' not found")

        if entity.is_cancelled:
            raise ValueError(f"Cannot execute step for cancelled workflow '{identifier}'")

        # If no step_id is provided, use the current step
        if not step_id:
            current_step = entity.get_current_step()
            if not current_step:
                current_step = entity.get_first_step()
                if not current_step:
                    raise ValueError("No step specified and no current step set")
            step_id = current_step.name

        # Get the workflow configuration
        config = self.get_workflow_config(entity.config_name)
        if not config:
            raise ValueError(f"Workflow configuration '{entity.config_name}' not found")

        # Find the step in the configuration
        step_config = next((s for s in config.steps if s["id"] == step_id), None)
        if not step_config:
            raise ValueError(f"Step '{step_id}' not found in workflow configuration")

        # Find the step in the entity's steps
        workflow_step = entity.get_step(step_id)
        
        # If the step doesn't exist in the entity's steps, create it
        # if not workflow_step:
        #     workflow_step = self._create_workflow_step_from_config(step_config)
        #     entity.steps.append(workflow_step)

        # Check if the step is pending
        if workflow_step.status != StepStatus.PENDING:
            raise ValueError(f"Step '{step_id}' is not pending")

        # Check if the step conditions are met
        if not self._check_step_conditions(step_config, entity.parameters):
            raise ValueError(f"Conditions for step '{step_id}' are not met")

        # Mark the step as the current step
        entity.start_step(workflow_step)
        entity.save()

        return {
            "entity": entity,
            "step": step_config,
            "type": step_config["type"],
            "instructions": step_config.get("instructions") if step_config["type"] == "manual" else None,
            "action": step_config.get("action") if step_config["type"] == "automated" else None
        }

    def complete_workflow_step(self, identifier, step_id=None, result=None):
        """Complete a workflow step."""
        entity = self.get_workflow_entity(identifier)
        if not entity:
            raise ValueError(f"Workflow entity '{identifier}' not found")

        if entity.is_cancelled:
            raise ValueError(f"Cannot complete step for cancelled workflow '{identifier}'")

        # If no step_id is provided, use the current step
        if not step_id:
            current_step = entity.get_current_step()
            if not current_step:
                raise ValueError("No step specified and no current step set")
            step_id = current_step.name

        # Get the workflow configuration
        config = self.get_workflow_config(entity.config_name)
        if not config:
            raise ValueError(f"Workflow configuration '{entity.config_name}' not found")

        # Find the step in the configuration
        step_config = next((s for s in config.steps if s["id"] == step_id), None)
        if not step_config:
            raise ValueError(f"Step '{step_id}' not found in workflow configuration")

        # Find the step in the entity's steps
        workflow_step = entity.get_step(step_id)
        
        # If the step doesn't exist in the entity's steps, create it
        if not workflow_step:
            workflow_step = self._create_workflow_step_from_config(step_config)
            entity.steps.append(workflow_step)
        
        # Store the result in the step
        if result:
            workflow_step.result = str(result) if not isinstance(result, str) else result

        # Mark the step as completed
        entity.complete_step(workflow_step)

        # Update parameters if result is provided
        if result and isinstance(result, dict):
            entity.update_parameters(result)

        # Update status if next_status is specified in the step
        if "next_status" in step_config and step_config["next_status"]:
            entity.parameters["status"] = step_config["next_status"]
            entity.add_log(f"Status updated to '{step_config['next_status']}'")

        # Find the next pending step
        pending_steps = entity.get_steps_by_status(StepStatus.PENDING)
        if pending_steps:
            entity.start_step(pending_steps[0])
        else:
            entity.add_log("All steps completed", "INFO")

        entity.save()
        return entity

    def cancel_workflow(self, identifier, reason=None):
        """Cancel a workflow."""
        entity = self.get_workflow_entity(identifier)
        if not entity:
            raise ValueError(f"Workflow entity '{identifier}' not found")

        if entity.is_cancelled:
            return entity  # Already cancelled

        entity.cancel(reason)
        entity.save()
        return entity

    # Workflow Config Operations

    def create_workflow_config(self, name, description=None, parameters=None, steps=None):
        """Create a new workflow configuration."""
        config = WorkflowConfig(
            db=self.db,
            name=name,
            description=description,
            parameters=parameters or {},
            steps=steps or []
        )
        config.save()
        return config

    def get_workflow_config(self, name):
        """Get a workflow configuration by name."""
        return WorkflowConfig.get_by_name(self.db, name)

    def list_workflow_configs(self):
        """List all workflow configurations."""
        return WorkflowConfig.list_all(self.db)

    def save_workflow_config_from_dict(self, config_dict):
        """Save a workflow configuration from a dictionary."""
        if "name" not in config_dict:
            raise ValueError("Workflow configuration must have a name")

        config = WorkflowConfig(
            db=self.db,
            name=config_dict["name"],
            description=config_dict.get("description"),
            parameters=config_dict.get("parameters", {}),
            steps=config_dict.get("steps", [])
        )
        config.save()
        return config

    # Helper methods

    def _check_step_conditions(self, step, parameters):
        """Check if a step's conditions are met."""
        if "conditions" not in step or not step["conditions"]:
            return True  # No conditions means always true

        for param_name, expected_value in step["conditions"].items():
            if param_name not in parameters:
                return False
            if parameters[param_name] != expected_value:
                return False
        return True
