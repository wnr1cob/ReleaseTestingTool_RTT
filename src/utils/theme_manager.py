"""
ThemeManager — loads, applies, and saves the app theme preference.
"""
import json
from pathlib import Path
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T

# Resolve absolute path regardless of working directory:
# theme_manager.py lives at  <project_root>/src/utils/theme_manager.py
# so 3 parents up  →  <project_root>
SETTINGS_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "settings.json"
DEFAULT_THEME = "light"

# Widget color properties to inspect and remap
_COLOR_PROPS = (
    "fg_color", "text_color", "border_color",
    "button_color", "button_hover_color", "hover_color",
    "progress_color", "scrollbar_button_color", "scrollbar_button_hover_color",
    "label_fg_color",   # CTkScrollableFrame internal label surface
)


class ThemeManager:
    """Single-responsibility class for theme lifecycle."""

    def __init__(self):
        self._current: str = DEFAULT_THEME  # "light" | "dark"

    # ── public API ───────────────────────────────────────────────

    def load(self) -> str:
        """Read saved preference from settings.json; return active theme name."""
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            saved = data.get("theme", DEFAULT_THEME).lower()
            self._current = saved if saved in ("light", "dark") else DEFAULT_THEME
        except (FileNotFoundError, json.JSONDecodeError):
            self._current = DEFAULT_THEME
        return self._current

    def apply(self, theme: str, root=None) -> None:
        """
        Apply theme immediately across the entire GUI.

        Steps:
          1. Build old→new hex color_map from AppTheme palette dicts.
          2. Update AppTheme class attributes so future widgets use correct colors.
          3. Call ctk.set_appearance_mode() for built-in ctk coloring.
          4. If root is supplied, walk every live widget and remap hardcoded colors.
        """
        theme = theme.lower()
        if theme not in ("light", "dark"):
            raise ValueError(f"Unknown theme: {theme!r}")

        old_palette = T.DARK if self._current == "dark" else T.LIGHT
        new_palette = T.DARK if theme == "dark" else T.LIGHT

        # Build hex→hex remap dict (only for keys present in both palettes)
        color_map: dict[str, str] = {
            old_palette[k]: new_palette[k]
            for k in old_palette
            if k in new_palette and old_palette[k] != new_palette[k]
        }

        # Update AppTheme class attributes so newly created widgets are correct
        for key, value in new_palette.items():
            if hasattr(T, key):
                setattr(T, key, value)

        self._current = theme

        # ── ORDER IS CRITICAL ────────────────────────────────────
        # Walk hardcoded widget colors BEFORE calling set_appearance_mode().
        # CTkScrollableFrame (and other "transparent" widgets) resolve their
        # canvas background by querying their parent chain at the moment
        # set_appearance_mode fires.  If we walk first, the parent chain
        # already holds the new palette colors when ctk does that query,
        # so transparent scroll-area backgrounds paint correctly.
        if root is not None and color_map:
            self._restyle_widgets(root, color_map)

        ctk.set_appearance_mode(theme)

    # ── internal helpers ─────────────────────────────────────────

    def _restyle_widgets(self, widget, color_map: dict) -> None:
        """Recursively remap palette colors on every widget in the tree."""
        kw: dict = {}
        for prop in _COLOR_PROPS:
            try:
                val = widget.cget(prop)
                # ctk sometimes returns ["light_hex", "dark_hex"] tuples
                if isinstance(val, (list, tuple)):
                    remapped = [color_map.get(v, v) for v in val]
                    if remapped != list(val):
                        kw[prop] = remapped
                elif isinstance(val, str) and val in color_map:
                    kw[prop] = color_map[val]
            except Exception:
                pass
        if kw:
            try:
                widget.configure(**kw)
            except Exception:
                pass

        # Allow individual pages/widgets to run extra refresh logic after
        # palette remapping (e.g. re-highlight dynamically-created list items).
        if callable(getattr(widget, "_on_theme_refresh", None)):
            try:
                widget._on_theme_refresh()
            except Exception:
                pass

        # CTkScrollableFrame stores user-placed children in an internal
        # _scrollable_frame that winfo_children() on the outer widget does NOT
        # expose.  Explicitly traverse it so cards inside scroll areas update.
        if isinstance(widget, ctk.CTkScrollableFrame) and hasattr(widget, "_scrollable_frame"):
            self._restyle_widgets(widget._scrollable_frame, color_map)

        for child in widget.winfo_children():
            self._restyle_widgets(child, color_map)

    def save(self) -> None:
        """Persist current theme to settings.json."""
        try:
            data = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            data = {}
        data["theme"] = self._current
        SETTINGS_PATH.write_text(json.dumps(data, indent=4), encoding="utf-8")

    @property
    def current(self) -> str:
        return self._current

    @property
    def is_dark(self) -> bool:
        return self._current == "dark"
