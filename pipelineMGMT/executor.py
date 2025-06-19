"""
Executor for pipeline steps.
"""

import string
from db.models import StepStatus, StepType

class WorkflowExecutor:
    """Executor for workflow steps."""

    def __init__(self, db_manager):
        """Initialize the workflow executor."""
        self.db_manager = db_manager
        # self.mcp_clients = {}  # Map of server name to MCP client

    def execute_step(self, workflow_id, stepName=None):
        """Execute a workflow step."""

        try:
            execution = self.execute_workflow_step(workflow_id, stepName)
        except ValueError as e:
            return {"error": str(e)}

        entity = execution["entity"]
        step = execution["step"]
        step_type = execution["type"]

        # For manual steps, return instructions
        if step_type == StepType.MANUAL:
            instructions = self._format_string_with_params(execution["instructions"], entity.context)

            return instructions

        elif step_type == StepType.AUTOMATED:
        # For automated steps, execute the action
            error = f"Automated steps are not implemented"
            entity.add_log(error, "ERROR")
            return {"error": error}
        else:
            error = f"Unknown step type '{step_type}' for step '{step.name}'"
            entity.add_log(error, "ERROR")
            entity.save()
            return {"error": error}
        
    def execute_workflow_step(self, identifier, step_id=None): #remove
        """Execute a workflow step."""
        entity = self.db_manager.get_workflow_entity(identifier)
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

        # Find the step in the entity's steps
        workflow_step = self.set_step_status(identifier, step_id, StepStatus.RUNNING)

        return {
            "entity": entity,
            "step": workflow_step,
            "type": workflow_step.step_type,
            "instructions": workflow_step.instructions if workflow_step.step_type == StepType.MANUAL else None,
            "action": workflow_step.action if workflow_step.step_type == StepType.AUTOMATED else None
        }
    
    def set_step_status(self, pipeline_id, step_name, status):
        """Set the status of a workflow step."""
        entity = self.db_manager.get_workflow_entity(pipeline_id)
        if not entity:
            raise ValueError(f"Workflow entity '{pipeline_id}' not found")

        step = entity.get_step(step_name)
        if not step:
            raise ValueError(f"Step '{step_name}' not found in workflow entity '{pipeline_id}'")

        step.status = status
        entity.save()
        return step
    
    def complete_workflow_step(self, identifier, step_id=None, result=None):
        """Complete a workflow step."""
        entity = self.db_manager.get_workflow_entity(identifier)
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

        # Find the step in the entity's steps
        workflow_step = entity.get_step(step_id)
        
        # If the step doesn't exist in the entity's steps, create it
        if not workflow_step:
            raise ValueError(f"Step '{step_id}' not found in workflow entity '{identifier}'")
        
        # Store the result in the step
        if result:
            workflow_step.result = str(result) if not isinstance(result, str) else result

        # Mark the step as completed
        entity.complete_step(workflow_step)

        # Update context if result is provided
        if result and isinstance(result, dict):
            entity.update_context(result)

        # Find the next pending step
        pending_steps = entity.get_steps_by_status(StepStatus.PENDING)
        if pending_steps:
            entity.start_step(pending_steps[0])
        else:
            entity.add_log("All steps completed", "INFO")

        entity.save()
        return entity

    def complete_manual_step(self, workflow_id, step_id, result=None):
        """Complete a manual workflow step."""
        try:
            entity = self.complete_workflow_step(workflow_id, step_id, result)
            current_step = entity.get_current_step()
            return {
                "workflow_id": entity.id,
                "step_id": step_id,
                "status": "completed",
                "next_step": current_step.name if current_step else None
            }
        except ValueError as e:
            return {"error": str(e)}

    def _format_string_with_params(self, text, params):
        """Format a string with workflow context."""
        if not text:
            return text

        # Create a formatter with custom braces
        formatter = string.Formatter()
        
        # Replace {param} with actual values
        formatted_text = text
        for param_name, param_value in params.items():
            placeholder = "{" + param_name + "}"
            if placeholder in formatted_text:
                formatted_text = formatted_text.replace(placeholder, str(param_value))
                
        return formatted_text

    def _format_dict_with_params(self, dict_obj, params):
        """Format a dictionary's values with workflow context."""
        if not dict_obj:
            return {}

        formatted_dict = {}
        for key, value in dict_obj.items():
            if isinstance(value, str):
                formatted_dict[key] = self._format_string_with_params(value, params)
            elif isinstance(value, dict):
                formatted_dict[key] = self._format_dict_with_params(value, params)
            elif isinstance(value, list):
                formatted_dict[key] = [
                    self._format_string_with_params(item, params) if isinstance(item, str)
                    else (self._format_dict_with_params(item, params) if isinstance(item, dict)
                          else item)
                    for item in value
                ]
            else:
                formatted_dict[key] = value
                
        return formatted_dict
