import configparser
import os
import sys

import click
from dotenv import dotenv_values, load_dotenv, set_key

from uvl.utils import _execute_command


def _init(
    uv_projects_directory: str = None,
    uv_project: str = None,
    create_if_not_exists: bool = False,
    add_local_group: bool = False,
):
    cwd = os.getcwd()
    dotenv_path = ".env"
    config = dotenv_values(dotenv_path)

    if "UV_PROJECT_ENVIRONMENT" not in config:
        set_key(dotenv_path=dotenv_path, key_to_set="UV_PROJECT_ENVIRONMENT", value_to_set=os.path.join(cwd, ".venv"))
    if uv_projects_directory is not None:
        set_key(
            dotenv_path=dotenv_path,
            key_to_set="UV_PROJECTS_DIRECTORY",
            value_to_set=os.path.join(cwd, uv_projects_directory),
        )
    else:
        uv_projects_directory = config.get("UV_PROJECTS_DIRECTORY", cwd)
    if uv_project is not None:
        uv_project_dir = os.path.join(cwd, uv_projects_directory, uv_project)
        set_key(dotenv_path=dotenv_path, key_to_set="UV_PROJECT", value_to_set=uv_project_dir)
    else:
        uv_project_dir = config.get("UV_PROJECT", os.path.join(cwd, uv_projects_directory))
        uv_project = os.path.basename(uv_project_dir)

    pyproject_path = os.path.join(uv_project_dir, "pyproject.toml")
    pyproject_exists = os.path.exists(pyproject_path)
    if not pyproject_exists and not create_if_not_exists:
        click.echo(f"{uv_project} project does not exists.", err=True)
        sys.exit(1)
    elif not pyproject_exists and create_if_not_exists:
        os.makedirs(uv_project_dir, exist_ok=True)
        _execute_command(
            ["uv", "init", "--app", "--no-package", "--author-from", "auto", "--name", uv_project, uv_project_dir]
        )

    load_dotenv(override=True)

    if add_local_group:
        _execute_command(["uv", "add", "--group", "local", "ipykernel"])

    config = configparser.RawConfigParser(allow_no_value=True)
    config.read(pyproject_path)
    if config.has_option("dependency-groups", "local"):
        _execute_command(["uv", "sync", "--group", "local"])
    else:
        _execute_command(["uv", "sync"])
