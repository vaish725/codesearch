#!/usr/bin/env python3
"""
Launch the CodeSearch web UI.
"""

import sys
import webbrowser
import time
import threading

try:
    import uvicorn
except ImportError:
    print("❌ FastAPI/Uvicorn not installed. Installing web dependencies...")
    import subprocess

    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "fastapi", "uvicorn[standard]", "pydantic"]
    )
    import uvicorn

from codesearch.web.api import app


def open_browser(url: str, delay: float = 1.5):
    """Open browser after a short delay."""
    time.sleep(delay)
    print(f"\n🌐 Opening browser at {url}")
    webbrowser.open(url)


def main():
    """Launch the web UI."""
    host = "127.0.0.1"
    port = 8080
    url = f"http://{host}:{port}"

    print("=" * 60)
    print("🚀 Starting CodeSearch Web UI")
    print("=" * 60)
    print(f"\n📍 URL: {url}")
    print("📝 API Docs: {}/docs".format(url))
    print("\n💡 Press Ctrl+C to stop the server\n")

    # Open browser in background
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    # Start server
    try:
        uvicorn.run(app, host=host, port=port, log_level="info", access_log=True)
    except KeyboardInterrupt:
        print("\n\n👋 Shutting down CodeSearch Web UI...")
        sys.exit(0)


if __name__ == "__main__":
    main()
