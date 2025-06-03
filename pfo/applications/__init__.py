import os

from halo import Halo
from cookiecutter.main import cookiecutter

spinner = Halo(text_color="blue", spinner="dots")
template_remote = "https://github.com/pyflowops/repo_additions.git"

def create_cli(appname: str) -> None:
    # This function will create a core app in the current directory
    app_type="click"
    main_repo_location = os.getcwd()

    if not os.path.exists(os.path.join(main_repo_location, ".git")):
        spinner.fail(
            "You need to run this command from within a git repo. Please navigate to the repo you want to create the app in first."
        )
        exit()
    
    # This is the path to the cookiecutter template
    try:
        cookiecutter(
            template_remote,
            # The template MUST be in the repo at the 'main' branch
            checkout="main",
            # The app type is the directory name in the cookiecutter template
            directory=app_type,
            no_input=True,
            # The app name is the name of the directory to create (which is the name of the application)
            extra_context={
                "app_name": appname
            },
            output_dir=os.path.join(main_repo_location)
        )
    except Exception as e:
        spinner.fail(
            f"Error creating core app: {e}"
        )
        exit()
