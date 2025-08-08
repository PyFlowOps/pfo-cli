import os
import subprocess

from halo import Halo
from k8s import k8s_config, _tempdir

BASE = os.path.dirname(os.path.abspath(__file__))

_loki_spinner = Halo(text_color="blue", spinner="dots")
loki_config = k8s_config.get("loki", {})

def add_repository() -> None:
    """Add the Loki Helm repository."""
    _loki_spinner.start("Adding Loki Helm repository...")

    try:
        _res = subprocess.run(["helm", "repo", "add", "loki", "https://grafana.github.io/loki/charts"], check=True, capture_output=True, text=True)
        _loki_spinner.succeed("Loki Helm repository added successfully.")
    except subprocess.CalledProcessError as e:
        _loki_spinner.fail(f"Failed to add Loki Helm repository: {e}")

    if _res.returncode != 0:
        _loki_spinner.fail("Loki Helm repository addition response code was not 0. Please check the Helm output for details.")

def install() -> None:
    """Install Loki in the Kubernetes cluster."""
    _loki_spinner.start("Installing Loki...")
    #add_repository()  # Ensure the Loki Helm repository is added

    try:
        _res = subprocess.run(["helm", "install", "loki-stack", "grafana/loki", "--namespace", "monitoring"], check=True, capture_output=True, text=True)
        _loki_spinner.succeed("Loki installed successfully.")
    except subprocess.CalledProcessError as e:
        _loki_spinner.fail(f"Failed to install Loki: {e}")

    if _res.returncode != 0:
        _loki_spinner.fail("Loki installation response code was not 0. Please check the Helm output for details.")

def update() -> None:
    """Update Loki configuration."""
    _loki_spinner.start("Updating Loki configuration...")

    _loki_basedir = os.path.expanduser(loki_config.get("basedir", "~/.pfo/k8s/pyops/overlays/loki"))

    if not os.path.exists(_tempdir):
        os.makedirs(_tempdir, exist_ok=True)

    # Create a Loki configuration file
    try:
        _res = subprocess.run(["kustomize", "build", _loki_basedir], check=True, capture_output=True, text=True)
        with open(os.path.join(_tempdir, "loki-config.yaml"), "w+") as f:
            f.write(_res.stdout)
        _loki_spinner.succeed("Loki configuration file created successfully.")
    except subprocess.CalledProcessError as e:
        _loki_spinner.fail(f"Failed to create Loki configuration file: {e}")
        return
    
    # Apply the Loki configuration
    try:
        _res = subprocess.run(["kubectl", "apply", "-f", os.path.join(_tempdir, "loki-config.yaml")], check=True, capture_output=True, text=True)
        if _res.returncode != 0:
            _loki_spinner.fail("Loki configuration response code was not 0. Please check the kubectl output for details.")
    except subprocess.CalledProcessError as e:
        _loki_spinner.fail(f"Failed to apply Loki configuration: {e}")
        return

    _loki_spinner.succeed("Loki configuration updated successfully.")
