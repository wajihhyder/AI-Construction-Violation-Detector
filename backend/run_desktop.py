"""
Desktop / PyInstaller entry: one process serves FastAPI (backend) + built React SPA (frontend).

Double-clicking ConstructionViolationDetection.exe sets the working directory to the exe folder,
writes logs there, and opens http://127.0.0.1:8000/ in your browser.

Repo dev:  python run_desktop.py
Build:      ../scripts/build_exe.ps1
"""

from __future__ import annotations

import multiprocessing
import os
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

APP_TITLE = "AI Powered Construction Violation Detection"


def _exe_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _log(line: str) -> None:
    try:
        with open(_exe_dir() / "app_launch.log", "a", encoding="utf-8") as f:
            f.write(line.rstrip() + "\n")
    except Exception:
        pass


def _fatal_box(title: str, text: str) -> None:
    text = (text or "")[:1024]
    if sys.platform != "win32":
        print(title, text, sep="\n")
        return
    try:
        import ctypes

        ctypes.windll.user32.MessageBoxW(None, text, title, 0x10)
    except Exception:
        print(title, text, sep="\n")


def _prepare() -> tuple[str, int, str]:
    """
    Must run before uvicorn imports `main` (so Settings / DB see correct env and cwd).
    """
    root = _exe_dir()
    os.chdir(root)
    _log(f"cwd={root}")

    uploads = root / "uploads"
    uploads.mkdir(parents=True, exist_ok=True)

    if getattr(sys, "frozen", False):
        # Bundled exe: force DB + uploads next to the executable (Windows cwd is unreliable)
        db_path = root / "vioscan.db"
        os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
        os.environ["UPLOAD_DIR"] = str(uploads)

    # Single-origin URL when UI is served by the same server as the API
    os.environ.setdefault("FRONTEND_URL", "http://127.0.0.1:8000")

    host = os.environ.get("VIOSCAN_HOST", "127.0.0.1")
    port = int(os.environ.get("VIOSCAN_PORT", "8000"))
    url = f"http://{host}:{port}/"
    return host, port, url


def _open_browser_delayed(url: str, delay: float = 2.0) -> None:
    def run() -> None:
        time.sleep(delay)
        try:
            webbrowser.open(url)
            _log(f"Opened browser: {url}")
        except Exception as e:
            _log(f"webbrowser.open failed: {e}")

    threading.Thread(target=run, daemon=True).start()


def main() -> None:
    multiprocessing.freeze_support()

    host, port, url = _prepare()

    try:
        import uvicorn
    except Exception:
        tb = traceback.format_exc()
        _log(tb)
        (_exe_dir() / "app_error.log").write_text(tb, encoding="utf-8")
        _fatal_box(
            APP_TITLE,
            "Could not load server components.\nSee app_error.log next to this program.",
        )
        sys.exit(1)

    _open_browser_delayed(url)
    _log(f"uvicorn main:app on {host}:{port}")

    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=False,
            factory=False,
            log_level="info",
        )
    except OSError as e:
        tb = traceback.format_exc()
        _log(tb)
        (_exe_dir() / "app_error.log").write_text(tb, encoding="utf-8")
        _fatal_box(
            APP_TITLE,
            f"Cannot bind {host}:{port}.\nClose other instances or set VIOSCAN_PORT in .env\n\n{e}",
        )
        sys.exit(1)
    except Exception:
        tb = traceback.format_exc()
        _log(tb)
        (_exe_dir() / "app_error.log").write_text(tb, encoding="utf-8")
        _fatal_box(APP_TITLE, "The server stopped unexpectedly.\nSee app_error.log")
        raise


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
    except Exception:
        tb = traceback.format_exc()
        _log(tb)
        try:
            (_exe_dir() / "app_error.log").write_text(tb, encoding="utf-8")
        except Exception:
            pass
        _fatal_box(APP_TITLE, tb[:900])
        sys.exit(1)
