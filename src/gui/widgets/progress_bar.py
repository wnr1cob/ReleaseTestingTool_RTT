"""
Animated progress bar widget with glow effect.
"""
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T


class GlowProgressBar(ctk.CTkFrame):
    """A futuristic progress bar with label, percentage, and glow accent."""

    def __init__(self, master, label: str = "Progress", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._label_text = label
        self._value = 0.0

        # ── header row (label + percentage) ─────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 6))

        self._label = ctk.CTkLabel(
            header,
            text=label,
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
        )
        self._label.pack(side="left")

        self._pct_label = ctk.CTkLabel(
            header,
            text="0 %",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            text_color=T.ACCENT_PRIMARY,
        )
        self._pct_label.pack(side="right")

        # ── progress bar ────────────────────────────────────────
        self._bar = ctk.CTkProgressBar(
            self,
            height=T.PROGRESS_HEIGHT,
            corner_radius=T.PROGRESS_HEIGHT // 2,
            fg_color=T.PROGRESS_BG,
            progress_color=T.PROGRESS_FG,
        )
        self._bar.pack(fill="x")
        self._bar.set(0)

    # ── public API ──────────────────────────────────────────────
    def set(self, value: float):
        """Set progress 0.0 – 1.0."""
        self._value = max(0.0, min(1.0, value))
        self._bar.set(self._value)
        self._pct_label.configure(text=f"{int(self._value * 100)} %")

        # colour shifts as progress advances
        if self._value >= 1.0:
            self._bar.configure(progress_color=T.ACCENT_SUCCESS)
            self._pct_label.configure(text_color=T.ACCENT_SUCCESS)
        elif self._value >= 0.7:
            self._bar.configure(progress_color=T.ACCENT_PRIMARY)
            self._pct_label.configure(text_color=T.ACCENT_PRIMARY)
        else:
            self._bar.configure(progress_color=T.PROGRESS_FG)
            self._pct_label.configure(text_color=T.ACCENT_PRIMARY)

    def get(self) -> float:
        return self._value

    def reset(self):
        self.set(0)
        self._bar.configure(progress_color=T.PROGRESS_FG)
        self._pct_label.configure(text_color=T.ACCENT_PRIMARY)

    def animate_to(self, target: float, step: float = 0.01, delay_ms: int = 15):
        """Smoothly animate the bar to *target* value."""
        current = self._value
        if abs(current - target) < step:
            self.set(target)
            return
        direction = step if target > current else -step
        self.set(current + direction)
        self.after(delay_ms, lambda: self.animate_to(target, step, delay_ms))
