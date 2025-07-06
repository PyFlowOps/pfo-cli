import os
import subprocess
import json

from halo import Halo

_traefik_spinner = Halo(text_color="blue", spinner="dots")

_helm = ["command", "-v", "helm"]
_kubectl = ["command", "-v", "kubectl"]

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE, "k8s_config.json")

with open(CONFIG_FILE, "r") as config_file:
    # Load the configuration file if it exists, otherwise use an empty dictionary
    _config = json.load(config_file)

traefik_values_file = _config.get("traefik", {}).get("values_file", "~/.pfo/k8s/local/overlays/traefik/values.yaml")

def is_helm_installed() -> bool:
    """Check if Helm is installed."""
    _res = subprocess.run(_helm, check=True, capture_output=True, text=True)
    if _res.returncode == 0:
        return True
    
    return False

def is_kubectl_installed() -> bool:
    """Check if kubectl is installed."""
    _res = subprocess.run(_kubectl, check=True, capture_output=True, text=True)
    if _res.returncode == 0:
        return True
    
    return False

if not is_helm_installed():
    _traefik_spinner.fail("Helm is not installed. Please install Helm to proceed.")

if not is_kubectl_installed():
    _traefik_spinner.fail("kubectl is not installed. Please install kubectl to proceed.")

def create_traefik_namespace() -> None:
    """Create the Traefik namespace if it doesn't exist."""
    try:
        _res = subprocess.run(["kubectl", "create", "namespace", "traefik"], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        if "AlreadyExists" not in str(e):
            _traefik_spinner.fail(f"Failed to create Traefik namespace: {e}")
        
    if _res.returncode != 0:
        _traefik_spinner.fail("Failed to create Traefik namespace. Please check the kubectl output for details.")
    
def add_repo_to_helm() -> None:
    """Add the Traefik Helm repository."""
    try:
        _res = subprocess.run(["helm", "repo", "add", "traefik", "https://traefik.github.io/charts"], check=True, capture_output=True, text=True)
        _res2 = subprocess.run(["helm", "repo", "update"], check=True, capture_output=True, text=True)
        _traefik_spinner.succeed("Traefik Helm repository added successfully.")
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to add Traefik Helm repository: {e}")

    if _res.returncode != 0 or _res2.returncode != 0:
        _traefik_spinner.fail("Failed to add Traefik Helm repository. Please check the Helm output for details.")

def check_values_file(traefik_values_file: str) -> bool:
    """Check if the Traefik values file exists."""
    return os.path.isfile(os.path.expanduser(traefik_values_file))

def install() -> None:
    """Install Traefik using Helm with the specified values file."""
    _traefik_spinner.start("Installing Traefik...")
    # Let's ensure the Hekm traefik repository is added
    add_repo_to_helm()

    # Create the namespace if it doesn't exist
    create_traefik_namespace()

    # Check if the values file exists
    if not check_values_file(traefik_values_file):
        raise FileNotFoundError(f"Values file '{traefik_values_file}' does not exist.")

    # Install Traefik with the specified values
    try:
        _cmd = ["helm", "install", "traefik", "traefik/traefik", "--namespace", "traefik", "-f", os.path.expanduser(traefik_values_file)]
        _res = subprocess.run(_cmd, check=True, capture_output=True, text=True)

    except subprocess.CalledProcessError as e:
        _traefik_spinner.fail(f"Failed to install Traefik: {e}")
    
    if _res.returncode != 0:
        _traefik_spinner.fail("Failed to install Traefik. Please check the Helm output for details.")

    _traefik_spinner.succeed("Traefik installed successfully.")
    _traefik_spinner.stop()
