"""Command-line entry point for `uvl`."""

import os

import click
from click_default_group import DefaultGroup
from dotenv import dotenv_values


@click.group(cls=DefaultGroup, default="init", default_if_no_args=False)
@click.pass_context
@click.version_option(prog_name="uvl", package_name="gds-idea-pkg-uvl")
def cli(ctx):
    """uvl - manage multiple uv projects in one directory."""


def complete_uv_project(ctx, param, incomplete):
    cwd = os.getcwd()
    dotenv_path = ".env"
    config = dotenv_values(dotenv_path)
    uv_projects_directory = config.get("UV_PROJECTS_DIRECTORY", cwd)
    projects_list = []
    for folder in os.listdir(uv_projects_directory):
        if folder.startswith(incomplete) and os.path.exists(
            os.path.join(uv_projects_directory, folder, "pyproject.toml")
        ):
            projects_list.append(folder)
    return projects_list


@cli.command()
@click.argument("uv_project", default=None, shell_complete=complete_uv_project)
@click.option("--uv-projects-directory", help="", default=None)
@click.option("--create-if-not-exists", help="", default=False, is_flag=True)
@click.option("--add-local-group", help="", default=False, is_flag=True)
def init(uv_project: str, uv_projects_directory: str, create_if_not_exists: bool, add_local_group: bool) -> None:
    """ """
    from uvl.init import _init
    from uvl.prerequisites import _check_prerequisites

    _check_prerequisites()

    _init(uv_projects_directory, uv_project, create_if_not_exists, add_local_group)


@cli.command()
@click.option("--uv", help="", default=False, is_flag=True)
@click.option("--uvl", help="", default=False, is_flag=True)
@click.option("--click-package-name", help="", default=None)
def init_shell(uv: bool, uvl: bool, click_package_name: str) -> None:
    """ """
    from uvl.init_shell import _init_shell

    _init_shell(uv, uvl, click_package_name)
