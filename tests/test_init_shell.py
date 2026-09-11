"""Tests for uvl.init_shell."""

import os

import pytest

import uvl.init_shell as init_shell_module
from uvl.init_shell import _create_completion_files, _init_shell, _uvl_zsh_script


class _FakeCompletedProcess:
    def __init__(self, stdout: str):
        self.stdout = stdout
        self.stderr = ""
        self.returncode = 0


@pytest.fixture
def record_execute_command(monkeypatch):
    calls = []

    def fake_execute_command(command, capture_output=False, env=None):
        calls.append({"command": command, "capture_output": capture_output, "env": env})
        return _FakeCompletedProcess(stdout=f"# completion for {command[0]}")

    monkeypatch.setattr(init_shell_module, "_execute_command", fake_execute_command)
    return calls


class TestCreateCompletionFiles:
    def test_writes_completion_file(self, tmp_path, record_execute_command):
        zshrc_path = tmp_path / ".zshrc"
        zshrc_path.write_text("")
        completion_folder = tmp_path / ".complete"
        completion_folder.mkdir()

        _create_completion_files("myapp", ["myapp", "complete"], str(completion_folder), str(zshrc_path), "")

        completion_file = completion_folder / "myapp-complete.zsh"
        assert completion_file.read_text() == "# completion for myapp"

    def test_appends_compinit_when_missing(self, tmp_path, record_execute_command):
        zshrc_path = tmp_path / ".zshrc"
        zshrc_path.write_text("existing content")
        completion_folder = tmp_path / ".complete"
        completion_folder.mkdir()

        _create_completion_files("myapp", ["myapp"], str(completion_folder), str(zshrc_path), "existing content")

        content = zshrc_path.read_text()
        assert "autoload -Uz compinit && compinit" in content

    def test_skips_compinit_when_already_present(self, tmp_path, record_execute_command):
        zshrc_path = tmp_path / ".zshrc"
        existing = "autoload -Uz compinit && compinit\n"
        zshrc_path.write_text(existing)
        completion_folder = tmp_path / ".complete"
        completion_folder.mkdir()

        _create_completion_files("myapp", ["myapp"], str(completion_folder), str(zshrc_path), existing)

        content = zshrc_path.read_text()
        assert content.count("autoload -Uz compinit && compinit") == 1  # unchanged, no duplicate appended

    def test_appends_source_line_when_missing(self, tmp_path, record_execute_command):
        zshrc_path = tmp_path / ".zshrc"
        zshrc_path.write_text("")
        completion_folder = tmp_path / ".complete"
        completion_folder.mkdir()

        _create_completion_files("myapp", ["myapp"], str(completion_folder), str(zshrc_path), "")

        completion_file = completion_folder / "myapp-complete.zsh"
        content = zshrc_path.read_text()
        assert f". {completion_file}" in content

    def test_skips_source_line_when_already_present(self, tmp_path, record_execute_command):
        zshrc_path = tmp_path / ".zshrc"
        completion_folder = tmp_path / ".complete"
        completion_folder.mkdir()
        completion_file = completion_folder / "myapp-complete.zsh"
        existing = f". {completion_file}\n"
        zshrc_path.write_text(existing)

        _create_completion_files("myapp", ["myapp"], str(completion_folder), str(zshrc_path), existing)

        content = zshrc_path.read_text()
        assert content.count(str(completion_file)) == 1

    def test_passes_env_to_execute_command(self, tmp_path, record_execute_command):
        zshrc_path = tmp_path / ".zshrc"
        zshrc_path.write_text("")
        completion_folder = tmp_path / ".complete"
        completion_folder.mkdir()

        _create_completion_files("myapp", ["myapp"], str(completion_folder), str(zshrc_path), "", env={"FOO": "bar"})

        assert record_execute_command[0]["env"] == {"FOO": "bar"}

    def test_omits_env_kwarg_when_not_provided(self, tmp_path, record_execute_command):
        zshrc_path = tmp_path / ".zshrc"
        zshrc_path.write_text("")
        completion_folder = tmp_path / ".complete"
        completion_folder.mkdir()

        _create_completion_files("myapp", ["myapp"], str(completion_folder), str(zshrc_path), "")

        assert record_execute_command[0]["env"] is None


@pytest.fixture
def fake_home(tmp_path, monkeypatch):
    """Redirect os.path.expanduser('~') to a temp directory with a .zshrc file."""
    (tmp_path / ".zshrc").write_text("")

    real_expanduser = os.path.expanduser

    def fake_expanduser(path):
        if path == "~":
            return str(tmp_path)
        return real_expanduser(path)

    monkeypatch.setattr(os.path, "expanduser", fake_expanduser)
    return tmp_path


class TestInitShell:
    def test_does_nothing_when_no_flags_set(self, fake_home, record_execute_command):
        _init_shell(uv=False, uvl=False, click_package_name=None)

        assert record_execute_command == []
        assert (fake_home / ".complete").is_dir()

    def test_installs_uv_completion(self, fake_home, record_execute_command):
        _init_shell(uv=True, uvl=False, click_package_name=None)

        assert len(record_execute_command) == 1
        assert record_execute_command[0]["command"] == ["uv", "generate-shell-completion", "zsh"]
        assert (fake_home / ".complete" / "uv-complete.zsh").exists()

    def test_installs_uvl_completion_and_wrapper_function(self, fake_home, record_execute_command):
        _init_shell(uv=False, uvl=True, click_package_name=None)

        assert record_execute_command[0]["command"] == ["uvl"]
        assert record_execute_command[0]["env"]["_UVL_COMPLETE"] == "zsh_source"
        zshrc_content = (fake_home / ".zshrc").read_text()
        assert _uvl_zsh_script in zshrc_content

    def test_does_not_duplicate_uvl_wrapper_function(self, fake_home, record_execute_command):
        (fake_home / ".zshrc").write_text(_uvl_zsh_script)

        _init_shell(uv=False, uvl=True, click_package_name=None)

        zshrc_content = (fake_home / ".zshrc").read_text()
        assert zshrc_content.count(_uvl_zsh_script.strip()) == 1

    def test_installs_completion_for_arbitrary_click_package(self, fake_home, record_execute_command):
        _init_shell(uv=False, uvl=False, click_package_name="my-tool")

        assert record_execute_command[0]["command"] == ["my-tool"]
        assert record_execute_command[0]["env"]["_MY_TOOL_COMPLETE"] == "zsh_source"
        assert (fake_home / ".complete" / "my-tool-complete.zsh").exists()

    def test_installs_all_three_when_all_flags_set(self, fake_home, record_execute_command):
        _init_shell(uv=True, uvl=True, click_package_name="my-tool")

        commands = [call["command"] for call in record_execute_command]
        assert commands == [
            ["uv", "generate-shell-completion", "zsh"],
            ["uvl"],
            ["my-tool"],
        ]

    def test_creates_completion_folder_if_missing(self, fake_home, record_execute_command):
        assert not (fake_home / ".complete").exists()

        _init_shell(uv=False, uvl=False, click_package_name=None)

        assert (fake_home / ".complete").is_dir()
