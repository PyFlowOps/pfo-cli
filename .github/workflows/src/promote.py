# This Python script will promote either a draft release to a pre-release, or a pre-release to a full release.
# It uses the GitHub API to perform the promotion.
# The script takes the following arguments:
import argparse
import json
import subprocess

parser = argparse.ArgumentParser(description="Promote a GitHub release.")
parser.add_argument(
    "--prerelease",
    action="store_true",
    help="Flag for promoting a draft release to a pre-release.",
)
parser.add_argument(
    "--release",
    action="store_true",
    help="Flag for promoting a pre-release to a full release.",
)

args = parser.parse_args()


def get_all_releases() -> list[dict]:
    """This function gets all releases from the GitHub API.

    returns:
        list[dict]: A list of dictionaries containing the release information.
    """
    _cmd = [
        "gh",
        "release",
        "list",
        "--json",
        "name,tagName,isDraft,isPrerelease,isLatest,createdAt,publishedAt",
    ]

    _result = subprocess.run(_cmd, capture_output=True, text=True)
    if _result.returncode != 0:
        raise Exception(f"Error: {_result.stderr}")

    _data = json.loads(_result.stdout)
    if type(_data) != list:
        raise Exception("[ERROR] - Expected a list of releases")

    if len(_data) > 1:
        raise Exception("[ERROR] - More than one draft release found")

    return _data


releases: list[dict] = get_all_releases()  # Get all releases for use in the script


def get_draft_release() -> list[dict]:
    """This function gets the draft release from the GitHub API.

    returns:
        dict: A dictionary containing the draft release information.
    """
    _data: list[dict] = releases  # Get all releases
    _draft = [i for i in _data if i["isDraft"]]  # Get the draft release

    return _draft  # Return the draft release, else []


def get_prerelease() -> list[dict]:
    """This function gets the draft release from the GitHub API.

    returns:
        dict: A dictionary containing the draft release information.
    """
    _data: list[dict] = releases  # Get all releases
    _prerelease = [i for i in _data if i["isPrerelease"]]  # Get the draft release

    return _prerelease  # Return the pre-release, else []


def assert_draft_release() -> bool:
    """This function asserts that a draft release exists.

    returns:
        bool: True if a draft release exists, False otherwise.
    """
    _draft: list[
        dict
    ] = get_draft_release()  # Get the draft release (MUST be a list of ONE dictionary)

    if bool(type(_draft) == list) and bool(len(_draft)):
        if len(_draft) > 1:
            raise Exception("[ERROR] - More than one draft release found")
        else:
            return True

    return False


def assert_prerelease() -> bool:
    """This function asserts that a pre-release exists.

    returns:
        bool: True if a pre-release exists, False otherwise.
    """
    _prerelease: list[
        dict
    ] = get_prerelease()  # Get the draft release (MUST be a list of ONE dictionary)

    if bool(type(_prerelease) == list) and bool(len(_prerelease)):
        if len(_prerelease) > 1:
            raise Exception("[ERROR] - More than one pre-release found")
        else:
            return True

    return False


def promote_draft():
    """This function promotes a draft release to a pre-release."""
    if assert_draft_release() is False:
        raise Exception("[ERROR] - No draft release found")

    _draft: list[
        dict
    ] = get_draft_release()  # Get the draft release (MUST be a list of ONE dictionary)
    _draft: dict = _draft[0]  # Get the first (and only) draft release

    _cmd = [
        "gh",
        "release",
        "edit",
        _draft["tagName"],
        "--draft=false",
        "--prerelease=true",
        "--latest=false",
    ]
    print("[INFO] - Promoting draft release to pre-release")
    # r = subprocess.run(_cmd, capture_output=True, text=True)
    # if r.returncode != 0:
    #    raise Exception(f"Error: {r.stderr}")


def promote_release():
    """This function promotes a pre-release to a full release."""
    if assert_prerelease() is False:
        raise Exception("[ERROR] - No pre-release found")

    _prerelease: list[
        dict
    ] = get_prerelease()  # Get the pre-release (MUST be a list of ONE dictionary)
    _prerelease: dict = _prerelease[0]  # Get the first (and only) pre-release

    _cmd = [
        "gh",
        "release",
        "edit",
        _prerelease["tagName"],
        "--draft=false",
        "--prerelease=true",
        "--latest=false",
    ]
    print("[INFO] - Promoting pre-release to full release")
    # r = subprocess.run(_cmd, capture_output=True, text=True)
    # if r.returncode != 0:
    #    raise Exception(f"Error: {r.stderr}")


if __name__ == "__main__":
    if args.prerelease:
        promote_draft()  # promote draft to pre-release

    if args.release:
        promote_release()  # promote pre-release to a full release
