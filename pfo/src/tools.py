import os
import json
import platform
import shutil
import socket
import subprocess
import time
from typing import Any

import click
import git
from halo import Halo
from src.config import MetaData

metadata = MetaData()

spinner = Halo(text_color="blue", spinner="dots")


class IgnoreRequiredWithList(click.Group):
    def parse_args(self, ctx, args):
        _args_length = len(args)
        _list = (
            True if "--list" in args else False
        )  # Let's set a variable to use if list is passed in
        try:
            return super(IgnoreRequiredWithList, self).parse_args(ctx, args)

        except click.MissingParameter as exc:
            if not _list and _args_length > 0:
                raise
            elif _args_length == 0:
                # Remove the required params so that help can display
                for param in self.params:
                    param.required = False

                # Let's ensure that --list is in the args since it was passed in
                if "--help" not in args:
                    args.append("--help")
            else:
                # Remove the required params so that help can display
                for param in self.params:
                    param.required = False

                # Let's ensure that --list is in the args since it was passed in
                if "--list" not in args:
                    args.append("--list")

            return super(IgnoreRequiredWithList, self).parse_args(ctx, args)


# docstrings
def docstrings(*sub):
    """Returns a docstring that substitutes values."""

    def dec(obj):
        obj.__doc__ = obj.__doc__.format(*sub)
        return obj

    return dec


def print_help_msg(command: Any) -> None:
    """Prints a help message if there is no options or arguments passed into the cli.entry_point()."""
    with click.Context(command) as ctx:
        click.echo(command.get_help(ctx))


def remove_dir_contents(folder) -> None:
    """Empties the contents of a directory passed in."""
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            pfo_log(msg=f"Failed to delete {file_path}. Reason: {e}", level="error")


def pfo_log(msg: str, level: str = "info") -> None:
    """Writes a message to the console."""
    level = level.upper()
    click.echo(f"pfo - [{level}] - {msg}")


### Deprecate ###
def assert_pfo_config_file() -> bool:
    """This function asserts that the required directories are present.

    If the directories are not present, then they will be created.

    """
    if "pfo.json" not in os.listdir(os.getcwd()):
        return False

    return True


def register() -> None:
    """This function registers the package to be managed by pfo."""
    if assert_pfo_config_file():
        spinner.warn("This package is already registered with pfo.")
        # TODO: Add a prompt to ask if the user wants to update the package data
        exit()

    # Let's initialize the git repository
    _path_to_root = subprocess.run(
        ["git", "rev-parse", "--show-cdup"],
        stdout=subprocess.PIPE,
        universal_newlines=True,
    ).stdout.strip()

    _package_path = subprocess.run(
        ["git", "rev-parse", "--show-prefix"],
        stdout=subprocess.PIPE,
        universal_newlines=True,
    ).stdout.strip()
    
    # If the output is essentially nothing, then we are at the root of the repository
    if (not _package_path) or (_package_path == "") or (_package_path == "\n"):
        _package_path = "."

    if (_path_to_root != "") or (_path_to_root != "\n") or (_path_to_root != None):
        _root = os.path.abspath(os.path.join(os.getcwd(), _path_to_root.strip()))
    else:
        _root = os.path.abspath(os.getcwd())

    _name = os.path.basename(os.path.join(_root, _package_path)) if not os.path.isdir(".git") else os.path.basename(os.getcwd())
    _path = os.path.abspath(os.getcwd())
    _base_version = metadata.base_version

    # Let's get github information for the package
    repo = git.Repo(_root)
    __r = repo.config_reader()

    try:
        _user_name = __r.get_value("user", "name")
    except:
        spinner.warn("Cannot pull the user from the git config file...")
        _user_name = None

    try:
        _user_email = __r.get_value("user", "email")
    except:
        spinner.warn("Cannot pull the email from the git config file...")
        _user_email = None

    _remote = repo.remotes.origin  # Let's get the remote origin URL

    # Let's write the data to the .pfo file
    _pfo_file = os.path.join(_path, metadata.pfo_json_file)
    _data = {
        "name": _name,
        "package_path": _package_path,
        "repo": _remote.url,
        "version": _base_version,
    }  # Base data instatiation

    # Let's add user data to the registration - who was the actor that registered the package
    _data["registrant"] = {}
    _data["registrant"]["user"] = _user_name
    _data["registrant"]["email"] = _user_email

    # We need to add a docker section to the registration
    _data["docker"] = {}

    # This will create a dict with the folder name as the key and the path to the dockerfile as the value
    # Example: Within the /docker folder of the project, there are two folders: app1 and app2
    # This will create a dict like this:
    # {
    #   "app1": {
    #       "base_path": "docker",
    #       "image": "app1",
    #       "repo_path": "docker/app1",
    #       "dockerfile": "Dockerfile"
    #   },
    #   "app2": {
    #       "base_path": "docker",
    #       "image": "app2",
    #       "repo_path": "docker/app2",
    #       "dockerfile": "Dockerfile"
    #   }
    # }
    # If the docker folder does not exist, it will not add anything to the docker section. docker: {}
    if os.path.exists(os.path.join(_path, "docker")):
        for _name in os.listdir(os.path.join(_path, "docker")):
            if os.path.isdir(os.path.join(_path, "docker", _name)):
                _data["docker"][_name] = {}
                _data["docker"][_name]["base_path"] = "docker"
                _data["docker"][_name]["image"] = f"{_name}"
                _data["docker"][_name]["repo_path"] = f"docker/{_name}"

                if os.path.exists(os.path.join(_path, "docker", _name, "Dockerfile")):
                    _data["docker"][_name]["dockerfile"] = "Dockerfile"
                else:
                    spinner.warn(
                        f"No Dockerfile found in docker/{_name}, defaulting to 'Dockerfile' for the dockerfile name."
                    )
                    _data["docker"][_name]["dockerfile"] = None

    # Let's add the kubernetes data to the registration
    _data["k8s"] = {}
    _data["k8s"]["name"] = _name
    _data["k8s"]["labels"] = {}
    _data["k8s"]["labels"]["app.kubernetes.io/name"] = _name
    _data["k8s"]["deploy"] = False  # Default to not deploy

    _json_data = json.dumps(_data, indent=2)
    with open(_pfo_file, "w") as file:
        file.write(_json_data)
        file.write("\n")


