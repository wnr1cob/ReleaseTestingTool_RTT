"""
Dashboard page – overview stats, quick actions, and activity log.
"""
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T
from src.gui.widgets.stat_card import StatCard
from src.gui.widgets.progress_bar import GlowProgressBar


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

        # ── Stat cards row ──────────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=30, pady=(20, 10))
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="card")

        cards_data = [
            ("📄", "0", "PDFs Analyzed", T.ACCENT_PRIMARY),
            ("📗", "0", "Excel Files", T.ACCENT_SUCCESS),
            ("📁", "0", "Folders Managed", T.ACCENT_WARNING),
            ("📈", "0", "Reports Generated", T.ACCENT_SECONDARY),
        ]
        self._cards: list[StatCard] = []
        for col, (icon, val, sub, color) in enumerate(cards_data):
            card = StatCard(cards_frame, icon=icon, value=val, subtitle=sub, accent=color)
            card.grid(row=0, column=col, padx=8, pady=8, sticky="nsew")
            self._cards.append(card)

        # ── Overall progress ────────────────────────────────────
        prog_frame = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        prog_frame.pack(fill="x", padx=30, pady=15)

        ctk.CTkLabel(
            prog_frame,
            text="Overall Release Progress",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 10))

        self._progress = GlowProgressBar(prog_frame, label="Completion")
        self._progress.pack(fill="x", padx=20, pady=(0, 20))

        # ── Quick Actions ───────────────────────────────────────
        actions_frame = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        actions_frame.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkLabel(
            actions_frame,
            text="Quick Actions",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 12))

        btn_row = ctk.CTkFrame(actions_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))

        actions = [
            ("🔍  Analyze PDF", T.ACCENT_PRIMARY),
            ("📗  Open Excel", T.ACCENT_SUCCESS),
            ("📁  Scan Folders", T.ACCENT_WARNING),
            ("📈  Generate Report", T.ACCENT_SECONDARY),
        ]
        for text, color in actions:
            ctk.CTkButton(
                btn_row,
                text=text,
                font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
                height=38,
                corner_radius=T.BUTTON_CORNER,
                fg_color=color,
                hover_color=T.SIDEBAR_BTN_HOVER,
                text_color=T.BG_DARK,
            ).pack(side="left", padx=(0, 10))

        # ── Activity / log area ─────────────────────────────────
        log_frame = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        log_frame.pack(fill="both", expand=True, padx=30, pady=(0, 20))

        ctk.CTkLabel(
            log_frame,
            text="Activity Log",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 8))

        self._log_box = ctk.CTkTextbox(
            log_frame,
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            fg_color=T.BG_SIDEBAR,
            text_color=T.TEXT_SECONDARY,
            corner_radius=6,
            activate_scrollbars=True,
        )
        self._log_box.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        self._log_box.insert("end", "  Application started.\n")
        self._log_box.insert("end", "  Ready – select an action to begin.\n")
        self._log_box.configure(state="disabled")

    # ── public helpers ──────────────────────────────────────────
    def demo_progress(self):
        """Run a demo animation on the progress bar."""
        self._progress.animate_to(0.85, step=0.008, delay_ms=20)

    def log(self, message: str):
        self._log_box.configure(state="normal")
        self._log_box.insert("end", f"  {message}\n")
        self._log_box.see("end")
        self._log_box.configure(state="disabled")
