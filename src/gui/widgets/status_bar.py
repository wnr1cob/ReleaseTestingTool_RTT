"""
Status bar widget – bottom strip with status text, progress, and clock.
"""
import time
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T


class StatusBar(ctk.CTkFrame):
    """Bottom status bar with message, mini progress, and live clock."""

    def __init__(self, master, **kwargs):
        super().__init__(
            master,
            height=32,
            corner_radius=0,
            fg_color=T.BG_HEADER,
            **kwargs,
        )
        self.pack_propagate(False)
        self._timer_id: str | None = None

        # left – status message
        self._msg = ctk.CTkLabel(
            self,
            text="Ready",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.ACCENT_PRIMARY,
        )
        self._msg.pack(side="left", padx=15)

        # right – clock
        self._clock = ctk.CTkLabel(
            self,
            text="",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        )
        self._clock.pack(side="right", padx=15)
        self._tick()

    def set_status(self, text: str, color: str = T.ACCENT_PRIMARY):
        self._msg.configure(text=text, text_color=color)

    def _tick(self):
        try:
            self._clock.configure(text=time.strftime("%H:%M:%S"))
            self._timer_id = self.after(1000, self._tick)
        except Exception:
            pass  # widget destroyed

    def destroy(self):
        if self._timer_id is not None:
            try:
                self.after_cancel(self._timer_id)
            except Exception:
                pass
        super().destroy()