def deregister() -> None:
    """This function removes the package from pfo management."""
    _path = os.path.abspath(os.getcwd())
    _file = os.path.join(_path, metadata.pfo_json_file)

    if os.path.exists(_file):
        os.remove(_file)
    else:
        spinner.info(
            f"This package -- {os.path.basename(_path)} -- is not currently registered with pfo."
        )
        exit()


def bump_version(type: str) -> None:
    """This function bumps the version of the package.

    Args:
        type (str): The type of version bump to perform. (major, minor, patch)
    """
    # Let's get github information for the package
    _path = os.path.abspath(os.getcwd())
    repo = git.Repo(_path)
    __r = repo.config_reader()

    try:
        _user_name = __r.get_value("user", "name")
    except:
        spinner.warn("Cannot pull the user from the git config file...")
        _user_name = None

    try:
        _user_email = __r.get_value("user", "email")
    except:
        spinner.warn("Cannot pull the email from the git config file...")
        _user_email = None

    _remote = repo.remotes.origin  # Let's get the remote origin URL

    with open(metadata.pfo_json_file, "r") as file:
        _data = json.load(file)

    _version = _data["version"]
    _version_augment = list(map(int, _version.split(".")))

    # To augment the version, we need to increase the version by 1
    # Major is at index 0, Minor is at index 1, and Patch is at index 2
    # When augmenting the version, we need to reset the lower indexes to 0
    if type == "major":
        _version_augment[0] += 1
        _version_augment[1] = 0
        _version_augment[2] = 0
    elif type == "minor":
        _version_augment[1] += 1
        _version_augment[2] = 0
    elif type == "patch":
        _version_augment[2] += 1

    spinner.info(
        f"Version augmented from {_version} to {'.'.join(map(str, _version_augment))}"
    )
    _data["version"] = ".".join(map(str, _version_augment))

    # Let's write the data to the .pfo file
    _pfo_file = os.path.join(os.getcwd(), metadata.pfo_json_file)

    # Let's add the change user, email, and date to the registration
    _data["changelog"] = {}
    _data["changelog"]["user"] = _user_name
    _data["changelog"]["email"] = _user_email
    _data["changelog"]["date"] = time.strftime("%Y-%m-%d %H:%M:%S")

    _json_data = json.dumps(_data, indent=2)
    with open(_pfo_file, "w") as file:
        file.write(_json_data)


def mac_only() -> None:
    """This function checks if the system is running on MacOS."""
    if platform.system() == "Darwin":
        return True
    else:
        return False


def network_check() -> None:
    """Returns True if there is a network connection, false otherwise."""
    # Let's check if there is a network connection becuase we need one for the CLI

    net = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    net.settimeout(5.0)

    try:
        net.connect(("google.com", 80))
    except socket.error as e:
        spinner.fail(f"Network connection error: {e} - The CLI needs a network connection.")
        exit()
