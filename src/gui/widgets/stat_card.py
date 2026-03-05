"""
Stat card widget – displays a metric with icon, value, and subtitle.
"""
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T


class StatCard(ctk.CTkFrame):
    """A small rounded card showing an icon, a big number, and a label."""

    def __init__(
        self,
        master,
        icon: str = "📄",
        value: str = "0",
        subtitle: str = "Items",
        accent: str = T.ACCENT_PRIMARY,
        **kwargs,
    ):
        super().__init__(
            master,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
            **kwargs,
        )
        self._accent = accent

        # icon
        ctk.CTkLabel(
            self,
            text=icon,
            font=(T.FONT_FAMILY, 26),
        ).pack(anchor="w", padx=18, pady=(18, 4))

        # value
        self._value_label = ctk.CTkLabel(
            self,
            text=value,
            font=(T.FONT_FAMILY, 28, "bold"),
            text_color=accent,
        )
        self._value_label.pack(anchor="w", padx=18)

        # subtitle
        ctk.CTkLabel(
            self,
            text=subtitle,
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(anchor="w", padx=18, pady=(0, 18))

    def update_value(self, value: str):
        self._value_label.configure(text=value)
