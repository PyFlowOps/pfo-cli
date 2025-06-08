import os

from .auth import DopplerAuth
from .config import DopplerConfig, check_doppler_config_exists
from .project import DopplerProject, check_doppler_project_exists
from .secrets import DopplerSecrets

_doppler = False

if os.environ.get("DOPPLER_TOKEN"):
    # If the DOPPLER_TOKEN is set in the environment, we can initialize the Doppler SDK
    _doppler = True
    dop_auth = DopplerAuth()
    dop_config = DopplerConfig()
    dop_project = DopplerProject()
    dop_secrets = DopplerSecrets()

print(f"REMOVE ME: _doppler = {_doppler}")
