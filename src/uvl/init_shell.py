import os

from uvl.utils import _execute_command


def _create_completion_files(
    app_name: str,
    command: list[str],
    completion_folder: str,
    zshrc_file_path: str,
    zshrc_file_content: str,
    env: dict[str] = None,
):
    if env is None:
        output = _execute_command(command, capture_output=True)
    else:
        output = _execute_command(command, capture_output=True, env=env)
    completion_file_path = os.path.join(completion_folder, f"{app_name}-complete.zsh")
    with open(completion_file_path, "w") as f:
        f.write(output.stdout)

    load_compinit = "autoload -Uz compinit && compinit"
    if "compinit" not in zshrc_file_content:
        with open(zshrc_file_path, "a") as f:
            f.write("\n")
            f.write(load_compinit)
            f.write("\n")

    source_file_command = f". {completion_file_path}"
    if source_file_command not in zshrc_file_content:
        with open(zshrc_file_path, "a") as f:
            f.write("\n")
            f.write(source_file_command)
            f.write("\n")


def _init_shell(uv: bool, uvl: bool, click_package_name: str):
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
        my_env = os.environ
        my_env["_UVL_COMPLETE"] = "zsh_source"
        _create_completion_files("uvl", ["uvl"], completion_folder, zshrc_file_path, zshrc_file_content, env=my_env)
    if click_package_name:
        my_env = os.environ
        my_env[f"_{click_package_name.upper().replace('-', '_')}_COMPLETE"] = "zsh_source"
        _create_completion_files(
            click_package_name, [click_package_name], completion_folder, zshrc_file_path, zshrc_file_content, env=my_env
        )
