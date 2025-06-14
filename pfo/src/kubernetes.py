"""
This module provides utilities for interacting with Kubernetes clusters (local only). This module is part of the pfo-cli package, and 
offers a method of standing up a Kind cluster for local development and testing purposes (easily).
"""
import click
import gnupg
import os
import json
import time
import subprocess
import base64

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
    _pubkey = os.path.join(os.path.expanduser("~"), ".pfo", "keys", "pfo.pub")
    _privkey = os.path.join(os.path.expanduser("~"), ".pfo", "keys", "pfo")
    
    if params.get("create", False):
        if not os.path.exists(_pubkey) or not os.path.exists(_privkey):
            create_keys() # Create the encryption keys for the project - ~/.pfo/keys/pfo.pub and ~/.pfo/keys/pfo
        
        _environment = click.prompt(
            "Select the environment for the Kind cluster",
            type=click.Choice(["local", "dev", "stg", "prd"], case_sensitive=False),
            default="local"
        )

        create_kind_cluster(env=_environment) # Create the Kind cluster for local development
        exit()

    if params.get("delete", False):
        print(params)
    
    if params.get("info", False):
        print(params)

    if params.get("update", False):
        cluster = Cluster(env="local")
        cluster.update()
        exit()

    if not any(params.values()):
        print_help_msg(k8s)


class Cluster():
    """Class for managing Kubernetes clusters (Kind)."""
    def __init__(self, env: str = "local") -> None:
        self.env: str = env
        self.temp: str = "/tmp/.pfo"
        self._k8s_dir: str = os.path.join(metadata.rootdir, "k8s")
        self._kind_config: str = os.path.join(self._k8s_dir, "kind-config.yaml")
        self._repos_with_pfo: dict[str, Any] = {} # Dictionary to hold repos with pfo.json configs
        self.epoch_tag: str = str(time.time()).split(".")[0] # Epoch timestamp for tagging resources

    @Halo(text="Creating Kind Cluster...\n", spinner="dots")
    def create(self) -> None:
        """Creates the Kubernetes cluster."""
        self.__ccluster() # Create the Kind cluster
        self.__cluster_info() # Get the Kind cluster info
        self.update() # Update the Kind cluster
        self.__set_context() # Set the Kind cluster context

    def delete(self) -> None:
        """Deletes the Kubernetes cluster."""
        print("Deleting the Kubernetes cluster...")

    @Halo(text="Updating Kind Cluster...\n", spinner="dots")
    def update(self) -> None:
        """Updates the Kubernetes cluster."""
        _owner = self.repo_owner
        if not _owner:
            spinner.fail("Cannot continue updating the Kubernetes cluster.")
            return
        
        Halo(text_color="blue", spinner="dots").info(f"Getting repository data from GitHub for Org: {_owner}")
        _repos: list|None = self.__current_repo_list(owner=_owner) # Get the current repo list for the owner
        # Let's get any repo in the Org that has a pfo.json config file in the root directory
        if not _repos:
            spinner.fail("No repositories found for the organization.")
            return

        # Now let's iterate through the repos and get the pfo.json config file if it exists
        # Will we augment the self._repos_with_pfo dictionary with the repo name as the key and the pfo.json content as the value
        for repo in _repos:
            self.__get_pfo_configs_for_repo(owner=_owner, repo=repo)

        # For each repo in the self._repos_with_pfo dictionary, we will apply the manifests to the Kind cluster
        # The pfo.json config file will have a "k8s" key, that will contain a subkey "deploy" which is a boolean value.
        # If true, we will need to get the docker image of the microservice from the "docker" key in the pfo.json config file.
        for repo, pfo_config in self._repos_with_pfo.items():
            if pfo_config.get("k8s", {}).get("deploy", False):
                # We need to get the artifact (docker image) for this project and add it to the manifest(s)
                pass # TODO: Implement the logic to get the docker image and apply the manifests to the Kind cluster

        spinner.succeed("Kind cluster updated successfully!")


    def info(self) -> None:
        """Displays information about the Kubernetes cluster."""
        print("Displaying information about the Kubernetes cluster...")

    def __ccluster(self) -> None:
        res = subprocess.run(["kind", "create", "cluster", "--config", self._kind_config, "--name", self.env], check=True)
        if res.returncode == 0:
            spinner.succeed("Kind cluster created successfully!")
        else:
            spinner.fail("Failed to create Kind cluster.")

    def __cluster_info(self) -> None:
        res = subprocess.run(["kubectl", "cluster-info", "--context", f"kind-{self.env}"], check=True)
        if res.returncode == 0:
            spinner.succeed("Kind cluster info retrieved successfully!")
        else:
            spinner.fail("Failed to retrieve Kind cluster info.")
        
    def __set_context(self) -> None:
        res = subprocess.run(["kubectl", "config", "use-context", "--current", f"--namespace={self.env}"], check=True)
        if res.returncode == 0:
            spinner.succeed("Kind cluster context set successfully!")
        else:
            spinner.fail("Failed to set Kind cluster context.")
    
    @property
    def repo_owner(self) -> str|None:
        try:
            res = subprocess.run(["gh", "repo", "view", "--json", "owner"], capture_output=True, text=True, check=True).stdout # This is a json string output
        except subprocess.CalledProcessError as e:
            spinner.fail(f"Failed to get repo owner: {e}")
        
        return json.loads(res)["owner"]["login"] if res else None
    
    def __current_repo_list(self, owner: str) -> list|None:
        res = subprocess.run(["gh", "repo", "list", owner, "--json", "name"], capture_output=True, text=True, check=True)
        if res.returncode == 0:
            repos = [i["name"] for i in json.loads(res.stdout)] #json.loads(res.stdout)
        else:
            spinner.fail("Failed to get repos for the org.")
        
        return repos if repos else None
    
    def __get_pfo_configs_for_repo(self, owner: str, repo: str) -> dict|None:
        try:
            res = subprocess.run(["gh", "api", f"/repos/{owner}/{repo}/contents/pfo.json"], capture_output=True, text=True, check=True)
            if res.returncode == 0:
                b64_content = json.loads(res.stdout)["content"]
                pfo_content = json.loads(base64.b64decode(b64_content).decode("utf-8"))
                self._repos_with_pfo.update({repo: pfo_content})
        except subprocess.CalledProcessError:
            pass


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

@Halo(text="Creating Kind Cluster...\n", spinner="dots")
def create_kind_cluster(env: str = "local") -> None:
    """Creates a Kind cluster for local development."""
    # Let's run our scripts that automate the creation of the Kind cluster
    _k8s_dir = os.path.join(metadata.rootdir, "k8s")
    _kind_config = os.path.join(_k8s_dir, "kind-config.yaml")
    _create_script = os.path.join(_k8s_dir, "create_cluster.sh")

    try:
        subprocess.run(["bash", "-l", _create_script, env], check=True)
        spinner.succeed("Kind cluster created successfully!")
    except subprocess.CalledProcessError as e:
        spinner.fail(f"Failed to create Kind cluster: {e}")
