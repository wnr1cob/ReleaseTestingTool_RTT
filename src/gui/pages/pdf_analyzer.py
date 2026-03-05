"""
PDF Analyzer page – browse a directory and analyze PDF files.
"""
import os
import shutil
from tkinter import filedialog
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T


class PDFAnalyzerPage(ctk.CTkFrame):
    """PDF Analyzer page with directory selection."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._selected_dir: str = ""
        self._pdf_files: list[str] = []
        self._build()

    def _build(self):
        # ── Page title ──────────────────────────────────────────
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(25, 5))

        ctk.CTkLabel(
            title_frame,
            text="PDF Analyzer",
            font=(T.FONT_FAMILY, T.FONT_SIZE_TITLE, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame,
            text="Select a directory to scan for PDF files",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="left", padx=(15, 0), pady=(6, 0))

        # ── Directory selection card ────────────────────────────
        dir_card = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        dir_card.pack(fill="x", padx=30, pady=(20, 15))

        ctk.CTkLabel(
            dir_card,
            text="📂  Select Directory",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 12))

        # Row: path display + browse button
        browse_row = ctk.CTkFrame(dir_card, fg_color="transparent")
        browse_row.pack(fill="x", padx=20, pady=(0, 20))

        self._path_entry = ctk.CTkEntry(
            browse_row,
            placeholder_text="No directory selected...",
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
            text="📁  Browse",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            height=38,
            width=120,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.BG_DARK,
            command=self._browse_directory,
        )
        self._browse_btn.pack(side="right")

        # ── Copy options card ──────────────────────────────────
        self._copy_card = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        self._copy_card.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkLabel(
            self._copy_card,
            text="📋  Copy Options",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 12))

        # Duplicate handling radio buttons
        self._dup_mode = ctk.StringVar(value="copy_duplicates")

        self._radio_copy_dup = ctk.CTkRadioButton(
            self._copy_card,
            text="Copy Duplicates (rename with _Dup suffix)",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            variable=self._dup_mode,
            value="copy_duplicates",
        )
        self._radio_copy_dup.pack(anchor="w", padx=20, pady=(0, 6))

        self._radio_ignore_dup = ctk.CTkRadioButton(
            self._copy_card,
            text="Ignore Duplicates (skip if already exists)",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            variable=self._dup_mode,
            value="ignore_duplicates",
        )
        self._radio_ignore_dup.pack(anchor="w", padx=20, pady=(0, 12))

        self._copy_btn = ctk.CTkButton(
            self._copy_card,
            text="📋  Copy PDFs to All_Available_Reports",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            height=38,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SECONDARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_BRIGHT,
            command=self._copy_pdfs,
        )
        self._copy_btn.pack(anchor="w", padx=20, pady=(0, 18))

        # ── Separator selection card ───────────────────────────
        self._sep_card = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        self._sep_card.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkLabel(
            self._sep_card,
            text="✂️  Separator Selection",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 12))

        self._sep_mode = ctk.StringVar(value="module_separator")

        self._radio_module_sep = ctk.CTkRadioButton(
            self._sep_card,
            text="Module Separator",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            variable=self._sep_mode,
            value="module_separator",
        )
        self._radio_module_sep.pack(anchor="w", padx=20, pady=(0, 6))

        self._radio_result_sep = ctk.CTkRadioButton(
            self._sep_card,
            text="Result Separator",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            variable=self._sep_mode,
            value="result_separator",
        )
        self._radio_result_sep.pack(anchor="w", padx=20, pady=(0, 18))

        # ── Status / info area (pinned to bottom) ─────────────────
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
            text="📄  PDF Files Found",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 8))

        self._status_label = ctk.CTkLabel(
            self._info_card,
            text="  No directory selected. Click 'Browse' to choose a folder.",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        )
        self._status_label.pack(anchor="w", padx=20, pady=(0, 18))

    # ── directory browser ───────────────────────────────────────
    def _browse_directory(self):
        """Open a native directory picker dialog."""
        directory = filedialog.askdirectory(
            title="Select Directory Containing PDF Files",
        )
        if directory:
            self._selected_dir = directory
            # Update path entry
            self._path_entry.configure(state="normal")
            self._path_entry.delete(0, "end")
            self._path_entry.insert(0, directory)
            self._path_entry.configure(state="disabled")
            # Scan for PDFs
            self._scan_directory(directory)

    def _scan_directory(self, directory: str):
        """Scan the selected directory for PDF files and show count."""
        self._pdf_files = []
        for root, _dirs, files in os.walk(directory):
            for f in files:
                if f.lower().endswith(".pdf") and "startup" not in f.lower():
                    self._pdf_files.append(os.path.join(root, f))

        if self._pdf_files:
            self._status_label.configure(
                text=f"  Found {len(self._pdf_files)} PDF file(s) in: {directory}",
                text_color=T.ACCENT_SUCCESS,
            )
            self._copy_btn.configure(state="normal", text="📋  Copy PDFs to All_Available_Reports")
        else:
            self._status_label.configure(
                text=f"  No PDF files found in: {directory}",
                text_color=T.ACCENT_WARNING,
            )

    def _copy_pdfs(self):
        """Copy scanned PDF files to All_Available_Reports folder."""
        if not self._pdf_files or not self._selected_dir:
            return

        parent_dir = os.path.dirname(self._selected_dir)
        dest_dir = os.path.join(parent_dir, "All_Available_Reports")
        os.makedirs(dest_dir, exist_ok=True)

        mode = self._dup_mode.get()
        copied = 0
        skipped = 0

        for pdf_path in self._pdf_files:
            filename = os.path.basename(pdf_path)
            dest_path = os.path.join(dest_dir, filename)

            if os.path.exists(dest_path):
                if mode == "ignore_duplicates":
                    skipped += 1
                    continue
                else:
                    # Rename with _Dup, _Dup1, _Dup2, etc.
                    name, ext = os.path.splitext(filename)
                    dest_path = os.path.join(dest_dir, f"{name}_Dup{ext}")
                    counter = 1
                    while os.path.exists(dest_path):
                        dest_path = os.path.join(dest_dir, f"{name}_Dup{counter}{ext}")
                        counter += 1

            shutil.copy2(pdf_path, dest_path)
            copied += 1

        status_parts = [f"Copied {copied} PDF file(s) to: {dest_dir}"]
        if skipped:
            status_parts.append(f"({skipped} duplicate(s) skipped)")
        self._status_label.configure(
            text=f"  {' '.join(status_parts)}",
            text_color=T.ACCENT_SUCCESS,
        )
        self._copy_btn.configure(state="disabled", text="✅  Copied Successfully")
