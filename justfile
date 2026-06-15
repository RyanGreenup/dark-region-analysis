default: check

check: fmt lint type test

fmt:
    uv run ruff format --check .

lint:
    uv run ruff check .

type:
    uv run pyright

test:
    uv run pytest
