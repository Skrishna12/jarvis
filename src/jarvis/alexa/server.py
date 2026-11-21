"""Local HTTP endpoint for an Alexa custom skill. Put HTTPS in front (ngrok)."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from jarvis.alexa.skill import alexa_response, handle_skill_body
from jarvis.runtime import app_session


def make_handler() -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, fmt: str, *args) -> None:
            print("alexa:", fmt % args)

        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length)
            try:
                body = json.loads(raw.decode("utf-8") or "{}")
            except json.JSONDecodeError:
                self._write(400, alexa_response("Bad request."))
                return
            if not isinstance(body, dict):
                self._write(400, alexa_response("Bad request."))
                return
            try:
                with app_session() as (session, _settings):
                    payload = handle_skill_body(body, session)
            except Exception as exc:
                payload = alexa_response(f"Jarvis hit an error: {exc}")
            self._write(200, payload)

        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Jarvis Alexa endpoint. POST skill requests here.\n")

        def _write(self, status: int, payload: dict) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    return Handler


def serve(host: str = "127.0.0.1", port: int = 39847) -> None:
    server = ThreadingHTTPServer((host, port), make_handler())
    print(f"Jarvis Alexa skill listening on http://{host}:{port}/")
    print("Amazon needs HTTPS. In another terminal: ngrok http {port}".format(port=port))
    print("Then paste the ngrok https URL into the Alexa skill endpoint.")
    print("Leave this running. Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print()
    finally:
        server.server_close()
