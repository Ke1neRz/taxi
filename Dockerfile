FROM python:3.12-slim

WORKDIR /app

ENV PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

COPY pyproject.toml ./
COPY src ./src

RUN pip install --no-cache-dir \
        "clickhouse-connect>=0.8.0" \
        "pydantic-settings>=2.6.0"

CMD ["python", "-m", "generator", "--repository", "clickhouse"]
