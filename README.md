# gds-idea-pkg-uvl

`uvl` is a small CLI for managing multiple [uv](https://docs.astral.sh/uv/)
projects that live as sibling folders under one parent directory. It stores
per-directory settings in a local `.env` file, can scaffold new `uv`
projects on demand, keeps them synced, and can install zsh shell completion
for `uv`, `uvl`, and other Click-based CLIs.

## Installation

`uvl` is installed as a global CLI tool, not as a per-project dependency. Install it via the [GDS IDEA package index](https://co-cddo.github.io/gds-idea-pypi/).

**Recommended — using `idea-tools`** (see the [index page](https://co-cddo.github.io/gds-idea-pypi/) for one-time setup):

```bash
idea-tools install gds-idea-pkg-uvl
```

**Alternative — without `idea-tools`:**

```bash
uv tool install gds-idea-pkg-uvl --index gds-idea=https://co-cddo.github.io/gds-idea-pypi/simple/
```

To upgrade to the latest version:

```bash
idea-tools upgrade gds-idea-pkg-uvl
# or without idea-tools:
uv tool upgrade gds-idea-pkg-uvl
```

If you previously installed from a git URL, switch to the index:

```bash
idea-tools install gds-idea-pkg-uvl --reinstall
```

Verify it's working:

```bash
uvl --version
```

## Usage

`uvl` expects a parent directory containing one or more `uv` project
folders (each with its own `pyproject.toml`). Run `uvl` commands from that
parent directory; settings are persisted to a `.env` file there.

### Initialize/sync an existing project

```bash
cd ~/code/my-projects   # parent directory holding several uv projects
uvl init my-service
```

This records `UV_PROJECT` (and `UV_PROJECT_ENVIRONMENT`) in `.env` and runs
`uv sync` for `my-service`. Because `init` is the default command, the
shorthand below is equivalent:

```bash
uvl my-service
```

### Scaffold a brand-new project

```bash
uvl init new-service --create-if-not-exists
```

If `new-service/pyproject.toml` doesn't exist yet, it's created via
`uv init --app --no-package` before syncing.

### Point at a different projects directory

```bash
uvl init my-service --uv-projects-directory ../other-projects
```

Stores `UV_PROJECTS_DIRECTORY` in `.env` so subsequent `uvl` calls (and
shell completion) default to that directory.

### Add a local `ipykernel` dependency group

```bash
uvl init my-service --add-local-group
```

Adds `ipykernel` under a `local` dependency group (handy for Jupyter
notebooks) before syncing, e.g. for `uv run --group local jupyter lab`.

### Install shell completion

```bash
uvl init-shell --uv --uvl
```

Generates zsh completion scripts for `uv` and `uvl` under `~/.complete` and
wires them into `~/.zshrc` (adding `compinit` if needed). Pass
`--click-package-name <name>` to install completion for any other
Click-based CLI:

```bash
uvl init-shell --click-package-name my-other-cli
```

Run `uvl --help`, `uvl init --help`, or `uvl init-shell --help` for the
full list of options.

## Contributing

### Prerequisites

- [uv](https://docs.astral.sh/uv/) for Python package management
- [git](https://git-scm.com/)
- [gitleaks](https://github.com/gitleaks/gitleaks) for pre-commit secret scanning (`brew install gitleaks`)

### Getting started

1. Clone the repository:

   ```bash
   git clone git@github.com:co-cddo/gds-idea-pkg-uvl.git
   cd gds-idea-pkg-uvl
   ```

2. Install dependencies:

   ```bash
   uv sync
   ```

3. Set up pre-commit hooks:

   ```bash
   uv run pre-commit install
   ```

   This is done automatically when the project is first scaffolded.
   Pre-commit runs [ruff](https://docs.astral.sh/ruff/) on every commit
   to auto-fix lint issues and enforce formatting.

## Development

### Running tests

```bash
uv run pytest
```

### Running linting manually

```bash
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

### Pre-commit hooks

Pre-commit hooks run automatically on `git commit`. They will:

- **Auto-fix** lint issues detected by `ruff check --fix`
- **Auto-format** code with `ruff format`
- **Check** YAML/TOML syntax, trailing whitespace, merge conflicts
- **Scan** for leaked secrets with gitleaks
- **Prevent** direct commits to `main`

If files are modified by the hooks, the commit will be aborted.
Review the changes, `git add` them, and commit again.

To run hooks against all files manually:

```bash
uv run pre-commit run --all-files
```

## Versioning

This project uses [hatch-vcs](https://github.com/ofek/hatch-vcs) for
automatic versioning from git tags. Versions are never set manually.

On merge to `main`, the auto-release workflow creates a new tag based on
PR labels:

- `bump:major` — major version bump
- `bump:minor` — minor version bump
- (default) — patch version bump

## Licence

[MIT License](LICENCE)
