"""Tests for uvl.utils."""

import subprocess

import pytest

from uvl.utils import _execute_command, _write_to_file


class TestExecuteCommand:
    def test_returns_completed_process_on_success(self):
        result = _execute_command(["true"])

        assert isinstance(result, subprocess.CompletedProcess)
        assert result.returncode == 0

    def test_captures_output_when_requested(self):
        result = _execute_command(["echo", "hello"], capture_output=True)

        assert result.stdout.strip() == "hello"

    def test_does_not_capture_output_by_default(self):
        result = _execute_command(["echo", "hello"])

        assert result.stdout is None

    def test_exits_with_code_1_when_command_fails(self):
        with pytest.raises(SystemExit) as exc_info:
            _execute_command(["false"])

        assert exc_info.value.code == 1

    def test_exits_with_code_1_when_command_fails_with_captured_output(self):
        with pytest.raises(SystemExit) as exc_info:
            _execute_command(["ls", "/no/such/path/at/all"], capture_output=True)

        assert exc_info.value.code == 1

    def test_uses_provided_env(self, monkeypatch):
        captured = {}

        def fake_run(command, check, capture_output, text, env):
            captured["env"] = env
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)

        _execute_command(["anything"], env={"FOO": "bar"})

        assert captured["env"] == {"FOO": "bar"}

    def test_passes_none_env_when_not_provided(self, monkeypatch):
        captured = {}

        def fake_run(command, check, capture_output, text, env):
            captured["env"] = env
            return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

        monkeypatch.setattr(subprocess, "run", fake_run)

        _execute_command(["anything"])

        assert captured["env"] is None


class TestWriteToFile:
    def test_append_mode_wraps_text_with_newlines(self, tmp_path):
        file_path = tmp_path / "out.txt"
        file_path.write_text("existing")

        _write_to_file(str(file_path), "new content", "a")

        assert file_path.read_text() == "existing\nnew content\n"

    def test_append_mode_is_default(self, tmp_path):
        file_path = tmp_path / "out.txt"
        file_path.write_text("existing")

        _write_to_file(str(file_path), "new content")

        assert file_path.read_text() == "existing\nnew content\n"

    def test_write_mode_overwrites_without_extra_newlines(self, tmp_path):
        file_path = tmp_path / "out.txt"
        file_path.write_text("existing")

        _write_to_file(str(file_path), "new content", "w")

        assert file_path.read_text() == "new content"

    def test_append_mode_creates_file_if_missing(self, tmp_path):
        file_path = tmp_path / "new.txt"

        _write_to_file(str(file_path), "content", "a")

        assert file_path.read_text() == "\ncontent\n"

    def test_multiple_appends_accumulate(self, tmp_path):
        file_path = tmp_path / "out.txt"
        file_path.write_text("start")

        _write_to_file(str(file_path), "first", "a")
        _write_to_file(str(file_path), "second", "a")

        assert file_path.read_text() == "start\nfirst\n\nsecond\n"
