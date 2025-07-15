#!/usr/bin/python3
#
# Copyright (C) 2025, PyFlowOps, Inc.
#
# pfo can not be copied and/or distributed without the express
# permission of PyFlowOps, Inc.
#
__name__ = "pfo"
__author__ = "Philip De Lorenzo"

import collections
import os
import shutil
import sys

import click

# Settings
_imp = os.path.dirname(__file__)
sys.path.append(_imp)

from halo import Halo
from src import config
from src.tools import docstrings, mac_only, network_check

# We want to ensure a network connection before any of the Doppler functions run
# The following imports require a network connection - this is for better messaging
network_check()

from pfo.shared.commands import update_cli
from src.github import repo
from src.package import package
from src.kubernetes import k8s
from applications import app

global metadata
metadata = config.MetaData()
spinner = Halo(text_color="blue", spinner="dots")

# We want to ensure that the pfo-cli tool has all of the required directories and files
@Halo(text="Loading database, directories, and files...\n", spinner="dots")
def check_for_required_directories_and_files():
    if not os.path.exists(metadata.rootdir):
        os.makedirs(metadata.rootdir)

    # We need to ensure that the CLI .env exists
    if not os.path.isfile(metadata.cli_env):
        shutil.copyfile(os.path.join(metadata.config_path, ".env.example"), metadata.cli_env)


class OptionGroup(click.Option):
    """Customizing the default click option"""

    def list_options(self, ctx: click.Context):
        """Sorts options in the specified order"""
        # By default, click alphabetically sorts options
        # This method will override that feature
        return self.opts.keys()


# This class ensures the order of the groups below you can control
class OrderedGroup(click.Group):
    def __init__(self, name=None, commands=None, **attrs):
        super(OrderedGroup, self).__init__(name, commands, **attrs)
        #: the registered subcommands by their exported names.
        self.commands = commands or collections.OrderedDict()

    def list_commands(self, ctx):
        return self.commands


# IMPORTANT: This directory structure is required for the CLI to work properly
if not mac_only():
    spinner.fail(
        "This CLI is only supported on MacOS. Please use the CLI on a MacOS machine."
    )
    exit()

check_for_required_directories_and_files() # Ensure the required directories and files are present

### CLI
@click.group(cls=OrderedGroup, invoke_without_command=True)
@click.option(
    "--update",
    "update",
    default=False,
    is_flag=True,
    help="Update the CLI to the latest version.",
)
@click.version_option(package_name=metadata._name)
@docstrings(metadata._name)
@click.pass_context
def cli(ctx, **params: dict) -> None:
    """{0} CLI tool"""
    if params["update"] == True:
        update_cli()
        exit()

    # If there is nothing passed to the CLI, print the help message
    if (params["update"] == False) and (
        click.get_current_context().invoked_subcommand is None
    ):
        click.echo(click.get_current_context().get_help())

cli.add_command(package)
cli.add_command(repo)
cli.add_command(app)
cli.add_command(k8s)

if __name__ == "__main__":
    cli()
