"""Command-line entry point for `uvl`."""

import os

import click
from click_default_group import DefaultGroup
from dotenv import dotenv_values


@click.group(cls=DefaultGroup, default="init", default_if_no_args=False)
@click.pass_context
@click.version_option(prog_name="uvl", package_name="gds-idea-pkg-uvl")
def cli(ctx: click.Context) -> None:
    """uvl - manage multiple uv projects in one directory."""


def complete_uv_project(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:
    """Shell-completion callback that suggests uv project names.

    Looks up ``UV_PROJECTS_DIRECTORY`` from the local ``.env`` file (falling
    back to the current working directory) and lists sub-folders that start
    with the partially typed text and contain a ``pyproject.toml`` file.

    Args:
        ctx: Click context (unused, required by the completion callback
             signature).
        param: The parameter being completed (unused, required by the
               completion callback signature).
        incomplete: The partial text the user has typed so far.

    Returns:
        A list of matching project folder names.
    """
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
@click.argument(
    "uv_project",
    help="Name of the uv project (sub-folder) to initialize.",
    default=None,
    shell_complete=complete_uv_project,
)
@click.option(
    "--uv-projects-directory",
    help="Directory containing uv projects. Defaults to the value stored in `.env` or the cwd.",
    default=None,
)
@click.option(
    "--create-if-not-exists",
    help="If True, scaffold the project with `uv init` when it does not already exist.",
    default=False,
    is_flag=True,
)
@click.option(
    "--add-local-group",
    help="If True, add an `ipykernel` dependency under a `local` dependency group before syncing.",
    default=False,
    is_flag=True,
)
def init(uv_project: str, uv_projects_directory: str, create_if_not_exists: bool, add_local_group: bool) -> None:
    """Initialize (and optionally create) a uv project, then sync it.

    Checks that required external tools are installed, then delegates to
    :func:`uvl.init._init` to configure ``.env`` values, optionally scaffold
    the project with ``uv init``, and run ``uv sync``.

    Args:
        uv_project: Name of the uv project (sub-folder) to initialize.
        uv_projects_directory: Directory containing uv projects. Defaults to
                                the value stored in ``.env`` or the cwd.
        create_if_not_exists: If True, scaffold the project with ``uv init``
                               when it does not already exist.
        add_local_group: If True, add an ``ipykernel`` dependency under a
                          ``local`` dependency group before syncing.
    """
    from uvl.init import _init
    from uvl.prerequisites import _check_prerequisites

    _check_prerequisites()

    _init(uv_projects_directory, uv_project, create_if_not_exists, add_local_group)


@cli.command()
@click.option("--uv", help="If True, generate and install completion for `uv`.", default=False, is_flag=True)
@click.option(
    "--uvl",
    help=(
        "If True, generate and install completion for `uvl` "
        "(also adds a small `uvl` zsh wrapper function to load `.env`)."
    ),
    default=False,
    is_flag=True,
)
@click.option(
    "--click-package-name",
    help="If provided, generate and install completion for an arbitrary click-based CLI with this name.",
    default=None,
)
def init_shell(uv: bool, uvl: bool, click_package_name: str) -> None:
    """Install zsh shell-completion scripts for uv/uvl/other click apps.

    Generates and writes zsh completion files for the requested tools, and
    ensures ``~/.zshrc`` sources ``compinit`` and the generated completion
    files.
    Function adds content to ``~/.zshrc``. In some unexpected cases you might
    need to modify the file manually.

    Args:
        uv: If True, generate and install completion for ``uv``.
        uvl: If True, generate and install completion for ``uvl`` (also adds
             a small ``uvl`` zsh wrapper function to load ``.env``).
        click_package_name: If provided, generate and install completion for
                             an arbitrary click-based CLI with this name.
    """
    from uvl.init_shell import _init_shell

    _init_shell(uv, uvl, click_package_name)
