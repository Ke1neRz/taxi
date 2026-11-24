import json
import threading
from http.client import HTTPConnection

from generator.control import ControlServer


def _request(server: ControlServer, method: str, path: str) -> tuple[int, dict[str, str]]:
    host, port = server.address
    connection = HTTPConnection(host, port, timeout=2)
    connection.request(method, path)
    response = connection.getresponse()
    payload = json.loads(response.read())
    connection.close()
    return response.status, payload


def test_control_server_reports_health_and_stops_generator() -> None:
    stop_event = threading.Event()
    server = ControlServer("127.0.0.1", 0, stop_event)
    server.start()

    try:
        assert _request(server, "GET", "/health") == (200, {"status": "ok"})
        assert _request(server, "GET", "/status") == (200, {"status": "running"})
        assert _request(server, "POST", "/stop") == (200, {"status": "stopping"})
        assert stop_event.is_set()
        assert _request(server, "GET", "/status") == (200, {"status": "stopping"})
    finally:
        server.close()
