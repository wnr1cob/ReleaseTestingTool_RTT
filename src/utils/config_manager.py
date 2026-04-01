"""config_manager — Single source of truth for all runtime paths.

When running as a PyInstaller bundle (frozen), config and logs directories
live next to the .exe (os.path.dirname(sys.executable)).  When running from
source, the project root is used instead (same location as config/).

Public API
----------
get_app_dir()    → str   # writable base directory
get_config_dir() → str   # <app_dir>/config/
get_logs_dir()   → str   # <app_dir>/logs/
ensure_config()           # idempotent — call once at startup
"""
import json
import os
import shutil
import sys


# ── path resolution ──────────────────────────────────────────────────────────

def get_app_dir() -> str:
    """Return the writable application base directory.

    * Frozen (PyInstaller): directory that contains the .exe.
    * Source: project root (two levels above this file).
    """
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    # src/utils/config_manager.py → two parents up → project root
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
    )


def get_config_dir() -> str:
    return os.path.join(get_app_dir(), "config")


def get_logs_dir() -> str:
    return os.path.join(get_app_dir(), "logs")


# ── bundled (read-only) config location when frozen ─────────────────────────

def _bundled_config_dir() -> str | None:
    """Return sys._MEIPASS/config when frozen and present; None otherwise.

    In --onefile mode _MEIPASS is a temp dir distinct from the exe directory.
    In --onedir mode _MEIPASS is the same folder as the exe, so the bundled
    config IS already the user config — ensure_config() becomes a no-op.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidate = os.path.join(sys._MEIPASS, "config")  # type: ignore[attr-defined]
        return candidate if os.path.isdir(candidate) else None
    return None


# ── seed defaults ────────────────────────────────────────────────────────────

_DEFAULT_SETTINGS: dict = {
    "app_name": "Release Testing Tool",
    "version": "1.0.0",
    "log_level": "INFO",
    "theme": "light",
}

# canonical_names starts empty; the dialog manages all edits
_DEFAULT_CANONICAL_NAMES: dict = {}


def _seed_file(dest: str, bundled_src: str | None, default_content: str) -> None:
    """Create *dest* only when it does not already exist.

    Priority:
      1. Skip entirely if *dest* already exists.
      2. Copy from the bundled (read-only) source if available.
      3. Write *default_content* as a fallback.
    """
    if os.path.isfile(dest):
        return
    if bundled_src and os.path.isfile(bundled_src):
        shutil.copy2(bundled_src, dest)
    else:
        with open(dest, "w", encoding="utf-8") as fh:
            fh.write(default_content)


# ── public initialisation ────────────────────────────────────────────────────

def ensure_config() -> None:
    """Guarantee that the config directory and required JSON files exist.

    Safe to call multiple times — only creates what is missing.
    Existing files are never overwritten.
    """
    cfg = get_config_dir()
    os.makedirs(cfg, exist_ok=True)

    bundled = _bundled_config_dir()

    # settings.json
    _seed_file(
        os.path.join(cfg, "settings.json"),
        bundled and os.path.join(bundled, "settings.json"),
        json.dumps(_DEFAULT_SETTINGS, indent=4),
    )

    # presets.json — seeded with bundled version when available; an empty
    # object is safe because load_presets() merges with DEFAULT_PRESETS.
    _seed_file(
        os.path.join(cfg, "presets.json"),
        bundled and os.path.join(bundled, "presets.json"),
        "{}",
    )

    # canonical_names.json
    _seed_file(
        os.path.join(cfg, "canonical_names.json"),
        bundled and os.path.join(bundled, "canonical_names.json"),
        json.dumps(_DEFAULT_CANONICAL_NAMES, indent=4),
    )
