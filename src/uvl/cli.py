"""Command-line entry point for `uvl`."""

import click


@click.group()
@click.pass_context
@click.version_option(prog_name="uvl", package_name="gds-idea-pkg-uvl")
def cli(ctx):
    """uvl - manage multiple uv projects in one directory."""


@cli.command()
@click.argument("uv_project", default=None)
@click.option("--uv-projects-directory", help="", default=None)
@click.option("--create-if-not-exists", help="", default=False, is_flag=True)
@click.option("--add-local-group", help="", default=False, is_flag=True)
def init(uv_project: str, uv_projects_directory: str, create_if_not_exists: bool, add_local_group: bool) -> None:
    """ """
    from uvl.init import _init
    from uvl.prerequisites import _check_prerequisites

    _check_prerequisites()

    _init(uv_projects_directory, uv_project, create_if_not_exists, add_local_group)
