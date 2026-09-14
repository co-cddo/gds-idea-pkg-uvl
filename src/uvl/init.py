import os
import sys
import tomllib

import click
from dotenv import dotenv_values, load_dotenv, set_key

from uvl.utils import _execute_command


def _init(
    uv_projects_directory: str | None = None,
    uv_project: str | None = None,
    create_if_not_exists: bool = False,
    add_local_group: bool = False,
) -> None:
    """Configure ``.env`` for a uv project and sync its dependencies.

    Persists ``UV_PROJECT_ENVIRONMENT``, ``UV_PROJECTS_DIRECTORY``, and
    ``UV_PROJECT`` values into the local ``.env`` file (creating/reusing
    values as needed), optionally scaffolds the project directory with
    ``uv init`` if it does not exist, optionally adds an ``ipykernel``
    dependency to a ``local`` dependency group, and finally runs
    ``uv sync`` (using the ``local`` group when present).

    Args:
        uv_projects_directory: Directory containing uv projects, relative
            to the current working directory. If None, the value is read
            from ``.env`` (``UV_PROJECTS_DIRECTORY``), defaulting to the
            current working directory.
        uv_project: Name of the uv project (sub-folder) to initialize. If
            None, the value is read from ``.env`` (``UV_PROJECT``).
        create_if_not_exists: If True and the project's ``pyproject.toml``
            does not exist, scaffold it via ``uv init``. If False, exit
            with an error instead.
        add_local_group: If True, add an ``ipykernel`` dependency under a
            ``local`` dependency group before syncing.

    Raises:
        SystemExit: If the project does not exist and
            ``create_if_not_exists`` is False, or if any invoked ``uv``
            command fails.
    """
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
        my_env = os.environ.copy()
        my_env.pop("UV_PROJECT", None)
        _execute_command(
            ["uv", "init", "--app", "--no-package", "--author-from", "auto", "--name", uv_project, uv_project_dir],
            env=my_env,
        )

    load_dotenv(override=True)

    if add_local_group:
        _execute_command(["uv", "add", "--group", "local", "ipykernel"])

    pyproject_config = {}
    if os.path.exists(pyproject_path):
        with open(pyproject_path, "rb") as f:
            pyproject_config = tomllib.load(f)
    if "local" in pyproject_config.get("dependency-groups", {}):
        _execute_command(["uv", "sync", "--group", "local"])
    else:
        _execute_command(["uv", "sync"])
