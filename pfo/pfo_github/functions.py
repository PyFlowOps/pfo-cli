"""
This is the pfo Github repo builder, maintenance tool.

This section will begin the process of creating a new github repo, and helping maintain it.
This is so that repos can be created with Github Actions, pipelines, linting, and other tools already in place.

This tools will create the repo, the environments for GCP integrations and a subsequent, respective project in Doppler.
"""

import json
import os
import shutil
import subprocess
import time

import git
from halo import Halo
from config import MetaData
from pfo_doppler import _doppler

# In the pfo_doppler package, the __init__ module has an attribute named _doppler: bool 
# If _doppler is set to true, then we will import the dop_project module.
if _doppler:
    from pfo_doppler import dop_project

metadata = MetaData()
config_data = metadata.config_data

spinner = Halo(text_color="blue", spinner="dots")


def get_gh_token() -> str:
    """This function gets the gh_token from the Doppler environment.

    Raises:
        Exception: If the Doppler token is not set in the environment.
    """
    if _doppler:
        results = dop_project.doppler.secrets.get(
            project="pfo", config="cli", name="GH_TOKEN"
        )
        gh_token = vars(results)["value"]["raw"].strip()
    else:
        gh_token = os.environ.get("GH_TOKEN", None)
    
    return gh_token


def set_main_branch():
    """This function sets the main branch for the project."""
    subprocess.run(["git", "config", "--global", "init.defaultBranch", "main"])
    spinner.info("Main branch set to 'main'")


def init_repo(repo: str) -> None:
    """This function initializes the repo."""
    if not os.path.exists(repo):
        os.makedirs(repo, exist_ok=True)

    subprocess.run(
        ["git", "init"],
        cwd=repo,
    )


