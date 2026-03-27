"""
RttButton — CTkButton that brightens its text colour on hover.

Overrides _on_enter / _on_leave so:
  • On mouse-enter  : saves the current text_color, then applies T.BTN_HOVER_TEXT
  • On mouse-leave  : restores the saved text_color

T.BTN_HOVER_TEXT is read dynamically on every enter so it automatically
reflects whatever theme ThemeManager has applied (#ffffff in dark, #0d1117 in light).

Usage
-----
    from src.gui.widgets.hover_button import RttButton

    btn = RttButton(parent, text="Click me", fg_color=T.ACCENT_PRIMARY, ...)
    # No extra configuration required – hover text brightening is automatic.
    # Override per-button if needed:
    btn2 = RttButton(parent, text="Special", hover_text_color="#ff0000", ...)
"""
from __future__ import annotations
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T


class RttButton(ctk.CTkButton):
    """
    CTkButton subclass with automatic hover-text-colour support.

    Parameters
    ----------
    hover_text_color : str | None
        Explicit hex colour for hover text.  When *None* (default) the value
        of ``AppTheme.BTN_HOVER_TEXT`` is used at runtime, so it always
        matches the active theme without any extra wiring.
    All other parameters are forwarded to CTkButton unchanged.
    """

    def __init__(self, *args, hover_text_color: str | None = None, **kwargs):
        self._hover_text_color_override: str | None = hover_text_color
        self._pre_hover_text: str | None = None
        super().__init__(*args, **kwargs)

    # ── internal overrides ────────────────────────────────────────────────────
    def _on_enter(self, event=None) -> None:  # type: ignore[override]
        # Snapshot the current text colour before CTkButton changes bg.
        val = self.cget("text_color")
        self._pre_hover_text = val[0] if isinstance(val, (list, tuple)) and val else val

        # Apply hover text colour (per-button override > theme default).
        hover_tc = self._hover_text_color_override or T.BTN_HOVER_TEXT
        self.configure(text_color=hover_tc)

        super()._on_enter(event)

    def _on_leave(self, event=None) -> None:  # type: ignore[override]
        super()._on_leave(event)

        # Restore saved text colour.
        if self._pre_hover_text is not None:
            self.configure(text_color=self._pre_hover_text)
