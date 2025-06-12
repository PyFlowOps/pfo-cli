"""
This module provides utilities for interacting with Kubernetes clusters (local only). This module is part of the pfo-cli package, and 
offers a method of standing up a Kind cluster for local development and testing purposes (easily).
"""
import click

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
    help=f"This registers the package to be managed by pfo",
)
@optgroup.option(
    "--delete",
    required=False,
    is_flag=True,
    help=f"This removes the package from pfo management",
)
@optgroup.option(
    "--update",
    required=False,
    is_flag=True,
    help=f"This bumps the version by a major release",
)
@optgroup.group(f"Kubernetes Cluster Data", help=f"Package versioning options")
@optgroup.option(
    "--info",
    required=False,
    is_flag=True,
    help=f"This is the version of the pfo managed package",
)

def k8s(**params: dict) -> None:
    """Functions applicable to package management, microservices and Docker images.

    This section will begin the process of creating a new package, updating the package (version), or releasing the package.
    """
    if params.get("create", False):
        print(params)

    if params.get("delete", False):
        print(params)
    
    if params.get("info", False):
        print(params)

    if params.get("update", False):
        print(params)

    print_help_msg(k8s)
