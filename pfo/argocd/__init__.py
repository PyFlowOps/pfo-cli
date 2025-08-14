import os
import json

BASE = os.path.dirname(os.path.abspath(__file__))
k8s_main = os.path.abspath(os.path.join(BASE, ".."))

from . import keys
from . import manifest
from . import tls

from .functions import install, update
from .functions import get_argocd_default_password as admin_password
from .functions import restart_argocd_server as restart_argocd
from .functions import wait_for_argocd_deployment as argocd_deployment_readiness
from .functions import wait_for_argocd_projects as project_readiness
from .functions import wait_for_argocd_server as argocd_server_wait
from .manifest import add_ssh_privkey_to_secret_manifest as add_ssh_key

keys.generate_ssh_keypair() # Generate SSH keypair for Kubernetes access, if not already present

if not keys.check_ssh_key_exists():
    keys.add_ssh_key_to_github()  # Add the SSH key to GitHub for Kubernetes access
