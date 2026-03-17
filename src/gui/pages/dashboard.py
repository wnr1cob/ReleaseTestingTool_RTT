"""
Dashboard page – overview stats, quick actions, and activity log.
"""
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T


class DashboardPage(ctk.CTkFrame):
    """Main dashboard shown on app launch."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    def _build(self):
        # ── Page title ──────────────────────────────────────────
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(25, 5))

        ctk.CTkLabel(
            title_frame,
            text="Dashboard",
            font=(T.FONT_FAMILY, T.FONT_SIZE_TITLE, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame,
            text="Overview & quick actions",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="left", padx=(15, 0), pady=(6, 0))

    # ── public helpers (stubs) ───────────────────────────────────
    def demo_progress(self):
        pass

    def log(self, message: str):
        pass
