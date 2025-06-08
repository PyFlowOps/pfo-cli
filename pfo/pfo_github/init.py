"""
This is the pfo Github repo builder, maintenance tool.

This section will begin the process of creating a new github repo, and helping maintain it.
This is so that repos can be created with Github Actions, pipelines, linting, and other tools already in place.

This tools will create the repo, the environments for GCP integrations and a subsequent, respective project in Doppler.
"""

#import json
import os
#import shutil
#import subprocess
import time

#import git
from halo import Halo
from config import MetaData
from pfo_github.functions import (
    create_repo,
    get_gh_token,
    github_auth,
    set_github_environments_for_new_repo,
    set_main_branch,
)

metadata = MetaData()
config_data = metadata.config_data
spinner = Halo(text_color="blue", spinner="dots")

@Halo(text="Building your repo...\n", spinner="dots")
def build_repo(repo_name: str) -> None:
    """This function builds the repo based on the PyFlowOps template."""
    gh_token = get_gh_token()  # Get the Github token from Doppler

    # Let's auth to github
    github_auth(gh_token=gh_token)

    # Let's set the main branch to 'main'
    set_main_branch()

    # Create the repo
    if os.path.exists(os.path.join(os.getcwd(), repo_name)):
        spinner.stop()
        spinner.fail(
            "Repo already exists. Please use a different name for your project..."
        )
        exit()

    # Let's create the repo
    # We want to create the repo in the current directory with base repo automation predetermined
    # This repo will be created based on the template -- @pyflowops/base-repo-template
    create_repo(repo_name=repo_name)  # This will create the repo using the gh cli

    time.sleep(1)  # Let's give it a second to create the repo

    # Let's create the repo environments
    set_github_environments_for_new_repo(obj=repo_name)

    # Origin URL
    origin_url = f"https://github.com/{metadata._github_org}/{repo_name}.git"