def github_auth(gh_token: str) -> None:
    """This function authenticates to Github."""
    try:
        subprocess.run(
            ["gh", "auth", "login", "--with-token"],
            input=gh_token,
            text=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    except Exception as e:
        spinner.stop()
        spinner.fail(f"Failed to authenticate to Github: {e}")
        exit()


def _get_github_teams() -> list[dict]:
    """This function gets the github teams for the organization.

    Returns:
        list[dict]: The github teams for the organization - only the teams which name startswith `mnscpd-`.
    """
    try:
        r = subprocess.run(
            ["gh", "api", f"/orgs/{metadata._github_org}/teams"], capture_output=True
        )
    except Exception as e:
        spinner.stop()
        spinner.fail(f"Failed to get the github teams: {e}")
        exit()

    _return_data = [
        i
        for i in json.loads(r.stdout.decode("utf-8"))
        if i["name"].startswith("mnscpd-")
    ]
    return _return_data


def _get_gcp_project_name(owner: str) -> str:
    if owner == "dev":
        return None

    if owner == "generic":
        return None

    return None


def create_repo(repo_name: str) -> None:
    """This function creates the repo."""
    team_affiliation = {
        "generic": "sre-internal"
    }  # Needs work - see get_github_teams()
    _team = ""
    _cmd = [
        "gh",
        "repo",
        "create",
        "--private",
        f"{metadata._github_org}/{repo_name}",
        "--template",
        f"{metadata._github_org}/{metadata._template_repo}",
        "--clone",
        "--disable-wiki",
        "--disable-issues",
    ]
    try:
        subprocess.run(_cmd, check=True)
    except Exception as e:
        spinner.stop()
        spinner.fail(f"Failed to create the repo: {e}")
        exit()


# Let's offer a function to create the environments for the repo in GitHub
def set_github_environments_for_new_repo(obj: str) -> None:
    """This function creates the GitHub environments for the repo.

    Args:
        obj (str): The final repo name. i.e. {owner}-{repo_name}

    These environments have respective projects in GCP.
    """
    _owner = obj.split("-")[0]  # Get the owner from the repo name
    envs = ["dev", "stg", "prd"]
    _env_url = (
        f"/repos/{metadata._github_org}/{obj}/environments"  # env will be /environment
    )
    _gcp_project = _get_gcp_project_name(owner=_owner)

    if _owner == "mnscpd":
        for _e in envs:
            if _e == "prd":
                _env = "production"

            if _e == "stg":
                _env = "staging"

            if _e == "dev":
                _env = "development"

            _environment_api_url = f"{_env_url}/{_env}"
            try:
                subprocess.run(
                    [
                        "gh",
                        "api",
                        "--method",
                        "PUT",
                        "-H",
                        "Accept: application/vnd.github.v3+json",
                        _environment_api_url,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                spinner.fail(f"Failed to create the github environment: {e}")

            spinner.succeed(f"Created the github environment: {_env}")

        return

    if _gcp_project:
        for _e in envs:
            _environment_api_url = f"{_env_url}/{_gcp_project}-{_e}"
            try:
                subprocess.run(
                    [
                        "gh",
                        "api",
                        "--method",
                        "PUT",
                        "-H",
                        "Accept: application/vnd.github.v3+json",
                        _environment_api_url,
                    ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception as e:
                spinner.fail(f"Failed to create the github environment: {e}")

            spinner.succeed(f"Created the github environment: {_gcp_project}-{_e}")
    else:
        spinner.info(f"This application does not require a GCP project.")


def repo_check():
    """This function checks if the repo exists."""
    try:
        subprocess.run(
            ["gh", "repo", "view", "--json", "name"],
            check=True,
            stderr=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError:
        spinner.stop()
        spinner.fail(
            "This directory is not a GitHub repo, please run this command from within a GitHub repo."
        )
        exit()


def get_current_repo_name() -> str:
    """This function gets the current repo name."""
    try:
        res = subprocess.run(
            ["gh", "repo", "view", "--json", "name"], capture_output=True
        )
    except subprocess.CalledProcessError:
        spinner.stop()
        spinner.fail(
            "This directory is not a GitHub repo, please run this command from within a GitHub repo."
        )
        exit()

    return json.loads(res.stdout.decode("utf-8"))[
        "name"
    ]  # This will return the repo name


def get_current_repo_github_environments(obj: str) -> list[str]:
    """This function gets the current repo environments."""
    url = f"/repos/{metadata._github_org}/{obj}/environments"
    try:
        res = subprocess.run(["gh", "api", f"{url}"], capture_output=True)
    except subprocess.CalledProcessError:
        spinner.stop()
        spinner.fail(
            "This directory is not a GitHub repo, please run this command from within a GitHub repo."
        )
        exit()

    _json_data = json.loads(res.stdout.decode("utf-8"))
    _envs = [i["name"] for i in _json_data["environments"]]
    return _envs  # This will return the repo name


def set_current_repo_github_environments(obj: str) -> None:
    """This function sets the current repo github environments."""
    _envs = get_current_repo_github_environments(obj=obj)
    if _envs:
        spinner.info(f"Environments already exist in the repo: {', '.join(_envs)}")
        spinner.info("Please remove the environments before continuing.")
        exit()

    # Let's create the environments
    _envs_to_create = ["development", "staging", "production"]

    _env_url = (
        f"/repos/{metadata._github_org}/{obj}/environments"  # env will be /environment
    )
    for _e in _envs_to_create:
        _environment_api_url = f"{_env_url}/{_e}"
        try:
            subprocess.run(
                [
                    "gh",
                    "api",
                    "--method",
                    "PUT",
                    "-H",
                    "Accept: application/vnd.github.v3+json",
                    _environment_api_url,
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except Exception as e:
            spinner.fail(f"Failed to create the github environment: {e}")

        spinner.succeed(f"Created the github environment: {_e}")


def get_latest_cli_release_version() -> str:
    """This function gets the latest release version of pfo from GitHub.

    Returns:
        str: The latest release version of pfo. --> digits only v2.4.3 == 2.4.3
    """
    try:
        res = subprocess.run(
            [
                "gh",
                "release",
                "view",
                "--repo",
                "PyFlowOps/pfo-cli",
                "--json",
                "tagName",
            ],
            capture_output=True,
        )
    except subprocess.CalledProcessError:
        spinner.fail(
            "This directory is not a GitHub repo, please run this command from within a GitHub repo."
        )
        exit()

    _ret = res.stdout.decode("utf-8")

    if ("release not found" in _ret) or (_ret == ""):
        spinner.warn("No releases found for pfo-cli.")
        exit()

    return json.loads(res.stdout.decode("utf-8"))["tagName"].lstrip(
        "v"
    )  # This will return the latest release versions
