import os
import json
import subprocess
from typing import Any

import click

# import requests
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
@optgroup.group(f"Registration", help=f"Package registration")
@optgroup.option(
    "--register",
    required=False,
    is_flag=True,
    help=f"This registers the package to be managed by pfo",
)
@optgroup.option(
    "--deregister",
    required=False,
    is_flag=True,
    help=f"This removes the package from pfo management",
)
@optgroup.group(f"Versioning", help=f"Package versioning options")
@optgroup.option(
    "--version",
    required=False,
    is_flag=True,
    help=f"This is the version of the pfo managed package",
)
@optgroup.option(
    "--major",
    required=False,
    is_flag=True,
    help=f"This bumps the version by a major release",
)
@optgroup.option(
    "--minor",
    required=False,
    is_flag=True,
    help=f"This bumps the version by a minor release",
)
@optgroup.option(
    "--patch",
    required=False,
    is_flag=True,
    help=f"This bumps the version by a patch release",
)
def package(**params: dict) -> None:
    """Functions applicable to package management, microservices and Docker images.

    This section will begin the process of creating a new package, updating the package (version), or releasing the package.
    """
    if params["register"]:
        _value = click.prompt(f"Are you sure? y|n", type=str)
        if _value.lower() == "y":
            # Run the degregistration code here
            register()
            spinner.succeed("Package registered!")
        else:
            spinner.info("Registration aborted.")
            exit()

        exit()  # To be removed later when functions are working

    if params["deregister"]:
        _value = click.prompt(f"Are you sure? y|n", type=str)
        if _value.lower() == "y":
            # Run the degregistration code here
            deregister()
            spinner.succeed("Package deregistered!")
        else:
            spinner.info("Deregistration aborted.")
            exit()

        exit()  # To be removed later when functions are working

    if assert_pfo_config_file():
        if params["version"]:
            _pfo_file_data = os.path.join(os.getcwd(), "pfo.json")
            with open(_pfo_file_data, "r") as f:
                data = json.load(f)
                version = data["version"]
            
            print(version)
            exit()

        if params["major"]:
            bump_version(type="major")
            spinner.succeed("Major version augmented...")
            exit()
        elif params["minor"]:
            bump_version(type="minor")
            spinner.succeed("Minor version augmented...")
            exit()
        elif params["patch"]:
            bump_version(type="patch")
            spinner.succeed("Patch version augmented...")
            exit()
        else:
            print_help_msg(package)
    else:
        print_help_msg(package)
        spinner.fail(
            "If this is a package that needs to be versioned by pfo, then you need to run `pfo package --register` from the package directory."
        )
