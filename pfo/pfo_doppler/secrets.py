"""
This module is used to get the secrets from the Doppler project and load them into the environment variables.
Usage:
    from pfo.src.pfo_doppler import DopplerSecrets

    # Create a DopplerSecrets object
    doppler_secrets = DopplerSecrets(project_name="your_project_name", config_name="your_config_name")

The scripts will automatically load the secrets into the environment variables. You can get the list of vars
by using the key_list attribute.

    # Get the list of keys
    keys = doppler_secrets.key_list
"""
import os

from pfo_doppler.auth import DopplerAuth

class DopplerSecrets():
    def __init__(self, project_name: str, config_name: str):
        self.project_name = project_name
        self.config_name = config_name
        self.doppler = DopplerAuth().doppler
        self.secrets: dict = self.get_secrets()
        self._load_env() # Load the secrets into the environment variables
        self.key_list = [k for k, v in self.secrets.items()]

    def get_secrets(self, key_list: list = []) -> dict:
        """This function gets the secret from the Doppler project.

        Args:
            secret_name (str): The name of the secret.

        Returns:
            dict: Key-value pairs of the secrets.
        """
        _return_data = {} # This is the data that will be returned

        _object = self.doppler.secrets.list(
            project = self.project_name,
            config = self.config_name
        )
        _secrets = _object.secrets
        for k, v in _secrets.items():
            key_list.append(k)
            _return_data[k] = v["computed"]

        return _return_data

    def _load_env(self) -> None:
        """This function loads the secrets into the environment variables."""
        for k, v in self.secrets.items():
            os.environ[k] = v

    def clean_env(self) -> None:
        """This function clears the secrets from the environment variables."""
        for k in self.key_list:
            os.environ.pop(k)
