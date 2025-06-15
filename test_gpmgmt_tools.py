import asyncio
from pipelineMGMT.manager import WorkflowManager
from gpmgmt import get_available_workflows, get_details_for_workflow, launch_workflow, create_workflow

async def main():
    print("Testing get_available_workflows()...")
    workflows_str = await get_available_workflows()
    print("Available workflows:")
    print(workflows_str)
    print("\n---\n")

    # Try to get the first workflow name from the output
    first_line = workflows_str.splitlines()[0] if workflows_str else None
    if first_line and ':' in first_line:
        workflow_name = first_line.split(':')[0].strip()
        print(f"Testing get_details_for_workflow('{workflow_name}')...")
        details = await get_details_for_workflow(workflow_name)
        print("Workflow details:")
        print(details)
        print("\n---\n")

        # Workflow creation
        print("Testing create_workflow('Test Workflow', 'Test workflow #1')...")
        creation_result = await create_workflow("assets-deployment", "Test workflow #1")
        print("Creation result:")
        print(creation_result)
        print("\n---\n")

        print("List all active pipelines...")
        workflows_str = WorkflowManager().list_workflows()
        print("Active workflows:")
        print(workflows_str)

        # Launch the workflow
        print(f"Testing launch_workflow('{str(creation_result)}')...")
        launch_result = await launch_workflow(str(creation_result))
        print("Launch result:")
        print(launch_result)
    else:
        print("No workflows found to test get_details_for_workflow or launch_workflow.")
    
    # Try launching a workflow with parameters
    # print("Testing launch_workflow without parameters...")
    # launch_result = await launch_workflow("assets-deployment")
    # print("Launch result without parameters:")
    # print(launch_result)

if __name__ == "__main__":
    asyncio.run(main())
