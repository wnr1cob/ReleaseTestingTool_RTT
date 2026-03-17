"""
Excel Tools page – browse and select an Excel file for processing.
"""
import os
from tkinter import filedialog
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T


class ExcelToolsPage(ctk.CTkFrame):
    """Excel Tools page with file selection."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._selected_file: str = ""
        self._build()

    def _build(self):
        # ── Page title ──────────────────────────────────────────
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(25, 5))

        ctk.CTkLabel(
            title_frame,
            text="Excel Tools",
            font=(T.FONT_FAMILY, T.FONT_SIZE_TITLE, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame,
            text="Select an Excel file to work with",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="left", padx=(15, 0), pady=(6, 0))

        # ── File selection card ─────────────────────────────────
        file_card = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        file_card.pack(fill="x", padx=30, pady=(20, 15))

        ctk.CTkLabel(
            file_card,
            text="Select Excel File",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 12))

        # Row: path display + browse button
        browse_row = ctk.CTkFrame(file_card, fg_color="transparent")
        browse_row.pack(fill="x", padx=20, pady=(0, 20))

        self._path_entry = ctk.CTkEntry(
            browse_row,
            placeholder_text="No file selected...",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            fg_color=T.BG_SIDEBAR,
            text_color=T.TEXT_PRIMARY,
            border_color=T.BORDER_COLOR,
            corner_radius=T.BUTTON_CORNER,
            height=38,
            state="disabled",
        )
        self._path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self._browse_btn = ctk.CTkButton(
            browse_row,
            text="Browse",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            height=38,
            width=120,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS,
            hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.BG_DARK,
            command=self._browse_file,
        )
        self._browse_btn.pack(side="right")

        # ── Status / info area (pinned to bottom) ───────────────
        self._info_card = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        self._info_card.pack(fill="x", side="bottom", padx=30, pady=(0, 20))

        ctk.CTkLabel(
            self._info_card,
            text="Excel File Info",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 8))

        self._status_label = ctk.CTkLabel(
            self._info_card,
            text="  No file selected. Click 'Browse' to choose an Excel file.",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        )
        self._status_label.pack(anchor="w", padx=20, pady=(0, 18))

    # ── file browser ────────────────────────────────────────────
    def _browse_file(self):
        """Open a native file picker dialog for Excel files."""
        filepath = filedialog.askopenfilename(
            title="Select Excel File",
            filetypes=[
                ("Excel Files", "*.xlsx *.xls *.xlsm"),
                ("All Files", "*.*"),
            ],
        )
        if filepath:
            self._selected_file = filepath
            # Update path entry
            self._path_entry.configure(state="normal")
            self._path_entry.delete(0, "end")
            self._path_entry.insert(0, filepath)
            self._path_entry.configure(state="disabled")
            # Show file info
            self._show_file_info(filepath)

    def _show_file_info(self, filepath: str):
        """Display basic info about the selected Excel file."""
        filename = os.path.basename(filepath)
        size_kb = os.path.getsize(filepath) / 1024
        self._status_label.configure(
            text=f"  Selected: {filename}  ({size_kb:.1f} KB)",
            text_color=T.ACCENT_SUCCESS,
        )
