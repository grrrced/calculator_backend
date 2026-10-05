"""HTTP JSON API for the separated calculator backend."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from calculator import ExpressionError, calculate
from database import HistoryRepository

ROOT = Path(__file__).resolve().parent
DB_PATH = os.environ.get("CALCULATOR_DB_PATH", str(ROOT / "data" / "calculator.sqlite3"))
repository = HistoryRepository(DB_PATH)


class CalculatorHandler(BaseHTTPRequestHandler):
    server_version = "CalculatorAPI/1.0"

    def log_message(self, format: str, *args) -> None:
        print(f"[{self.log_date_time_string()}] {format % args}")

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 20_000:
                raise ValueError("Request body is too large")
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(payload, dict):
                raise ValueError("Request body must be a JSON object")
            return payload
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise ExpressionError("Request body must be valid JSON") from error

    def do_OPTIONS(self) -> None:
        self._send_json({"success": True})

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json({"success": True, "service": "calculator-backend"})
            return
        if parsed.path == "/api/history":
            limit = parse_qs(parsed.query).get("limit", ["100"])[0]
            try:
                records = repository.list(int(limit))
            except ValueError:
                self._send_json({"success": False, "message": "limit must be an integer"}, HTTPStatus.BAD_REQUEST)
                return
            self._send_json({"success": True, "items": records})
            return
        self._send_json({"success": False, "message": "Not found"}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/calculate":
            self._send_json({"success": False, "message": "Not found"}, HTTPStatus.NOT_FOUND)
            return
        try:
            payload = self._read_json()
            expression = payload.get("expression")
            if not isinstance(expression, str):
                raise ExpressionError("expression must be a string")
            expression = expression.strip()
            result = calculate(expression)
            record = repository.add(expression, result)
            self._send_json({"success": True, **record}, HTTPStatus.CREATED)
        except ExpressionError as error:
            self._send_json({"success": False, "message": str(error)}, HTTPStatus.BAD_REQUEST)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/history":
            deleted = repository.clear()
            self._send_json({"success": True, "deleted": deleted})
            return
        prefix = "/api/history/"
        if parsed.path.startswith(prefix):
            try:
                record_id = int(parsed.path[len(prefix):])
            except ValueError:
                self._send_json({"success": False, "message": "Invalid history id"}, HTTPStatus.BAD_REQUEST)
                return
            if repository.delete(record_id):
                self._send_json({"success": True, "id": record_id})
            else:
                self._send_json({"success": False, "message": "History record not found"}, HTTPStatus.NOT_FOUND)
            return
        self._send_json({"success": False, "message": "Not found"}, HTTPStatus.NOT_FOUND)


def main() -> None:
    host = os.environ.get("CALCULATOR_HOST", "127.0.0.1")
    port = int(os.environ.get("CALCULATOR_PORT", os.environ.get("PORT", "8000")))
    server = ThreadingHTTPServer((host, port), CalculatorHandler)
    print(f"Calculator backend listening at http://{host}:{port}")
    print(f"SQLite database: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping calculator backend")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
