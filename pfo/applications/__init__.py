import os
import click

from halo import Halo
from click_option_group import optgroup
from cookiecutter.main import cookiecutter
from pfo.shared.commands import OrderedGroup
from tools import print_help_msg


spinner = Halo(text_color="blue", spinner="dots")
template_remote = "https://github.com/pyflowops/repo_additions.git"


@click.group(cls=OrderedGroup, invoke_without_command=True)
@optgroup.group(f"Github", help=f"PFO applications.")
@optgroup.option(
    "--cli",
    required=False,
    is_flag=True,
    help=f"This creates a CLI app based on the PyFlowOps template.",
)
def app(**params: dict) -> None:
    """This is the pfo applications builder, maintenance tool."""
    if params["cli"]:
        # If the user wants to create a CLI app, we will call the create_cli function
        appname: str = click.prompt(
            "Please enter the name of your CLI app",
            default="my_cli_app",
            show_default=True,
            required=True,
            type=str
        )
        description: str = click.prompt(
            "Please enter a description for your CLI app",
            default="A PyFlowOps CLI application",
            show_default=True,
            required=True,
            type=str
        )
        author: str = click.prompt(
            "Please enter the name of the author",
            default="PyFlowOps Team",
            show_default=True,
            required=True,
            type=str
        )
        email: str = click.prompt(
            'Please enter the email of the author',
            default="email@notarealdomain.com",
            show_default=True,
            required=True,
            type=str
        )
        github_org: str = click.prompt(
            "Please enter the name of the Github Organization",
            default="pyflowops",
            show_default=True,
            required=True,
            type=str
        )

        create_cli(
            appname=appname,
            description=description,
            author=author,
            email=email,
            github_org=github_org
            )

    if params["api"]:
        pass

    if params["strealit"]:
        pass

    if params["reflex"]:
        pass
    
    print_help_msg(app)


def create_cli(**kwargs) -> None:
    # This function will create a core app in the current directory
    if not kwargs:
        spinner.fail("No parameters provided for creating CLI app.")
        exit()

    # Let's make sure that we have ALL of the required parameters to create the CLU application
    required_params = ("appname", "description", "author", "email", "github_org")
    
    if not all(param in kwargs for param in required_params):
        spinner.fail("You must provide all parameters to create a CLI app.")
        exit()

    app_type="click" # We're setting this manually because we already know we want the CLI by being within this logic block

    if not os.path.exists(os.path.join(os.getcwd(), ".git")):
        spinner.fail(
            "You need to run this command from within a git repo. Please navigate to the repo you want to create the app in first. \n" \
            "If you want to create a new repo, please run `pfo repo --init` first."
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
                "name": kwargs["appname"],
                "description": kwargs["description"],
                "author": kwargs["author"],
                "email": kwargs["email"],
                "github_org": kwargs["github_org"]
            },
            output_dir=os.path.join(os.getcwd())
        )
    except Exception as e:
        spinner.fail(
            f"Error creating core app: {e}"
        )
        exit()
