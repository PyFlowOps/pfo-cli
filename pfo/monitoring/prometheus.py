import os
import subprocess

from halo import Halo
from pfo.monitoring import monitoring_config
from k8s import _tempdir

BASE = os.path.dirname(os.path.abspath(__file__))

_prometheus_spinner = Halo(text_color="blue", spinner="dots")
prometheus_config = monitoring_config.get("prometheus", {})

def add_repository() -> None:
    """Add the Prometheus Helm repository."""
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
    _prometheus_spinner.start("Installing Prometheus...")
    add_repository()  # Ensure the Prometheus Helm repository is added

    try:
        _res = subprocess.run(["helm", "install", "prometheus", "prometheus-community/prometheus", "--namespace", "monitoring", "--create-namespace"], check=True, capture_output=True, text=True)
        _prometheus_spinner.succeed("Prometheus installed successfully.")
    except subprocess.CalledProcessError as e:
        _prometheus_spinner.fail(f"Failed to install Prometheus: {e}")

    if _res.returncode != 0:
        _prometheus_spinner.fail("Prometheus installation response code was not 0. Please check the Helm output for details.")
