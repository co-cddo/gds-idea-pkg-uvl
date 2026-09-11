"""Tests for uvl.prerequisites."""

import subprocess

import pytest

from uvl.prerequisites import _check_prerequisites


class TestCheckPrerequisites:
    def test_passes_when_all_tools_available(self, monkeypatch):
        monkeypatch.setattr(
            subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(args, 0),
        )

        _check_prerequisites()

    def test_exits_when_tool_missing_file_not_found(self, monkeypatch):
        def fake_run(*args, **kwargs):
            raise FileNotFoundError

        monkeypatch.setattr(subprocess, "run", fake_run)

        with pytest.raises(SystemExit) as exc_info:
            _check_prerequisites()

        assert exc_info.value.code == 1

    def test_exits_when_tool_check_command_fails(self, monkeypatch):
        def fake_run(*args, **kwargs):
            raise subprocess.CalledProcessError(1, args[0] if args else [])

        monkeypatch.setattr(subprocess, "run", fake_run)

        with pytest.raises(SystemExit) as exc_info:
            _check_prerequisites()

        assert exc_info.value.code == 1

    def test_prints_missing_tools_to_stderr(self, monkeypatch, capsys):
        def fake_run(*args, **kwargs):
            raise FileNotFoundError

        monkeypatch.setattr(subprocess, "run", fake_run)

        with pytest.raises(SystemExit):
            _check_prerequisites()

        captured = capsys.readouterr()
        assert "uv" in captured.err
        assert "brew install uv" in captured.err

    def test_only_filters_checked_tools(self, monkeypatch):
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0)

        monkeypatch.setattr(subprocess, "run", fake_run)

        _check_prerequisites(only=["nonexistent-tool"])

        assert calls == []

    def test_only_still_checks_matching_tool(self, monkeypatch):
        calls = []

        def fake_run(command, **kwargs):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0)

        monkeypatch.setattr(subprocess, "run", fake_run)

        _check_prerequisites(only=["uv"])

        assert calls == [["uv", "--version"]]
