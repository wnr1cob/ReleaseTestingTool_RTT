"""
Settings page – Appearance section with Dark Mode toggle.
"""
import os
import sys
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T
from src.utils.theme_manager import ThemeManager
from src.gui.widgets.hover_button import RttButton


class SettingsPage(ctk.CTkFrame):
    """Full settings page, starting with the Appearance section."""

    def __init__(self, master, theme_mgr: ThemeManager, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._theme_mgr = theme_mgr
        # Track the pending (not-yet-applied) theme selection
        self._pending_theme: str = theme_mgr.current
        self._build()

    # ── build ────────────────────────────────────────────────────

    def _build(self):
        # Page header row
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 5))
        ctk.CTkLabel(
            header,
            text="Settings",
            font=(T.FONT_FAMILY, T.FONT_SIZE_TITLE, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text="Appearance & preferences",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="left", padx=(15, 0), pady=(6, 0))

        # ── Appearance section card ─────────────────────────────
        card = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        card.pack(fill="x", padx=30, pady=(20, 0))

        # Section label inside card
        ctk.CTkLabel(
            card,
            text="  Appearance",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.ACCENT_PRIMARY,
        ).pack(anchor="w", padx=20, pady=(16, 10))

        # Divider
        ctk.CTkFrame(card, height=1, fg_color=T.BORDER_COLOR).pack(fill="x", padx=20)

        # Toggle row ─────────────────────────────────────────────
        toggle_row = ctk.CTkFrame(card, fg_color="transparent")
        toggle_row.pack(fill="x", padx=20, pady=(18, 6))

        ctk.CTkLabel(
            toggle_row,
            text="Theme",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
            width=160,
            anchor="w",
        ).pack(side="left")

        ctk.CTkLabel(
            toggle_row,
            text="Light",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 6))

        self._theme_var = ctk.BooleanVar(value=self._theme_mgr.is_dark)
        self._theme_switch = ctk.CTkSwitch(
            toggle_row,
            text="Dark Mode",
            variable=self._theme_var,
            onvalue=True,
            offvalue=False,
            command=self._on_theme_toggled,
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
            progress_color=T.ACCENT_PRIMARY,
            button_color=T.ACCENT_PRIMARY,
            button_hover_color=T.BORDER_GLOW,
        )
        self._theme_switch.pack(side="left")

        # Pending-change notice (hidden until toggle moves) ──────
        self._notice_label = ctk.CTkLabel(
            card,
            text="",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.ACCENT_WARNING,
            anchor="w",
        )
        self._notice_label.pack(anchor="w", padx=28, pady=(0, 14))

        # ── Bottom action bar ───────────────────────────────────
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=30, side="bottom", pady=20)

        self._feedback_label = ctk.CTkLabel(
            action_bar,
            text="",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.ACCENT_SUCCESS,
        )
        self._feedback_label.pack(side="left")

        self._apply_btn = RttButton(
            action_bar,
            text="Apply & Restart",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.BORDER_GLOW,
            text_color="#000000",
            width=160,
            state="disabled",           # disabled until toggle is changed
            command=self._on_apply,
        )
        self._apply_btn.pack(side="right")

    # ── event handlers ───────────────────────────────────────────

    def _on_theme_toggled(self):
        """Record pending selection — do NOT apply or restart yet."""
        self._pending_theme = "dark" if self._theme_var.get() else "light"
        if self._pending_theme != self._theme_mgr.current:
            self._apply_btn.configure(state="normal")
            self._notice_label.configure(
                text=f"⚠  Theme will change to '{self._pending_theme}' after restart."
            )
        else:
            # Toggled back to the current saved state
            self._apply_btn.configure(state="disabled")
            self._notice_label.configure(text="")

    def _on_apply(self):
        """Save preference, then restart the application to apply the theme."""
        self._theme_mgr._current = self._pending_theme   # update in-memory state
        self._theme_mgr.save()                           # persist to settings.json

        self._apply_btn.configure(state="disabled", text="Restarting…")
        self._feedback_label.configure(text="Saving & restarting…")

        # Schedule restart after a short delay so the UI can repaint
        self.after(300, self._restart_app)

    def _restart_app(self):
        """Destroy the current window and relaunch the process."""
        import subprocess
        root = self.winfo_toplevel()
        root.destroy()
        # Re-execute the same interpreter with the same arguments
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)

