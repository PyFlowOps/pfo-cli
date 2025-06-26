import configparser
import os
import virtualenv

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
        self.config_path: str = (
            self._config_path()
        )  # The root folder of the config file (config.ini)
        self.config_file: str = (
            self._config_file()
        )  # The path to the config file (config.ini)
        self.config_data: configparser.ConfigParser = (
            self._config_data()
        )  # This is a dictionary of the config file (config.ini)
        self.context_root: str = (
            self._context_root()
        )  # Set the directory in context of THIS file.
        
        # Set the root directory for the CLI -- MAIN CLI CONFIG DIR -- ~/.pfo 
        self.rootdir: str = (
            self._cli_root_directory()
        )

        ### Python and Pip Executables
        # We need to install a python environment in the root directory
        virtualenv.cli_run(["--python=python3.12.6", f"{self.rootdir}/.python"])
        
        self.python_executable: str = (
            os.path.join(self.rootdir, ".python", "bin", "python")
        )  # The Python interpreter to use, default is python3
        self.python_pip: str = (
            os.path.join(self.rootdir, ".python", "bin", "pip")
        )  # The Python pip to use, default is python3 -m pip

        self.cli_env: str = os.path.join(self.rootdir, ".env")
        self.shell_scripts_directory: str = self._shell_scripts_directory()
        self.pfo_json_file: str = "pfo.json"  # The PyFlowOps JSON file - configuration for the package to be tracked
        self.base_version: str = (
            "0.0.1"  # The base version the package being tracked by PyFlowOps
        )
        self.template_repo_url: str = (
            f"{self._github_org_url}/{self._template_repo}.git"
        )
        self.local_github_repo_template: str = (
            self._local_github_repo_template()
        )

    def __str__(self) -> str:
        """Returns the string representation of the MetaData class."""
        return f"MetaData --> <{self._name}>"

    def _shell_scripts_directory(self) -> str:
        """Returns the path to the shell scripts directory."""
        return os.path.abspath(os.path.join(self.context_root, "scripts"))

    def _context_root(self) -> str:
        """Returns the path to the root directory of the CLI -- REPO ROOT."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    def _cli_root_directory(self) -> str:
        """Returns the path to the root directory of the CLI."""
        return os.path.abspath(os.path.join(os.environ.get("HOME", "~"), ".pfo"))

    def _local_github_repo_template(self) -> str:
        """Returns the path to the github repo local template."""
        return os.path.abspath(
            os.path.join(self.rootdir, ".templates", self._template_repo)
        )

    def _config_path(self) -> str:
        """Returns the path to the config file."""
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    def _config_file(self) -> str:
        """Returns the path to the config file."""
        return os.path.join(self.config_path, "config.ini")

    def _config_data(self) -> configparser.ConfigParser:
        """Returns the config data from the config file."""
        data = configparser.ConfigParser()
        data.read(self.config_file)
        return data
