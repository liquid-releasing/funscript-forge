# Copyright (c) 2026 Liquid Releasing. Licensed under the MIT License.
# Written by human and Claude AI (Claude Sonnet).

"""Funscript Forge launcher.

Entry point for both development (`python launcher.py`) and the PyInstaller
packaged executable.  Starts the Streamlit web server on a free local port
and opens the default browser automatically.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser


def _find_free_port() -> int:
    """Return an OS-assigned free TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _open_browser(url: str, delay: float = 3.0) -> None:
    """Wait *delay* seconds then open *url* in the default browser."""
    time.sleep(delay)
    webbrowser.open(url)


def _base_dir() -> str:
    """Return the project root whether running frozen or from source."""
    if getattr(sys, "frozen", False):
        # PyInstaller extracts everything under sys._MEIPASS
        return sys._MEIPASS  # type: ignore[attr-defined]
    return os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    base = _base_dir()
    app_path = os.path.join(base, "ui", "streamlit", "app.py")

    if not os.path.exists(app_path):
        sys.exit(f"[Funscript Forge] Cannot find app.py at: {app_path}")

    port = _find_free_port()
    url = f"http://localhost:{port}"

    # Configure Streamlit via environment variables (before import).
    os.environ.setdefault("STREAMLIT_SERVER_PORT", str(port))
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_SERVER_ENABLE_CORS", "false")
    os.environ.setdefault("STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION", "false")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHER_USAGE_STATS", "false")
    os.environ.setdefault("STREAMLIT_THEME_BASE", "dark")

    # Add project root to sys.path so all package imports resolve.
    if base not in sys.path:
        sys.path.insert(0, base)

    print(f"[Funscript Forge] Starting on {url}")

    # Open the browser after a short delay so Streamlit has time to start.
    threading.Thread(target=_open_browser, args=(url,), daemon=True).start()

    # Run Streamlit in-process (blocking until the window is closed).
    from streamlit.web import bootstrap  # noqa: PLC0415

    bootstrap.run(app_path, "", [], {})


if __name__ == "__main__":
    main()
