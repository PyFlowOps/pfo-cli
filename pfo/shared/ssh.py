# This module is used to handle the SSH key creation that is to be used by ArgoCD to access the Git repositories.
# Will create the private and public keys in the ~/.pfo/argocd directory.
# Use these files to configure the ArgoCD SSH credentials - in Github this is done by adding the public key to the repository settings under Deploy Keys.
# The private key will be used by ArgoCD to authenticate with the Git repository.
import os
import subprocess

from halo import Halo
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.backends import default_backend

_ssh_key_location: str = os.path.expanduser("~/.pfo/argocd")
_password: str|None = None
_sshspinner = Halo(text="Generating SSH keypair", spinner="dots")

def generate_ssh_keypair(private_key="argocd_github", public_key="argocd_github.pub", password=None):
    """
    Generates an RSA SSH keypair and saves them to specified files.

    Args:
        private_key_path (str): The file path for the private key.
        public_key_path (str): The file path for the public key.
        password (str, optional): A password to encrypt the private key. If None, the private key will not be encrypted.
    """
    _sshspinner.start()
    os.makedirs(_ssh_key_location, exist_ok=True)  # Ensure the directory exists

    _pkeypriv = os.path.join(_ssh_key_location, private_key)
    _pkeypub = os.path.join(_ssh_key_location, public_key)
    encryption_algorithm = serialization.NoEncryption()

    if os.path.isfile(_pkeypriv) or os.path.isfile(_pkeypub):
        _sshspinner.fail(f"SSH key files already exist at {_ssh_key_location}. Please remove them before generating new keys.")
        exit()

    # Generate a new RSA private key
    private_key = ed25519.Ed25519PrivateKey.generate()

    # Derive the public key from the private key
    public_key = private_key.public_key()

    # --- Save the Private Key ---
    encoding = serialization.Encoding.PEM
    format = serialization.PrivateFormat.OpenSSH # OpenSSH format for private key
    encryption_algorithm = serialization.NoEncryption()

    if password:
        # If a password is provided, encrypt the private key
        encryption_algorithm = serialization.BestAvailableEncryption(password.encode('utf-8'))

    with open(_pkeypriv, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=encoding,
            format=format,
            encryption_algorithm=encryption_algorithm
        ))

    # Set appropriate permissions for the private key (read-only for owner)
    os.chmod(_pkeypriv, 0o600)

    # --- Save the Public Key ---
    with open(_pkeypub, "wb") as f:
        f.write(public_key.public_bytes(
            encoding=serialization.Encoding.OpenSSH, # OpenSSH format for public key
            format=serialization.PublicFormat.OpenSSH
        ) + b"\n")

    _sshspinner.succeed(f"SSH keypair generated successfully at {_ssh_key_location}.")
    exit()

def check_ssh_key_exists():
    """
    Checks the Github api for the SSH key. If the key exists, it will return True.
    If the key does not exist, it will return False.

    Returns:
        bool: True if the SSH key exists, False otherwise.
    """
    _cmd = ["gh", "ssh-key", "list"]
    try:
        result = subprocess.run(_cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        _sshspinner.fail(f"Error running command {' '.join(_cmd)}: {e}")
        return False

    _data = [i.strip() for i in result.stdout.split("\t")] # Debugging line to see the output of the command
    for i in _data:
        if "argocd_github" in i:
            return True
    
    _sshspinner.fail(f"Cannot find the SSH key in the Github API. Please ensure you have the GitHub CLI installed, and the SSH Private Key ~/.pfo/argocd/argocd_github is in Github") 

    return False

def add_ssh_key_to_github():
    """
    Adds the SSH key to the Github account.
    """
    _sshspinner.start(text="Adding SSH key to Github")
    _cmd = ["gh", "ssh-key", "add", os.path.join(_ssh_key_location, "argocd_github.pub"), "--title", "argocd_github"]
    
    try:
        subprocess.run(_cmd, check=True)
        _sshspinner.succeed("SSH key added to Github successfully.")
    except subprocess.CalledProcessError as e:
        _sshspinner.fail(f"Error adding SSH key to Github: {e}")
        exit()
