"""
Release Testing Tool - Main Entry Point

Run this file to launch the application.
"""
import sys
import os
import logging
import logging.handlers
import traceback
from datetime import datetime
from src.utils.config_manager import ensure_config, get_logs_dir
from src.utils.state_manager import restore_state, rotate_logs
from src.version import __version__

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Windows taskbar icon fix ──────────────────────────────────────────────────
# Must be called BEFORE any Tk window is created so Windows uses our .ico
# instead of grouping the process under the generic Python taskbar button.
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        f"WNR1COB.ReleaseTestingTool.{__version__}"
    )
except Exception:
    pass

from src.gui.main_window import MainWindow


def _setup_logging() -> None:
    """Configure the root logger with a rotating file handler."""
    log_dir = get_logs_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "rtt.log")

    handler = logging.handlers.RotatingFileHandler(
        log_file, maxBytes=2 * 1024 * 1024, backupCount=5, encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)


def _write_crash_log(tb: str) -> str:
    """Write *tb* to logs/crash_YYYYMMDD.log and return the file path."""
    log_dir = get_logs_dir()
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"crash_{datetime.now().strftime('%Y%m%d')}.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as fh:
        fh.write(f"\n{'='*60}\n{timestamp}\n{tb}\n")
    return log_file


def main():
    """Application entry point."""
    _setup_logging()
    ensure_config()
    rotate_logs(max_files=5)  # Clean up old rotated logs from parent/logs/
    
    logger = logging.getLogger("rtt")
    logger.info("Application starting")
    try:
        # Restore UI state from previous run (window geometry, active page, etc.)
        state = restore_state(default={"active_page": 0})
        app = MainWindow(initial_state=state)
        app.run()
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        tb = traceback.format_exc()
        log_file = _write_crash_log(tb)
        # Show a native error dialog so the user sees the crash reason
        try:
            import tkinter as tk
            from tkinter import messagebox
            _root = tk.Tk()
            _root.withdraw()
            messagebox.showerror(
                "Release Testing Tool — Crash",
                f"An unexpected error occurred:\n\n{exc}\n\n"
                f"Full details saved to:\n{log_file}",
            )
            _root.destroy()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
