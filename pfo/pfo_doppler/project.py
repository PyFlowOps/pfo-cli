import os

from halo import Halo
from pfo_doppler import DopplerAuth

spinner = Halo(text_color="blue", spinner="dots")


def check_doppler_project_exists(project_name: str) -> bool:
    """This function checks if a Doppler project exists.

    Args:
        project (str): The project name.

    Returns:
        bool: True if the project exists, False otherwise.
    """
    try:
        _doppler = DopplerAuth().doppler
    except Exception as e:
        spinner.fail(f"Error connecting to Doppler: {e}")
        exit()

    try:
        _doppler.projects.get(project=project_name)
    except Exception as e:
        spinner.warn(f"Project '{project_name}' does not exist!")
        return False

    spinner.info(f"Doppler project - '{project_name}' already exists, continuing...")
    return True


class DopplerProject:
    def __init__(self):
        self.doppler = DopplerAuth().doppler

    @Halo(text="Creating Doppler Project...\n", spinner="dots")
    def create_doppler_project(self, project_name: str) -> None:
        """This function creates a Doppler project."""
        if not project_name:
            spinner.fail("A project name is required to create a project...")
            exit()

        request_input = {
            "name": project_name,
            "description": f"This is the {project_name} project - created by the pfo CLI.",
        }

        try:
            self.doppler.projects.create(request_input=request_input)
        except Exception as e:
            spinner.fail(f"Error creating the project: {e}")
            exit()

    @Halo(text="Deleting Doppler Project...\n", spinner="dots")
    def delete_doppler_project(self, project_name: str) -> None:
        """This function deletes a Doppler project."""
        if not project_name:
            spinner.fail("A project name is required to create a project...")
            exit()

        request_input = {
            "name": project_name,
            "description": f"This is the {project_name} project - created by the pfo CLI.",
        }

        try:
            results = self.doppler.projects.delete(request_input=request_input)
        except Exception as e:
            spinner.fail(f"Error deleting the project: {e}")
            exit()
