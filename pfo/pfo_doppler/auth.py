import os

from dopplersdk import DopplerSDK
from halo import Halo

spinner = Halo(text_color="blue", spinner="dots")


class DopplerAuth:
    def __init__(self):
        self.doppler_token = self.get_doppler_token()
        self.doppler = DopplerSDK()
        self.doppler.set_access_token(self.doppler_token)

    @staticmethod
    def doppler_token_exists() -> bool:
        """This function checks to see if the Doppler token exists in the environment."""
        if os.environ.get("DOPPLER_TOKEN"):
            return True

        return False

    @Halo(text="Getting Doppler Token...", spinner="dots")
    def get_doppler_token(self) -> str:
        """This function gets the Doppler token from the environment.

        Returns:
            str: The Doppler token.

        Raises:
            Exception: If the Doppler token is not set in the environment.
        """
        if self.doppler_token_exists():
            # We need to access the Doppler token that has access to create configs, and projects
            # The personal access token gives access to pfo, but does not give access to the projects
            # and configs. We need to use the token that has access to the projects and configs.
            # This is set within the pfo Doppler project as PFO_DOPPLER_TOKEN
            if not os.environ.get("PFO_DOPPLER_TOKEN"):
                try:
                    doppler = DopplerSDK()
                    doppler.set_access_token(os.environ.get("DOPPLER_TOKEN"))
                    res = doppler.secrets.get(
                        name="PFO_DOPPLER_TOKEN", project="pyflowops", config="pfo-cli"
                    )
                    value_vars = vars(res)
                    # We need to set the PFO_DOPPLER_TOKEN in the environment
                    # so that we can use it in the rest of the CLI
                    os.environ["PFO_DOPPLER_TOKEN"] = value_vars["value"]["computed"]
                except Exception as e:
                    spinner.fail(
                        f"Permissions (Doppler) cannot be accessed... -- {e}"
                    )  # This means the PFO_DOPPLER_TOKEN is not set in the environment
                    exit()

            # We need to set the PFO_DOPPLER_TOKEN in the environment
            if os.environ.get("PFO_DOPPLER_TOKEN"):
                if os.environ.get("PFO_DOPPLER_TOKEN") != "":
                    # We need to set the PFO_DOPPLER_TOKEN in the environment
                    return os.environ.get("PFO_DOPPLER_TOKEN")

            spinner.fail(
                "Permissions (Doppler) cannot be accessed..."
            )  # This means the PFO_DOPPLER_TOKEN is not set in the environment
        else:
            spinner.stop()
            spinner.info(
                "Doppler token cannot be found, please setup your Doppler account and export your PFO_DOPPLER_TOKEN..."
            )
