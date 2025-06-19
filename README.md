# GP-MGMT: General Purpose Pipeline Management

GP-MGMT is an MCP (Model Context Protocol) server that manages general purpose pipelines and workflows. It was designed to handle operational workflows that contain different multistep flows and require many services to work together.

## Overview

The application takes carefully described workflows in a configuration format (JSON/YAML) and, upon user request in Claude or Copilot, initializes pipelines, guides users through manual steps, and performs automated steps (emails, script execution, etc.) for them. Automated steps are executed via other MCP servers, making the system easily extensible, especially when using open source and custom MCP servers.

### Key Benefits

- **For Manual Steps**: 
  - Improved stability for users of any experience level
  - Reduced errors
  - Moderate speed improvement

- **For Automated Steps**:
  - Significant speed improvement
  - Enhanced accuracy
  - Increased transparency

## Architecture

GP-MGMT consists of several key components:

- **Workflow Manager**: Manages workflow operations, including creating, launching, and updating workflows
- **Workflow Parser**: Parses workflow configuration files (JSON/YAML)
- **Workflow Executor**: Executes workflow steps, both manual and automated
- **Database Manager**: Manages the SQLite database for storing workflow entities and configurations

### Database Models

- **WorkflowEntity**: Represents an instance of a workflow
- **WorkflowStep**: Represents an individual step in a workflow

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Initialize the database:
   ```
   python -c "from db.manager import DatabaseManager; DatabaseManager().initialize()"
   ```

## Usage

### Starting the MCP Server

```bash
python gpmgmt.py
```

### Running test scripts

```bash
python test_gpmgmt_tools.py
```

### Available MCP Tools

- `get_available_workflows()`: Get a list of available workflow configurations
- `get_details_for_workflow(name)`: Get details for a specific workflow configuration
- `create_workflow(name, description, config_name)`: Create a new workflow instance
- `list_workflows()`: List all active workflow instances
- `launch_workflow(name, context)`: Launch a workflow with the given name and context

## Workflow Configuration

Workflows are defined in JSON configuration files located in the `workflows` directory. Each workflow configuration includes:

- **name**: The name of the workflow
- **description**: A description of the workflow
- **context**: The context required for the workflow
- **steps**: The steps in the workflow

### Example Workflow Configuration

```json
{
  "name": "assets-deployment",
  "description": "Assets deployment workflow",
  "context": {
    "ticket_number": { "type": "string", "required": true },
    "ext-app-id": { "type": "string", "required": true },
    "assets-location": { "type": "string", "required": false },
    "built-assets-location": { "type": "string", "required": false }
  },
  "steps": [
    {
      "id": "get-assets",
      "name": "Get Assets for Deployment",
      "type": "manual",
      "conditions": {
        "assets-location": "!null",
        "ext-app-id": "!null"
      },
      "instructions": "Please get assets from the location: {customer_id} and copy them to the git repo folder.",
      "completion": "User has to confirm that they copied the assets to the git repo folder."
    },
    {
      "id": "run-build-job",
      "name": "Assets build job",
      "type": "manual",
      "conditions": {
        "status": "step_1_completed"
      },
      "instructions": "Please run the build job for the assets in the git repo folder then provide it to build-assets-location property.",
      "completion": "built-assets-location != null"
    }
    // Additional steps...
  ]
}
```

### Step Types

- **Manual Steps**: Require user interaction and provide instructions
- **Automated Steps**: Execute actions automatically using MCP servers

### Step Conditions

Steps can have conditions that determine when they should be executed. Conditions are based on workflow context and can include:

- Parameter existence checks
- Parameter value checks
- Status checks

## Use Case Example: Whitelabel Application Customer Decommission

A typical workflow might involve:

1. Getting application credentials and details
2. Making a database request for active users to decommission
3. Decommissioning each user with another request
4. Making internal system requests to other teams to complete the process in other systems
5. Sending emails to concerned teams
6. Announcing the successful decommission

With GP-MGMT, this entire process can be defined as a workflow, with each step clearly defined and executed in sequence. The system guides users through manual steps and automates steps where possible.

## Extending with MCP Servers

GP-MGMT can be extended by integrating with other MCP servers. This allows for:

- Adding new automated actions
- Integrating with external systems
- Customizing workflows for specific use cases
