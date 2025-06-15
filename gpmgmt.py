from mcp.server.fastmcp import FastMCP
from helpers import make_nws_request, format_alert
from pipelineMGMT.manager import WorkflowManager

mcp = FastMCP("gpmgmt")
workflowManager = WorkflowManager()

NWS_API_BASE = "https://api.weather.gov"

# @mcp.tool()
# async def get_alerts(state: str) -> str:
#     """Get weather alerts for a US state.

#     Args:
#         state: Two-letter US state code (e.g. CA, NY)
#     """
#     url = f"{NWS_API_BASE}/alerts/active/area/{state}"
#     data = await make_nws_request(url)

#     if not data or "features" not in data:
#         return "Unable to fetch alerts or no alerts found."

#     if not data["features"]:
#         return "No active alerts for this state."

#     alerts = [format_alert(feature) for feature in data["features"]]
#     return "\n---\n".join(alerts)

# @mcp.tool()
# async def get_forecast(latitude: float, longitude: float) -> str:
#     """Get weather forecast for a location.

#     Args:
#         latitude: Latitude of the location
#         longitude: Longitude of the location
#     """
#     # First get the forecast grid endpoint
#     points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
#     points_data = await make_nws_request(points_url)

#     if not points_data:
#         return "Unable to fetch forecast data for this location."

#     # Get the forecast URL from the points response
#     forecast_url = points_data["properties"]["forecast"]
#     forecast_data = await make_nws_request(forecast_url)

#     if not forecast_data:
#         return "Unable to fetch detailed forecast."

#     # Format the periods into a readable forecast
#     periods = forecast_data["properties"]["periods"]
#     forecasts = []
#     for period in periods[:5]:  # Only show next 5 periods
#         forecast = f"""
# {period['name']}:
# Temperature: {period['temperature']}°{period['temperatureUnit']}
# Wind: {period['windSpeed']} {period['windDirection']}
# Forecast: {period['detailedForecast']}
# """
#         forecasts.append(forecast)

#     return "\n---\n".join(forecasts)

@mcp.tool()
async def get_available_workflows() -> str:
    """Get a list of available workflows."""
    workflows = workflowManager.load_workflow_configs()
    result = []

    for wf in workflows:
        name = wf.get("name", "NA")
        desc = wf.get("description", "NA")
        result.append(f"{name}: {desc}")
    
    return "\n".join(result)

@mcp.tool()
async def get_details_for_workflow(name: str) -> str:
    """Get details for the workflow."""
    workflows = workflowManager.load_workflow_configs()
    result = []

    filtered_configs = [config for config in workflows if config.get("name", "NA") == name]

    if len(filtered_configs) < 1:
        return f"Workflow '{name}' not found."
    
    return f"{filtered_configs[0]}\n"

@mcp.tool()
async def create_workflow(name: str, description: str = None, config_name: str = None) -> str:
    """Create a new workflow configuration."""
    if not name:
        return "Workflow name is required."

    try:
        workflow = workflowManager.create_workflow(name, description, config_name)
        # return f"""Workflow '{workflow["name"]}' created successfully."""
    
        return f"""{workflow["id"]}""" #tmp
    except ValueError as e:
        return f"Error creating workflow: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

@mcp.tool()
async def launch_workflow(name: str, parameters: dict = None) -> str:
    """Launch a workflow with the given name and parameters."""
    if parameters is None:
        parameters = {}

    try:
        workflow = workflowManager.launch_workflow(name, parameters)
        return f"""Workflow '{workflow["name"]}' launched successfully."""
    
        # The first step is: {workflow["name"]} of type {workflow["step_execution"]["type"]}.
        # The following instructions are to be followed: \n {workflow["step_execution"]["instructions"]}"""
    except ValueError as e:
        return f"Error launching workflow: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport='stdio')