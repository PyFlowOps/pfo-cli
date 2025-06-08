import os
import subprocess

# import requests
from typing import Any

import click
from click_option_group import optgroup
from halo import Halo
from shared.commands import RepoGroup
from config import MetaData
from tools import assert_pfo_config_file, print_help_msg

import pfo_doppler
#from pfo_doppler.config import DopplerConfig, check_doppler_config_exists
#from pfo_doppler.project import DopplerProject, check_doppler_project_exists
from pfo_github.functions import (
    get_current_repo_github_environments,
    get_current_repo_name,
    repo_check,
    set_current_repo_github_environments,
    set_github_environments_for_new_repo,
)
from pfo_github.init import build_repo

__author__ = "Philip De Lorenzo"

# Let's get the information from the config.cfg file
metadata = MetaData()
config_data = metadata.config_data
spinner = Halo(text_color="blue", spinner="dots")


@click.group(cls=RepoGroup, invoke_without_command=True)
@click.pass_context # Recommended to add for accessing context
@optgroup.group(f"Github", help=f"Github Repo Operations.")
@optgroup.option(
    "--init",
    required=False,
    is_flag=True,
    help=f"This creates a repo based on the PyFlowOps template.",
)
@optgroup.option(
    "--set-github-environments",
    required=False,
    is_flag=True,
    help=f"This adds environments to a GitHub Repo, i.e. ~> dev|stg|prd.",
)
@optgroup.option(
    "--test",
    required=False,
    is_flag=True,
    help=f"This allows for user to run tests.",
)
def repo(ctx: click.Context, **params: dict) -> None:
    """This is the pfo Github repo builder, maintenance tool.

    This section will begin the process of creating a new github repo, and helping maintain it.
    """
    if not pfo_doppler._doppler:
        if not os.environ.get("GH_TOKEN"):
            spinner.fail(
                "If not using Doppler, you must set the GH_TOKEN environment variable to use this command."
            )
            exit()

    if params["init"]:
        # Let's get the owner of the repo from the user
        _accepted_owners = ["generic", "dev", "infra", "sre", "data"]
        _owner = click.prompt(
            f"Please enter the owner of the repo",
            type=click.Choice(
                ["generic", "dev", "infra", "sre", "data"], case_sensitive=False
            ),
            default="generic",
        )

        if _owner not in _accepted_owners:
            spinner.fail(
                f"Owner '{_owner}' is not accepted. Please use one of the following: {', '.join(_accepted_owners)}"
            )
            exit()

        # Let's get the repo name from the user -- this is a temp name, it will need to be cleaned
        _trepo_name = click.prompt(
            f"Please enter the project name",
            type=str,
            default="my_project",
        )

        _pn = f"{_owner}-apps"  # The doppler project name to use

        _repo_name = (
            _trepo_name.replace(" ", "-").replace("_", "-").lower()
        )  # Let's replace spaces, and underscores with dashes
        _final_repo_name = f"{_owner}-{_repo_name}"  # This is the final repo name, use this to create the repo

        # Let's set the repo name to the current directory name
        spinner.info(f"This will create the repo in GitHub: {_final_repo_name}")
        _value = click.prompt(
            f"Are you sure? y|n", type=str
        )  # This is a yes/no prompt - Confirm that this is what the user wants to do.

        if _value.lower() == "y":
            # Let's ensure that the Doppler project for the owner exists
            if pfo_doppler._doppler:
                if not pfo_doppler.check_doppler_project_exists(
                    project_name=_pn
                ):  # This will fail if the project does not exists
                    pfo_doppler.dop_project.create_doppler_project(project_name=_pn)

            build_repo(_final_repo_name)  # This will create the repo in GitHub

            # Let's ensure that the Doppler config doesn't already exist in the project
            # For the config name, we will use the repo name NOT the _final_repo_name -- the config
            # name will be the same as the repo name, but with the owner removed
            if pfo_doppler._doppler:
                if not pfo_doppler.check_doppler_config_exists(
                    project_name=_pn, config_name=_repo_name
                ):
                    pfo_doppler.dop_config.create_doppler_configs(
                        repo_name=_final_repo_name
                    )  # This will create the config in the project

                spinner.succeed("Repo Created!")
                ctx.exit(0)
            else:
                spinner.info("Initial Repo creation aborted.")
                ctx.exit(0)

    if params["set_github_environments"]:
        spinner.start("Setting up GitHub Environments...")
        # Let's get the owner of the repo from the user
        repo_check()  # This will check if the repo exists in the current directory

        # Let's ensure that there are no existing environments in the repo
        _envs: list = get_current_repo_github_environments(obj=get_current_repo_name())
        if _envs:
            spinner.fail(f"Environments already exist in the repo: {', '.join(_envs)}")
            spinner.info("Please remove the environments before continuing.")
            ctx.exit(0)

        set_current_repo_github_environments(obj=get_current_repo_name())
        spinner.succeed("GitHub Environments Success!")
        ctx.exit(0)

    if params["test"]:
        print("### UNDER CONSTRUCTION ###")
        print("This is the test section, add your code here to test the repo.")
        ctx.exit(0)

    click.echo(ctx.get_help())

    # This checks for a .pfo.json config file - analysis still needed to ensure this is a good function to have
    # if assert_pfo_config_file():
    #    pass
    # else:
    #    print_help_msg(repo)
