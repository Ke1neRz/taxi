# Taxi Streaming Analytics

Учебный end-to-end проект потоковой аналитики поездок на такси.

На текущем этапе создан базовый Python-каркас генератора:
модели, env-конфигурация, backfill/realtime-цикл и HTTP-контроль остановки.

## Local development

```bash
uv sync
uv run pytest
```

## Generator demos

```bash
uv run python demos/01_in_memory.py
uv run python demos/02_control_api.py
```

Для непрерывного запуска с ClickHouse используйте `docker compose up --build`.
Состояние генератора доступно по `GET http://localhost:8080/health`, остановка —
по `POST http://localhost:8080/stop`.
