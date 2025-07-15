from . import keys
from . import manifest

keys.generate_ssh_keypair() # Generate SSH keypair for Kubernetes access, if not already present

if not keys.check_ssh_key_exists():
    keys.add_ssh_key_to_github()  # Add the SSH key to GitHub for Kubernetes access


from .functions import install
from .functions import get_argocd_default_password as admin_password
from .manifest import add_ssh_privkey_to_secret_manifest as add_ssh_key
