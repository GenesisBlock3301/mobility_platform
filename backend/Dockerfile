# syntax=docker/dockerfile:1
FROM python:3.14.10-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /usr/local/bin/uv
WORKDIR /app

# Runtime image: production dependencies only, runs as a non-root user.
FROM base AS runtime
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY data ./data
RUN useradd --system --uid 10001 --no-create-home appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-server-header"]

# Test image: adds development dependencies and the test suite.
FROM base AS test
ENV PYTEST_ADDOPTS="-p no:cacheprovider" \
    HOME=/tmp
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project
COPY . .
RUN useradd --system --uid 10001 --no-create-home appuser
USER appuser
CMD ["pytest", "-q"]
