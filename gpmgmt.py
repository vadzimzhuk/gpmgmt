from mcp.server.fastmcp import FastMCP
from helpers import make_nws_request, format_alert
from pipelineMGMT.manager import WorkflowManager
from pipelineMGMT.configManager import ConfigManager

mcp = FastMCP("gpmgmt")
workflowManager = WorkflowManager()
configManager = ConfigManager()

# PIPELINE MGMT TOOLS
#@mcp.resource("resource://available-workflows")
@mcp.tool()
async def get_available_workflows() -> str:
    """Get a list of available workflows."""
    workflows = configManager.load_workflow_configs()
    result = []

    for wf in workflows:
        name = wf.get("name", "NA")
        desc = wf.get("description", "NA")
        result.append(f"{name}: {desc}")
    
    return "\n".join(result)

#@mcp.resource("resource://workflow-details/{name}")
@mcp.tool()
async def get_details_for_workflow(name: str) -> str:
    """Get details for the workflow."""
    workflows = configManager.load_workflow_configs()
    result = []

    filtered_configs = [config for config in workflows if config.get("name", "NA") == name]

    if len(filtered_configs) < 1:
        return f"Workflow '{name}' not found."
    
    return f"{filtered_configs[0]}\n"

@mcp.tool()
async def create_workflow(name: str, description: str = None, config_name: str = None) -> str:
    """Create a new workflow configuration. Returns new pipeline ID."""
    if not name:
        return "Workflow name is required."

    try:
        workflow = workflowManager.create_workflow(name, description, config_name)
        # return f"""Workflow '{workflow["name"]}' has been successfully created with the following details: {workflow}"""
    
        return f"""{workflow["id"]}""" #tmp
    except ValueError as e:
        return f"Error creating workflow: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

#@mcp.resource("resource://active-pipelines")
@mcp.tool()
async def list_workflows() -> str:
    """List all active pipelines(workflows)."""
    workflows = workflowManager.list_workflows()
    if not workflows:
        return "No active workflows found."
    
    result = []
    for wf in workflows:
        result.append(f"{wf['id']}: {wf['name']} - {wf['description']}")
    
    return "\n".join(result)

@mcp.tool()
async def launch_workflow(pipepline_id: str) -> str:
    """Launch a workflow with the given name and context."""

    try:
        workflow = workflowManager.launch_workflow(pipepline_id)
        # return f"""Workflow '{workflow["name"]}' launched successfully. Current step is: {workflow["current_step"]}."""
        return {
            "id": workflow["id"],
            "name": workflow["name"],
            "current_step": workflow["current_step"],
            "step_execution": workflow["step_execution"],
            "steps": workflow["steps"]
        }
    
        # The current step is: {workflow["name"]} of type {workflow["step_execution"]["type"]}.
        # The following instructions are to be followed: \n {workflow["step_execution"]["instructions"]}"""
    except ValueError as e:
        return f"Error launching workflow: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
@mcp.tool()
async def update_workflow(pipepline_id: str, context: dict = None) -> str:
    """Update an existing workflow with the given name and context."""
    if context is None:
        context = {}

    try:
        workflow = workflowManager.update_workflow(pipepline_id, context)
        return f"""Workflow '{workflow["name"]}' updated successfully."""
    except ValueError as e:
        return f"Error updating workflow: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
@mcp.tool()
async def cancel_workflow(pipepline_id: str, reason: str = None) -> str:
    """Cancel a workflow with the given name."""
    try:
        workflow = workflowManager.cancel_workflow(pipepline_id, reason)
        return f"""Workflow '{workflow["name"]}' has been cancelled successfully."""
    except ValueError as e:
        return f"Error cancelling workflow: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
# PIPELINE MGMT TOOLS
@mcp.tool()
async def execute_pipeline_step(pipepline_id: str, step_id: str = None) -> str:
    """Execute step in the pipeline. Current step will be executed if step_id is not provided."""
    try:
        execution = workflowManager.execute_workflow_step(pipepline_id, step_id)
        if "error" in execution:
            return f"Error executing step: {execution['error']}"
        
        if execution["type"] == "manual":
            return f"""Manual step '{execution['step_id']}' requires your attention. Instructions: {execution['instructions']}"""
        elif execution["type"] == "automated":
            return f"""Automated step '{execution['step_id']}' executed successfully."""
        else:
            return "Unknown step type."
    except ValueError as e:
        return f"Error executing workflow step: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
@mcp.tool()
async def complete_pipeline_step(pipepline_id, step_name: str) -> str:
    """Complete the current step in the pipeline."""
    try:
        step_completion_result = workflowManager.complete_workflow_step(pipepline_id, step_name)
        # return information about the completed step and further instructions if any. If the pipeline is finished, return a message indicating completion.
        return step_completion_result
        # return f"Step '{step_id}' in workflow '{name}' has been marked as completed."
    except ValueError as e:
        return f"Error completing step: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
@mcp.tool()
async def complete_pipeline_current_step(pipepline_id) -> str:
    """Complete the current step in the pipeline."""
    try:
        step_completion_result = workflowManager.complete_workflow_current_step(pipepline_id)
        # return information about the completed step and further instructions if any. If the pipeline is finished, return a message indicating completion.
        return step_completion_result
        # return f"Step '{step_id}' in workflow '{name}' has been marked as completed."
    except ValueError as e:
        return f"Error completing step: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio')