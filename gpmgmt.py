from mcp.server.fastmcp import FastMCP
from helpers import make_nws_request, format_alert
from pipelineMGMT.manager import WorkflowManager
from pipelineMGMT.configManager import ConfigManager
from mcp.server.fastmcp.prompts.prompt_manager import Prompt

mcp = FastMCP("gpmgmt")
workflowManager = WorkflowManager()
configManager = ConfigManager()

# PROMPTS
@mcp.prompt()
def execute_pipeline_step(pipeline_id: str, step_name: str = None) -> str:
    """Automatically execute the step of the pipeline. If step_id is not provided, the current step will be executed."""
    return f"Please call 'get_execution_instructions' tool to get instructions for execution of the step with name {step_name} or current step of the following pipeline:\n\n{pipeline_id}. Then ignoring the step type execute the instructions provided in the response on your own. If you don't have enough tools such as MCP Servers to complete this - please indicate that.\n\n"

# PIPELINE MGMT TOOLS
#@mcp.resource("resource://available-workflows")
@mcp.tool()
async def get_available_workflows() -> str:
    """Get a list of available workflow configurations. Based on the workflow configuration files in the workflows directory pipelines are created."""
    workflows = configManager.load_workflow_configs()
    result = []

    for wf in workflows:
        name = wf.get("name", "NA")
        desc = wf.get("description", "NA")
        result.append(f"{name}: {desc}")
    
    return "\n".join(result)

#@mcp.resource("resource://launch_result-details/{name}")
@mcp.tool()
async def get_details_for_workflow(config_name: str) -> str:
    """Get details for the launch_result."""
    workflows = configManager.load_workflow_configs()

    filtered_configs = [config for config in workflows if config.get("name", "NA") == config_name]

    if len(filtered_configs) < 1:
        return f"Workflow '{config_name}' not found."
    elif len(filtered_configs) > 1:
        return f"Multiple workflows found with the name '{config_name}'. Please specify a unique name."
    
    return f"{filtered_configs[0]}\n"

@mcp.tool()
async def create_pipeline(config_name: str, custom_name: str) -> str:
    """Create new pipeline based on workflow congiguration with the provided config_name. If succeeded, returns new pipeline ID."""
    if not config_name:
        return "Workflow configuration name is required."
    
    if not custom_name:
        return "Custom name for the pipeline is required."

    try:
        launch_result = workflowManager.create_workflow(config_name, custom_name)

        return f"""{launch_result["id"]}""" #tmp
    except ValueError as e:
        return f"Error creating launch_result: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

#@mcp.resource("resource://active-pipelines")
@mcp.tool()
async def list_active_pipelines() -> str:
    """List all active pipelines(workflows)."""
    pipelines = workflowManager.list_workflows()

    if not pipelines:
        return "No active pipelines found."
    
    result = []
    for wf in pipelines:
        result.append(f"{wf['id']}: {wf['name']} - {wf['status']}")
        result.append(f"Current step: {wf['current_step']}")
    
    return "\n".join(result)

@mcp.tool()
async def launch_pipeline(pipepline_id: str) -> str:
    """Launch pipeline with the given name. Then execute the instructions for the first step returned in the response."""

    try:
        launch_result = workflowManager.launch_workflow(pipepline_id)
        
        return f"""The following instructions to be executed: {launch_result["step_execution"]["instructions"]}"""
    
    except ValueError as e:
        return f"Error launching pipeline: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
@mcp.tool()
async def update_pipeline_context(pipepline_id: str, context: dict = None) -> str:
    """Update pipeline context."""
    if context is None:
        context = {}

    try:
        update_result = workflowManager.update_workflow(pipepline_id, context)
        return f"""Pipeline '{update_result["name"]}' updated successfully."""
    except ValueError as e:
        return f"Error updating pipeline: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
@mcp.tool()
async def cancel_pipeline(pipepline_id: str, reason: str = None) -> str:
    """Cancel pipeline with the reason(optional)."""
    try:
        cancel_result = workflowManager.cancel_workflow(pipepline_id, reason)
        return f"""Pipeline '{cancel_result["name"]}' has been cancelled successfully."""
    except ValueError as e:
        return f"Error cancelling pipeline: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
# PIPELINE MGMT TOOLS
@mcp.tool()
async def get_execution_instructions(pipepline_id: str, step_id: str = None) -> str:
    """Get execution instructions for the step in the pipeline. Current step instructions will be returned if step_id is not provided."""
    try:
        execution = workflowManager.execute_workflow_step(pipepline_id, step_id)
        if "error" in execution:
            return f"Error executing step: {execution['error']}"
        
        return f"Execute on your own the instructions provided in the response: {execution}.\n\n"
        
    except ValueError as e:
        return f"Error executing launch_result step: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
@mcp.tool()
async def complete_pipeline_step(pipepline_id, step_name: str) -> str:
    """Complete the current step in the pipeline."""
    try:
        step_completion_result = workflowManager.complete_workflow_step(pipepline_id, step_name)
        # return information about the completed step and further instructions if any. If the pipeline is finished, return a message indicating completion.
        return step_completion_result
        # return f"Step '{step_id}' in launch_result '{name}' has been marked as completed."
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
        # return f"Step '{step_id}' in launch_result '{name}' has been marked as completed."
    except ValueError as e:
        return f"Error completing step: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
@mcp.tool()
async def get_pipeline_logs(pipeline_id: str) -> str:
    """Return logs from pipeline entity (WorkflowEntity) stored in db."""
    try:
        entity = workflowManager.db_manager.get_workflow_entity(pipeline_id)
        if not entity:
            return f"Pipeline with id {pipeline_id} not found."
        logs = entity.logs
        if not logs:
            return "No logs found for this pipeline."
        return "\n".join(f"[{log['timestamp']}] {log['level']}: {log['message']}" for log in logs)
    except Exception as e:
        return f"Error retrieving logs: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio')