FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN uv sync --frozen --no-dev

CMD ["uv", "run", "python", "-m", "generator", "--repository", "clickhouse"]
