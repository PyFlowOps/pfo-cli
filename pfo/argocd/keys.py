import os
import subprocess

from halo import Halo

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ed25519
from cryptography.hazmat.backends import default_backend

_ssh_key_location: str = os.path.expanduser("~/.pfo/argocd")
_password: str|None = None
_keyspinner = Halo(spinner="dots", text_color="blue")

def get_pub_key() -> str:
    """
    Retrieves the public SSH key from the default location.
    
    Returns:
        str: The public SSH key as a string.
    """
    _keyspinner.start("Retrieving public SSH key...")
    ssh_key_location = os.path.join(os.path.expanduser("~"), ".pfo", "argocd")
    pub_key_path = os.path.join(ssh_key_location, "argocd_github.pub")
    
    if not os.path.exists(pub_key_path):
        _keyspinner.fail(f"Public SSH key not found at {pub_key_path}")
    
    with open(pub_key_path, "r") as pub_key_file:
        _data = pub_key_file.read()
        return pub_key_file.read().strip()  # Return the public key without extra whitespace
    
    _keyspinner.succeed("Public SSH key retrieved successfully.")
    return _data.strip()  # Return the public key without extra whitespace

def get_private_key() -> str:
    """
    Retrieves the private SSH key from the default location.
    
    Returns:
        str: The private SSH key as a string.
    """
    _keyspinner.start("Retrieving private SSH key...")
    ssh_key_location = os.path.join(os.path.expanduser("~"), ".pfo", "argocd")
    priv_key_path = os.path.join(ssh_key_location, "argocd_github")
    
    if not os.path.exists(priv_key_path):
        _keyspinner.fail(f"Private SSH key not found at {priv_key_path}")
    
    with open(priv_key_path, "r") as priv_key_file:
        _data = priv_key_file.read()
        return priv_key_file.read().strip()  # Return the private key without extra whitespace
    
    _keyspinner.succeed("Private SSH key retrieved successfully.")
    return _data.strip()  # Return the private key without extra whitespace

# This module is used to handle the SSH key creation that is to be used by ArgoCD to access the Git repositories.
# Will create the private and public keys in the ~/.pfo/argocd directory.
# Use these files to configure the ArgoCD SSH credentials - in Github this is done by adding the public key to the repository settings under Deploy Keys.
# The private key will be used by ArgoCD to authenticate with the Git repository.
def generate_ssh_keypair(private_key="argocd_github", public_key="argocd_github.pub", password=None) -> None:
    """
    Generates an RSA SSH keypair and saves them to specified files.

    Args:
        private_key_path (str): The file path for the private key.
        public_key_path (str): The file path for the public key.
        password (str, optional): A password to encrypt the private key. If None, the private key will not be encrypted.
    """
    os.makedirs(_ssh_key_location, exist_ok=True) # Ensure the directory exists

    _pkeypriv = os.path.join(_ssh_key_location, private_key)
    _pkeypub = os.path.join(_ssh_key_location, public_key)
    encryption_algorithm = serialization.NoEncryption()

    if os.path.isfile(_pkeypriv) or os.path.isfile(_pkeypub):
        #_keyspinner.info(f"SSH keypair already exists at {_ssh_key_location}...")
        return

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

    _keyspinner.succeed(f"SSH keypair generated successfully at {_ssh_key_location}.")

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
        _keyspinner.fail(f"Error running command {' '.join(_cmd)}: {e}")
        return False

    _data = [i.strip() for i in result.stdout.split("\t")] # Debugging line to see the output of the command
    for i in _data:
        if "argocd_github" in i:
            return True
    
    _keyspinner.fail(f"Cannot find the SSH key in the Github API. Please ensure you have the GitHub CLI installed, and the SSH Private Key ~/.pfo/argocd/argocd_github is in Github") 

    return False

def add_ssh_key_to_github():
    """
    Adds the SSH key to the Github account.
    """
    _keyspinner.start(text="Adding SSH key to Github")
    _cmd = ["gh", "ssh-key", "add", os.path.join(_ssh_key_location, "argocd_github.pub"), "--title", "argocd_github"]
    
    try:
        subprocess.run(_cmd, check=True)
        _keyspinner.succeed("SSH key added to Github successfully.")
    except subprocess.CalledProcessError as e:
        _keyspinner.fail(f"Error adding SSH key to Github: {e}")
        exit()
