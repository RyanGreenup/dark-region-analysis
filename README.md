# dark-region-analysis

Detect dark regions on a white rectangle surrounded by bright textured blobs.

The CLI adapts the research prototype in `sam-overlay` into a small Python
package with typed, documented modules. It detects the smooth white rectangle,
finds dark holes enclosed by that rectangle, reports measurements, and writes an
annotated image.

## Prerequisites

- **uv** ([install](https://docs.astral.sh/uv/getting-started/installation/))
- **just** ([install](https://github.com/casey/just)) for the task runner (optional)

## Quick start

```bash
uv sync --all-extras --dev          # create .venv and install dev tools
uv run dark-region-analysis --help
just check                          # fmt + lint + type + test
git init && uv run pre-commit install
```

## CLI

The generated command is installed from `[project.scripts]`:

```bash
uv run dark-region-analysis --help
uv run dark-region-analysis detect input.jpeg annotated.jpeg
uv run dark-region-analysis regions input.jpeg annotated.jpeg
uv run dark-region-analysis regions input.jpeg annotated.jpeg --report-format json
```

`detect` finds the white rectangle and saves a bounding-box annotation.

`regions` finds dark regions inside the rectangle, prints their measurements,
and saves an annotation with labels and lines from the rectangle center.

Key options:

| Option | Default | Meaning |
|--------|---------|---------|
| `--dark-value` | `0.85` | Maximum normalized brightness for a dark mark |
| `--min-area-frac` | `0.0002` | Minimum region area as a fraction of rectangle area |
| `--max-aspect` | `3.0` | Maximum bounding-box aspect ratio for accepted regions |
| `--report-format` | `plain` | Output format: `plain`, `json`, or `csv` |

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
src/dark_region_analysis/models.py
                          measurement dataclasses
src/dark_region_analysis/detection.py
                          pure image-analysis functions
src/dark_region_analysis/annotation.py
                          Pillow drawing helpers
src/dark_region_analysis/reporting.py
                          plain, JSON, and CSV reports
src/dark_region_analysis/cli.py
                          Typer commands and console entry point
tests/                    pytest suite
pyproject.toml            project + ruff + pyright + pytest + coverage config
.pre-commit-config.yaml   ruff + uv-lock hooks
```

## Notes

- ruff is set to `select = ["ALL"]` with docstring rules (`D`) disabled by default.
  Turn the subset you want back on in `pyproject.toml` under `[tool.ruff.lint]`.
- Tests relax a few rules (`S101`, `PLR2004`, `ANN`) via `per-file-ignores`.
- `uv.lock` is gitignored by default; remove it from `.gitignore` if you want to commit
  a pinned lockfile (recommended for applications, optional for libraries).
