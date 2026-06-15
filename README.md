# dark-region-analysis

Analysis of dark regions on a white rectangle

A Python Typer CLI scaffolded with [uv](https://docs.astral.sh/uv/), linted and formatted
with [ruff](https://docs.astral.sh/ruff/) (`select = ["ALL"]`), type-checked with
[pyright](https://microsoft.github.io/pyright/) in strict mode, and tested with pytest +
coverage. The package lives at `src/dark_region_analysis/`.

## Prerequisites

- **uv** ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **just** ([install](https://github.com/casey/just)) for the task runner (optional)

## Quick start

```bash
uv sync --all-extras --dev          # create .venv and install dev tools
uv run dark-region-analysis greet Ada # run the exemplar CLI command
just check                          # fmt + lint + type + test
git init && uv run pre-commit install
```

## CLI

The generated command is installed from `[project.scripts]`:

```bash
uv run dark-region-analysis --help
uv run dark-region-analysis greet Ada
```

## Tasks

The `justfile` wraps the common loops:

| Command     | What it does                          |
|-------------|---------------------------------------|
| `just`      | runs `check` (fmt, lint, type, test)  |
| `just fmt`  | `ruff format --check .`               |
| `just lint` | `ruff check .`                        |
| `just type` | `pyright`                             |
| `just test` | `pytest` with coverage                |

Run any underlying tool directly with `uv run <tool>` if you do not have `just`.

## Layout

```
src/dark_region_analysis/   package source
src/dark_region_analysis/cli.py
                          Typer app, exemplar command, and console entry point
tests/                    pytest suite
pyproject.toml            project + ruff + pyright + pytest + coverage config
.pre-commit-config.yaml   ruff + uv-lock hooks
.github/workflows/ci.yml  CI: format check, lint, typecheck, test
```

## Notes

- ruff is set to `select = ["ALL"]` with docstring rules (`D`) disabled by default.
  Turn the subset you want back on in `pyproject.toml` under `[tool.ruff.lint]`.
- Tests relax a few rules (`S101`, `PLR2004`, `ANN`) via `per-file-ignores`.
- `uv.lock` is gitignored by default; remove it from `.gitignore` if you want to commit
  a pinned lockfile (recommended for applications, optional for libraries).
