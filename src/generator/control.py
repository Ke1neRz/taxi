"""HTTP-контроль жизненного цикла генератора такси."""

from __future__ import annotations

import json
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


class ControlServer:
    """Запустить минимальный HTTP API для проверки состояния и остановки."""

    def __init__(self, host: str, port: int, stop_event: threading.Event) -> None:
        """Создать сервер, связанный с событием остановки генератора."""

        self._stop_event = stop_event
        self._server = ThreadingHTTPServer((host, port), self._handler_class())
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)

    @property
    def address(self) -> tuple[str, int]:
        """Вернуть фактический адрес, включая выбранный системой порт."""

        host, port = self._server.server_address[:2]
        return str(host), int(port)

    def start(self) -> None:
        """Запустить HTTP-сервер в фоновом потоке."""

        self._thread.start()

    def close(self) -> None:
        """Остановить HTTP-сервер и дождаться его фонового потока."""

        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=2.0)

    def _handler_class(self) -> type[BaseHTTPRequestHandler]:
        """Создать обработчик с доступом к событию текущего сервера."""

        stop_event = self._stop_event

        class Handler(BaseHTTPRequestHandler):
            """Обработать endpoints контроля генератора."""

            def do_GET(self) -> None:
                """Вернуть health или состояние процесса в JSON."""

                if self.path == "/health":
                    self._send_json(HTTPStatus.OK, {"status": "ok"})
                elif self.path == "/status":
                    self._send_json(
                        HTTPStatus.OK,
                        {"status": "stopping" if stop_event.is_set() else "running"},
                    )
                else:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

            def do_POST(self) -> None:
                """Принять команду остановки генератора."""

                if self.path == "/stop":
                    stop_event.set()
                    self._send_json(HTTPStatus.OK, {"status": "stopping"})
                else:
                    self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

            def log_message(self, format: str, *args: Any) -> None:
                """Не писать стандартные access-логи в stderr процесса."""

                del format, args

            def _send_json(self, status: HTTPStatus, payload: dict[str, str]) -> None:
                """Отправить компактный JSON-ответ с корректными заголовками."""

                body = json.dumps(payload).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        return Handler
