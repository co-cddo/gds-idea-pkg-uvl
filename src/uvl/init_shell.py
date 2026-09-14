import os

from uvl.utils import _execute_command, _write_to_file

_uvl_zsh_script = """\
uvl() {
  command uvl "$@"
  [ -f ".env" ] && export $(cat .env | xargs)
}
"""


def _create_completion_files(
    app_name: str,
    command: list[str],
    completion_folder: str,
    zshrc_file_path: str,
    zshrc_file_content: str,
    env: dict[str, str] | None = None,
) -> None:
    """Generate a zsh completion file for an app and wire it up in .zshrc.

    Runs ``command`` to capture the app's zsh completion script, writes it
    to ``<completion_folder>/<app_name>-complete.zsh``, and ensures
    ``.zshrc`` loads ``compinit`` and sources the generated file (appending
    lines only if not already present).

    Args:
        app_name: Name of the application, used to build the completion
                  file name.
        command: Command (and arguments) to execute that prints the zsh
                  completion script to stdout.
        completion_folder: Directory where the completion file will be
                            written.
        zshrc_file_path: Path to the user's ``.zshrc`` file to update.
        zshrc_file_content: Current contents of ``.zshrc``, used to avoid
                             duplicate entries.
        env: Optional environment variables to pass when running
             ``command``. If None, the command runs with the current
             process environment.
    """
    if env is None:
        output = _execute_command(command, capture_output=True)
    else:
        output = _execute_command(command, capture_output=True, env=env)
    completion_file_path = os.path.join(completion_folder, f"{app_name}-complete.zsh")
    _write_to_file(completion_file_path, output.stdout, "w")

    load_compinit = "autoload -Uz compinit && compinit"
    if "compinit" not in zshrc_file_content:
        _write_to_file(zshrc_file_path, load_compinit)

    source_file_command = f". {completion_file_path}"
    if source_file_command not in zshrc_file_content:
        _write_to_file(zshrc_file_path, source_file_command)


def _init_shell(uv: bool, uvl: bool, click_package_name: str | None) -> None:
    """Install zsh completion for uv, uvl, and/or another click-based CLI.

    Ensures the ``~/.complete`` folder exists, then for each requested tool
    generates its zsh completion script and wires it into ``~/.zshrc`` via
    :func:`_create_completion_files`. When ``uvl`` completion is requested,
    also appends a small ``uvl`` zsh wrapper function (``_uvl_zsh_script``)
    that re-exports ``.env`` values after each invocation.

    Args:
        uv: If True, install completion for the ``uv`` CLI.
        uvl: If True, install completion for the ``uvl`` CLI and the
             ``uvl`` zsh wrapper function.
        click_package_name: If provided, install completion for an
            arbitrary click-based CLI with this executable name.
    """
    home_dir = os.path.expanduser("~")
    zshrc_file_path = os.path.join(home_dir, ".zshrc")
    with open(zshrc_file_path) as f:
        zshrc_file_content = f.read()

    completion_folder = os.path.join(home_dir, ".complete")
    os.makedirs(completion_folder, exist_ok=True)
    if uv:
        _create_completion_files(
            "uv", ["uv", "generate-shell-completion", "zsh"], completion_folder, zshrc_file_path, zshrc_file_content
        )
    if uvl:
        if _uvl_zsh_script not in zshrc_file_content:
            _write_to_file(zshrc_file_path, _uvl_zsh_script)
        my_env = os.environ.copy()
        my_env["_UVL_COMPLETE"] = "zsh_source"
        _create_completion_files("uvl", ["uvl"], completion_folder, zshrc_file_path, zshrc_file_content, env=my_env)
    if click_package_name:
        my_env = os.environ.copy()
        my_env[f"_{click_package_name.upper().replace('-', '_')}_COMPLETE"] = "zsh_source"
        _create_completion_files(
            click_package_name, [click_package_name], completion_folder, zshrc_file_path, zshrc_file_content, env=my_env
        )
