default: check

check: fmt lint type test

tailwind-install:
    npm install

tailwind-build:
    npm run build:css

tailwind-watch:
    npm run watch:css

web:
    uv run dark-region-analysis-web

fmt:
    uv run ruff format --check .

lint:
    uv run ruff check .

type:
    uv run pyright

test:
    uv run pytest
