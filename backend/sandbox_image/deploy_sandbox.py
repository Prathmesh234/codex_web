import subprocess
import json
import uuid
from pathlib import Path

TEMPLATE_FILE = Path(__file__).parent / "sandbox_template.json"
RESOURCE_GROUP = "codex_rg"
LOCATION = "eastus"

def deploy_sandbox(resource_group: str = RESOURCE_GROUP, location: str = LOCATION) -> dict:
    """Deploy the sandbox ARM template and return connection info.

    This function requires the Azure CLI to be installed and logged in.
    """
    deployment_name = f"deploy-sandbox-{uuid.uuid4().hex[:8]}"
    try:
        subprocess.run([
            "az", "deployment", "group", "create",
            "--resource-group", resource_group,
            "--name", deployment_name,
            "--template-file", str(TEMPLATE_FILE),
            "--parameters", f"location={location}"
        ], check=True, capture_output=True, text=True)

        connection_string = subprocess.check_output([
            "az", "deployment", "group", "show",
            "--resource-group", resource_group,
            "--name", deployment_name,
            "--query", "properties.outputs.storageConnectionString.value",
            "-o", "tsv"
        ], text=True).strip()

        return {
            "status": "success",
            "storage_queue_key": connection_string,
            "id": deployment_name
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "message": e.stderr,
            "id": deployment_name
        }
