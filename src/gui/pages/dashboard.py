"""
Dashboard page – overview stats, quick actions, and activity log.
"""
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T

# ── Tab cards metadata (icon, title, description) ───────────────
_TAB_CARDS = [
    (
        "📄",
        "Report Analyzer",
        "Analyze PDF test reports, extract structured results,\n"
        "and generate consolidated Excel summaries.",
    ),
    (
        "📗",
        "SystemTestListe Analyzer",
        "Match system test lists against test results,\n"
        "compare expected vs. actual outcomes, and export reports.",
    ),
    (
        "📁",
        "Folder Mgmt",
        "Manage and organize output folders, copy and sort\n"
        "testing files into the correct directory structure.",
    ),
    (
        "📈",
        "Reports",
        "Browse generated reports, review historical analysis\n"
        "results, and export findings in various formats.",
    ),
    (
        "⚙️",
        "Settings",
        "Configure application preferences, choose the UI theme,\n"
        "and define default output paths and file options.",
    ),
]

_CARDS_PER_ROW = 3


class DashboardPage(ctk.CTkFrame):
    """Main dashboard shown on app launch."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._build()

    # ── builders ────────────────────────────────────────────────
    def _build(self):
        self._build_header()
        self._build_cards()

    def _build_header(self):
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

        # Divider
        ctk.CTkFrame(
            self,
            height=1,
            fg_color=T.BORDER_COLOR,
        ).pack(fill="x", padx=30, pady=(8, 20))

    def _build_cards(self):
        """Lay out one card per sidebar tab in a responsive grid."""
        scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=T.BORDER_COLOR,
            scrollbar_button_hover_color=T.ACCENT_PRIMARY,
        )
        scroll.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Configure uniform columns
        for col in range(_CARDS_PER_ROW):
            scroll.columnconfigure(col, weight=1, uniform="card_col")

        for idx, (icon, title, desc) in enumerate(_TAB_CARDS):
            row, col = divmod(idx, _CARDS_PER_ROW)
            self._make_card(scroll, icon, title, desc, row, col)

    def _make_card(
        self,
        parent: ctk.CTkScrollableFrame,
        icon: str,
        title: str,
        desc: str,
        row: int,
        col: int,
    ):
        card = ctk.CTkFrame(
            parent,
            fg_color=T.BG_CARD,
            corner_radius=T.CARD_CORNER,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        card.columnconfigure(0, weight=1)

        # Icon
        ctk.CTkLabel(
            card,
            text=icon,
            font=(T.FONT_FAMILY, 32),
        ).grid(row=0, column=0, padx=18, pady=(18, 6), sticky="w")

        # Title
        ctk.CTkLabel(
            card,
            text=title,
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
            anchor="w",
        ).grid(row=1, column=0, padx=18, pady=(0, 6), sticky="ew")

        # Accent divider
        ctk.CTkFrame(
            card,
            height=2,
            fg_color=T.ACCENT_PRIMARY,
            corner_radius=2,
        ).grid(row=2, column=0, padx=18, pady=(0, 10), sticky="ew")

        # Description
        ctk.CTkLabel(
            card,
            text=desc,
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
            justify="left",
            wraplength=220,
        ).grid(row=3, column=0, padx=18, pady=(0, 18), sticky="ew")

    # ── public helpers (stubs) ───────────────────────────────────
    def demo_progress(self):
        pass

    def log(self, message: str):
        pass
