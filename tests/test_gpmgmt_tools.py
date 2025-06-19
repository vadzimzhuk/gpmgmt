import sys
import os

# Add parent directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
from pipelineMGMT.manager import WorkflowManager
from gpmgmt import get_available_workflows, get_details_for_workflow, launch_workflow, create_workflow


async def main():
    # Get available workflows
    print("Testing get_available_workflows()...")
    workflows_str = await get_available_workflows()
    print("Available workflows:")
    print(workflows_str)
    if not workflows_str:
        print("❌")
        return
    else:
        print("✅")
    print("\n---\n")

    # Get details for the test workflow
    print(f"Testing get_details_for_workflow: '01 Test workflow config'...")
    details = await get_details_for_workflow("01 Test workflow config")
    print("Workflow details:")

    if not details:
        print("❌")
        return
    else:
        print("✅")
    print("\n---\n")

    # Workflow creation
    print("Testing create_workflow('Test Workflow', 'Test workflow #1')...")
    creation_result = await create_workflow("01 Test workflow config", "Test workflow #1")
    print("Pipeline created with id:" + str(creation_result))
    if not creation_result:
        print("❌")
        return
    else:
        print("✅")
    print("\n---\n")

    # List all active pipelines
    print("List all active pipelines...")
    workflows_str = WorkflowManager().list_workflows()
    print("Active workflows:")
    print(workflows_str)

    print("\n---\n")

    # Launch the workflow
    print(f"Testing launch_workflow('{str(creation_result)}')...")
    launch_result = await launch_workflow(str(creation_result))

    print("Pipeline has been launched: " + launch_result["name"])
    print("Current step inctructions: " + str(launch_result["step_execution"]))
    print("Current steps execution status:")
    for step in launch_result["steps"]:
        print(f"• {step['name']}: ({step['status']})")

if __name__ == "__main__":
    asyncio.run(main())
