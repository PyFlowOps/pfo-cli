import os
import subprocess

from halo import Halo
from pfo.k8s import k8s_config

# We need to get the monitoring configuration from the k8s_config
monitoring_config = k8s_config.get("monitoring", {})

from .prometheus import install as prometheus_install
from .grafana import install as grafana_install
from .loki import install as loki_install
from .grafana import get_grafana_default_password as grafana_admin_password

_monspinner = Halo(text_color="blue", spinner="dots")
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

if not is_kubectl_installed():
    _monspinner.fail("kubectl is not installed. Please install kubectl to proceed.")

if not is_helm_installed():
    _monspinner.fail("Helm is not installed. Please install Helm to proceed.")
