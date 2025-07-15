import os
import subprocess
import json

from halo import Halo

_metallb_spinner = Halo(text_color="blue", spinner="dots")

_kubectl = ["command", "-v", "kubectl"]

BASE = os.path.dirname(os.path.abspath(__file__))

def is_kubectl_installed() -> bool:
    """Check if kubectl is installed."""
    _res = subprocess.run(_kubectl, check=True, capture_output=True, text=True)
    if _res.returncode == 0:
        return True
    
    return False

def install() -> None:
    """Install MetalLB in the Kubernetes cluster."""
    if not is_kubectl_installed():
        _metallb_spinner.fail("kubectl is not installed. Please install kubectl to proceed.")
    
    _metallb_spinner.start("Installing MetalLB...")

    try:
        # Apply the MetalLB manifest
        _res = subprocess.run(["kubectl", "apply", "-f", "https://raw.githubusercontent.com/metallb/metallb/v0.15.2/config/manifests/metallb-native.yaml"], check=True, capture_output=True, text=True)
        _metallb_spinner.succeed("MetalLB installed successfully.")
    except subprocess.CalledProcessError as e:
        _metallb_spinner.fail(f"Failed to install MetalLB: {e}")

    if _res.returncode != 0:
        _metallb_spinner.fail("MetalLb installation reponse code was not 0. Please check the kubectl output for details.")
