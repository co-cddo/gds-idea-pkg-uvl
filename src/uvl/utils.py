import subprocess
import sys


def _execute_command(command: list[str], capture_output=False):
    try:
        completed_process = subprocess.run(command, check=True, capture_output=capture_output, text=True)
    except subprocess.CalledProcessError:
        sys.exit(1)

    return completed_process
