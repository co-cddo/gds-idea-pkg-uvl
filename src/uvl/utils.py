import subprocess
import sys


def _execute_command(command: list[str], capture_output=False, env=None):
    try:
        completed_process = subprocess.run(command, check=True, capture_output=capture_output, text=True, env=env)
    except subprocess.CalledProcessError:
        sys.exit(1)

    return completed_process


def _write_to_file(file_path, text, mode="a"):
    with open(file_path, mode) as f:
        if mode == "a":
            f.write("\n")
        f.write(text)
        if mode == "a":
            f.write("\n")
