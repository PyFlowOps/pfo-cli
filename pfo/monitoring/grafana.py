import os
import subprocess
import base64
from halo import Halo
from pfo.monitoring import monitoring_config
from pfo.k8s import _tempdir

BASE = os.path.dirname(os.path.abspath(__file__))

_grafana_spinner = Halo(text_color="blue", spinner="dots")
grafana_config = monitoring_config.get("grafana", {})

def add_repository() -> None:
    """Add the Grafana Helm repository."""
    _grafana_spinner.start("Adding Grafana Helm repository...")

    try:
        _res = subprocess.run(["helm", "repo", "add", "grafana", "https://grafana.github.io/helm-charts"], check=True, capture_output=True, text=True)
        _grafana_spinner.succeed("Grafana Helm repository added successfully.")
    except subprocess.CalledProcessError as e:
        _grafana_spinner.fail(f"Failed to add Grafana Helm repository: {e}")

    if _res.returncode != 0:
        _grafana_spinner.fail("Grafana Helm repository addition response code was not 0. Please check the Helm output for details.")

def install() -> None:
    """Install Grafana in the Kubernetes cluster."""
    _grafana_spinner.start("Installing Grafana...")
    add_repository()  # Ensure the Grafana Helm repository is added

    try:
        _res = subprocess.run(["helm", "install", "grafana", "grafana/grafana", "--namespace", "monitoring"], check=True, capture_output=True, text=True)
        _grafana_spinner.succeed("Grafana installed successfully.")
    except subprocess.CalledProcessError as e:
        _grafana_spinner.fail(f"Failed to install Grafana: {e}")

    if _res.returncode != 0:
        _grafana_spinner.fail("Grafana installation response code was not 0. Please check the Helm output for details.")

def get_grafana_default_password() -> str:
    """Retrieve the Grafana admin password."""
    try:
        _res = subprocess.run(["kubectl", "get", "secret", "grafana", "--namespace", "monitoring", "-o", "jsonpath='{.data.admin-password}'"], check=True, capture_output=True, text=True)
        if _res.returncode != 0:
            _grafana_spinner.fail("Failed to retrieve Grafana admin password. Please check the kubectl output for details.")
            return ""
        
        password = base64.b64decode(_res.stdout.strip().strip("'")).decode('utf-8')
        return password
    except subprocess.CalledProcessError as e:
        _grafana_spinner.fail(f"Failed to retrieve Grafana admin password: {e}")
        return ""

def update() -> None:
    """Update Grafana configuration."""
    _grafana_spinner.start("Updating Grafana configuration...")

    _grafana_basedir = os.path.expanduser(grafana_config.get("basedir", "~/.pfo/k8s/pyops/overlays/grafana"))

    if not os.path.exists(_tempdir):
        os.makedirs(_tempdir, exist_ok=True)

    # Create a Grafana configuration file
    try:
        _res = subprocess.run(["kustomize", "build", _grafana_basedir], check=True, capture_output=True, text=True)
        with open(os.path.join(_tempdir, "grafana-config.yaml"), "w+") as f:
            f.write(_res.stdout)
        _grafana_spinner.succeed("Grafana configuration file created successfully.")
    except subprocess.CalledProcessError as e:
        _grafana_spinner.fail(f"Failed to create Grafana configuration file: {e}")
        return

    # Apply the Grafana configuration
    try:
        _res = subprocess.run(["kubectl", "apply", "-f", os.path.join(_tempdir, "grafana-config.yaml")], check=True, capture_output=True, text=True)
        if _res.returncode != 0:
            _grafana_spinner.fail("Grafana configuration response code was not 0. Please check the kubectl output for details.")
    except subprocess.CalledProcessError as e:
        _grafana_spinner.fail(f"Failed to apply Grafana configuration: {e}")
        return

    _grafana_spinner.succeed("Grafana configuration updated successfully.")
