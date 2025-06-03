import os
import shutil
import subprocess
import time

import click
from halo import Halo
from config import MetaData

metadata = MetaData()
spinner = Halo(spinner="dots")


class DefaultCommandGroup(click.Group):
    """allow a default command for a group"""

    def command(self, *args, **kwargs):
        default_command = kwargs.pop("default_command", False)
        if default_command and not args:
            kwargs["name"] = kwargs.get("name", "<>")
        decorator = super(DefaultCommandGroup, self).command(*args, **kwargs)

        if default_command:
            def new_decorator(f):
                cmd = decorator(f)
                self.default_command = cmd.name
                return cmd

            return new_decorator

        return decorator

    def resolve_command(self, ctx, args):
        try:
            # test if the command parses
            return super(DefaultCommandGroup, self).resolve_command(ctx, args)
        except click.UsageError:
            # command did not parse, assume it is the default command
            args.insert(0, self.default_command)
            return super(DefaultCommandGroup, self).resolve_command(ctx, args)



class RepoGroup(click.Group):
    def parse_args(self, ctx, args):
        _init = (
            True if "--init" in args else False
        )  # Let's set a variable to use if list is passed in

        # if _init:
        #    # --owner now required if --init is present
        #    for param in self.params:
        #        if param.name == "owner":
        #            param.required = True

        return super(RepoGroup, self).parse_args(ctx, args)


'''
Examples of custom command groups that can be used in the future


class StrapiCommandGroup(click.Group):
    def parse_args(self, ctx, args):
        _args_length = len(args)
        if "--environment" in args or "-e" in args:
            _env_index = (
                args.index("--environment")
                if "--environment" in args
                else args.index("-e")
            )
            _environment = args[_env_index + 1]

        _release = (
            True if "--release" in args else False
        )  # Let's set a variable to use if list is passed in
        _restore = (
            True if "--restore" in args else False
        )  # Let's set a variable to use if list is passed in
        _backup = (
            True if "--backup" in args else False
        )  # Let's set a variable to use if list is passed in
        _diagnostics = (
            True if "--diagnostics" in args or "-d" in args else False
        )  # Let's set a variable to use if list is passed in

        try:
            return super(StrapiCommandGroup, self).parse_args(ctx, args)

        except click.MissingParameter as exc:
            if _release:
                args.append("--release")
                for param in self.params:
                    if param.name == "environment":
                        param.required = False
            elif _restore:
                args.append("--restore")
                for param in self.params:
                    if param.name == "environment":
                        param.required = True
            elif _diagnostics:
                args.append("--diagnostics")
                for param in self.params:
                    param.required = False
            elif _args_length == 0:
                for param in self.params:
                    param.required = False
            else:
                raise

            return super(StrapiCommandGroup, self).parse_args(ctx, args)


class SecurityCommandGroup(click.Group):
    def parse_args(self, ctx, args):
        _args_length = len(args)
        if "--environment" in args or "-e" in args:
            _env_index = (
                args.index("--environment")
                if "--environment" in args
                else args.index("-e")
            )
            _environment = args[_env_index + 1]

        _ssl = (
            True if "--ssl" in args else False
        )  # Let's set a variable to use if list is passed in

        try:
            return super(SecurityCommandGroup, self).parse_args(ctx, args)

        except click.MissingParameter as exc:
            if _args_length == 0:
                for param in self.params:
                    param.required = False
            else:
                if _ssl:
                    args.append("--ssl")
                    for param in self.params:
                        if param.name == "environment":
                            param.required = False

            return super(SecurityCommandGroup, self).parse_args(ctx, args)
'''

@Halo(text="Update in progress...", spinner="dots")
def update_cli():
    """This command updates the CLI with the latest configuration"""
    # Check for a newer version of the CLI
    import importlib

    from pfo_github.functions import get_latest_cli_release_version

    __current_version = importlib.metadata.version(metadata._name)
    __latest_version = get_latest_cli_release_version()

    if __current_version == __latest_version:
        spinner.succeed(
            f"You are already on the latest version of the CLI -- v{__latest_version}."
        )
        exit()

    if __current_version != __latest_version:
        spinner.info(f"Updating the CLI to the latest version...v{__latest_version}")

        _cmd = "curl -sSf https://raw.githubusercontent.com/PyFlowOps/pfo-cli/refs/heads/main/.install/install.sh | bash -l"
        res = subprocess.run(_cmd, shell=True, capture_output=True)

        if res.returncode != 0:
            spinner.fail(f"Error updating the CLI...{res.stdout.decode('utf-8')}")
            exit()

        if not os.path.isdir(metadata.rootdir):
            os.makedirs(metadata.rootdir)

        if not os.path.isfile(metadata.cli_env):
            shutil.copyfile(
                os.path.join(metadata.config_path, ".env"), metadata.cli_env
            )

        # We need to ensure that github template repo exists, and is up-to-date
        _template_location = os.path.join(metadata.rootdir, ".templates")
        if not _template_location:
            os.makedirs(_template_location)

    spinner.succeed("Update complete!")
