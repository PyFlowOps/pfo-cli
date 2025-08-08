import os
import json
import base64
import time
import subprocess
import requests
import urllib3

from halo import Halo
from pfo.k8s import k8s_config, _tempdir

_argocd_spinner = Halo(text_color="blue", spinner="dots")
argocd_config = k8s_config["argocd"]

# Suppress only the InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def install() -> None:
    """This function will install ArgoCD in the Kind cluster."""
    # Now we will install ArgoCD in the Kind cluster
    # This will install ArgoCD in the argocd namespace
    install_argocd()  # Install ArgoCD
    install_image_updater()  # Install the ArgoCD Image Updater
    time.sleep(15) # Wait for ArgoCD to be fully deployed

def install_argocd() -> None:
    """This function will install ArgoCD in the Kind cluster."""
    # Now we will install ArgoCD in the Kind cluster
    # This will install ArgoCD in the argocd namespace
    _argo_deployment = ["kubectl", "apply", "-n", "argocd", "-f", f"https://raw.githubusercontent.com/argoproj/argo-cd/{argocd_config['version']}/manifests/install.yaml"]
    try:
        _resp = subprocess.run(_argo_deployment, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        _argocd_spinner.fail(f"Failed to install ArgoCD: {e}")
        return
    
    if _resp.returncode != 0:
        _argocd_spinner.fail(f"Failed to install ArgoCD: {_resp.stderr}")
        return

    _argocd_spinner.succeed("ArgoCD deployment installed successfully!")

def install_image_updater() -> None:
    """This function will install the ArgoCD Image Updater in the Kind cluster."""
    _imupd_deployment = ["kubectl", "apply", "-n", "argocd", "-f", "https://raw.githubusercontent.com/argoproj-labs/argocd-image-updater/stable/manifests/install.yaml"]
    try:
        _resp = subprocess.run(_imupd_deployment, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        _argocd_spinner.fail(f"Failed to install ArgoCD: {e}")
        return

def get_argocd_default_password() -> str|None:
    """
    Retrieves the default password for the ArgoCD admin user by accessing the
    'argocd-initial-admin-secret' Kubernetes secret in the 'argocd' namespace.
    Uses kubectl to fetch the base64-encoded password, decodes it, and returns
    the password as a string.
    Returns:
        str | None: The decoded ArgoCD admin password if successful, otherwise None.
    Raises:
        None explicitly, but logs failure and returns None if the subprocess fails.
    """
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
        _argocd_spinner.fail(f"Failed to get ArgoCD initial admin - {e}")
        return

def install_with_helm() -> None:
    """
    Installs ArgoCD in a Kind Kubernetes cluster using Helm.

    This function performs the following steps:
    1. Adds the Argo Helm repository.
    2. Updates the Helm repositories.
    3. Installs the ArgoCD chart into the 'argocd' namespace, creating the namespace if it does not exist.

    If any step fails, it reports the failure using the spinner and exits the function.
    On success, it notifies that ArgoCD was installed successfully.
    """
    """This function will install ArgoCD in the Kind cluster using Helm."""
    _helm_repo_add = ["helm", "repo", "add", "argo", "https://argoproj.github.io/argo-helm"]
    _helm_repo_update = ["helm", "repo", "update"]
    _helm_install = ["helm", "install", "argocd", "argo/argo-cd", "-n", "argocd", "--create-namespace"]

    try:
        subprocess.run(_helm_repo_add, check=True)
        subprocess.run(_helm_repo_update, check=True)
        subprocess.run(_helm_install, check=True)
    except subprocess.CalledProcessError as e:
        _argocd_spinner.fail(f"Failed to install ArgoCD with Helm: {e}")
        return

    _argocd_spinner.succeed("ArgoCD installed successfully with Helm!")

def restart_argocd_server() -> None:
    """Restart the ArgoCD server to apply changes."""
    _restart_cmd = ["kubectl", "-n", "argocd", "rollout", "restart", "deployment/argocd-server"]
    try:
        _resp = subprocess.run(_restart_cmd, check=True, capture_output=True, text=True)
        if _resp.returncode != 0:
            _argocd_spinner.fail(f"Failed to restart ArgoCD server: {_resp.stderr}")
            return
    except subprocess.CalledProcessError as e:
        _argocd_spinner.fail(f"Failed to restart ArgoCD server: {e}")
        return

    _argocd_spinner.succeed("ArgoCD server restarted successfully!")

def wait_for_argocd_server() -> None:
    """Wait for the ArgoCD server to be ready."""
    ready = False
    _argocd_spinner.start("Waiting for ArgoCD server to be ready...")
    count = 0
    while count < 20:
        _resp = requests.get("https://argocd.pyflowops.local:30443", verify=False, allow_redirects=False)
        if _resp.status_code == 200:
            ready = True
            _argocd_spinner.succeed("ArgoCD server is ready!")
            break
        else:
            time.sleep(10)
            count += 1

    if not ready:
        _argocd_spinner.fail("ArgoCD server is not ready after 20 attempts. Please check the logs for more details.")
    
    return

def wait_for_argocd_projects() -> None:
    # Now we will wait for the CRD to be established
    _max = 10
    _attempt = 0
    _waitspin = Halo(text_color="blue", spinner="dots")
    _crdcmd = ["kubectl", "wait", "--for=condition=established", "crd/appprojects.argoproj.io", "--timeout=60s"]
    _waitspin.start(text="Waiting for Kubernetes Cluster required resources to become available...")  # Start the spinner for waiting
    
    while _attempt < _max:
        try:
            _resp = subprocess.run(_crdcmd, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            _attempt += 1
            time.sleep(5)  # Wait for 5 seconds before retrying

        if _resp.returncode == 0:
            _waitspin.succeed(f"crd/appprojects.argoproj.io established successfully!")
            time.sleep(5) # Wait for a few seconds to ensure the CRD is established
            break
        else:
            if _attempt == _max - 1:
                _waitspin.fail(f"Failed to establish CRD: {_resp.stderr}; Max attempts reached. Exiting...")
                return
            
    _waitspin.stop()  # Stop the spinner after waiting

def wait_for_argocd_deployment() -> None:
    _argocd_spinner.start("Waiting for the Kind cluster to be ready...\n\n")
    count = 0
    while True:
        try:
            _res = subprocess.run(["kubectl", "get", "secrets", "--namespace", "argocd", "argocd-initial-admin-secret", "-o", "json"], check=True, capture_output=True, text=True)
            if _res.returncode == 0:
                _argocd_spinner.succeed("Kind cluster is ready!")
                break
            else:
                _argocd_spinner.fail("Kind cluster is not ready yet. Retrying...")
                count += 1
                if count >= 15:
                    _argocd_spinner.fail("Kind cluster is not ready after 15 attempts. Exiting...")
                    exit(1)

        except subprocess.CalledProcessError:
            if count < 15:
                count += 1
                time.sleep(10)  

def update() -> None:
    """Updates the ArgoCD installation (configure with Kustomize) in the Kind cluster."""
    _argocd_spinner.start("Configuring ArgoCD...")
    _argocd_basedir = os.path.expanduser(argocd_config.get("basedir", "~/.pfo/k8s/pyops/overlays/argocd"))
    
    if not os.path.exists(_tempdir):
        os.makedirs(_tempdir, exist_ok=True)

    try:
        _res = subprocess.run(["kustomize", "build", _argocd_basedir], check=True, capture_output=True, text=True)
        with open(os.path.join(_tempdir, "argocd-config.yaml"), "w+") as f:
            f.write(_res.stdout)
        _argocd_spinner.succeed("ArgoCD configuration file created successfully.")
    except subprocess.CalledProcessError as e:
        _argocd_spinner.fail(f"Failed to update ArgoCD: {e}")
        return

    try:
        _res = subprocess.run(["kubectl", "apply", "-f", os.path.join(_tempdir, "argocd-config.yaml")], check=True, capture_output=True, text=True)
        if _res.returncode != 0:
            _argocd_spinner.fail(f"Failed to apply ArgoCD configuration: {_res.stderr}")
            return
    except subprocess.CalledProcessError as e:
        _argocd_spinner.fail(f"Failed to apply ArgoCD configuration: {e}")
        return

    # Restart the ArgoCD server to apply changes
    restart_argocd_server()

    # Wait for the ArgoCD server to be ready
    wait_for_argocd_server()

    # If everything is successful, we can mark the spinner as succeeded
    _argocd_spinner.succeed("ArgoCD updated successfully!")
