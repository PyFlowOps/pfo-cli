import os
import boto3
import base64
import json
import yaml

from halo import Halo

spinner = Halo(text_color="blue", spinner="dots")

# Constants
BASE = os.path.dirname(os.path.abspath(__file__))
ARGOCD_MANIFESTS_DIR = os.path.abspath(os.path.join(BASE, ".."))
ADRIFT_SECRET_FILE = os.path.join(ARGOCD_MANIFESTS_DIR, "base", "secret.yaml")

# Variables
_region = os.environ.get("AWS_REGION", "us-east-2")  # Default region, can be overridden
_aws_account_id = os.environ.get("AWS_ACCOUNT_ID", "1234567890")  # Default account ID, can be overridden
_ecr_registry = f"{_aws_account_id}.dkr.ecr.{_region}.amazonaws.com"

# Let's run some preliminary checks to ensure the environment is set up correctly
if not _aws_account_id or _aws_account_id == "1234567890":
    spinner.fail("AWS_ACCOUNT_ID environment variable is not set or is set to the default value. Please set it to your actual AWS account ID.")
    exit()

def get_ecr_auth_token() -> dict|None:
    client = boto3.client('ecr', region_name=_region)
    try:
        response = client.get_authorization_token(
            registryIds=[_aws_account_id]
        )
        auth_data = response['authorizationData'][0]
        token = auth_data['authorizationToken']
        proxy_endpoint = auth_data['proxyEndpoint']

        # The token is base64 encoded "username:password"
        decoded_token = base64.b64decode(token).decode('utf-8')
        username, password = decoded_token.split(':')

        return {
            "username": username,
            "password": password,
            "proxy_endpoint": proxy_endpoint,
            "auth_string_base64": base64.b64encode(f"{username}:{password}".encode('utf-8')).decode('utf-8')
        }
    except Exception as e:
        print(f"Error getting ECR authorization token: {e}")
        return None

def get_secret_data() -> dict|None:
    """Read the secret data from the YAML file."""
    try:
        with open(ADRIFT_SECRET_FILE, 'r') as file:
            secret_data = yaml.safe_load(file)
    except Exception as e:
        print(f"Error reading secret file: {e}")
        return None
    
    return secret_data

def update_secret_file():
    auth_data = get_ecr_auth_token()
    if not auth_data:
        spinner.fail("Failed to retrieve ECR authorization token.")

    secret_data: dict|None = get_secret_data()
    if not secret_data:
        spinner.fail("Failed to retrieve secret data.")
        exit()

    print(secret_data)

def docker_login(cloud: str = "aws"):
    """Login to Docker with AWS credentials."""
    auth_data = get_ecr_auth_token()
    if not auth_data:
        spinner.fail("Failed to retrieve ECR authorization token.")
        exit()

    update_secret_file() # This updates the secret file with the ECR auth data