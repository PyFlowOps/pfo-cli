# This file creates the TLS configuration for the Kind Kubernetes cluster if not already present.
import os
import json
import yaml
import base64
import datetime

from cryptography import x509
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from halo import Halo

def load_argocd_config():
    """
    Load the configuration file if it exists, otherwise return an empty dictionary.
    """
    if os.path.isfile(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as config_file:
            _data = json.load(config_file)
            return _data["argocd"]

    return {}

BASE = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE, "..", "k8s", "k8s_config.json")
_env = "pyops"
_data = load_argocd_config()  # Load the configuration data from the JSON file, specifically for ArgoCD.
_cert_file = os.path.expanduser(_data.get("tls_cert", ""))
_key_file =  os.path.expanduser(_data.get("tls_key", ""))

_tls_spinner = Halo(text_color="blue", spinner="dots")

def str_presenter(dumper, data):
    if '\n' in data:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

def check_tls_config_exists() -> bool:
    """
    Check if the TLS configuration for ArgoCD already exists.
    """
    if os.path.isfile(_cert_file) and os.path.exists(_key_file):
        return True

    return False

def clean():
    if os.path.exists(_cert_file):
        os.remove(_cert_file)

    if os.path.exists(_key_file):
        os.remove(_key_file)

def create_tls_config():
    """
    Create the TLS configuration for the Kind Kubernetes cluster if not already present.
    """
    if check_tls_config_exists():
        _tls_spinner.info("TLS configuration for ArgoCD already exists. Skipping creation.")
        return

    tls_dir = os.path.expanduser("~/.pfo/k8s")
    
    # Check if the TLS certificate and key already exist
    if not os.path.exists(tls_dir):
        os.makedirs(tls_dir)
        
    if not os.path.isfile(_cert_file) or not os.path.isfile(_key_file):
        clean() # Clean up any existing files if paths are not set
        
        _tls_spinner.start("Creating TLS configuration for ArgoCD...")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )

        # Create a certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, "argocd.pyflowops.local")
        ])
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(datetime.datetime.utcnow())
            .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
            .add_extension(
                x509.SubjectAlternativeName([x509.DNSName("argocd.pyflowops.local")]),
                critical=False
            )
            .sign(private_key, hashes.SHA256())
        )
        
        # Save the certificate and key to files
        with open(_key_file, "wb") as kf:
            kf.write(
                private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption()
                )
            )

        with open(_cert_file, "wb") as cf:
            cf.write(cert.public_bytes(serialization.Encoding.PEM))
        
        _tls_spinner.succeed("TLS configuration created.")
        
        return

def get_tls_cert_contents() -> str:
    """
    Get the TLS certificate for ArgoCD.
    
    Returns:
        str: The path to the TLS certificate file.
    """
    with open(_cert_file, "r") as cf:
        cert_data = cf.read()

    return cert_data.strip()

def get_tls_key_contents() -> str:
    """
    Get the TLS key for ArgoCD.
    
    Returns:
        str: The path to the TLS key file.
    """
    with open(_key_file, "r") as kf:
        key_data = kf.read()

    return key_data.strip()

def add_cert_data_to_secret():
    """
    Add the TLS certificate and key data to the ArgoCD secret.
    """
    _tls_spinner.start("Adding TLS certificate and key to ArgoCD secret...")

    try:
        _secret_yaml_file = _data.get("secret_manifest", f"~/.pfo/k8s/{_env}/overlays/argocd/argocd-ssl-certs.yaml")  # The name of the secret in Kubernetes

        # We need to get the contents of the secret manifest file.
        with open(os.path.expanduser(_secret_yaml_file), "r") as f:
            _secret_yaml = yaml.safe_load(f.read())

        yaml.add_representer(str, str_presenter)  # Ensure multiline strings are handled correctly

        # Here, we need to get the contents of the certificates, and the key - encode them in base64, and then create a Kubernetes secret.
        cert_data = get_tls_cert_contents()
        key_data = get_tls_key_contents()

        # Encode the cert and key in base64
        cert_b64 = base64.b64encode(cert_data.encode('utf-8'))
        key_b64 = base64.b64encode(key_data.encode('utf-8'))

        # We need to write the base64 encoded cert and key to the secret manifest file.
        _secret_yaml["data"]["tls.crt"] = cert_b64.decode('utf-8')  # Decode to string for YAML
        _secret_yaml["data"]["tls.key"] = key_b64.decode('utf-8')  # Decode to string for YAML

        with open(os.path.expanduser(_secret_yaml_file), "w") as _f:
            yaml.dump(_secret_yaml, _f, default_flow_style=False)

    except Exception as e:
        _tls_spinner.fail(f"Failed to add TLS certificate and key to ArgoCD secret: {e}")
        return

    _tls_spinner.succeed("TLS certificate and key added to ArgoCD secret.")
    return

def install():
    """
    Install the TLS configuration for ArgoCD.
    """
    _secret_yaml_file = _data.get("secret_manifest", f"~/.pfo/k8s/{_env}/overlays/argocd/argocd-ssl-certs.yaml")  # The name of the secret in Kubernetes

    if not check_tls_config_exists():
        create_tls_config() # Create the TLS configuration if it does not exist
    else:
        _tls_spinner.info("TLS configuration for ArgoCD already exists. Skipping installation.")

    with open(os.path.expanduser(_secret_yaml_file), "r") as f:
        _secret_yaml = yaml.safe_load(f.read())

    if (_secret_yaml["data"].get("tls.crt") == "") or (_secret_yaml["data"].get("tls.key") == ""):
        add_cert_data_to_secret()  # Add the certificate and key to the ArgoCD
    else:
        _tls_spinner.info("TLS certificate and key already present in the secret manifest. Skipping addition.")
