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
    "--pfo", action="store_true", help="The version to set in pfo.json"
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

def _version_check(version: str) -> bool:
    """
    Checks if the version is in the correct format.

    Args:
        version (str): The version to check.

    Returns:
        bool: True if the version is in the correct format, False otherwise.
    """
    if not isinstance(version, str):
        return False

    parts = version.lstrip("v").split(".")
    if len(parts) != 3:
        return False

    return all(part.isdigit() for part in parts)

def version_tuple(v):
    return tuple(map(int, v.lstrip("v").split(".")))

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
    _toml = get_toml_version() if os.path.isfile(os.path.join(os.getcwd(), "pyproject.toml")) else None
    _pfo = get_pfo_version() if os.path.isfile(os.path.join(os.getcwd(), "pfo.json")) else None

    ic("Releases found in the repoistory")
    ic(f"Draft-Release: {_draftrelease}")
    ic(f"Pre-Release: {_prerelease}")
    ic(f"Latest Release: {_latest}")
    ic(f"Version Toml: {_toml}")
    ic(f"Version PFO: {_pfo}")

    # Let's run this logic block if there is NO draft release found
    if _toml is None and _pfo is None:
        raise Exception(
            "There must be a version in either pyproject.toml or pfo.json to set the draft release."
        )

    if not _draftrelease:
        # We need to make sure that the new draft version is higher than the any current pre-releases, or published releases
        # If this current toml_version is higher than the latest release, AND any current pre-releases, then we can use this as the draft version
        ic("No Draft Release Found")

        # If there is a latest release, then the pre-release must be greater than the latest release
        if _latest:
            if _toml:
                if not version_tuple(_toml) > version_tuple(_latest):
                    raise Exception(
                        "The toml version must be greater than the latest version."
                    )
            if _pfo:

                if not version_tuple(_pfo) > version_tuple(_latest):
                    raise Exception(
                        "The pfo version must be greater than the latest version."
                    )

            if _prerelease:
                if not version_tuple(_prerelease) > version_tuple(_latest):
                    raise Exception(
                        "The pre-release version should be greater than the latest version."
                    )
                if _toml:
                    if not version_tuple(_toml) > version_tuple(_prerelease):
                        raise Exception(
                            "The toml version must be greater than the pre-release."
                        )
                if _pfo:
                    if not version_tuple(_pfo) > version_tuple(_prerelease):
                        raise Exception(
                            "The pfo version must be greater than the pre-release."
                        )

            ic(f"Latest Release: Pass!")

        else:
            if _prerelease:
                # Since there is no latest release (this will be the first release), and no new draft release, the pre-release must be equal to the version in pyproject.toml
                if _toml:
                    if not _toml.split(".") > _prerelease.lstrip("v").split("."):
                        raise Exception(
                            "The toml version must be greater than the pre-release."
                        )
                if _pfo:
                    if not _pfo.split(".") > _prerelease.lstrip("v").split("."):
                        raise Exception(
                            "The pfo version must be greater than the pre-release."
                        )

            ic(f"Pre-Release: Pass!")
    else:
        if _latest:
            # If there is a draft release, then the draft release must be greater than the latest release
            if _prerelease:
                # With ALSO a prerelease, then draft release must be greater than the prerelease
                # Pre-release must be greater than the latest release
                if not version_tuple(_draftrelease) > version_tuple(_prerelease):
                    raise Exception(
                        "The version of the draft release must be greater than the prerelease version."
                    )

                if not version_tuple(_prerelease) > version_tuple(_latest):
                    raise Exception(
                        "The pre-release version should be greater than the latest version."
                    )
            else:
                if not version_tuple(_draftrelease) > version_tuple(_latest):
                    raise Exception(
                        "The version of the draft release must be greater than the latest version."
                    )

        else:
            if _prerelease:
                if not version_tuple(_draftrelease) > version_tuple(_prerelease):
                    raise Exception(
                        "The version of the draft release must be greater than the prerelease version."
                    )

        # If there's a draft release, it must be the same as the toml version
        if _toml:
            if not version_tuple(_draftrelease) == version_tuple(_toml):
                raise Exception(
                    "The draft release version must be the same in pyproject.toml."
                )
        if _pfo:
            if not version_tuple(_draftrelease) == version_tuple(_pfo):
                raise Exception(
                    "The draft release version must be the same in pfo.json."
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
        pyproject_data["tool"]["poetry"]["version"] != None
    ), "The version in pyproject.toml should not be None."
    assert (
        pyproject_data["tool"]["poetry"]["version"] != ""
    ), "The version in pyproject.toml should not be empty."

    return pyproject_data["tool"]["poetry"]["version"]


def get_pfo_version() -> str:
    """
    Reads the version from pfo.json.

    Returns:
        str: The version from pfo.json. (#.#.#)
    """
    # Construct the path to pyproject.toml
    pfo_path = os.path.join(os.getcwd(), "pfo.json")

    # Check if the file exists
    if not os.path.exists(pfo_path):
        raise FileNotFoundError(f"pfo.json not found in {os.getcwd()}")

    with open(pfo_path, "r") as f:
        pfo_data = json.loads(f.read())

    assert (
        pfo_data["version"] != None
    ), "The version in pfo.json should not be None."
    assert (
        pfo_data["version"] != ""
    ), "The version in pfo.json should not be empty."

    return pfo_data["version"]


def get_draft_release_version(obj: list[dict]) -> str|None:
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


def get_latest_version(obj: list[dict]) -> str|None:
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


def get_prerelease_version(obj: list[dict]) -> str|None:
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


def draft_release(obj: list[dict]) -> str|None:
    """
    Reads the version from the draft release.

    Returns:
        str: The version from the draft release. (#.#.#)
    """
    ic(f"JSON Data: {obj}")  # Debugging

    prechecks(
        obj=obj
    )  # Run some prechecks to make sure that the data is correct, this will raise an exception if the data is incorrect

    if os.path.isfile(os.path.join(os.getcwd(), "pyproject.toml")):
        # If the toml flag is set, we will use the version from pyproject.toml
        ic("Using version from pyproject.toml")
        return f"v{get_toml_version()}"
    
    if os.path.isfile(os.path.join(os.getcwd(), "pfo.json")):
        # If the pfo flag is set, we will use the version from pfo.json
        ic("Using version from pfo.json")
        return f"v{get_pfo_version()}"

    print("[ERROR] No version specified. There must be a version in either pyproject.toml or pfo.json.")
    return None


if __name__ == "__main__":
    if args.toml:
        # This will print the version from pyproject.toml
        print(get_toml_version())

    if args.pfo:
        # This will print the version from pfo.json
        print(get_pfo_version())

    if args.latest:
        obj = get_repo_data()  # This is a list of dictionaries from JSON format (json.loads())
        print(get_latest_version(obj=obj))

    if args.prerelease:
        obj = get_repo_data()  # This is a list of dictionaries from JSON format (json.loads())
        print(get_prerelease_version(obj=obj))

    if args.draft:
        obj = get_repo_data()  # This is a list of dictionaries from JSON format (json.loads())
        print(get_draft_release_version(obj=obj))

    if args.draft_release:
        obj = get_repo_data() # This is a list of dictionaries from JSON format (json.loads())
        print(draft_release(obj=obj))
