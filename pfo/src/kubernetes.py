"""
This module provides utilities for interacting with Kubernetes clusters (local only). This module is part of the pfo-cli package, and 
offers a method of standing up a Kind cluster for local development and testing purposes (easily).
"""
import click
import gnupg
import os

from typing import Any
from click_option_group import optgroup
from halo import Halo

from shared.commands import DefaultCommandGroup
from src.config import MetaData

from src.tools import (
    assert_pfo_config_file,
    bump_version,
    deregister,
    print_help_msg,
    register,
)


__author__ = "Philip De Lorenzo"

# Let's get the information from the config.cfg file
metadata = MetaData()
config_data = metadata.config_data
spinner = Halo(text_color="blue", spinner="dots")


@click.group(cls=DefaultCommandGroup, invoke_without_command=True)
@optgroup.group(f"Kubernetes CRUD Commands", help=f"Kubnernetes (Kind) cluster administration")
@optgroup.option(
    "--create",
    required=False,
    is_flag=True,
    help=f"Creates the Kubernetes cluster (Kind) with the latest manifests",
)
@optgroup.option(
    "--delete",
    required=False,
    is_flag=True,
    help=f"Deletes the Kubernetes cluster (Kind) and all associated resources",
)
@optgroup.option(
    "--update",
    required=False,
    is_flag=True,
    help=f"This updates the Kubernetes cluster (Kind) to the latest manifests",
)
@optgroup.group(f"Kubernetes Cluster Data", help=f"Kubnernetes (Kind) cluster information")
@optgroup.option(
    "--info",
    required=False,
    is_flag=True,
    help=f"Displays information about the current Kubernetes cluster (Kind)",
)

def k8s(**params: dict) -> None:
    """Functions applicable to package management, microservices and Docker images.

    This section will begin the process of creating a new package, updating the package (version), or releasing the package.
    """
    if params.get("create", False):
        create_keys() # Create the encryption keys for the project - ~/.pfo/keys/pfo.pub and ~/.pfo/keys/pfo
        exit()

    if params.get("delete", False):
        print(params)
    
    if params.get("info", False):
        print(params)

    if params.get("update", False):
        print(params)

    if not any(params.values()):
        print_help_msg(k8s)


@Halo(text="Creating Encryption Keys...\n", spinner="dots")
def create_keys():
    """This function creates the encryption keys for the project."""
    # Let's create the encryption directory if it doesn't exist
    create_enc_directory() # Create the encryption directory, ~/.pfo/keys
    _ecryption_dir = os.path.join(os.path.expanduser("~"), ".pfo", "keys")

    params = {
        "key_type": "RSA",
        "key_length": 4096,
        "subkey_type": "RSA",
        "subkey_length": 4096,
        "name_real": "pfo-cli",
        "name_comment": "GPG Keys for pfo-cli",
        "name_email": "pfo.application",
        "expire_date": 0,
        "no_protection": True,
    }

    gpg = gnupg.GPG(gnupghome=os.path.join(os.path.expanduser("~"), ".pfo", "keys"))

    input_data = gpg.gen_key_input(**params)
    key = gpg.gen_key(input_data)

    if key.fingerprint:
        Halo(text_color="blue", spinner="dots").info(f"Generated Key Fingerprint: {key.fingerprint}")
    else:
        Halo(text_color="blue", spinner="dots").fail("Key generation failed!")

    _public_key_file = os.path.join(
        _ecryption_dir, f"pfo.pub"
    )
    _private_key_file = os.path.join(
        _ecryption_dir, "pfo"
    )
    public_key = gpg.export_keys(key.fingerprint, armor=True)
    private_key = gpg.export_keys(
        key.fingerprint, armor=True, secret=True, expect_passphrase=False
    )

    with open(_public_key_file, "w") as pub_file:
        pub_file.write(public_key)

    with open(_private_key_file, "w") as priv_file:
        priv_file.write(private_key)

def create_enc_directory():
    """Creates the encryption directory for the project."""
    _home = os.path.join(os.path.expanduser("~"), ".pfo")
    _keys = os.path.join(_home, "keys")
    if not os.path.exists(_keys):
        os.makedirs(_keys)
