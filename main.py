"""
Release Testing Tool - Main Entry Point

Run this file to launch the application.
"""
import sys
import os
import traceback
import logging
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Windows taskbar icon fix ──────────────────────────────────────────────────
# Must be called BEFORE any Tk window is created so Windows uses our .ico
# instead of grouping the process under the generic Python taskbar button.
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "WNR1COB.ReleaseTestingTool.2.4"
    )
except Exception:
    pass

# ── Crash log setup ──────────────────────────────────────────────────────────
_LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
os.makedirs(_LOG_DIR, exist_ok=True)
_LOG_FILE = os.path.join(_LOG_DIR, f"crash_{datetime.now().strftime('%Y%m%d')}.log")

from logging.handlers import RotatingFileHandler as _RFH
_handler = _RFH(_LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=2, encoding="utf-8")
_handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-8s  %(message)s",
                                        datefmt="%Y-%m-%d %H:%M:%S"))
logging.basicConfig(level=logging.DEBUG, handlers=[_handler])

from src.gui.main_window import MainWindow


def main():
    """Application entry point."""
    logging.info("Application starting.")
    try:
        app = MainWindow()
        app.run()
        logging.info("Application exited normally.")
    except KeyboardInterrupt:
        logging.info("Application interrupted by user.")
    except Exception as exc:
        tb = traceback.format_exc()
        logging.critical("Unhandled exception:\n%s", tb)
        # Show a native error dialog so the user sees the crash reason
        try:
            import tkinter as tk
            from tkinter import messagebox
            _root = tk.Tk()
            _root.withdraw()
            messagebox.showerror(
                "Release Testing Tool — Crash",
                f"An unexpected error occurred:\n\n{exc}\n\n"
                f"Full details saved to:\n{_LOG_FILE}",
            )
            _root.destroy()
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
