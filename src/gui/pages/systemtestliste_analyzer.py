"""
SystemTestListe Analyzer page – cross-reference PDF results against an Excel SystemTestListe.
"""
import logging
import os
import time
import threading
from tkinter import filedialog
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T
from src.gui.widgets.segmented_progress import SegmentedProgressBar
from src.gui.widgets.hover_button import RttButton
from src.utils import fmt_elapsed as _fmt_elapsed
from src.core.systemtestliste.utils import parse_sw_variant
from src.core.systemtestliste.utils import normalize_sw_for_comparison
from src.core.systemtestliste.presets import (
    load_presets,
    variant_map_from_presets,
    sw_patterns_from_presets,
    result_keywords_from_presets,
    sw_comparison_regex_from_presets,
)
from src.core.systemtestliste.excel_reader import (
    load_sheet_names,
    read_sheet_data,
    find_header_row,
    filter_hilts_rows,
    OUTPUT_COLS,
)
from src.core.systemtestliste.pdf_matcher import build_pdf_index, match_all_rows
from src.core.systemtestliste.report_writer import write_stl_helper


class SystemTestListePage(ctk.CTkFrame):
    """SystemTestListe Analyzer page – verify PDF result/variant/SW info against an Excel sheet."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._excel_file: str = ""
        self._pdf_dir: str = ""
        self._all_tabs: list[str] = []
        self._selected_tab: str = ""
        self._sw_name: str = ""
        self._variant: str = ""
        self._result_path: str = ""
        # poll-based UI update state (worker writes, main thread flushes at 50 ms)
        self._poll_lock = threading.Lock()          # protects _pending_* dicts
        self._pending_status: tuple | None = None   # (text, color)
        self._pending_segs: dict = {}               # {idx: value}
        self._pending_seg_labels: dict = {}         # {idx: text}
        self._poll_running: bool = False
        self._cancel_event = threading.Event()      # cooperative cancellation
        self._worker_thread: threading.Thread | None = None
        self._logger = logging.getLogger(__name__)
        self._build()

    # ────────────────────────────────────────────────────────────
    # Build layout
    # ────────────────────────────────────────────────────────────
    def _build(self):
        # Scrollable container so all cards are reachable
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self._scroll.pack(fill="both", expand=True)

        # ── Page title ──────────────────────────────────────────
        title_frame = ctk.CTkFrame(self._scroll, fg_color="transparent")
        title_frame.pack(fill="x", padx=30, pady=(25, 5))

        ctk.CTkLabel(
            title_frame,
            text="SystemTestListe Analyzer",
            font=(T.FONT_FAMILY, T.FONT_SIZE_TITLE, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(side="left")

        ctk.CTkLabel(
            title_frame,
            text="Verify PDF results against the SystemTestListe Excel sheet",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="left", padx=(15, 0), pady=(6, 0))

        # ── Cards 1 & 4 · Excel (50%) + Folder (50%) side by side ──
        self._file_row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._file_row.pack(fill="x", padx=30, pady=(20, 15))
        self._file_row.columnconfigure(0, weight=1)
        self._file_row.columnconfigure(1, weight=1)

        self._build_excel_card()

        # ── Cards 2 & 3 · Tab list (90%) + SW/Variant (10%) side by side
        self._side_row = ctk.CTkFrame(self._scroll, fg_color="transparent")
        self._side_row.pack(fill="x", padx=30, pady=(0, 15))
        self._side_row.columnconfigure(0, weight=9)  # 90%
        self._side_row.columnconfigure(1, weight=1)  # 10%

        self._build_tab_card()
        self._build_sw_variant_card()

        # ── Card 4 · Folder selection (built into _file_row) ──
        self._build_folder_card()

        # ── Card 5 · Verification options ───────────────────────
        self._build_options_card()

        # ── Bottom bar ──────────────────────────────────────────
        self._build_bottom_bar()

    # ── Card 1 ─────────────────────────────────────────────────
    def _build_excel_card(self):
        card = ctk.CTkFrame(
            self._file_row,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            card,
            text="SystemTestListe Excel File",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 12))

        row = ctk.CTkFrame(card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 20))

        self._excel_entry = ctk.CTkEntry(
            row,
            placeholder_text="No Excel file selected...",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            fg_color=T.BG_SIDEBAR,
            text_color=T.TEXT_PRIMARY,
            border_color=T.BORDER_COLOR,
            corner_radius=T.BUTTON_CORNER,
            height=38,
            state="disabled",
        )
        self._excel_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        RttButton(
            row,
            text="Browse",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            height=38,
            width=120,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS,
            hover_color=T.SIDEBAR_BTN_HOVER,
            text_color="#000000",
            command=self._browse_excel,
        ).pack(side="right")

    # ── Card 2 ─────────────────────────────────────────────────
    def _build_tab_card(self):
        self._tab_card = ctk.CTkFrame(
            self._side_row,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        self._tab_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(
            self._tab_card,
            text="Select Sheet / Tab",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(9, 5))

        # Filter row
        self._filter_row = ctk.CTkFrame(self._tab_card, fg_color="transparent")
        self._filter_row.pack(fill="x", padx=20, pady=(0, 5))
        filter_row = self._filter_row

        ctk.CTkLabel(
            filter_row,
            text="Filter:",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 8))

        self._filter_var = ctk.StringVar()
        self._filter_var.trace_add("write", lambda *_: self._apply_filter())

        self._filter_entry = ctk.CTkEntry(
            self._filter_row,
            textvariable=self._filter_var,
            placeholder_text="Type to filter tabs...",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            fg_color=T.BG_SIDEBAR,
            text_color=T.TEXT_PRIMARY,
            border_color=T.BORDER_COLOR,
            corner_radius=T.BUTTON_CORNER,
            height=34,
        )
        self._filter_entry.pack(side="left", fill="x", expand=True)

        RttButton(
            self._filter_row,
            text="✖",
            width=34,
            height=34,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR,
            hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_SECONDARY,
            command=lambda: self._filter_var.set(""),
        ).pack(side="left", padx=(6, 0))

        # List of tab buttons (plain frame – outer scroll handles scrolling)
        self._tab_list_frame = ctk.CTkFrame(
            self._tab_card,
            fg_color=T.BG_SIDEBAR,
            corner_radius=T.BUTTON_CORNER,
        )
        self._tab_list_frame.pack(fill="x", padx=20, pady=(0, 9))

        # ── Selected-tab row (hidden until a tab is chosen) ─────
        self._selected_row = ctk.CTkFrame(self._tab_card, fg_color="transparent")
        # not packed yet

        self._selected_name_label = ctk.CTkLabel(
            self._selected_row,
            text="",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            text_color=T.ACCENT_PRIMARY,
            anchor="w",
        )
        self._selected_name_label.pack(side="left", fill="x", expand=True, padx=(0, 10))

        RttButton(
            self._selected_row,
            text="Reset",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            height=32,
            width=90,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR,
            hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_SECONDARY,
            command=self._reset_tab_selection,
        ).pack(side="right")

        self._tab_buttons: dict[str, ctk.CTkButton] = {}

    # ── Card 3 ─────────────────────────────────────────────────
    def _build_sw_variant_card(self):
        self._sw_card = ctk.CTkFrame(
            self._side_row,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        self._sw_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            self._sw_card,
            text="Detected SW & Variant",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(9, 6))

        info_row = ctk.CTkFrame(self._sw_card, fg_color="transparent")
        info_row.pack(fill="x", padx=20, pady=(0, 9))

        # SW name chip
        sw_box = ctk.CTkFrame(info_row, fg_color=T.BG_SIDEBAR, corner_radius=T.BUTTON_CORNER)
        sw_box.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            sw_box,
            text="SW",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(anchor="w", padx=12, pady=(4, 0))

        self._sw_label = ctk.CTkLabel(
            sw_box,
            text="—",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.ACCENT_PRIMARY,
        )
        self._sw_label.pack(padx=12, pady=(0, 4))

        # Variant chip
        var_box = ctk.CTkFrame(info_row, fg_color=T.BG_SIDEBAR, corner_radius=T.BUTTON_CORNER)
        var_box.pack(side="left")

        ctk.CTkLabel(
            var_box,
            text="Variant",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(anchor="w", padx=12, pady=(4, 0))

        self._variant_label = ctk.CTkLabel(
            var_box,
            text="—",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.ACCENT_WARNING,
        )
        self._variant_label.pack(padx=12, pady=(0, 4))

    # ── Card 4 ─────────────────────────────────────────────────
    def _build_folder_card(self):
        self._folder_card = ctk.CTkFrame(
            self._file_row,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        self._folder_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(
            self._folder_card,
            text="PDF Reports Directory",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 12))

        row = ctk.CTkFrame(self._folder_card, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=(0, 20))

        self._dir_entry = ctk.CTkEntry(
            row,
            placeholder_text="No directory selected...",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            fg_color=T.BG_SIDEBAR,
            text_color=T.TEXT_PRIMARY,
            border_color=T.BORDER_COLOR,
            corner_radius=T.BUTTON_CORNER,
            height=38,
            state="disabled",
        )
        self._dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self._folder_browse_btn = RttButton(
            row,
            text="Browse",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            height=38,
            width=120,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            text_color="#000000",
            command=self._browse_directory,
        )
        # not packed yet – shown only after a SW tab is selected

    # ── Card 5 ─────────────────────────────────────────────────
    def _build_options_card(self):
        opt_card = ctk.CTkFrame(
            self._scroll,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        opt_card.pack(fill="x", padx=30, pady=(0, 15))

        ctk.CTkLabel(
            opt_card,
            text="Verification Options",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 12))

        checks_row = ctk.CTkFrame(opt_card, fg_color="transparent")
        checks_row.pack(anchor="w", padx=20, pady=(0, 18))

        self._chk_result_var  = ctk.BooleanVar(value=True)
        self._chk_sw_var      = ctk.BooleanVar(value=True)
        self._chk_variant_var = ctk.BooleanVar(value=True)
        self._chk_library_var = ctk.BooleanVar(value=True)

        _chk_opts = dict(
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            onvalue=True,
            offvalue=False,
        )
        for var, label in [
            (self._chk_result_var, "Result Status"),
            (self._chk_sw_var,     "SW Version"),
        ]:
            ctk.CTkCheckBox(checks_row, text=label, variable=var, **_chk_opts
                            ).pack(side="left", padx=(0, 30))

        self._variant_chk = ctk.CTkCheckBox(
            checks_row, text="Variant Information",
            variable=self._chk_variant_var, **_chk_opts
        )
        self._variant_chk.pack(side="left", padx=(0, 30))

        self._library_chk = ctk.CTkCheckBox(
            checks_row, text="Library Check",
            variable=self._chk_library_var, **_chk_opts
        )
        self._library_chk.pack(side="left", padx=(0, 30))

    # ── Bottom bar ──────────────────────────────────────────────
    def _build_bottom_bar(self):
        self._bottom_card = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        self._bottom_card.pack(fill="x", side="bottom", padx=30, pady=(0, 20))

        self._status_label = ctk.CTkLabel(
            self._bottom_card,
            text="  Select an Excel file to begin.",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        )
        self._status_label.pack(anchor="w", padx=20, pady=(14, 6))

        self._progress = SegmentedProgressBar(
            self._bottom_card,
            segments=[
                {"label": "Reading Excel",  "color": T.ACCENT_SUCCESS},
                {"label": "Scanning PDFs",  "color": T.ACCENT_PRIMARY},
                {"label": "Report",         "color": T.ACCENT_SECONDARY},
            ],
        )
        self._progress.pack(fill="x", padx=20, pady=(0, 10))

        btn_row = ctk.CTkFrame(self._bottom_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 14))

        self._start_btn = RttButton(
            btn_row,
            text="Start",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            height=40,
            width=140,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS,
            hover_color="#00c853",
            text_color="#000000",
            command=self._start_analysis,
        )
        self._start_btn.pack(side="right")

        self._open_btn = RttButton(
            btn_row,
            text="Open Result",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            height=40,
            width=140,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            text_color="#000000",
            state="normal",
            command=self._open_result_file,
        )
        # Hidden until a successful analysis produces an output file
        self._open_btn_row = btn_row  # keep reference for re-packing

    # ────────────────────────────────────────────────────────────
    # Excel browser & tab loading
    # ────────────────────────────────────────────────────────────
    def _browse_excel(self):
        path = filedialog.askopenfilename(
            title="Select SystemTestListe Excel File",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")],
        )
        if not path:
            return
        self._excel_file = path
        self._excel_entry.configure(state="normal")
        self._excel_entry.delete(0, "end")
        self._excel_entry.insert(0, path)
        self._excel_entry.configure(state="disabled")

        # Reset downstream state
        self._selected_tab = ""
        self._sw_name = ""
        self._variant = ""
        self._sw_label.configure(text="—")
        self._variant_label.configure(text="—")

        self._status_label.configure(
            text="  Reading Excel sheets…", text_color=T.TEXT_SECONDARY
        )
        threading.Thread(target=self._load_tabs, daemon=True).start()

    def _load_tabs(self):
        """Read sheet names from the Excel file (background thread)."""
        try:
            tabs = load_sheet_names(self._excel_file)
        except Exception as e:
            self._ui(lambda: self._status_label.configure(
                text=f"  Failed to read Excel: {e}",
                text_color=T.ACCENT_DANGER,
            ))
            return

        self._all_tabs = tabs
        self._ui(self._populate_tab_list)

    def _populate_tab_list(self):
        """Build tab buttons inside the scrollable list (main thread)."""
        # Clear previous buttons
        for btn in self._tab_buttons.values():
            btn.destroy()
        self._tab_buttons.clear()
        self._filter_var.set("")
        # Ensure filter + list are visible (e.g. after reloading a new file)
        self._selected_row.pack_forget()
        self._filter_row.pack(fill="x", padx=20, pady=(0, 5))
        self._tab_list_frame.pack(fill="x", padx=20, pady=(0, 9))

        for tab in self._all_tabs:
            btn = RttButton(
                self._tab_list_frame,
                text=tab,
                font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
                anchor="w",
                height=32,
                corner_radius=T.BUTTON_CORNER,
                fg_color="transparent",
                hover_color=T.SIDEBAR_BTN_ACTIVE_BG,
                text_color=T.TEXT_PRIMARY,
                border_width=0,
                command=lambda t=tab: self._on_tab_select(t),
            )
            btn.pack(fill="x", pady=2, padx=4)
            self._tab_buttons[tab] = btn

        self._status_label.configure(
            text=f"  {len(self._all_tabs)} sheet(s) loaded. Select a tab.",
            text_color=T.TEXT_SECONDARY,
        )

    # ── Filter ──────────────────────────────────────────────────
    def _apply_filter(self):
        query = self._filter_var.get().lower()
        for tab, btn in self._tab_buttons.items():
            if query in tab.lower():
                btn.pack(fill="x", pady=2, padx=4)
            else:
                btn.pack_forget()

    # ── Tab selection ───────────────────────────────────────────
    def _on_theme_refresh(self) -> None:
        """Re-apply tab highlight colors after a theme switch."""
        if not self._tab_buttons:
            return
        for name, btn in self._tab_buttons.items():
            if name == self._selected_tab:
                btn.configure(
                    fg_color=T.SIDEBAR_BTN_ACTIVE_BG,
                    text_color=T.ACCENT_PRIMARY,
                    border_width=1,
                    border_color=T.ACCENT_PRIMARY,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=T.TEXT_PRIMARY,
                    border_width=0,
                )

    def _on_tab_select(self, tab: str):
        self._selected_tab = tab

        # Highlight selected button, reset all others
        for name, btn in self._tab_buttons.items():
            if name == tab:
                btn.configure(
                    fg_color=T.SIDEBAR_BTN_ACTIVE_BG,
                    text_color=T.ACCENT_PRIMARY,
                    border_width=1,
                    border_color=T.ACCENT_PRIMARY,
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=T.TEXT_PRIMARY,
                    border_width=0,
                )

        sw, variant = parse_sw_variant(tab)
        self._sw_name = sw
        self._variant = variant

        self._sw_label.configure(text=sw or "—")
        self._variant_label.configure(text=variant or "—")

        self._status_label.configure(
            text=f"  Selected: {tab}   |   SW: {sw}   |   Variant: {variant}",
            text_color=T.ACCENT_SUCCESS,
        )

        # Show/hide Variant checkbox based on SW name (hide when 2nd segment is '200')
        segs = sw.split("_")
        is_200 = len(segs) >= 2 and segs[1] == "200"
        if is_200:
            self._chk_variant_var.set(False)
            self._variant_chk.pack_forget()
            self._library_chk.pack_forget()
        else:
            self._variant_chk.pack(side="left", padx=(0, 30))
            self._library_chk.pack(side="left", padx=(0, 30))

        # Show folder browse now that a SW is selected
        self._folder_browse_btn.pack(side="right")

        # Collapse filter + list; show compact name chip
        self._selected_name_label.configure(text=tab)
        self._filter_row.pack_forget()
        self._tab_list_frame.pack_forget()
        self._selected_row.pack(fill="x", padx=20, pady=(0, 9))

        # Scroll the page back to the top so the chip and rest of the form are visible
        try:
            self._scroll._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass

    # ── Reset tab selection ─────────────────────────────────────
    def _reset_tab_selection(self):
        """Clear the selected tab and restore the filter + list."""
        self._selected_tab = ""
        self._sw_name = ""
        self._variant = ""
        self._sw_label.configure(text="—")
        self._variant_label.configure(text="—")
        # Deselect all buttons
        for btn in self._tab_buttons.values():
            btn.configure(
                fg_color="transparent",
                text_color=T.TEXT_PRIMARY,
                border_width=0,
            )
        # Hide folder browse until a SW tab is re-selected
        self._folder_browse_btn.pack_forget()
        # Restore variant + library checkbox visibility
        self._variant_chk.pack(side="left", padx=(0, 30))
        self._library_chk.pack(side="left", padx=(0, 30))
        # Show filter + list; hide name chip
        self._filter_var.set("")
        self._selected_row.pack_forget()
        self._filter_row.pack(fill="x", padx=20, pady=(0, 5))
        self._tab_list_frame.pack(fill="x", padx=20, pady=(0, 9))
        self._status_label.configure(
            text=f"  {len(self._all_tabs)} sheet(s) loaded. Select a tab.",
            text_color=T.TEXT_SECONDARY,
        )

        # Scroll back to top so the filter+list are immediately visible
        try:
            self._scroll._parent_canvas.yview_moveto(0.0)
        except Exception:
            pass

    # ── Folder browser ──────────────────────────────────────────
    def _browse_directory(self):
        directory = filedialog.askdirectory(
            title="Select Directory Containing PDF Reports",
        )
        if not directory:
            return
        self._pdf_dir = directory
        self._dir_entry.configure(state="normal")
        self._dir_entry.delete(0, "end")
        self._dir_entry.insert(0, directory)
        self._dir_entry.configure(state="disabled")
        if self._selected_tab:
            self._status_label.configure(
                text="  Ready. Click '▶  Start' to begin verification.",
                text_color=T.ACCENT_SUCCESS,
            )

    # ── Thread-safe GUI helpers ─────────────────────────────────
    def _ui(self, fn):
        """Schedule *fn* on the main thread (one-shot, for infrequent events only)."""
        self.after(0, fn)

    def _set_status(self, text: str, color: str = T.TEXT_PRIMARY):
        """Worker thread: stash latest status; poll loop applies it."""
        with self._poll_lock:
            self._pending_status = (text, color)

    def _set_seg(self, idx: int, value: float):
        """Worker thread: stash latest segment value; poll loop applies it."""
        with self._poll_lock:
            self._pending_segs[idx] = value

    def _set_seg_label(self, idx: int, text: str):
        """Worker thread: stash latest segment label; poll loop applies it."""
        with self._poll_lock:
            self._pending_seg_labels[idx] = text

    # ── 50 ms poll loop ─────────────────────────────────────
    def _start_poll(self):
        """Start the GUI-flush loop. Call from main thread before launching worker."""
        with self._poll_lock:
            self._pending_status = None
            self._pending_segs = {}
            self._pending_seg_labels = {}
        self._poll_running = True
        self.after(50, self._do_poll)

    def _do_poll(self):
        """Flush any pending worker updates to widgets. Reschedules while running."""
        with self._poll_lock:
            status = self._pending_status
            self._pending_status = None
            segs = dict(self._pending_segs)
            self._pending_segs.clear()
            seg_labels = dict(self._pending_seg_labels)
            self._pending_seg_labels.clear()
        if status is not None:
            text, color = status
            self._status_label.configure(text=text, text_color=color)
        if segs:
            self._progress.set_segments_batch(segs)
        for idx, lbl in seg_labels.items():
            self._progress.set_segment_label(idx, lbl)
        if self._poll_running:
            self.after(50, self._do_poll)

    # ── Open result file ────────────────────────────────────────
    def _open_result_file(self):
        if self._result_path and os.path.isfile(self._result_path):
            os.startfile(self._result_path)

    # ── Start analysis ──────────────────────────────────────────
    def _start_analysis(self):
        if not self._excel_file:
            self._status_label.configure(
                text="  Please select a SystemTestListe Excel file first.",
                text_color=T.ACCENT_WARNING,
            )
            return
        if not self._selected_tab:
            self._status_label.configure(
                text="  Please select a sheet / tab from the list.",
                text_color=T.ACCENT_WARNING,
            )
            return
        if not self._pdf_dir:
            self._status_label.configure(
                text="  Please select the PDF reports directory first.",
                text_color=T.ACCENT_WARNING,
            )
            return

        self._open_btn.pack_forget()
        self._start_btn.configure(state="disabled", text="Analyzing...")
        self._progress.reset()
        self._cancel_event.clear()
        self._start_poll()

        # Snapshot Tk variables on the main thread to avoid cross-thread Tcl access
        chk_result_snap  = self._chk_result_var.get()
        chk_sw_snap      = self._chk_sw_var.get()
        chk_variant_snap = self._chk_variant_var.get()
        chk_library_snap = self._chk_library_var.get()

        thread = threading.Thread(
            target=self._run_worker,
            args=(chk_result_snap, chk_sw_snap, chk_variant_snap, chk_library_snap),
            daemon=True,
        )
        self._worker_thread = thread
        thread.start()

    # ── Background worker ───────────────────────────────────────
    def _run_worker(self, chk_result: bool, chk_sw: bool, chk_variant: bool, chk_library: bool):
        """Analysis worker – runs on a daemon thread.

        Checkbox values are captured on the main thread and passed as parameters.
        """
        from datetime import datetime

        # ── Step 1: Read selected sheet ─────────────────────────
        self._set_status(f"  Reading sheet '{self._selected_tab}' from Excel…")
        self._set_seg(0, 0.2)
        _t0 = time.perf_counter()

        try:
            all_rows = read_sheet_data(self._excel_file, self._selected_tab)
        except Exception as e:
            self._set_status(f"  Failed to read Excel: {e}", T.ACCENT_DANGER)
            self._poll_running = False
            self._ui(lambda: self._start_btn.configure(state="normal", text="Start"))
            return

        self._set_seg(0, 0.6)

        # ── Find header row ────────────────────────────────────
        try:
            best_idx, _header_row, col_map = find_header_row(all_rows)
        except ValueError as e:
            self._set_status(f"  {e}", T.ACCENT_DANGER)
            self._poll_running = False
            self._ui(lambda: self._start_btn.configure(state="normal", text="Start"))
            return

        self._set_seg(0, 1.0)
        _elapsed = time.perf_counter() - _t0
        self._set_seg_label(0, f"Reading Excel ({_fmt_elapsed(_elapsed)})")

        # ── Step 2: Filter rows where Description contains HILTS
        self._set_status("  Filtering HILTS rows…")
        self._set_seg(1, 0.3)
        _t1 = time.perf_counter()

        data_rows = filter_hilts_rows(all_rows, best_idx, col_map)

        self._set_seg(1, 1.0)

        # ── Step 3 & 4: Scan PDFs and collect results ───────────
        self._set_status("  Scanning PDFs and updating results…")
        self._set_seg(1, 0.0)

        pdf_index   = build_pdf_index(self._pdf_dir)
        sw_name     = self._sw_name  if chk_sw      else ""
        variant     = self._variant  if chk_variant else ""

        # Load live presets so any changes saved on the Presets page are
        # picked up immediately without restarting the application.
        from src.core.systemtestliste.presets import library_settings_from_presets
        presets          = load_presets()
        variant_map      = variant_map_from_presets(presets) if chk_variant else {}
        sw_patterns      = sw_patterns_from_presets(presets) if chk_sw      else None
        sw_cmp_regex     = sw_comparison_regex_from_presets(presets) if chk_sw else ""
        keywords         = result_keywords_from_presets(presets)
        result_page_idx  = presets["result_extraction"]["page"] - 1
        sw_page_idx      = presets["sw_extraction"]["page"] - 1
        variant_page_idx = presets["variant_extraction"]["page"] - 1
        lib_settings     = library_settings_from_presets(presets)
        library_page_idx          = lib_settings["page"] - 1
        library_search_text       = lib_settings["search_text"]    if chk_library else ""
        library_version_pattern   = lib_settings["version_pattern"] if chk_library else r"[vV]\d+\.\d+"
        total            = len(data_rows)

        def _pdf_progress(processed: int, total_: int, pdf_result: str) -> None:
            frac = processed / total_ if total_ else 1.0
            self._set_seg(1, frac)
            self._set_status(
                f"  Scanning PDFs {processed}/{total_}  |  SW: {sw_name or '—'}"
                f"  |  Variant: {variant or '—'}  |  Last: {pdf_result}",
                T.TEXT_SECONDARY,
            )

        match_dicts = match_all_rows(
            data_rows, pdf_index,
            sw_name=sw_name, variant=variant,
            variant_map=variant_map,
            sw_patterns=sw_patterns,
            keywords=keywords,
            result_page_idx=result_page_idx,
            sw_page_idx=sw_page_idx,
            variant_page_idx=variant_page_idx,
            library_page_idx=library_page_idx,
            library_search_text=library_search_text,
            library_version_pattern=library_version_pattern,
            on_progress=_pdf_progress,
        )

        _pdf_elapsed = time.perf_counter() - _t1
        self._set_seg_label(1, f"Scanning PDFs ({_fmt_elapsed(_pdf_elapsed)})")

        # Unpack parallel lists from the result dicts
        pdf_results        = [d["result"]          for d in match_dicts]
        page3_sw_list      = [d["page3_sw"]        for d in match_dicts]
        page3_variant_list = [d["page3_variant"]   for d in match_dicts]
        library_ver_raw    = [d.get("library_version", "") for d in match_dicts]

        # ── Step 5: Compute match flags ─────────────────────────
        stl_result_idx = 2  # OUTPUT_COLS index for "Result"

        match_flags: list[bool] | None = None
        if chk_result:
            match_flags = [
                row[stl_result_idx].strip().lower() == pdf_res.strip().lower()
                for row, pdf_res in zip(data_rows, pdf_results)
            ]

        sw_match_flags: list[bool] | None = None
        out_page3_sw: list[str] | None = None
        if chk_sw:
            out_page3_sw   = page3_sw_list
            norm_expected  = normalize_sw_for_comparison(sw_name, sw_cmp_regex)
            sw_match_flags = [
                bool(p3) and norm_expected == normalize_sw_for_comparison(p3, sw_cmp_regex)
                for p3 in page3_sw_list
            ]

        variant_match_flags: list[bool] | None = None
        out_page3_variant: list[str] | None = None
        if chk_variant:
            out_page3_variant   = page3_variant_list
            variant_match_flags = [
                bool(p3) and variant.strip().lower() == p3.strip().lower()
                for p3 in page3_variant_list
            ]

        out_library_ver: list[str] | None = library_ver_raw if chk_library else None

        # ── Step 6: Write output Excel ───────────────────────────
        output_dir = os.path.dirname(self._excel_file)
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        _t2 = time.perf_counter()
        try:
            output_path = write_stl_helper(
                output_dir, data_rows, pdf_results, OUTPUT_COLS, timestamp,
                sw_name=sw_name,
                variant=variant,
                match_flags=match_flags,
                page3_sw_list=out_page3_sw,
                sw_match_flags=sw_match_flags,
                page3_variant_list=out_page3_variant,
                variant_match_flags=variant_match_flags,
                library_version_list=out_library_ver,
            )
        except Exception as e:
            self._set_status(f"  Failed to save output: {e}", T.ACCENT_DANGER)
            self._poll_running = False
            self._ui(lambda: self._start_btn.configure(state="normal", text="Start"))
            return

        self._result_path = output_path
        self._set_seg(2, 1.0)
        _report_elapsed = time.perf_counter() - _t2
        self._set_seg_label(2, f"Report ({_fmt_elapsed(_report_elapsed)})")

        # ── Summary message ───────────────────────────────────────
        parts: list[str] = []
        if match_flags is not None:
            parts.append(f"Result: {sum(match_flags)}/{len(data_rows)}")
        if sw_match_flags is not None:
            parts.append(f"SW: {sum(sw_match_flags)}/{len(data_rows)}")
        if variant_match_flags is not None:
            parts.append(f"Variant: {sum(variant_match_flags)}/{len(data_rows)}")
        if out_library_ver is not None:
            linked = sum(1 for v in out_library_ver if v)
            parts.append(f"Library: {linked}/{len(data_rows)} linked")
        match_info = ("  |  Match – " + "  ".join(parts)) if parts else ""

        final = (
            f"  ✅  Done – {len(data_rows)} HILTS row(s) written to "
            f"{os.path.basename(output_path)}  |  Header found at row {best_idx + 1}"
            f"{match_info}"
        )
        self._set_status(final, T.ACCENT_SUCCESS)
        self._poll_running = False
        self._ui(lambda: self._start_btn.configure(state="normal", text="Start"))
        self._ui(lambda: self._open_btn.pack(side="right", padx=(0, 10)))

