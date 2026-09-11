"""Tests for uvl.init."""

import os

import pytest
from dotenv import dotenv_values

import uvl.init as init_module
from uvl.init import _init


@pytest.fixture
def project_dir(tmp_path, monkeypatch):
    """Chdir into a fresh temp directory to act as the uvl invocation root."""
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def record_execute_command(monkeypatch):
    """Replace _execute_command with a recorder that returns success."""
    calls: list[list[str]] = []

    def fake_execute_command(command, capture_output=False, env=None):
        calls.append(command)

        class _Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return _Result()

    monkeypatch.setattr(init_module, "_execute_command", fake_execute_command)
    return calls


class TestInitHappyPath:
    def test_persists_env_values_and_syncs(self, project_dir, record_execute_command):
        project = project_dir / "projects" / "myproj"
        project.mkdir(parents=True)
        (project / "pyproject.toml").write_text("[project]\nname = 'myproj'\n")

        _init(uv_projects_directory="projects", uv_project="myproj")

        env = dotenv_values(str(project_dir / ".env"))
        assert env["UV_PROJECT_ENVIRONMENT"] == os.path.join(str(project_dir), ".venv")
        assert env["UV_PROJECTS_DIRECTORY"] == os.path.join(str(project_dir), "projects")
        assert env["UV_PROJECT"] == os.path.join(str(project_dir), "projects", "myproj")
        assert record_execute_command == [["uv", "sync"]]

    def test_does_not_overwrite_existing_uv_project_environment(self, project_dir, record_execute_command):
        project = project_dir / "projects" / "myproj"
        project.mkdir(parents=True)
        (project / "pyproject.toml").write_text("[project]\nname = 'myproj'\n")
        env_file = project_dir / ".env"
        env_file.write_text('UV_PROJECT_ENVIRONMENT="/custom/venv"\n')

        _init(uv_projects_directory="projects", uv_project="myproj")

        env = dotenv_values(str(env_file))
        assert env["UV_PROJECT_ENVIRONMENT"] == "/custom/venv"

    def test_uses_dependency_group_local_sync_when_present(self, project_dir, record_execute_command):
        project = project_dir / "projects" / "myproj"
        project.mkdir(parents=True)
        (project / "pyproject.toml").write_text(
            "[project]\nname = 'myproj'\n\n[dependency-groups]\nlocal = [\"ipykernel\"]\n"
        )

        _init(uv_projects_directory="projects", uv_project="myproj")

        assert record_execute_command == [["uv", "sync", "--group", "local"]]

    def test_add_local_group_adds_ipykernel_before_sync(self, project_dir, record_execute_command):
        project = project_dir / "projects" / "myproj"
        project.mkdir(parents=True)
        (project / "pyproject.toml").write_text("[project]\nname = 'myproj'\n")

        _init(uv_projects_directory="projects", uv_project="myproj", add_local_group=True)

        assert record_execute_command == [
            ["uv", "add", "--group", "local", "ipykernel"],
            ["uv", "sync"],
        ]


class TestInitMissingProject:
    def test_exits_when_project_missing_and_create_if_not_exists_false(
        self, project_dir, record_execute_command, capsys
    ):
        with pytest.raises(SystemExit) as exc_info:
            _init(uv_projects_directory="projects", uv_project="myproj", create_if_not_exists=False)

        assert exc_info.value.code == 1
        assert "myproj project does not exists." in capsys.readouterr().err
        assert record_execute_command == []

    def test_scaffolds_project_when_create_if_not_exists_true(self, project_dir, record_execute_command):
        _init(uv_projects_directory="projects", uv_project="myproj", create_if_not_exists=True)

        project = project_dir / "projects" / "myproj"
        assert project.is_dir()
        assert record_execute_command[0] == [
            "uv",
            "init",
            "--app",
            "--no-package",
            "--author-from",
            "auto",
            "--name",
            "myproj",
            str(project),
        ]
        # No pyproject.toml was actually produced (execute_command mocked), so
        # the dependency-groups check falls through to a plain sync.
        assert record_execute_command[1] == ["uv", "sync"]


class TestInitReadsFromEnv:
    def test_reads_uv_project_from_existing_env_when_not_provided(self, project_dir, record_execute_command):
        project = project_dir / "projects" / "myproj"
        project.mkdir(parents=True)
        (project / "pyproject.toml").write_text("[project]\nname = 'myproj'\n")
        env_file = project_dir / ".env"
        env_file.write_text(f'UV_PROJECT="{project}"\n')

        _init(uv_projects_directory="projects")

        assert record_execute_command == [["uv", "sync"]]

    def test_reads_uv_projects_directory_from_existing_env_when_not_provided(self, project_dir, record_execute_command):
        project = project_dir / "projects" / "myproj"
        project.mkdir(parents=True)
        (project / "pyproject.toml").write_text("[project]\nname = 'myproj'\n")
        env_file = project_dir / ".env"
        env_file.write_text(f'UV_PROJECTS_DIRECTORY="{project_dir / "projects"}"\n')

        _init(uv_project="myproj")

        assert record_execute_command == [["uv", "sync"]]

    def test_defaults_uv_projects_directory_to_cwd_when_not_in_env(self, project_dir, record_execute_command):
        (project_dir / "pyproject.toml").write_text("[project]\nname = 'root'\n")
        env_file = project_dir / ".env"
        env_file.write_text(f'UV_PROJECT="{project_dir}"\n')

        _init()

        assert record_execute_command == [["uv", "sync"]]
