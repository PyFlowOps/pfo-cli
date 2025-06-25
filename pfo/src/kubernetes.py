"""
This module provides utilities for interacting with Kubernetes clusters (local only). This module is part of the pfo-cli package, and 
offers a method of standing up a Kind cluster for local development and testing purposes (easily).
"""
import click
import gnupg
import os
import json
import time
import docker
import subprocess
import shutil
import base64
import yaml

from cookiecutter.main import cookiecutter
from typing import Any
from git import Repo
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
    help=f"Deletes the Kubernetes cluster (Kind) and all associated resources in the local namespace",
)
@optgroup.option(
    "--delete-all",
    required=False,
    is_flag=True,
    help=f"Deletes all Kubernetes (Kind) clusters and all associated resources",
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
        
        # This logic block will allow the user to select the environment for the Kind cluster
        # Currently, local is the only supported environment, but this can be extended in the future
        # _environment = click.prompt(
        #     "Select the environment for the Kind cluster",
        #     type=click.Choice(["local", "dev", "stg", "prd"], case_sensitive=False),
        #     default="local"
        # )

        cluster = Cluster(env="local")
        cluster.create() # Create the Kind cluster
        exit()

    if params.get("delete", False):
        # Deletes the Kind cluster and all associated resources in the local namespace
        Cluster.delete()

    if params.get("delete_all", False):
        # Deletes all Kind clusters and associated resources
        Cluster.delete_all()
    
    if params.get("info", False):
        Cluster.cluster_info()

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
        self._k8s_dir: str = os.path.join(metadata.rootdir, "k8s") # Directory for the Kubernetes manifests
        self._kind_config: str = os.path.join(self._k8s_dir, "kind-config.yaml")
        self._repos_with_pfo: dict[str, Any] = {} # Dictionary to hold repos with pfo.json configs
        self.epoch_tag: str = str(time.time()).split(".")[0] # Epoch timestamp for tagging resources

    @property
    def repo_owner(self) -> str|None:
        try:
            res = subprocess.run(["gh", "repo", "view", "--json", "owner"], capture_output=True, text=True, check=True).stdout # This is a json string output
        except subprocess.CalledProcessError as e:
            spinner.fail(f"Failed to get repo owner: {e}")
        
        return json.loads(res)["owner"]["login"] if res else None
    
    def create(self) -> None:
        """Creates the Kubernetes cluster."""
        _cspin = Halo(text_color="blue", spinner="dots")
        if self.__cluster_exists() is False: # Check if the Kind cluster already exists
            _cspin.start(f"Creating Kind cluster {self.env}...\n\n")
            self.__create_cluster() # Create the Kind cluster
            self.__cluster_info() # Get the Kind cluster info
            _cspin.succeed(f"Kind cluster {self.env} created successfully!")
        else:
            _cspin.info(f"Kind cluster {self.env} already exists. Use --update to update the cluster.")

        self.update() # Update the Kind cluster
        self.__set_context() # Set the Kind cluster context
    
    @staticmethod
    @Halo(text="Deleting Kind Cluster...\n\n", spinner="dots")
    def delete_all() -> None:
        """Deletes the Kubernetes cluster."""
        _cmd = ["kind get clusters | xargs -t -n1 kind delete cluster --name"]
        try:
            subprocess.run(_cmd, shell=True, check=True, capture_output=True, text=True)
            spinner.succeed("All Kind clusters deleted successfully!")
        except subprocess.CalledProcessError as e:
            spinner.fail(f"Failed to delete Kind clusters: {e}")
            return

    @staticmethod
    @Halo(text="Deleting Kind Cluster - local Namespace...\n\n", spinner="dots")
    def delete() -> None:
        """Deletes the Kubernetes cluster."""
        _cmd = ["kind delete cluster --name local"]
        try:
            subprocess.run(_cmd, shell=True, check=True, capture_output=True, text=True)
            spinner.succeed("All Kind clusters deleted successfully!")
        except subprocess.CalledProcessError as e:
            spinner.fail(f"Failed to delete Kind clusters: {e}")
            return
    
    @staticmethod
    def cluster_info() -> None:
        print("\n") # This is here for a line break in the console output
        try:
            res = subprocess.run(["kubectl", "cluster-info", "--context", f"kind-local"], check=True)
        except subprocess.CalledProcessError as e:
            spinner.fail(f"Failed to retrieve Kind cluster info: {e}")
            return

        print("\n") # This is here for a line break in the console output

    @Halo(text="Updating Kind Cluster...\n\n", spinner="dots")
    def update(self) -> None:
        """Updates the Kubernetes cluster."""
        _owner = self.repo_owner
        if not _owner:
            spinner.fail("Cannot continue updating the Kubernetes cluster.")
            return
        
        Halo(text_color="blue", spinner="dots").info(f"Retrieving repository data from GitHub for Org: {_owner}")
        _repos: list|None = self.__current_repo_list(owner=_owner) # Get the current repo list for the owner
        # Let's get any repo in the Org that has a pfo.json config file in the root directory
        if not _repos:
            spinner.info("No repositories found for the organization.")
            return

        # Will we augment the self._repos_with_pfo dictionary with the repo name as the key and the pfo.json content as the value
        # self._repos_with_pfo data population; {repo_name: pfo.json content}
        # Now let's iterate through the repos and get the pfo.json config file if it exists
        for repo in _repos:
            self.__get_pfo_configs_for_repo(owner=_owner, repo=repo)

        # Now we will create/update the base Kubernetes manifests for the project
        self.set_configs_and_manifests()

        # For each repo in the self._repos_with_pfo dictionary, we will apply the manifests to the Kind cluster
        # The pfo.json config file will have a "k8s" key, that will contain a subkey "deploy" which is a boolean value.
        # If true, we will need to get the docker image of the microservice from the "docker" key in the pfo.json config file.
        for repo, pfo_config in self._repos_with_pfo.items():
            # If we have a docker image to build in the repo, this logic block will be entered and handle building the image and applying the manifests
            if pfo_config.get("docker", {}):
                if pfo_config["docker"] == {}:
                    spinner.info(f"No docker image(s) found for repo {repo}. Skipping...")
                    continue

                # Let's clone the repo to a temporary directory
                repo_url = f"https://github.com/{_owner}/{repo}.git" # Construct the repo URL
                local_path = os.path.join(self.temp, repo)

                # Clone the repo to the temporary directory
                self.__clone_repo(
                    repo_url=repo_url,
                    local_path=local_path
                )
            
                # Let's build the docker images for the repo
                self.__build_and_load_docker_images(pfo_config=pfo_config)

                # If we have a k8s deploy key set to true, we will apply the manifests to the Kind cluster
                if pfo_config.get("k8s", {}).get("deploy", False):
                    _kustomize_config = yaml.safe_load(open(os.path.join(self._k8s_dir, self.env, "kustomization.yaml")))
                    with open(os.path.join(self._k8s_dir, self.env, "kustomization.yaml"), "r") as kf:
                        # Since the deploy key is true, we will add the docker image to the kustomization.yaml file
                        _kdata = yaml.safe_load(kf)
                    
                    # Let's augment the kustomization.yaml file with the docker image
                    for _iname, idata in pfo_config["docker"].items():
                        #_kdata["images"].append({"name": pfo_config["docker"][_iname]["image"], "newName": f"{pfo_config['docker'][_iname]['image'].split('/')[-1]}", "newTag": self.env})
                        _kdata["images"].append(
                            {
                                "name": pfo_config["docker"][_iname]["image"],
                                "newName": f"{pfo_config['docker'][_iname]['image']}",
                                "newTag": self.env
                            }
                        )

                    # Now we will write the kustomization.yaml file back to the disk
                    with open(os.path.join(self._k8s_dir, self.env, "kustomization.yaml"), "w") as kf:
                        yaml.dump(_kdata, kf, default_flow_style=False)
            else:
                spinner.warn(f"No docker image(s) found for repo {repo}. Skipping...")

        # Now we will build the Kubernetes manifests using kustomize and apply them to the Kind cluster
        self.kustomize_build() # Build the Kubernetes manifests using kustomize and apply them

        spinner.succeed("Kind cluster updated successfully!")

    # UNDER CONSTRUCTION
    def info(self) -> None:
        """Displays information about the Kubernetes cluster."""
        print("Displaying information about the Kubernetes cluster...")

    ### Manifests creation/update methods
    def set_configs_and_manifests(self) -> None:
        """Gets the Kubernetes config and manifests for the project.
        
        This function gets the data from the k8s_installs git repository in PyFlowOps, which contains the base Kubernetes manifests and configurations.
        It will clone the repository to a temporary directory and create the necessary Kubernetes namespace for the project.
        """
        k8s_remote = "https://github.com/pyflowops/k8s-installs.git"

        if os.path.exists(os.path.join(metadata.rootdir, "k8s")):
            shutil.rmtree(os.path.join(metadata.rootdir, "k8s"))  # Remove the existing k8s directory

        try:
            cookiecutter(
                k8s_remote,
                checkout="main",
                directory="kind-cluster",
                no_input=True,
                extra_context={
                    "namespace": self.env
                },
                output_dir=os.path.join(metadata.rootdir),
            )
        except Exception as e:
            spinner.fail(f"Failed to create Kubernetes manifests: {e}")
            return

    def run_command(self, cmd: list) -> None:
        try:
            res = subprocess.run(
                cmd,
                check=True,
                shell=True,
                capture_output=True,
                text=True
            )
            if res.returncode == 0:
                pass
            else:
                spinner.fail(f"Command {cmd} failed!")
                spinner.fail(f"ERROR -  {res.stderr}")
        except subprocess.CalledProcessError as e:
            spinner.fail(f"Command {cmd} failed!")
            spinner.fail(f"ERROR -  {e}")

    def kustomize_build(self) -> None:
        _cmd = [f"kustomize build {os.path.join(metadata.rootdir, "k8s", self.env)} | kubectl apply -f -"]
        self.run_command(_cmd) # Builds the Kubernetes manifests using kustomize and applies them to the cluster

    def __load_image(self, image_name: str, nodes: str) -> None:
        """Loads a Docker image from the local filesystem to the kind cluster.
        
        Args:
            image_name (str): The name of the Docker image to load.
            nodes (str): The list of worker nodes to load the image to, separated by commas (e.g., "node1,node2").
        """
        # ONLY *:local images can be loaded into Kind clusters, so we will use the local tag
        if image_name.endswith(":local"):
            _cmd = [f"kind load docker-image {image_name} --name {self.env} --nodes {nodes} -v 5"]
            self.run_command(cmd=_cmd) # Run the command to load the Docker image
            return
        
        spinner.info(f"Only images with the ':local' tag can be loaded into Kind clusters. - disregarding tag: {image_name.split(':')[-1]}")

    def __clone_repo(self, repo_url: str, local_path: str) -> None:
        """Clones the repository to the local path."""
        # Let's clone the repo to a temporary directory
        _repo_name = repo_url.split("/")[-1].replace(".git", "")  # Get the repo name from the URL
        local_path = os.path.join(self.temp, _repo_name)

        if os.path.exists(local_path):
            shutil.rmtree(local_path)  # Remove the existing repo directory

        # Clone the repo to the temporary directory
        try:
            Repo.clone_from(repo_url, local_path)
        except Exception as e:
            spinner.fail(f"Error: {e}")

    def __build_and_load_docker_images(self, pfo_config: Any) -> None:
        # Now we need to get the docker image from the repo - it should now be cloned to /tmp/.pfo/<repo>
        # We need to get the artifact (docker image) for this project and add it to the manifest(s)
        client = self.__docker_connection()
        _version = pfo_config.get("version", "latest")

        if not client:
            spinner.fail("Docker client connection failed. Cannot build images.")
            return
        
        # Build phase
        for _, _img_data in pfo_config["docker"].items():
            try:
                # In order to build the Documentation site for your PyFlowOps project, there is some preliminary code that needs to be run
                if pfo_config.get("name", None) == "documentation":
                    _pip_cmd = [metadata.python_pip, "install", "-r", os.path.join(self.temp, pfo_config["name"], "requirements.txt")]
                    _pipresp = subprocess.run(
                        _pip_cmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    if _pipresp.returncode != 0:
                        spinner.fail(f"Error installing requirements: {_resp.stderr}")
                        return
                    
                    _pycmd = [metadata.python_executable, os.path.join(self.temp, pfo_config["name"], "scripts", "build-docs-src.py")]
                    _resp = subprocess.run(
                        _pycmd,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                
                    if _resp.returncode != 0:
                        spinner.fail(f"Error building documentation source: {_resp.stderr}")
                        return

                image, build_logs = client.images.build(
                    path=os.path.join(self.temp, pfo_config["name"]),
                    dockerfile=str(os.path.join(self.temp, pfo_config["name"], _img_data["repo_path"], _img_data["dockerfile"])),
                    tag=f"{_img_data['image']}:local",
                    rm=True,
                    pull=True
                )
                _img = client.images.get(f"{_img_data['image']}:local")
                _img.tag(f"{_img_data['image']}:{_version}") # Tag the image with the version

                spinner.succeed(f"Docker image {_img_data['image']}:local built successfully!")
            except Exception as e:
                spinner.fail(f"Error: {e}")

        # Load phase
        for _, _img_data in pfo_config["docker"].items():
            try:
                _wkrs = subprocess.run(["kind", "get", "nodes", "--name", self.env], capture_output=True, text=True, check=True)
                _wknodes = ','.join([i for i in _wkrs.stdout.strip().split("\n") if "control-plane" not in i]) # Get the list of worker nodes, convert to a comma-separated string

                if _wkrs.returncode != 0:
                    spinner.fail(f"Error getting Kind nodes: {_wkrs.stderr}")
                    return

                self.__load_image(image_name=f"{_img_data['image']}:local", nodes=_wknodes)  # Load the image to the Kind cluster
                spinner.succeed(f"Docker image {_img_data['image']}:local loaded successfully!")
            except Exception as e:
                spinner.fail(f"Error: {e}")

    def __cluster_exists(self) -> bool:
        """Checks if the Kubernetes cluster is running."""
        try:
            res = subprocess.run(["kind", "get", "clusters"], capture_output=True, text=True, check=True)
            if self.env in res.stdout:
                return True
        except subprocess.CalledProcessError as e:
            spinner.fail(f"Error checking Kind cluster: {e}")
            return False
        
        return False

    def __create_cluster(self) -> None:
        if not os.path.exists(self._kind_config):
            spinner.fail(f"Kind config file not found at {self._kind_config}. Please ensure it exists.")
            return
        
        try:
            res = subprocess.run(["kind", "create", "cluster", "--config", self._kind_config, "--name", self.env], check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e:
            spinner.fail(f"Failed to create Kind cluster: {e}")
            return
        
        if res.returncode == 0:
            spinner.succeed("Kind cluster created successfully!")
        else:
            spinner.fail("Failed to create Kind cluster.")

    def __cluster_info(self) -> None:
        print("\n") # This is here for a line break in the console output
        try:
            res = subprocess.run(["kubectl", "cluster-info", "--context", f"kind-{self.env}"], check=True)
        except subprocess.CalledProcessError as e:
            spinner.fail(f"Failed to retrieve Kind cluster info: {e}")
            return
        print("\n")
        
    def __set_context(self) -> None:
        res = subprocess.run(["kubectl", "config", "set-context", "--current", f"--namespace={self.env}"], check=True, capture_output=True, text=True)
        if res.returncode == 0:
            spinner.succeed("Kind cluster context set successfully!")
        else:
            spinner.fail("Failed to set Kind cluster context.")
    
    def __docker_connection(self) -> docker.DockerClient|None:
        """Returns a Docker client connection."""
    
        # Check if Docker socket exists
        if os.path.exists("/var/run/docker.sock"):
            socket_path = '/var/run/docker.sock'
        
        if os.path.exists(os.path.expanduser("~/.docker/run/docker.sock")):
            socket_path = os.path.expanduser("~/.docker/run/docker.sock")
        
        if not os.path.exists(socket_path):
            spinner.warn(f"Docker socket not found at {socket_path}")
            spinner.warn("This usually means Docker isn't running")
            exit()
        
        # Try to connect to Docker
        try:
            client = docker.DockerClient(base_url=f"unix://{socket_path}")
            client.ping()
            return client
        except FileNotFoundError:
            spinner.warn("Docker daemon not running or not accessible")
            spinner.warn("  Solutions:")
            spinner.warn("  - Start Docker Desktop (Windows/Mac)")
            spinner.warn("  - Run 'sudo systemctl start docker' (Linux)")
            spinner.warn("  - Check if Docker is installed")
            return None
        except Exception as e:
            spinner.fail(f"Unexpected error: {e}")
            return None
    
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
            return None


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
