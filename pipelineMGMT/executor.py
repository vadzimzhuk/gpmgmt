"""
Executor for workflow steps.
"""
import json
import string
from typing import Dict, Any, Optional
# from fastmcp.client.client import Client as FastMCPClient


class WorkflowExecutor:
    """Executor for workflow steps."""

    def __init__(self, db_manager):
        """Initialize the workflow executor."""
        self.db_manager = db_manager
        self.mcp_clients = {}  # Map of server name to MCP client

    # def register_mcp_client(self, server_name, client):
    #     """Register an MCP client for a server."""
    #     self.mcp_clients[server_name] = client

    def execute_step(self, workflow_id, step_id=None):
        """Execute a workflow step."""
        # Get the step execution details
        try:
            execution = self.db_manager.execute_workflow_step(workflow_id, step_id)
        except ValueError as e:
            return {"error": str(e)}

        entity = execution["entity"]
        step = execution["step"]
        step_type = execution["type"]

        # For manual steps, return instructions
        if step_type == "manual":
            instructions = self._format_string_with_params(
                execution["instructions"], entity.parameters
            )
            return {
                "type": "manual",
                "workflow_id": entity.id,
                "step_id": step["id"],
                "instructions": instructions,
                "status": "pending"
            }

        # For automated steps, execute the action
        elif step_type == "automated": # to be implemented
            # action = execution["action"]
            # server_name = action["server"] # another MCP server name
            # tool_name = action["tool"] # another MCP server tool name
            
            # # Format the arguments with the workflow parameters
            # args = {}
            # if "args" in action:
            #     args = self._format_dict_with_params(action["args"], entity.parameters)

            # # Check if we have a client for this server
            # if server_name not in self.mcp_clients:
            #     error = f"No MCP client registered for server '{server_name}'"
            #     entity.add_log(error, "ERROR")
            #     entity.save()
            #     return {"error": error}

            # # Execute the tool
            # try:
            #     client = self.mcp_clients[server_name]
            #     result = client.execute_tool(tool_name, args)
                
            #     # Complete the step with the result
            #     self.db_manager.complete_workflow_step(entity.id, step["id"], result)
                
            #     return {
            #         "type": "automated",
            #         "workflow_id": entity.id,
            #         "step_id": step["id"],
            #         "result": result,
            #         "status": "completed"
            #     }
            # except Exception as e:
            #     error = f"Error executing step '{step['id']}': {str(e)}"
            #     entity.add_log(error, "ERROR")
            #     entity.save()
            #     return {"error": error}
            error = f"Automated steps are not implemented"
            entity.add_log(error, "ERROR")
            return {"error": error}
        else:
            error = f"Unknown step type '{step_type}' for step '{step['id']}'"
            entity.add_log(error, "ERROR")
            entity.save()
            return {"error": error}

    def complete_manual_step(self, workflow_id, step_id, result=None):
        """Complete a manual workflow step."""
        try:
            entity = self.db_manager.complete_workflow_step(workflow_id, step_id, result)
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
        """Format a string with workflow parameters."""
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
        """Format a dictionary's values with workflow parameters."""
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


# class MCPClient:
#     """Client for interacting with MCP servers."""

#     def __init__(self, server_name, base_url=None):
#         """Initialize the MCP client."""
#         self.server_name = server_name
#         self.base_url = base_url or f"http://localhost:3000"
#         self.client = FastMCPClient(server_name=server_name, base_url=self.base_url)

#     def execute_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
#         """Execute a tool on the MCP server."""
#         try:
#             result = self.client.execute_tool(tool_name, args)
#             return result
#         except Exception as e:
#             print(f"Error executing tool '{tool_name}' on server '{self.server_name}': {e}")
#             return {"status": "error", "message": str(e)}

#     def access_resource(self, uri: str) -> Dict[str, Any]:
#         """Access a resource on the MCP server."""
#         try:
#             result = self.client.access_resource(uri)
#             return result
#         except Exception as e:
#             print(f"Error accessing resource '{uri}' on server '{self.server_name}': {e}")
#             return {"status": "error", "message": str(e)}
