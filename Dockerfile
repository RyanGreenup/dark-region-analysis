FROM node:22-bookworm-slim AS assets

WORKDIR /app

COPY package.json ./
COPY src/dark_region_analysis/templates ./src/dark_region_analysis/templates
COPY src/dark_region_analysis/static/src ./src/dark_region_analysis/static/src

RUN npm install
RUN npm run build:css

FROM ghcr.io/astral-sh/uv:python3.13-alpine AS app

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV UV_NO_CACHE=1

RUN apk upgrade --no-cache

COPY pyproject.toml README.md ./
COPY src ./src
COPY --from=assets /app/src/dark_region_analysis/static/dist ./src/dark_region_analysis/static/dist

RUN uv sync --no-dev --no-cache && rm -rf /root/.cache/uv

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "dark-region-analysis-web"]
