import argparse
import json
import logging
import os
import subprocess

import pytoml
from icecream import ic
from pythonjsonlogger.json import JsonFormatter

# Basic configuration for logging
logging.basicConfig(
    level=logging.INFO,  # Set the logging level to INFO
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Define log message format
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

handler = logging.StreamHandler()
handler.setFormatter(JsonFormatter())

logger.addHandler(handler)
# End of basic configuration for logging

parser = argparse.ArgumentParser(description="Get the versions for the project.")
parser.add_argument(
    "--debug", action="store_true", default=False, help="Sets debugging output"
)
parser.add_argument(
    "--draft", action="store_true", help="The draft release version in the repository"
)
parser.add_argument(
    "--prerelease", action="store_true", help="The prerelease version in the repository"
)
parser.add_argument(
    "--latest",
    action="store_true",
    help="The latest release versions in the repository",
)
parser.add_argument(
    "--toml", action="store_true", help="The version to set in pyproject.toml"
)
parser.add_argument(
    "--draft_release",
    action="store_true",
    help="The new draft release version to set in the repository",
)
args = parser.parse_args()

# This sets debugging based on the flag passed in
if args.debug:
    ic.enable()
else:
    ic.disable()


def prechecks(obj: list[dict]) -> bool:
    """
    This function will run some prechecks to make sure that the data is correct.

    Args:
        obj (list[dict]): The data from the repository -- get_repo_data().

    This function will check the following:
    1. If there is a draft release, it must be higher than both the latest release, and any pre-releases.

    Returns:
        bool: True if the data is correct, False otherwise.

    """
    ic("Running Prechecks...")  # Debugging

    _draftrelease = get_draft_release_version(obj=obj)
    _prerelease = get_prerelease_version(obj=obj)
    _latest = get_latest_version(obj=obj)
    _toml = get_toml_version()

    ic("Releases found in the repoistory")
    ic(f"Draft-Release: {_draftrelease}")
    ic(f"Pre-Release: {_prerelease}")
    ic(f"Latest Release: {_latest}")
    ic(f"Version Toml: {_toml}")

    # Let's run this logic block if there is NO draft release found
    if not _draftrelease:
        # We need to make sure that the new draft version is higher than the any current pre-releases, or published releases
        # If this current toml_version is higher than the latest release, AND any current pre-releases, then we can use this as the draft version
        ic("No Draft Release Found")

        # If there is a latest release, then the pre-release must be greater than the latest release
        if _latest:
            if not _toml.split(".") > _latest.lstrip("v").split("."):
                raise Exception(
                    "The toml version must be greater than the latest version."
                )

            if _prerelease:
                if not _prerelease.split(".") > _latest.lstrip("v").split("."):
                    raise Exception(
                        "The pre-release version should be greater than the latest version."
                    )

                if not _toml.split(".") > _prerelease.lstrip("v").split("."):
                    raise Exception(
                        "The toml version must be greater than the pre-release."
                    )

            ic(f"Latest Release: Pass!")

        else:
            if _prerelease:
                # Since there is no latest release (this will be the first release), and no new draft release, the pre-release must be equal to the version in pyproject.toml
                if not _toml.split(".") > _prerelease.lstrip("v").split("."):
                    raise Exception(
                        "The toml version must be greater than the pre-release."
                    )

            ic(f"Pre-Release: Pass!")
    else:
        if _latest:
            # If there is a draft release, then the draft release must be greater than the latest release
            if _prerelease:
                # With ALSO a prerelease, then draft release must be greater than the prerelease
                # Pre-release must be greater than the latest release
                if not _draftrelease.lstrip("v").split(".") > _prerelease.lstrip(
                    "v"
                ).split("."):
                    raise Exception(
                        "The version of the draft release must be greater than the prerelease version."
                    )

                if not _prerelease.lstrip("v").split(".") > _latest.lstrip("v").split(
                    "."
                ):
                    raise Exception(
                        "The pre-release version should be greater than the latest version."
                    )
            else:
                if not _draftrelease.lstrip("v").split(".") > _latest.lstrip("v").split(
                    "."
                ):
                    raise Exception(
                        "The version of the draft release must be greater than the latest version."
                    )

        else:
            if _prerelease:
                if not _draftrelease.lstrip("v").split(".") > _prerelease.lstrip(
                    "v"
                ).split("."):
                    raise Exception(
                        "The version of the draft release must be greater than the prerelease version."
                    )

        # If there's a draft release, it must be the same as the toml version
        if not _draftrelease.lstrip("v").split(".") == _toml.split("."):
            raise Exception(
                "The draft release version must be the same in pyproject.toml."
            )

        ic(f"Draft Release: Pass!")


def get_repo_data() -> list[dict]:
    # Get the directory of the current repo
    _cmd = [
        "gh",
        "release",
        "list",
        "--json",
        "isLatest,isDraft,createdAt,isPrerelease,name,tagName,publishedAt",
    ]
    _data = subprocess.run(_cmd, capture_output=True, text=True, check=True)

    if _data.returncode != 0:
        raise Exception(f"Error: {_data.stderr.strip()}")

    return json.loads(_data.stdout)


def get_toml_version() -> str:
    """
    Reads the version from pyproject.toml.

    Returns:
        str: The version from pyproject.toml. (#.#.#)
    """
    # Construct the path to pyproject.toml
    pyproject_path = os.path.join(os.getcwd(), "pyproject.toml")

    # Check if the file exists
    if not os.path.exists(pyproject_path):
        raise FileNotFoundError(f"pyproject.toml not found in {os.getcwd()}")

    with open(pyproject_path, "r") as f:
        pyproject_data = pytoml.load(f)

    assert (
        pyproject_data["project"]["version"] != None
    ), "The version in pyproject.toml should not be None."
    assert (
        pyproject_data["project"]["version"] != ""
    ), "The version in pyproject.toml should not be empty."

    return pyproject_data["project"]["version"]


def get_draft_release_version(obj: list[dict]) -> str:
    """
    Reads the latest draft release from the repository.

    Args:
        obj (list[dict]): The data from the repository -- get_repo_data().

    Returns:
        str: The draft release version. (json.dumps(_cmd.stdout.strip()))
    """
    # Get the directory of the current repo
    _draftrelease = [i["tagName"] for i in obj if i["isDraft"] == True]
    assert (
        len(_draftrelease) <= 1
    ), "There's more than one draft release registering, this cannot be so. Please check the Draft Releases!s."

    ic(f"Draft-Release: {_draftrelease}")  # Debugging
    return _draftrelease[0] if _draftrelease else None


def get_latest_version(obj: list[dict]) -> str:
    """
    Reads the latest version from the repository.

    Args:
        obj (list[dict]): The data from the repository -- get_repo_data().

    Returns:
        str: The latest version. (json.dumps(_cmd.stdout.strip()))
    """
    # Get the directory of the current repo
    _latest = [i["tagName"] for i in obj if i["isLatest"] == True]
    assert len(_latest) <= 1, "There should only be one latest release, if any at all."

    ic(f"Latest Release: {_latest}")  # Debugging
    return _latest[0] if _latest else None


def get_prerelease_version(obj: list[dict]) -> str:
    """
    Reads the latest prerelease from the repository.

    Args:
        obj (list[dict]): The data from the repository -- get_repo_data().

    Returns:
        str: The prerelease version. (json.dumps(_cmd.stdout.strip()))
    """
    # Get the directory of the current repo
    _prerelease = [i["tagName"] for i in obj if i["isPrerelease"] == True]
    assert len(_prerelease) <= 1, "There should only be one prerelease, if any at all."

    ic(f"Pre-Release: {_prerelease}")  # Debugging
    return _prerelease[0] if _prerelease else None


def draft_release(obj: list[dict]) -> str:
    """
    Reads the version from the draft release.

    Returns:
        str: The version from the draft release. (#.#.#)
    """
    ic(f"JSON Data: {obj}")  # Debugging

    prechecks(
        obj=obj
    )  # Run some prechecks to make sure that the data is correct, this will raise an exception if the data is incorrect

    return f"v{get_toml_version()}"


if __name__ == "__main__":
    if args.toml:
        print(get_toml_version())

    if args.latest:
        obj = (
            get_repo_data()
        )  # This is a list of dictionaries from JSON format (json.loads())
        print(get_latest_version(obj=obj))

    if args.prerelease:
        obj = (
            get_repo_data()
        )  # This is a list of dictionaries from JSON format (json.loads())
        print(get_prerelease_version(obj=obj))

    if args.draft:
        obj = (
            get_repo_data()
        )  # This is a list of dictionaries from JSON format (json.loads())
        print(get_draft_release_version(obj=obj))

    if args.draft_release:
        obj = (
            get_repo_data()
        )  # This is a list of dictionaries from JSON format (json.loads())
        print(draft_release(obj=obj))
