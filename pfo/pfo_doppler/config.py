import os
import time

from dopplersdk import DopplerSDK
from halo import Halo
from pfo_doppler import DopplerAuth

spinner = Halo(text_color="blue", spinner="dots")


def check_doppler_config_exists(project_name: str, config_name: str) -> bool:
    """This function checks if a Doppler config exists within a project.

    Args:
        project (str): The project name.
        config (str): The config name.

    Returns:
        bool: True if the config exists, False otherwise.
    """
    try:
        _doppler = DopplerAuth().doppler
    except Exception as e:
        spinner.fail(f"Error connecting to Doppler: {e}")
        exit()

    try:
        response = _doppler.configs.list(project=project_name)
        for config in response.configs:
            if config_name in config["name"]:
                if config["name"].startswith("sbx_"):
                    # If this is a sandbox config, we don't want to check for it
                    continue

                spinner.info(
                    f"Config '{config_name}' already exists in project '{project_name}', continuing..."
                )
                return True

    except Exception as e:
        spinner.fail(f"Project '{project_name}' does not exist! --> {e}")
        exit()

    return False


class DopplerConfig:
    def __init__(self):
        self.doppler = DopplerAuth().doppler

    def _owner_from_repo_name(self, repo_name: str) -> str:
        return repo_name.split("-")[0]

    def _project_from_repo_name(self, repo_name: str) -> str:
        return repo_name.split("-")[0] + "-apps"

    def _config_from_repo_name(self, repo_name: str) -> str:
        """This function gets the config name from the repo name."""
        _data = repo_name.split("-")
        _data.pop(0)  # Remove the owner from the repo name
        cfg_name = ""
        for i in _data:
            if _data.index(i) == len(_data) - 1:
                cfg_name += i
            else:
                cfg_name += i + "-"

        return cfg_name

    def _envs(self) -> list:
        return ["dev", "stg", "prd"]

    @Halo(text="Creating Doppler Config...\n", spinner="dots")
    def create_doppler_configs(self, repo_name) -> None:
        """This function creates a Doppler config in a project.

        Args:
            repo_name (str): The project name.
        """
        for _e in self._envs():
            request_input = {
                "name": f"{_e}_{self._config_from_repo_name(repo_name=repo_name)}",
                "project": self._project_from_repo_name(repo_name=repo_name),
                "environment": _e,
            }

            try:
                self.doppler.configs.create(
                    request_input=request_input
                )  # This will create the config
            except Exception as e:
                spinner.fail(
                    f"Error creating the config - {_e}_{self._config_from_repo_name(repo_name=repo_name)} in project - {self._project_from_repo_name(repo_name=repo_name)}: {e}"
                )
                exit()

            time.sleep(1)  # Let's give it a second to create the config
