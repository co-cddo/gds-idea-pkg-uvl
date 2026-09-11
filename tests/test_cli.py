"""Tests for uvl.cli."""

import pytest
from click.testing import CliRunner

import uvl.init
import uvl.init_shell
import uvl.prerequisites
from uvl.cli import cli, complete_uv_project


@pytest.fixture
def runner():
    return CliRunner()


class TestCliGroup:
    def test_help(self, runner):
        result = runner.invoke(cli, ["--help"])

        assert result.exit_code == 0
        assert "manage multiple uv projects in one directory" in result.output

    def test_version_option(self, runner):
        result = runner.invoke(cli, ["--version"])

        assert result.exit_code == 0
        assert "uvl" in result.output

    def test_no_args_does_not_trigger_default_command(self, runner, monkeypatch):
        called = {"init": False}
        monkeypatch.setattr(uvl.init, "_init", lambda *a, **k: called.__setitem__("init", True))
        monkeypatch.setattr(uvl.prerequisites, "_check_prerequisites", lambda *a, **k: None)

        runner.invoke(cli, [])

        assert called["init"] is False


class TestInitCommand:
    def test_checks_prerequisites_before_init(self, runner, monkeypatch):
        call_order = []
        monkeypatch.setattr(uvl.prerequisites, "_check_prerequisites", lambda *a, **k: call_order.append("prereqs"))
        monkeypatch.setattr(uvl.init, "_init", lambda *a, **k: call_order.append("init"))

        result = runner.invoke(cli, ["init", "myproj"])

        assert result.exit_code == 0
        assert call_order == ["prereqs", "init"]

    def test_passes_positional_and_flags_to_init(self, runner, monkeypatch):
        captured = {}

        def fake_init(uv_projects_directory, uv_project, create_if_not_exists, add_local_group):
            captured.update(
                uv_projects_directory=uv_projects_directory,
                uv_project=uv_project,
                create_if_not_exists=create_if_not_exists,
                add_local_group=add_local_group,
            )

        monkeypatch.setattr(uvl.prerequisites, "_check_prerequisites", lambda *a, **k: None)
        monkeypatch.setattr(uvl.init, "_init", fake_init)

        result = runner.invoke(
            cli,
            [
                "init",
                "myproj",
                "--uv-projects-directory",
                "projects",
                "--create-if-not-exists",
                "--add-local-group",
            ],
        )

        assert result.exit_code == 0
        assert captured == {
            "uv_projects_directory": "projects",
            "uv_project": "myproj",
            "create_if_not_exists": True,
            "add_local_group": True,
        }

    def test_defaults_when_no_flags_given(self, runner, monkeypatch):
        captured = {}

        def fake_init(uv_projects_directory, uv_project, create_if_not_exists, add_local_group):
            captured.update(
                uv_projects_directory=uv_projects_directory,
                uv_project=uv_project,
                create_if_not_exists=create_if_not_exists,
                add_local_group=add_local_group,
            )

        monkeypatch.setattr(uvl.prerequisites, "_check_prerequisites", lambda *a, **k: None)
        monkeypatch.setattr(uvl.init, "_init", fake_init)

        result = runner.invoke(cli, ["init", "myproj"])

        assert result.exit_code == 0
        assert captured == {
            "uv_projects_directory": None,
            "uv_project": "myproj",
            "create_if_not_exists": False,
            "add_local_group": False,
        }

    def test_bare_project_name_routes_to_init_via_default_group(self, runner, monkeypatch):
        captured = {}

        def fake_init(uv_projects_directory, uv_project, create_if_not_exists, add_local_group):
            captured["uv_project"] = uv_project

        monkeypatch.setattr(uvl.prerequisites, "_check_prerequisites", lambda *a, **k: None)
        monkeypatch.setattr(uvl.init, "_init", fake_init)

        result = runner.invoke(cli, ["myproj"])

        assert result.exit_code == 0
        assert captured["uv_project"] == "myproj"


class TestInitShellCommand:
    def test_passes_flags_to_init_shell(self, runner, monkeypatch):
        captured = {}

        def fake_init_shell(uv, uvl, click_package_name):
            captured.update(uv=uv, uvl=uvl, click_package_name=click_package_name)

        monkeypatch.setattr(uvl.init_shell, "_init_shell", fake_init_shell)

        result = runner.invoke(cli, ["init-shell", "--uv", "--uvl", "--click-package-name", "my-tool"])

        assert result.exit_code == 0
        assert captured == {"uv": True, "uvl": True, "click_package_name": "my-tool"}

    def test_defaults_when_no_flags_given(self, runner, monkeypatch):
        captured = {}

        def fake_init_shell(uv, uvl, click_package_name):
            captured.update(uv=uv, uvl=uvl, click_package_name=click_package_name)

        monkeypatch.setattr(uvl.init_shell, "_init_shell", fake_init_shell)

        result = runner.invoke(cli, ["init-shell"])

        assert result.exit_code == 0
        assert captured == {"uv": False, "uvl": False, "click_package_name": None}


class TestCompleteUvProject:
    def test_lists_folders_with_matching_prefix_and_pyproject(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "project-alpha").mkdir()
        (tmp_path / "project-alpha" / "pyproject.toml").write_text("")
        (tmp_path / "project-beta").mkdir()
        (tmp_path / "project-beta" / "pyproject.toml").write_text("")
        (tmp_path / "other").mkdir()
        (tmp_path / "other" / "pyproject.toml").write_text("")

        result = complete_uv_project(None, None, "project-")

        assert sorted(result) == ["project-alpha", "project-beta"]

    def test_excludes_folders_without_pyproject(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "project-alpha").mkdir()
        (tmp_path / "project-alpha" / "pyproject.toml").write_text("")
        (tmp_path / "project-no-pyproject").mkdir()

        result = complete_uv_project(None, None, "project-")

        assert result == ["project-alpha"]

    def test_uses_uv_projects_directory_from_env_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        projects_dir = tmp_path / "elsewhere"
        projects_dir.mkdir()
        (projects_dir / "myproj").mkdir()
        (projects_dir / "myproj" / "pyproject.toml").write_text("")
        (tmp_path / ".env").write_text(f'UV_PROJECTS_DIRECTORY="{projects_dir}"\n')

        result = complete_uv_project(None, None, "my")

        assert result == ["myproj"]

    def test_defaults_to_cwd_when_no_env_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "myproj").mkdir()
        (tmp_path / "myproj" / "pyproject.toml").write_text("")

        result = complete_uv_project(None, None, "my")

        assert result == ["myproj"]

    def test_empty_incomplete_matches_all_projects(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        (tmp_path / "a").mkdir()
        (tmp_path / "a" / "pyproject.toml").write_text("")
        (tmp_path / "b").mkdir()
        (tmp_path / "b" / "pyproject.toml").write_text("")

        result = complete_uv_project(None, None, "")

        assert sorted(result) == ["a", "b"]
