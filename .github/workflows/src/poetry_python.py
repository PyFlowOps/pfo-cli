# This script reads the python version from pyproject.toml and prints it.
# If the poetry project requires python version 3.12.2 in the pyproject.toml file, it will print 3.12.2.
# It also includes logging and debugging capabilities.
import argparse
import logging
import os

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
args = parser.parse_args()

# This sets debugging based on the flag passed in
if args.debug:
    ic.enable()
else:
    ic.disable()


def get_python_version() -> str:
    """
    Reads the python version from pyproject.toml.

    Returns:
        str: The python version from pyproject.toml. (#.#.#)
    """
    # Construct the path to pyproject.toml
    pyproject_path = os.path.join(os.getcwd(), "pyproject.toml")

    # Check if the file exists
    if not os.path.exists(pyproject_path):
        raise FileNotFoundError(f"pyproject.toml not found in {os.getcwd()}")

    with open(pyproject_path, "r") as f:
        pyproject_data = pytoml.load(f)

    assert (
        pyproject_data["project"]["requires-python"] != None
    ), "The version in pyproject.toml should not be None."
    assert (
        pyproject_data["project"]["requires-python"] != ""
    ), "The version in pyproject.toml should not be empty."

    return pyproject_data["project"]["requires-python"]


if __name__ == "__main__":
    print(get_python_version())
