from __future__ import annotations

import json
import mimetypes
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from fanta.config import AppConfig
from fanta.schemas import EventInput
from fanta.services.planner import ConferencePlannerService


ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"


class FantaRequestHandler(BaseHTTPRequestHandler):
    server_version = "FantaServer/1.0"

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/api/health":
          self._send_json({"status": "ok"})
          return

        if parsed.path == "/api/latest-plan":
            self._handle_latest_plan()
            return

        self._serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/plan":
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(content_length) or b"{}")
            event = EventInput(
                category=payload.get("category", "AI"),
                location=payload.get("location", "India"),
                audience_size=int(payload.get("audience_size", 500)),
                topic=payload.get("topic", "Large Language Models"),
                budget=payload.get("budget", "50 lakhs"),
            )

            service = ConferencePlannerService(AppConfig.from_env())
            result = service.run(event, save_outputs=True)
            self._send_json(result.to_dict())
        except Exception as exc:  # pragma: no cover
            self._send_json(
                {"error": "Planner execution failed", "details": str(exc)},
                status=HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    def _handle_latest_plan(self) -> None:
        plan_path = AppConfig.from_env().output_plan_path
        if not plan_path.exists():
            self._send_json({"error": "conference_plan.json not found"}, status=HTTPStatus.NOT_FOUND)
            return

        with plan_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        self._send_json(payload)

    def _serve_static(self, path: str) -> None:
        if path in ("/", ""):
            target = FRONTEND_DIR / "index.html"
        elif path.startswith("/frontend/"):
            relative = path.removeprefix("/frontend/")
            target = FRONTEND_DIR / relative
        else:
            self._send_json({"error": "Not found"}, status=HTTPStatus.NOT_FOUND)
            return

        if not target.exists() or not target.is_file():
            self._send_json({"error": "File not found"}, status=HTTPStatus.NOT_FOUND)
            return

        content_type, _ = mimetypes.guess_type(target.name)
        with target.open("rb") as handle:
            data = handle.read()

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def run_server(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), FantaRequestHandler)
    print(f"Serving Fanta on http://{host}:{port}/frontend/")
    server.serve_forever()


if __name__ == "__main__":
    run_server()
