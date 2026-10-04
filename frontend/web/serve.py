"""
serve.py — Lightweight local static file server for the web frontend.
Serves frontend/web/ at http://localhost:5500

Usage:
    python frontend/web/serve.py
"""

import http.server
import socketserver
import os
import webbrowser
from pathlib import Path

PORT = 5500
DIRECTORY = Path(__file__).parent   # frontend/web/


class CORSHandler(http.server.SimpleHTTPRequestHandler):
    """Static file handler with CORS headers so the browser
    can call the FastAPI backend on localhost:8000."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        super().end_headers()

    def log_message(self, fmt, *args):
        # Quieter log — only print non-200 responses and key events
        code = args[1] if len(args) > 1 else "???"
        if str(code) not in ("200", "304"):
            super().log_message(fmt, *args)


def main():
    os.chdir(DIRECTORY)

    with socketserver.TCPServer(("", PORT), CORSHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 56)
        print("  TripCostAI — Web Frontend Server")
        print("=" * 56)
        print(f"  Serving : {DIRECTORY}")
        print(f"  URL     : {url}")
        print(f"  Backend : http://localhost:8000  (must be running)")
        print("=" * 56)
        print("  Press Ctrl+C to stop.\n")

        try:
            webbrowser.open(url)
        except Exception:
            pass

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped.")


if __name__ == "__main__":
    main()
