from mcp.server.fastmcp import FastMCP
from helpers import make_nws_request, format_alert
from pipelineMGMT.manager import WorkflowManager
from pipelineMGMT.configManager import ConfigManager
from mcp.server.fastmcp.prompts.prompt_manager import Prompt
# from fastapi import FastAPI, WebSocket

mcp = FastMCP("gpmgmt")
workflowManager = WorkflowManager()
configManager = ConfigManager()

# myapi = FastAPI()

# SOCKETS
# @myapi.websocket("/ws")
# async def websocket_endpoint(websocket: WebSocket):
#     await websocket.accept()
#     while True:
#         data = await websocket.receive_text()
#         try:
#             message = json.loads(data)
#             action = message.get("action")
#             payload = message.get("payload", {})

#             if action == "get_workflows":
#                 workflows = configManager.load_workflow_configs()
#                 await websocket.send_json({"type": "workflows", "data": workflows})
#             elif action == "ping":
#                 await websocket.send_json({"type": "pong"})
#             else:
#                 await websocket.send_json({"type": "error", "message": "Unknown action"})
#         except Exception as e:
#             await websocket.send_json({"type": "error", "message": str(e)})

# PROMPTS
@mcp.prompt()
def execute_pipeline_step(pipeline_id: str, step_name: str = None) -> str:
    """Automatically execute the step of the pipeline. If step_id is not provided, the current step will be executed."""
    return f"Please call 'get_execution_instructions' tool to get instructions for execution of the step with name {step_name} or current step of the following pipeline:\n\n{pipeline_id}. Then ignoring the step type try to execute the instructions provided in the response on your own.\n\n"

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

#@mcp.resource("resource://launch_result-details/{name}")
@mcp.tool()
async def get_details_for_workflow(config_name: str) -> str:
    """Get details for the launch_result."""
    workflows = configManager.load_workflow_configs()
    result = []

    filtered_configs = [config for config in workflows if config.get("name", "NA") == config_name]

    if len(filtered_configs) < 1:
        return f"Workflow '{name}' not found."
    
    return f"{filtered_configs[0]}\n"

@mcp.tool()
async def create_workflow(config_name: str, custom_name: str = None) -> str:
    """Create a new launch_result configuration. Returns new pipeline ID."""
    if not config_name:
        return "Workflow configuration name is required."

    try:
        launch_result = workflowManager.create_workflow(config_name, custom_name)
        # return f"""Workflow '{launch_result["config_name"]}' has been successfully created with the following details: {launch_result}"""
    
        return f"""{launch_result["id"]}""" #tmp
    except ValueError as e:
        return f"Error creating launch_result: {str(e)}"
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
        result.append(f"{wf['id']}: {wf['name']} - {wf['status']}")
        result.append(f"Current step: {wf['current_step']}")
    
    return "\n".join(result)

@mcp.tool()
async def launch_workflow(pipepline_id: str) -> str:
    """Launch a launch_result with the given name. Try to execute the instructions returned in the response."""

    try:
        launch_result = workflowManager.launch_workflow(pipepline_id)
        # print(str(launch_result["current_step"]))
        print(f"Workflow state: {launch_result['status']}")
        print(f"Current step: {launch_result['current_step']}")
        # return f"""Workflow '{launch_result["name"]}' launched successfully. Current step is: {launch_result["current_step"]}."""
        
        return f"""The following instructions to be executed: {launch_result["step_execution"]["instructions"]}"""
        # return {
        #     "id": launch_result["id"],
        #     "name": launch_result["name"],
        #     "current_step": launch_result["current_step"],
        #     "step_execution": launch_result["step_execution"]#,
        #     # "steps": launch_result["steps"]
        # }
    
        # The current step is: {launch_result["name"]} of type {launch_result["step_execution"]["type"]}.
        # The following instructions are to be followed: \n {launch_result["step_execution"]["instructions"]}"""
    except ValueError as e:
        return f"Error launching launch_result: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
@mcp.tool()
async def update_workflow(pipepline_id: str, context: dict = None) -> str:
    """Update an existing launch_result with the given name and context."""
    if context is None:
        context = {}

    try:
        launch_result = workflowManager.update_workflow(pipepline_id, context)
        return f"""Workflow '{launch_result["name"]}' updated successfully."""
    except ValueError as e:
        return f"Error updating launch_result: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
@mcp.tool()
async def cancel_workflow(pipepline_id: str, reason: str = None) -> str:
    """Cancel a launch_result with the given name."""
    try:
        launch_result = workflowManager.cancel_workflow(pipepline_id, reason)
        return f"""Workflow '{launch_result["name"]}' has been cancelled successfully."""
    except ValueError as e:
        return f"Error cancelling launch_result: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
    
# PIPELINE MGMT TOOLS
@mcp.tool()
async def get_execution_instructions(pipepline_id: str, step_id: str = None) -> str:
    """Get execution instructions for the step in the pipeline. Current step will be executed if step_id is not provided."""
    try:
        execution = workflowManager.execute_workflow_step(pipepline_id, step_id)
        if "error" in execution:
            return f"Error executing step: {execution['error']}"
        
        return f"Please try to execute the instructions provided in the response: {execution} on your own.\n\n"
        
        # if execution["type"] == "manual":
        #     return f"""Manual step '{execution['step_id']}' requires your attention. Instructions: {execution['instructions']}"""
        # elif execution["type"] == "automated":
        #     return f"""Automated step '{execution['step_id']}' executed successfully."""
        # else:
        #     return "Unknown step type."
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

if __name__ == "__main__":
    mcp.run(transport='stdio')