import os
import yaml
import subprocess

from halo import Halo


_manspinner = Halo(spinner="dots", text_color="blue")
_private_ssh_key: str = os.path.join(os.path.expanduser("~"), ".pfo", "argocd", "argocd_github")
_public_ssh_key: str = os.path.join(os.path.expanduser("~"), ".pfo", "argocd", "argocd_github.pub")
_manifest_path: str = os.path.join(os.path.expanduser("~"), ".pfo", "k8s", "local", "overlays", "argocd")
_secret_manifests = [os.path.join(_manifest_path, i) for i in os.listdir(_manifest_path) if "secret" in i and i.endswith(".yaml")]

# Read the private SSH key contents
with open(_private_ssh_key, "r") as f:
    _priv_contents = f.read().strip().strip("\n")

def add_ssh_privkey_to_secret_manifest() -> None:
    """Adds the SSH private key to the ArgoCD secret.
    
    The pfo CLI tool uses ArgoCD to manage Kubernetes resources, and this function
    is responsible for adding the SSH private key to the ArgoCD secret. This is necessary
    for ArgoCD to authenticate with Git repositories that require SSH access.

    The pfo CLI creates the SSH key pair in the `~/.pfo/argocd` directory, and this function
    reads the private key from that location and adds it to the ArgoCD secret.

    Args:
        manifest (dict): The manifest dictionary containing the ArgoCD configuration (dict from yaml.safe_load()s)

    """
    _manspinner.start("Adding SSH private key to ArgoCD secret manifests...")
    if len(_secret_manifests) == 0:
        _manspinner.fail("No secret manifests found in the specified path. Please ensure you have created the necessary secret manifests.")
        return
    
    for manifest in _secret_manifests:
        with open(manifest, "r") as f:
            _mdata = yaml.safe_load(f.read())

        yaml.add_representer(str, str_presenter)  # Ensure multiline strings are handled correctly

        if _mdata.get("kind", None) != "Secret":
            _manspinner.fail(f"The manifest {manifest} is named as a secret but not of kind Secret. Skipping...")
            continue

        if _mdata.get("stringData", None).get("sshPrivateKey", None):
            _mdata["stringData"]["sshPrivateKey"] = f"""{_priv_contents.strip("\n")}"""
            with open(manifest, "w") as f:
                yaml.dump(_mdata, f, default_flow_style=False)
            _manspinner.succeed(f"SSH private key added to {manifest}")
        _manspinner.stop()

def str_presenter(dumper, data):
    if '\n' in data:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)
