import subprocess

from halo import Halo
from .prometheus import install

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
