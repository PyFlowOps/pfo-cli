import os
import subprocess
import json

from halo import Halo
from k8s import k8s_config, _tempdir

BASE = os.path.dirname(os.path.abspath(__file__))

_metallb_spinner = Halo(text_color="blue", spinner="dots")
_kubectl = ["command", "-v", "kubectl"]

metallb_config = k8s_config.get("metallb", {})

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
        _res = subprocess.run(["kubectl", "apply", "-f", f"https://raw.githubusercontent.com/metallb/metallb/{metallb_config['version']}/config/manifests/metallb-native.yaml"], check=True, capture_output=True, text=True)
        _metallb_spinner.succeed("MetalLB installed successfully.")
    except subprocess.CalledProcessError as e:
        _metallb_spinner.fail(f"Failed to install MetalLB: {e}")

    if _res.returncode != 0:
        _metallb_spinner.fail("MetalLb installation reponse code was not 0. Please check the kubectl output for details.")

def update() -> None:
    """Configure MetalLB with a specific IP address pool."""
    _metallb_spinner.start("Configuring MetalLB...")
    _metallb_basedir = os.path.expanduser(metallb_config.get("basedir", "~/.pfo/k8s/pyops/overlays/metallb"))

    if not os.path.exists(_tempdir):
        os.makedirs(_tempdir, exist_ok=True)

    # Create a MetalLB configuration file
    try:
        _res = subprocess.run(["kustomize", "build", _metallb_basedir], check=True, capture_output=True, text=True)
        with open(os.path.join(_tempdir, "metallb-config.yaml"), "w+") as f:
            f.write(_res.stdout)
        _metallb_spinner.succeed("MetalLB configuration file created successfully.")
    except subprocess.CalledProcessError as e:
        _metallb_spinner.fail(f"Failed to create MetalLB configuration file: {e}")
        return

    # Apply the MetalLB configuration
    try:
        _res = subprocess.run(["kubectl", "apply", "-f", os.path.join(_tempdir, "metallb-config.yaml")], check=True, capture_output=True, text=True)
        if _res.returncode != 0:
            _metallb_spinner.fail("MetalLB configuration response code was not 0. Please check the kubectl output for details.")
    except subprocess.CalledProcessError as e:
        _metallb_spinner.fail(f"Failed to apply MetalLB configuration: {e}")

    _metallb_spinner.succeed("MetalLB configured successfully.")