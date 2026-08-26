# syntax=docker/dockerfile:1
FROM python:3.14.7-slim-trixie@sha256:83ff1d245a3d57d04152252d3ef9cb361494d0b3395abd65a5ebe91c401c8e83 AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
	PYTHONUNBUFFERED=1 \
	PYTHONFAULTHANDLER=1 \
	UV_NO_CACHE=1 \
	UV_NO_DEV=1 \
	UV_LINK_MODE=copy \
	UV_COMPILE_BYTECODE=1 \
	UV_PYTHON_DOWNLOADS=never \
	UV_PROJECT_ENVIRONMENT=/app/.venv



FROM base AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.5 /uv /uvx /bin/
WORKDIR /app

# install dependencies only
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --frozen --no-install-project --no-dev

# install the project itself
COPY . .
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --frozen --no-dev



FROM base AS runtime
RUN groupadd -g 1000 app && useradd -u 1000 -g app -r -s /usr/sbin/nologin app
WORKDIR /app
RUN mkdir -p /var/lib/viperlith && chown -R app:app /var/lib/viperlith
COPY --from=build --chown=app:app /app /app
USER app

ENV DEBUG=0
ENTRYPOINT ["./launch.sh"]
