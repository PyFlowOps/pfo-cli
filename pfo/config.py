import configparser
import os

from halo import Halo

spinner = Halo(text="Loading configuration...", spinner="dots")


class MetaData:
    _name = "pfo"
    _authors = [
        "Philip De Lorenzo",
    ]
    _company: str = "PyFlowOps"
    _contributors: list = ["Philip De Lorenzo"]
    _organization: str = "PyFlowOps"
    _github_org: str = "pyflowops"
    _github_org_url: str = f"https://github.com/{_github_org}"
    _template_repo: str = "base-repo-template"

    def __init__(self):
        self.config_path: os.path.abspath = (
            self._config_path()
        )  # The root folder of the config file (config.ini)
        self.config_file: str = (
            self._config_file()
        )  # The path to the config file (config.ini)
        self.config_data: dict = (
            self._config_data()
        )  # This is a dictionary of the config file (config.ini)
        self.context_root: os.path.abspath = (
            self._context_root()
        )  # Set the directory in context of THIS file.
        self.rootdir: os.path.abspath = (
            self._cli_root_directory()
        )  # Set the root directory for the CLI (where the .env file is located)
        self.cli_env: os.path.abspath = os.path.join(self.rootdir, ".env")
        self.shell_scripts_directory: os.path.abspath = self._shell_scripts_directory()
        self.pfo_json_file: str = "pfo.json"  # The PyFlowOps JSON file - configuration for the package to be tracked
        self.base_version: str = (
            "0.0.1"  # The base version the package being tracked by PyFlowOps
        )
        self.template_repo_url: str = (
            f"{self._github_org_url}/{self._template_repo}.git"
        )
        self.local_github_repo_template: os.path.abspath = (
            self._local_github_repo_template()
        )

    def __str__(self) -> str:
        """Returns the string representation of the MetaData class."""
        return f"MetaData --> <{self._name}>"

    def _shell_scripts_directory(self) -> os.path.abspath:
        """Returns the path to the shell scripts directory."""
        return os.path.abspath(os.path.join(self.context_root, "scripts"))

    def _context_root(self) -> os.path.abspath:
        """Returns the path to the root directory of the CLI."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def _cli_root_directory(self) -> os.path.abspath:
        """Returns the path to the root directory of the CLI."""
        if os.getenv("HOME"):
            return os.path.abspath(os.path.join(os.getenv("HOME"), ".pfo"))
        else:
            return os.path.abspath(os.path.join("~", ".pfo"))

    def _local_github_repo_template(self) -> os.path.abspath:
        """Returns the path to the github repo local template."""
        return os.path.abspath(
            os.path.join(self.rootdir, ".templates", self._template_repo)
        )

    def _config_path(self) -> os.path.abspath:
        """Returns the path to the config file."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _config_file(self) -> str:
        """Returns the path to the config file."""
        return os.path.join(self.config_path, "config.ini")

    def _config_data(self) -> dict:
        """Returns the config data from the config file."""
        data = configparser.ConfigParser()
        data.read(self.config_file)
        return data
