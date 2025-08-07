import os
import subprocess

from halo import Halo
from k8s import k8s_config, _tempdir

BASE = os.path.dirname(os.path.abspath(__file__))

_prometheus_spinner = Halo(text_color="blue", spinner="dots")
_kubectl = ["command", "-v", "kubectl"]
_helm = ["command", "-v", "helm"]

def is_kubectl_installed() -> bool:
    """Check if kubectl is installed."""
    _res = subprocess.run(_kubectl, check=True, capture_output=True, text=True)
    if _res.returncode == 0:
        return True
    
    return False

def is_helm_installed() -> bool:
    """Check if Helm is installed."""
    _res = subprocess.run(_helm, check=True, capture_output=True, text=True)
    if _res.returncode == 0:
        return True
    
    return False

prometheus_config = k8s_config.get("prometheus", {})

def add_repository() -> None:
    """Add the Prometheus Helm repository."""
    if not is_helm_installed():
        _prometheus_spinner.fail("Helm is not installed. Please install Helm to proceed.")
    
    _prometheus_spinner.start("Adding Prometheus Helm repository...")

    try:
        _res = subprocess.run(["helm", "repo", "add", "prometheus-community", "https://prometheus-community.github.io/helm-charts"], check=True, capture_output=True, text=True)
        _prometheus_spinner.succeed("Prometheus Helm repository added successfully.")
    except subprocess.CalledProcessError as e:
        _prometheus_spinner.fail(f"Failed to add Prometheus Helm repository: {e}")

    if _res.returncode != 0:
        _prometheus_spinner.fail("Prometheus Helm repository addition response code was not 0. Please check the Helm output for details.")

def install() -> None:
    """Install Prometheus in the Kubernetes cluster."""
    if not is_kubectl_installed():
        _prometheus_spinner.fail("kubectl is not installed. Please install kubectl to proceed.")
    
    if not is_helm_installed():
        _prometheus_spinner.fail("Helm is not installed. Please install Helm to proceed.")
            
    _prometheus_spinner.start("Installing Prometheus...")
    add_repository()  # Ensure the Prometheus Helm repository is added

    try:
        _res = subprocess.run(["helm", "install", "prometheus", "prometheus-community/prometheus", "--namespace", "monitoring"], check=True, capture_output=True, text=True)
        _prometheus_spinner.succeed("Prometheus installed successfully.")
    except subprocess.CalledProcessError as e:
        _prometheus_spinner.fail(f"Failed to install Prometheus: {e}")

    if _res.returncode != 0:
        _prometheus_spinner.fail("Prometheus installation response code was not 0. Please check the Helm output for details.")
