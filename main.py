from typing import Any
from mcp.server.fastmcp import FastMCP
from helpers import make_nws_request, format_alert
from pipelineMGMT import WorkflowManager

mcp = FastMCP("gpmgmt")

# def main():
#     print("Hello from gpmgmt!")

# @mcp.tool()
# async def get_available_workflows() -> str:
#     """Get a list of available workflows."""
#     manager = WorkflowManager()
#     workflows = manager.load_workflow_configs()
#     result = []
#     for wf in workflows:
#         name = wf.get("name", "Unnamed")
#         desc = wf.get("description", "No description")
#         result.append(f"{name}: {desc}")
#     return "\n".join(result)


# if __name__ == "__main__":
#     main()
if __name__ == "__main__":
    mcp.run(transport='stdio')