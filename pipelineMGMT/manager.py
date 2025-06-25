"""
Manager for workflow operations.
"""

from db.manager import DatabaseManager
from pipelineMGMT.executor import WorkflowExecutor
from pipelineMGMT.configManager import ConfigManager
from db.models import WorkflowStatus, StepStatus
from db.workflowStep import WorkflowStep

class WorkflowManager:
    """Manager for workflow operations."""

    def __init__(self, db_path="workflows.db", workflows_dir="workflows"):
        """Initialize the workflow manager."""
        self.db_manager = DatabaseManager(db_path)
        self.executor = WorkflowExecutor(self.db_manager)
        self.workflows_dir = workflows_dir

    def close(self):
        """Close the workflow manager."""
        self.db_manager.close()

    def __enter__(self):
        """Context manager enter method."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit method."""
        self.close()

    def load_workflow_configs(self):
        """Load all workflow configurations from the workflows directory."""
        configs = ConfigManager().load_workflow_configs()
            
        return configs

    # Workflow Entity Operations

    def create_workflow(self, workflow_config_name, custom_name=None, context=None):
        """Create and launch a new pipeline (workflow entity) based on workflow config(template), custom pipeline name and optional context."""
        try:
            config = next((config for config in self.load_workflow_configs() if config.get("name") == workflow_config_name), None)

            entity = self.db_manager.create_workflow_entity(
                config, name=custom_name
            )
            
            # Generate a description if not provided
            if not entity.description:

                if config and config.description:
                    # Create a description based on the workflow config and context
                    desc_parts = [config.description]
                    
                    # Add key context to the description
                    for param_name, param_value in entity.context.items():
                        if param_name in ["customer_id", "ticket_number", "id", "name"] and param_value:
                            desc_parts.append(f"{param_name.replace('_', ' ').title()}: {param_value}")
                    
                    entity.description = " - ".join(desc_parts)
                    entity.save()
            
            # Prepare response with proper handling of WorkflowStep objects
            response = {
                "id": entity.id,
                "name": entity.name,
                "description": entity.description,
                "config_name": entity.config_name#,
                # "context": entity.context,
                # "steps": entity.to_dict()["steps"]
            }
            
            # Initialize  first step
            # Handle current_step if it's a WorkflowStep object
            # current_step = entity.get_current_step()
            current_step = entity.get_first_step()
            if current_step:
                response["current_step"] = current_step.name
            elif current_step is None:
                response["current_step"] = None
                
            return response
        except ValueError as e:
            return {"error": str(e)}

    def launch_workflow(self, pipeline_id):
        """Launch a pipeline(workflow entity) with id."""
        try:
            # Run the first step of the workflow
            step_execution = self.executor.execute_step(pipeline_id)

            # Get updated workflow entity
            entity = self.db_manager.get_workflow_entity(pipeline_id)

            print("\nid: " + str(step_execution["entity"].id) + " STATUS: " + str(step_execution["entity"].status))
            print("id:" + str(entity.id) + " STATUS:" + str(entity.status) + "\n")

            response = {
                "id": entity.id,
                "name": entity.name,
                "description": entity.description,
                "config_name": entity.config_name,
                "context": entity.context,
                "steps": entity.to_dict()["steps"],
                "status": str(entity.status)
            }
            
            current_step = entity.get_first_step()

            if current_step:
                response["current_step"] = current_step.name
            else:
                response["current_step"] = None

            response["step_execution"] = step_execution
                
            return response
        except ValueError as e:
            return {"error": str(e)}

    def get_workflow(self, identifier): #todo: rename to get_workflow_entity
        """Get a pipeline (workflow entity) by ID, name, or description."""
        try:
            entity = self.db_manager.get_workflow_entity(identifier)
            if not entity:
                return {"error": f"Workflow '{identifier}' not found"}
            
            entity_dict = entity.to_dict()
            
            # Ensure current_step is a string for API compatibility
            current_step = entity.get_current_step()
            if current_step:
                entity_dict["current_step"] = current_step.name
            else:
                entity_dict["current_step"] = None
                
            return entity_dict
        except Exception as e:
            return {"error": str(e)}

    def update_workflow(self, identifier, context):
        """Update a workflow entity's context."""
        try:
            entity = self.update_workflow_entity(identifier, context)

            response = {
                "id": entity.id,
                "name": entity.name,
                "context": entity.context,
                "steps": entity.to_dict()["steps"]
            }
            

            current_step = entity.get_current_step()
            if current_step:
                response["current_step"] = current_step.name
            else:
                response["current_step"] = None
                
            return response
        except ValueError as e:
            return {"error": str(e)}
        
    def update_workflow_entity(self, identifier, context):
        """Update a workflow entity's context."""
        entity = self.db_manager.get_workflow_entity(identifier)
        if not entity:
            raise ValueError(f"Workflow entity '{identifier}' not found")

        # Update context
        entity.update_context(context)

        # Get the workflow configuration
        # config = ConfigManager().get_workflow_config(entity.config_name) #switch from config to entity
        # if not config:
        #     raise ValueError(f"Workflow configuration '{entity.config_name}' not found")

        # Get existing step names
        # existing_step_names = [step.name for step in entity.steps]
 
        # Check if there are any steps that may assume a status of completed
        # completed_steps = entity.get_steps_by_status(StepStatus.COMPLETED)
        # Check for steps that should/can be triggered
        # for step_config in config.steps:
        #     step_id = step_config["id"]
        #     if (step_id not in [s.name for s in entity.get_steps_by_status(StepStatus.COMPLETED)] and 
        #         step_id not in existing_step_names):
        #         # self._check_step_conditions(step_config, entity.context)):
        #         # Create a new WorkflowStep object
        #         step = WorkflowStep.from_config(step_config)
        #         entity.steps.append(step)
        #         entity.add_log(f"Step '{step_id}' added to steps")

        # If no current step is set and there are pending steps, set the first one
        # if not entity.get_current_step() and entity.get_steps_by_status(StepStatus.PENDING):
        #     # Find the first pending step
        #     first_pending_step = entity.get_steps_by_status(StepStatus.PENDING)[0]
        #     entity.start_step(first_pending_step)

        entity.save()
        return entity
    
    def complete_workflow(self, pipelineId):
        """Complete a workflow."""
        entity = self.db_manager.get_workflow_entity(pipelineId)
        if not entity:
            raise ValueError(f"Workflow entity '{pipelineId}' not found")

        if entity.status == WorkflowStatus.CANCELLED or entity.status == WorkflowStatus.COMPLETED:
            raise ValueError(f"Cannot complete cancelled or completed workflow '{pipelineId}'")

        # Mark the workflow as completed
        entity.complete()
        # entity.save()

        return {
            "id": entity.id,
            "name": entity.name,
            "is_completed": True,
            "completed_at": entity.updated_at
        }

    def execute_workflow_step(self, pipelineId, step_id=None):
        """Execute a workflow step."""
        execution = self.executor.execute_step(pipelineId, step_id)
        # todo: handle errors
        return execution
    
    def complete_workflow_current_step(self, pipelineId):
        """Complete the current step in the workflow."""
        entity = self.db_manager.get_workflow_entity(pipelineId)
        if not entity:
            raise ValueError(f"Workflow entity '{pipelineId}' not found")

        current_step = entity.get_current_step()
        if not current_step:
            raise ValueError("No current step set for the workflow")

        return self.complete_workflow_step(pipelineId, current_step.name)

    def complete_workflow_step(self, pipelineId, stepName, result=None):
        """Complete a workflow step."""
        step_completion_result = self.executor.complete_manual_step(pipelineId, stepName, result)

        next_step = None
        remaining_running_steps = self.get_workflow_steps_with_status(pipelineId, StepStatus.RUNNING)
        
        if remaining_running_steps:
            next_step = remaining_running_steps[0] if remaining_running_steps else None
        else:
            remaining_pending_steps = self.get_workflow_steps_with_status(pipelineId, StepStatus.PENDING)
            next_step = remaining_pending_steps[0] if remaining_pending_steps else None
        
        if not next_step:
            self.complete_workflow(pipelineId)
            return {
                "message": "Workflow completed successfully."
                # "completed_at": step_completion_result.completed_at,
                # "result": step_completion_result.result
            }
        all_pipeline_steps = self.get_workflow_steps(pipelineId)
        steps_strings = [f"{step.name}: {step.status}" for step in all_pipeline_steps]

        result = f"Current step has been successfully completed! \n Current pipeline execution state: \n {steps_strings} \n The next step to proceed with is: {next_step.name}. \n Please follow the instruction: {next_step.instructions}"

        return result

    def cancel_workflow(self, identifier, reason=None):
        """Cancel a workflow."""
        try:
            entity = self.db_manager.get_workflow_entity(identifier)
            if not entity:
                raise ValueError(f"Workflow entity '{identifier}' not found")

            if entity.is_cancelled:
                return entity  # Already cancelled

            entity.cancel(reason)
            entity.save()

            return {
                "id": entity.id,
                "name": entity.name,
                "is_cancelled": entity.is_cancelled,
                "cancelled_at": entity.cancelled_at
            }
        except ValueError as e:
            return {"error": str(e)}

    def list_workflows(self, filters=None):
        """List all workflow entities with optional filters."""
        try:
            entities = self.db_manager.list_workflow_entities(filters)
            return [
                {
                    "id": entity.id,
                    "name": entity.name,
                    "description": entity.description,
                    "config_name": entity.config_name,
                    "current_step": entity.get_current_step().name if entity.get_current_step() else None,
                    "status": str(entity.status),
                    "created_at": entity.created_at,
                    "updated_at": entity.updated_at
                }
                for entity in entities
            ]
        except Exception as e:
            return {"error": str(e)}

    def list_workflow_configs(self):
        """List all workflow configurations."""
        try:
            configs = self.db_manager.list_workflow_configs()
            return [config.to_dict() for config in configs]
        except Exception as e:
            return {"error": str(e)}
    
    def get_workflow_steps(self, pipelineId):
        """Get all workflow steps."""
        try:
            steps = self.db_manager.get_workflow_entity(pipelineId).steps
            return steps
        except Exception as e:
            return {"error": str(e)}
        
    def get_workflow_steps_with_status(self, identifier, status):
        """Get workflow steps with a specific status."""
        try:
            entity = self.db_manager.get_workflow_entity(identifier)
            if not entity:
                raise ValueError(f"Workflow entity '{identifier}' not found")

            steps = entity.get_steps_by_status(status)
            return steps
        except ValueError as e:
            return {"error": str(e)}
        except Exception as e:
            return {"error": str(e)}