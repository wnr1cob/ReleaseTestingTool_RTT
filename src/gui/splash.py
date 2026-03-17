"""
Splash screen shown while the main window builds.

Displayed as a centered, borderless CTkToplevel on the hidden root window.
Provides set_progress(value, message) for incremental build feedback.
"""
from __future__ import annotations
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T


class SplashScreen:
    """Centered splash window with animated progress bar."""

    WIDTH  = 520
    HEIGHT = 300

    def __init__(self, root: ctk.CTk):
        self._root = root

        win = ctk.CTkToplevel(root)
        win.overrideredirect(True)          # borderless
        win.configure(fg_color=T.BG_DARK)
        win.resizable(False, False)
        win.attributes("-topmost", True)

        # Centre on screen
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x  = (sw - self.WIDTH)  // 2
        y  = (sh - self.HEIGHT) // 2
        win.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self._win = win
        self._build()

    # ── UI ──────────────────────────────────────────────────────
    def _build(self):
        w = self._win

        # Outer border frame (accent glow)
        border = ctk.CTkFrame(w, fg_color=T.ACCENT_PRIMARY, corner_radius=14)
        border.pack(fill="both", expand=True)

        inner = ctk.CTkFrame(border, fg_color=T.BG_DARK, corner_radius=12)
        inner.pack(fill="both", expand=True, padx=2, pady=2)

        # App name
        ctk.CTkLabel(
            inner,
            text="Release Testing Tool",
            font=(T.FONT_FAMILY, 26, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(pady=(42, 4))

        # Subtitle
        ctk.CTkLabel(
            inner,
            text="RTT  ·  Test Execution Analysis Suite",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.ACCENT_PRIMARY,
        ).pack(pady=(0, 30))

        # Status message
        self._msg_label = ctk.CTkLabel(
            inner,
            text="Initializing…",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        )
        self._msg_label.pack(pady=(0, 8))

        # Progress bar
        self._bar = ctk.CTkProgressBar(
            inner,
            width=420,
            height=6,
            corner_radius=3,
            fg_color=T.BG_SIDEBAR,
            progress_color=T.ACCENT_PRIMARY,
            mode="determinate",
        )
        self._bar.set(0.0)
        self._bar.pack(pady=(0, 0))

        # Version / footer
        ctk.CTkLabel(
            inner,
            text="v1.0.0",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="bottom", pady=14)

    # ── Public API ───────────────────────────────────────────────
    def set_progress(self, value: float, message: str = ""):
        """Update the progress bar (0.0 – 1.0) and status message."""
        self._bar.set(value)
        if message:
            self._msg_label.configure(text=message)

    def close(self):
        """Destroy the splash window."""
        try:
            self._win.destroy()
        except Exception:
            pass
