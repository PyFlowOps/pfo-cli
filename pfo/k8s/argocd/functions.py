import os
import json
import base64
import time
import subprocess

from halo import Halo

spinner = Halo(text_color="blue", spinner="dots")

def install() -> None:
    """This function will install ArgoCD in the Kind cluster."""
    # Now we will install ArgoCD in the Kind cluster
    # This will install ArgoCD in the argocd namespace
    install_argcod()  # Install ArgoCD
    install_image_updater()  # Install the ArgoCD Image Updater
    time.sleep(15) # Wait for ArgoCD to be fully deployed


def install_argcod() -> None:
    """This function will install ArgoCD in the Kind cluster."""
    # Now we will install ArgoCD in the Kind cluster
    # This will install ArgoCD in the argocd namespace
    _argo_deployment = ["kubectl", "apply", "-n", "argocd", "-f", "https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml"]
    try:
        _resp = subprocess.run(_argo_deployment, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        spinner.fail(f"Failed to install ArgoCD: {e}")
        return
    
    if _resp.returncode != 0:
        spinner.fail(f"Failed to install ArgoCD: {_resp.stderr}")
        return

    spinner.succeed("ArgoCD deployment installed successfully!")
def install_image_updater() -> None:
    """This function will update the ArgoCD image in the Kind cluster."""
    _imupd_deployment = ["kubectl", "apply", "-n", "argocd", "-f", "https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml"]
    try:
        _resp = subprocess.run(_imupd_deployment, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        spinner.fail(f"Failed to install ArgoCD: {e}")
        return

def get_argocd_default_password() -> str|None:
    """Retrieves the default password for the ArgoCD admin user."""
    _p1_cmd = ["kubectl", "-n", "argocd", "get", "secret", "argocd-initial-admin-secret", "-o", "jsonpath='{.data.password}'"]
    try:
        _resp = subprocess.run(_p1_cmd, check=True, capture_output=True, text=True)
        _data = _resp.stdout.strip()
        
        if type(_data) == bytes:
            _decoded_data = _data.decode("utf-8")
            _pass = base64.b64decode(_decoded_data).decode("utf-8") # Decode the base64 encoded data
            return _pass
        
        if type(_data) == str:
            _pass = base64.b64decode(_data).decode("utf-8")  # Remove the single quotes around the data
            return _pass
        
    except subprocess.CalledProcessError as e:
        spinner.fail(f"Failed to get ArgoCD initial admin - {e}")
        return
