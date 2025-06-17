import subprocess
import json
import uuid
from pathlib import Path
import time
import os
from dotenv import load_dotenv
import getpass

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
# Load environment variables from .env file in the same directory
load_dotenv(SCRIPT_DIR / ".env")

TEMPLATE_FILE = SCRIPT_DIR / "sandbox_template.bicep"
RESOURCE_GROUP = "codex_rg"
LOCATION = "eastus"
REGISTRY_NAME = "registrycodex64425830"
IMAGE_NAME = "sandbox/sandbox-image:bashfix"
CONTAINER_NAME = "sandbox-container"  # Default container name
FILE_SHARE_NAME = "projects"  # Default file share name
MOUNT_PATH = "/projects"  # Default mount path in container
STORAGE_ACCOUNT_NAME = None  # Will be auto-generated if not specified

def get_github_token() -> str:
    """Get GitHub token from environment or prompt user."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("\n🔑 GitHub token not found in .env file")
        print("Please enter your GitHub token (it will not be displayed):")
        token = getpass.getpass()
        
        # Ask if user wants to save the token
        save_token = input("\nWould you like to save this token to .env file? (y/n): ").lower()
        if save_token == 'y':
            env_path = SCRIPT_DIR / ".env"
            with open(env_path, 'a') as f:
                f.write(f"\nGITHUB_TOKEN={token}\n")
            print("✅ Token saved to .env file")
    
    return token

def check_github_token():
    """Check if GitHub token is set."""
    try:
        token = get_github_token()
        if not token:
            raise ValueError("GitHub token is required")
        return True
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

def build_and_push_image():
    """Build and push the Docker image to ACR."""
    print("\n🐳 Building and pushing Docker image...")
    build_context = str(Path(__file__).parent)
    
    # Create and use buildx builder
    try:
        subprocess.run([
            "docker", "buildx", "create", "--use", "--bootstrap", "--name", "sbx-builder"
        ], check=True, capture_output=True)
    except subprocess.CalledProcessError:
        # If builder already exists, just use it
        subprocess.run([
            "docker", "buildx", "use", "sbx-builder"
        ], check=True, capture_output=True)
    
    # Build and push multi-platform image
    try:
        subprocess.run([
            "docker", "buildx", "build",
            "--platform", "linux/amd64,linux/arm64",
            "-t", f"{REGISTRY_NAME}.azurecr.io/{IMAGE_NAME}",
            "--push", build_context
        ], check=True, capture_output=True)
        print("✅ Docker image built and pushed successfully")
    except subprocess.CalledProcessError as e:
        print("❌ Docker build and push failed!")
        print("STDOUT:\n", e.stdout.decode() if e.stdout else "")
        print("STDERR:\n", e.stderr.decode() if e.stderr else "")
        raise

def get_acr_credentials():
    """Get ACR credentials."""
    print("\n🔑 Retrieving ACR credentials...")
    username = subprocess.check_output([
        "az", "acr", "credential", "show",
        "-n", REGISTRY_NAME,
        "--query", "username",
        "-o", "tsv"
    ], text=True).strip()
    
    password = subprocess.check_output([
        "az", "acr", "credential", "show",
        "-n", REGISTRY_NAME,
        "--query", "passwords[0].value",
        "-o", "tsv"
    ], text=True).strip()
    
    print("✅ ACR credentials retrieved successfully")
    return username, password

def deploy_sandbox(
    resource_group: str = RESOURCE_GROUP,
    location: str = LOCATION,
    container_name: str = CONTAINER_NAME,
    file_share_name: str = FILE_SHARE_NAME,
    mount_path: str = MOUNT_PATH,
    storage_account_name: str = STORAGE_ACCOUNT_NAME
) -> dict:
    """Deploy the sandbox Bicep template and return connection info.
    
    Args:
        resource_group: Azure resource group name
        location: Azure region
        container_name: Name for the container instance
        file_share_name: Name for the storage file share
        mount_path: Path where the storage will be mounted in the container
        storage_account_name: Name for the storage account (will be auto-generated if not specified)
    """
    deployment_name = f"deploy-sandbox-{uuid.uuid4().hex[:8]}"
    print(f"\n🔧 Starting deployment with name: {deployment_name}")
    print(f"📍 Location: {location}")
    print(f"🏢 Resource Group: {resource_group}")
    print(f"📦 Container Name: {container_name}")
    print(f"💾 File Share Name: {file_share_name}")
    print(f"📂 Mount Path: {mount_path}")
    if storage_account_name:
        print(f"🏪 Storage Account Name: {storage_account_name}")
    else:
        print("🏪 Storage Account Name: (will be auto-generated)")
    
    try:
        # Get ACR credentials
        username, password = get_acr_credentials()
        
        # Get GitHub token
        github_token = get_github_token()
        
        print("\n📦 Deploying Bicep template...")
        start_time = time.time()
        
        # Build parameters list
        parameters = [
            f"registryName={REGISTRY_NAME}",
            f"containerImage={REGISTRY_NAME}.azurecr.io/{IMAGE_NAME}",
            f"containerRegistryServer={REGISTRY_NAME}.azurecr.io",
            f"containerRegistryUsername={username}",
            f"containerRegistryPassword=@securestring={password}",  # Mark as secure string
            f"location={location}",
            f"fileShareName={file_share_name}",
            f"mountPath={mount_path}",
            f"containerName={container_name}",
            f"githubToken=@securestring={github_token}"  # Mark as secure string
        ]
        
        # Add storage account name if specified
        if storage_account_name:
            parameters.append(f"storageAccountName={storage_account_name}")
        
        # Print the command we're about to run (without sensitive data)
        print("\n🔍 Running Azure deployment command...")
        safe_params = [p for p in parameters if "Password" not in p and "Token" not in p]
        print(f"Parameters: {safe_params}")
        
        # Run the deployment command
        result = subprocess.run([
            "az", "deployment", "group", "create",
            "--resource-group", resource_group,
            "--name", deployment_name,
            "--template-file", str(TEMPLATE_FILE),
            "--parameters", *parameters
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"\n❌ Deployment failed!")
            print(f"Error details: {result.stderr}")
            return {
                "status": "error",
                "message": result.stderr,
                "id": deployment_name
            }
            
        print("✅ Bicep template deployment initiated")
        print("⏳ Waiting for container to be ready...")
        
        # Wait for container to be ready (max 5 minutes)
        max_wait_time = 60  # 5 minutes
        start_wait = time.time()
        while time.time() - start_wait < max_wait_time:
            try:
                # Check if container exists and is running
                container_status = subprocess.run([
                    "az", "container", "show",
                    "-g", resource_group,
                    "-n", container_name,
                    "--query", "properties.instanceView.state",
                    "-o", "tsv"
                ], capture_output=True, text=True)
                
                if container_status.returncode == 0:
                    state = container_status.stdout.strip()
                    if state == "Running":
                        print("\n✅ Container is running!")
                        break
                    print(f".", end="", flush=True)
                else:
                    print(f".", end="", flush=True)
                
                time.sleep(10)  # Wait 10 seconds before checking again
            except Exception:
                print(f".", end="", flush=True)
                time.sleep(10)
        else:
            print("\n❌ Timeout waiting for container to be ready")
            return {
                "status": "error",
                "message": "Timeout waiting for container to be ready",
                "id": deployment_name
            }
        
        deployment_time = time.time() - start_time
        print(f"⏱️ Total deployment time: {deployment_time:.2f} seconds")

        # Get container IP
        print("\n🌐 Retrieving container IP...")
        ip = subprocess.check_output([
            "az", "container", "show",
            "-g", resource_group,
            "-n", container_name,
            "--query", "ipAddress.ip",
            "-o", "tsv"
        ], text=True).strip()
        
        # Get storage account name and connection string
        print("\n💾 Retrieving storage account details...")
        storage = subprocess.check_output([
            "az", "deployment", "group", "show",
            "-g", resource_group,
            "-n", deployment_name,
            "--query", "properties.outputs.storageAccountName.value",
            "-o", "tsv"
        ], text=True).strip()

        connection_string = subprocess.check_output([
            "az", "deployment", "group", "show",
            "-g", resource_group,
            "-n", deployment_name,
            "--query", "properties.outputs.storageConnectionString.value",
            "-o", "tsv"
        ], text=True).strip()

        return {
            "status": "success",
            "ip": ip,
            "storage_account": storage,
            "storage_connection_string": connection_string,
            "container_name": container_name,
            "file_share_name": file_share_name,
            "mount_path": mount_path,
            "id": deployment_name
        }
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Deployment failed!")
        print(f"Error details: {e.stderr}")
        return {
            "status": "error",
            "message": e.stderr,
            "id": deployment_name
        }

def main():
    """Main function to deploy the sandbox environment."""
    print("\n🚀 Starting sandbox deployment process...")
    print("=" * 50)
    
    try:
        check_github_token()
        build_and_push_image()
        
        # You can customize these values
        container_name = "my-sandbox-container"  # Custom container name
        file_share_name = "my-sandbox-files"     # Custom file share name
        mount_path = "/projects"                 # Default mount path
        storage_account_name = "mysandboxstorage"  # Custom storage account name
        
        result = deploy_sandbox(
            container_name=container_name,
            file_share_name=file_share_name,
            mount_path=mount_path,
            storage_account_name=storage_account_name
        )
        
        print("\n" + "=" * 50)
        if result["status"] == "success":
            print(f"\n✨ Deployment successful!")
            print(f"📋 Deployment ID: {result['id']}")
            print(f"📦 Container Name: {result['container_name']}")
            print(f"🌐 Container IP: {result['ip']}")
            print(f"💾 Storage Account: {result['storage_account']}")
            print(f"📁 File Share Name: {result['file_share_name']}")
            print(f"📂 Mount Path: {result['mount_path']}")
            print(f"🔑 Storage Connection String: {result['storage_connection_string']}")
        else:
            print(f"\n❌ Deployment failed!")
            print(f"Error: {result['message']}")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("=" * 50)

if __name__ == "__main__":
    main()
