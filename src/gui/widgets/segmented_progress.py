"""
Segmented progress bar – shows distinct execution phases side by side.

Each segment has its own label, colour, and 0→100 % progress indicator.
"""

import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T


class SegmentedProgressBar(ctk.CTkFrame):
    """A progress bar split into labelled execution segments.

    Parameters
    ----------
    master : widget
        Parent widget.
    segments : list[dict]
        ``[{"label": "Copying", "color": "#00D4FF"}, ...]``
        Each dict defines one visual segment.
    """

    def __init__(self, master, segments: list[dict], **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self._segment_defs = segments
        self._bars: list[ctk.CTkProgressBar] = []
        self._step_labels: list[ctk.CTkLabel] = []
        self._pct_labels: list[ctk.CTkLabel] = []
        self._values: list[float] = [0.0] * len(segments)
        # Track current bar colours to avoid redundant configure() redraws
        self._bar_colors: list[str] = [seg["color"] for seg in segments]
        # Original label texts stored for reset()
        self._original_labels: list[str] = [seg["label"] for seg in segments]

        # ── overall header ──────────────────────────────────────
        overall_row = ctk.CTkFrame(self, fg_color="transparent")
        overall_row.pack(fill="x", pady=(0, 4))

        self._overall_label = ctk.CTkLabel(
            overall_row,
            text="Processing",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
        )
        self._overall_label.pack(side="left")

        self._overall_pct = ctk.CTkLabel(
            overall_row,
            text="0 %",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            text_color=T.ACCENT_PRIMARY,
            width=54,
            anchor="e",
        )
        self._overall_pct.pack(side="right")

        # ── segments container ──────────────────────────────────
        seg_row = ctk.CTkFrame(self, fg_color="transparent")
        seg_row.pack(fill="x")

        for i, seg in enumerate(segments):
            col = ctk.CTkFrame(seg_row, fg_color="transparent")
            col.pack(side="left", fill="both", expand=True,
                     padx=(0 if i == 0 else 6, 0))

            # step label + segment pct
            hdr = ctk.CTkFrame(col, fg_color="transparent")
            hdr.pack(fill="x", pady=(0, 3))

            # Pack pct label FIRST (side="right") so it always gets its
            # requested width.  The step label fills the remaining space
            # and will truncate gracefully if too long — instead of
            # pushing the percentage off-screen.
            pct_lbl = ctk.CTkLabel(
                hdr,
                text="0 %",
                font=(T.FONT_FAMILY, 10, "bold"),
                text_color=seg["color"],
                width=44,
                anchor="e",
            )
            pct_lbl.pack(side="right")

            step_lbl = ctk.CTkLabel(
                hdr,
                text=seg["label"],
                font=(T.FONT_FAMILY, 10),
                text_color=T.TEXT_SECONDARY,
                anchor="w",
            )
            step_lbl.pack(side="left", fill="x", expand=True)

            bar = ctk.CTkProgressBar(
                col,
                height=T.PROGRESS_HEIGHT,
                corner_radius=T.PROGRESS_HEIGHT // 2,
                fg_color=T.PROGRESS_BG,
                progress_color=seg["color"],
            )
            bar.pack(fill="x")
            bar.set(0)

            self._bars.append(bar)
            self._step_labels.append(step_lbl)
            self._pct_labels.append(pct_lbl)

    # ── public API ──────────────────────────────────────────────

    def set_segment(self, index: int, value: float):
        """Set progress for segment *index* (0‑based), value 0.0–1.0."""
        value = max(0.0, min(1.0, value))
        self._values[index] = value
        # colour shift for completed segments
        color = T.ACCENT_SUCCESS if value >= 1.0 else self._segment_defs[index]["color"]
        pct_text = f"{round(value * 100)} %"
        # Only reconfigure the bar colour when it actually changes
        if color != self._bar_colors[index]:
            self._bars[index].configure(progress_color=color)
            self._bar_colors[index] = color
            self._pct_labels[index].configure(text=pct_text, text_color=color)
        else:
            self._pct_labels[index].configure(text=pct_text)
        self._bars[index].set(value)
        self._update_overall()

    def set_segments_batch(self, updates: dict):
        """Update multiple segment values at once; recalculates overall only once.

        Parameters
        ----------
        updates : dict
            ``{index: value}`` mapping – values in 0.0–1.0.
        """
        for index, value in updates.items():
            value = max(0.0, min(1.0, value))
            self._values[index] = value
            color = T.ACCENT_SUCCESS if value >= 1.0 else self._segment_defs[index]["color"]
            pct_text = f"{round(value * 100)} %"
            if color != self._bar_colors[index]:
                self._bars[index].configure(progress_color=color)
                self._bar_colors[index] = color
                self._pct_labels[index].configure(text=pct_text, text_color=color)
            else:
                self._pct_labels[index].configure(text=pct_text)
            self._bars[index].set(value)
        if updates:
            self._update_overall()

    def set_segment_label(self, index: int, text: str):
        """Update the step label for segment *index* (e.g. to append elapsed time)."""
        self._step_labels[index].configure(text=text)

    def get_segment(self, index: int) -> float:
        return self._values[index]

    def reset(self):
        """Reset all segments to 0 and restore original labels."""
        for i, seg in enumerate(self._segment_defs):
            self._values[i] = 0.0
            self._bar_colors[i] = seg["color"]
            self._bars[i].set(0)
            self._bars[i].configure(progress_color=seg["color"])
            self._pct_labels[i].configure(text="0 %", text_color=seg["color"])
            self._step_labels[i].configure(text=self._original_labels[i])
        self._overall_label.configure(text="Processing")
        self._overall_pct.configure(text="0 %", text_color=T.ACCENT_PRIMARY)

    def set_overall_label(self, text: str):
        """Change the top-level label text."""
        self._overall_label.configure(text=text)

    def set_item_counter(self, completed: int, total: int):
        """Update the overall label to show item completion count (e.g., "Processing — 45 of 100 items")."""
        label_text = f"Processing — {completed} of {total} items"
        self._overall_label.configure(text=label_text)

    # ── internals ───────────────────────────────────────────────

    def _update_overall(self):
        """Recalculate the combined percentage from all segments."""
        n = len(self._values)
        overall = sum(self._values) / n if n else 0
        pct = round(overall * 100)
        color = T.ACCENT_SUCCESS if overall >= 1.0 else T.ACCENT_PRIMARY
        self._overall_pct.configure(text=f"{pct} %", text_color=color)
