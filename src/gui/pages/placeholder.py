"""
Placeholder page – used for sections not yet implemented.
"""
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T


class PlaceholderPage(ctk.CTkFrame):
    """Generic placeholder with icon and title."""

    def __init__(self, master, title: str = "Coming Soon", icon: str = "🚧", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        inner = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        inner.place(relx=0.5, rely=0.45, anchor="center")

        ctk.CTkLabel(
            inner,
            text=icon,
            font=(T.FONT_FAMILY, 48),
        ).pack(padx=60, pady=(40, 10))

        ctk.CTkLabel(
            inner,
            text=title,
            font=(T.FONT_FAMILY, T.FONT_SIZE_TITLE, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack()

        ctk.CTkLabel(
            inner,
            text="This module will be implemented in a future step.",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_SECONDARY,
        ).pack(padx=40, pady=(6, 40))
