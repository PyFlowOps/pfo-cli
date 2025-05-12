# Author: Philip De Lorenzo <philip.delorenzo@gmail.com>
import json
import subprocess


def prereq() -> bool:
    """
    Check if the prerequisites are met.

    Returns:
        bool: True if the prerequisites are met, False otherwise.

        The prerequisites meaning that if the release already exists, then we don't need to create it again. -- False

    Raises:
        Exception: If there is an error checking for existing releases.
    """
    ## Code to check if the prerequisites are met goes here
    _cmd = ["gh", "release", "list", "--json", "tagName"]

    try:
        _r = subprocess.run(_cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] - Error checking for existing releases: {e}")
        raise

    if _r.returncode != 0:
        raise Exception(f"[ERROR] - Error checking for existing releases: {_r.returncode}")

    _json_data = json.loads(
        _r.stdout.decode("utf-8").strip()
    )  # We need to decode and convert the captured output to JSON

    if _json_data and len(_json_data) > 0:
        return False

    return True


def create_initial_release():
    """
    Create the initial release for the project.
    """
    # Code to create the initial release goes here
    _cmd = [
        "gh",
        "release",
        "create",
        "v0.0.0",
        "--title",
        "Initial Release",
        "--notes",
        "Initial release of the project.",
        "--draft",
    ]

    # If the prereq() returns False, then the release already exists
    if not prereq():
        print("[INFO] - Initial release already exists, nothing to do.")
        exit(0)
    else:
        r = subprocess.run(_cmd, check=True)

        if r.returncode != 0:
            raise Exception("[ERROR] - Error creating initial release")
        else:
            print("[SUCCESS] - Initial release created successfully.")


# This will call the initial release function. If the prerequisites are not met, then it will not create the release.
# The prerequisites are essentially, if there are ANY releases, then the prereqs are not met, because a prereq is that there are no releases.
if __name__ == "__main__":
    create_initial_release()  # Call the function to create the initial release
