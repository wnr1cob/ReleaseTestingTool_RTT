"""
Sidebar navigation widget – CCleaner-style vertical menu.
"""
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T
from src.gui.widgets.hover_button import RttButton


class Sidebar(ctk.CTkFrame):
    """Left-hand navigation panel with icon + label buttons."""

    def __init__(self, master, on_select_callback, **kwargs):
        super().__init__(
            master,
            width=T.SIDEBAR_WIDTH,
            corner_radius=0,
            fg_color=T.BG_SIDEBAR,
            **kwargs,
        )
        self.pack_propagate(False)
        self._callback = on_select_callback
        self._buttons: list[ctk.CTkButton] = []
        self._active_index = 0

        self._build_logo()
        self._build_menu()

    # ── internal builders ───────────────────────────────────────
    def _build_logo(self):
        logo_frame = ctk.CTkFrame(self, fg_color="transparent")
        logo_frame.pack(fill="x", pady=(25, 30), padx=15)

        ctk.CTkLabel(
            logo_frame,
            text="⚡",
            font=(T.FONT_FAMILY, 28),
            text_color=T.ACCENT_PRIMARY,
        ).pack(side="left", padx=(0, 8))

        ctk.CTkLabel(
            logo_frame,
            text="Release Tool",
            font=(T.FONT_FAMILY, T.FONT_SIZE_TITLE, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(side="left")

    def _build_menu(self):
        for idx, (label, icon) in enumerate(T.MENU_ITEMS):
            btn = RttButton(
                self,
                text=f"  {icon}   {label}",
                font=(T.FONT_FAMILY, T.FONT_SIZE_SIDEBAR),
                anchor="w",
                height=44,
                corner_radius=T.BUTTON_CORNER,
                fg_color="transparent",
                text_color=T.TEXT_SECONDARY,
                hover_color=T.SIDEBAR_BTN_HOVER,
                command=lambda i=idx: self._on_click(i),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self._buttons.append(btn)

        # version label at bottom
        ctk.CTkLabel(
            self,
            text="v2.2.0",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="bottom", pady=15)

        # highlight first item
        self._highlight(0)

    # ── selection logic ─────────────────────────────────────────
    def _on_click(self, index: int):
        self._highlight(index)
        self._callback(index)

    def _highlight(self, index: int):
        for i, btn in enumerate(self._buttons):
            if i == index:
                btn.configure(
                    fg_color=T.SIDEBAR_BTN_ACTIVE_BG,
                    text_color=T.ACCENT_PRIMARY,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=T.TEXT_SECONDARY,
                )
        self._active_index = index
