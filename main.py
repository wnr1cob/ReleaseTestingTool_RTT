"""
Release Testing Tool - Main Entry Point

Run this file to launch the application.
"""
import sys
import os
import traceback
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# ── Windows taskbar icon fix ──────────────────────────────────────────────────
# Must be called BEFORE any Tk window is created so Windows uses our .ico
# instead of grouping the process under the generic Python taskbar button.
try:
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
        "WNR1COB.ReleaseTestingTool.3.0"
    )
except Exception:
    pass

from src.gui.main_window import MainWindow


def _write_crash_log(tb: str) -> str:
    """Write *tb* to logs/crash_YYYYMMDD.log and return the file path."""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"crash_{datetime.now().strftime('%Y%m%d')}.log")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_file, "a", encoding="utf-8") as fh:
        fh.write(f"\n{'='*60}\n{timestamp}\n{tb}\n")
    return log_file


def main():
    """Application entry point."""
    try:
        app = MainWindow()
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
