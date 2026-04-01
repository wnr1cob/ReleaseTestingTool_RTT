"""StateManager — exit-time persistence with atomic writes.

Saves/restores application state (window geometry, active page, etc.) across runs.
Stores logs and cache in parent directories, isolated from config.
Atomic writes prevent corruption if the app crashes during save.

Works correctly with PyInstaller --onefile (no temp paths to worry about).

Public API
----------
restore_state(default: dict) → dict      # load from cache or return default
save_state(state: dict) → None           # persist atomically
rotate_logs(max_files=5) → None          # cleanup old log.N files
get_cache_dir() → Path                   # ../cache/ directory
get_logs_dir() → Path                    # ../logs/ directory
"""
import json
import logging
import os
import tempfile
from pathlib import Path

from src.utils.config_manager import get_app_dir


# ── paths (parent directory, not config/) ────────────────────────────────────

def get_cache_dir() -> Path:
    """Return ../cache/ (parent of app_dir)."""
    parent = Path(get_app_dir()).parent
    cache = parent / "cache"
    cache.mkdir(parents=True, exist_ok=True)
    return cache


def get_logs_dir() -> Path:
    """Return ../logs/ (parent of app_dir)."""
    parent = Path(get_app_dir()).parent
    logs = parent / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs


# ── state file location ──────────────────────────────────────────────────────
# Resolved lazily (not at module-import time) to avoid creating directories
# before ensure_config() has run.  The first call caches the result.

_STATE_FILE: Path | None = None

def _get_state_file() -> Path:
    global _STATE_FILE
    if _STATE_FILE is None:
        _STATE_FILE = get_cache_dir() / "app_state.json"
    return _STATE_FILE


# ── atomic write helper ──────────────────────────────────────────────────────

def _atomic_write(path: Path, content: str) -> None:
    """Write *content* to *path* atomically via temp file + rename.

    Guarantees that *path* is never left corrupted, even if the process
    crashes mid-write or during disk flush.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to a temp file in the same directory (ensures same filesystem)
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(content)
        # Atomic rename — on POSIX this is atomic; on Windows it replaces
        os.replace(tmp_path, path)
    except Exception:
        # Clean up temp file if something went wrong
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise


# ── public API ───────────────────────────────────────────────────────────────

def restore_state(default: dict | None = None) -> dict:
    """Load application state from cache; return *default* if missing/corrupt.

    Args:
        default: fallback dict (window geometry, active page index, etc.)
                If None, empty dict is used.

    Returns:
        Restored state, or default if file does not exist or is invalid JSON.
    """
    if default is None:
        default = {}

    state_file = _get_state_file()
    if not state_file.exists():
        return default

    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            return data
    except (json.JSONDecodeError, ValueError) as e:
        logging.getLogger("rtt.state").warning(
            f"Could not restore state from {state_file}: {e}"
        )
    return default


def save_state(state: dict) -> None:
    """Persist application state to cache atomically.

    Args:
        state: dict with keys like 'window_geometry', 'active_page', etc.
    """
    try:
        content = json.dumps(state, indent=2, default=str)
        _atomic_write(_get_state_file(), content)
    except Exception as e:
        logging.getLogger("rtt.state").error(f"Failed to save state: {e}")


# ── log rotation ─────────────────────────────────────────────────────────────

def rotate_logs(max_files: int = 5) -> None:
    """Keep only the most recent *max_files* log.N files in ../logs/.

    Removes older rotated logs to prevent unbounded disk growth.
    Called once at app startup.

    Args:
        max_files: maximum number of rotated logs to keep (e.g. 5 = keep log.1 to log.5)
    """
    logs_dir = get_logs_dir()
    try:
        # Find all log.N files, sort by modification time (newest first)
        pattern = logs_dir / "log.*"
        rotated = sorted(
            logs_dir.glob("log.*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        # Delete oldest ones beyond max_files
        for old_log in rotated[max_files:]:
            try:
                old_log.unlink()
            except Exception as e:
                logging.getLogger("rtt.state").debug(f"Could not delete {old_log}: {e}")
    except Exception as e:
        logging.getLogger("rtt.state").debug(f"Log rotation error: {e}")
