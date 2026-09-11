import subprocess
import sys


def _execute_command(
    command: list[str], capture_output: bool = False, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess:
    """Run an external command, exiting the process if it fails.

    Args:
        command: The command and its arguments to execute.
        capture_output: If True, capture stdout/stderr on the returned
                        ``CompletedProcess`` instead of inheriting the
                        parent's streams.
        env: Optional environment variables to use for the subprocess. If
             None, the current process environment is inherited.

    Returns:
        The completed process, with ``stdout``/``stderr`` populated as text
        when ``capture_output`` is True.

    Raises:
        SystemExit: If the command exits with a non-zero status.
    """
    try:
        completed_process = subprocess.run(command, check=True, capture_output=capture_output, text=True, env=env)
    except subprocess.CalledProcessError:
        sys.exit(1)

    return completed_process


def _write_to_file(file_path: str, text: str, mode: str = "a") -> None:
    """Write text to a file, optionally surrounding it with newlines.

    Args:
        file_path: Path to the file to write to.
        text: The text content to write.
        mode: File open mode (e.g. ``"a"`` to append, ``"w"`` to overwrite).
              When ``"a"``, a newline is written before and after ``text``.
    """
    with open(file_path, mode) as f:
        if mode == "a":
            f.write("\n")
        f.write(text)
        if mode == "a":
            f.write("\n")
