"""
Presets page – configure SW-name patterns and Variant ↔ SWFL mappings
used by the SystemTestListe Analyser.

Two cards:
  1. SW Pattern Card  – manage regex patterns + extraction page number.
  2. Variant Info Card – manage Variant ↔ SWFL table + extraction page number,
                         with bulk import from a Variant_Info .txt file.

All changes are persisted to ``config/presets.json``.
"""
import re
from tkinter import filedialog, messagebox
import customtkinter as ctk

from src.gui.styles.theme import AppTheme as T
from src.gui.widgets.hover_button import RttButton
from src.core.systemtestliste.presets import (
    load_presets,
    save_presets,
    import_variant_txt,
    try_add_sw_pattern,
    library_settings_from_presets,
    sw_comparison_regex_from_presets,
)


# ── tiny helpers ─────────────────────────────────────────────────
def _entry(parent, placeholder="", width=None, **kw) -> ctk.CTkEntry:
    opts = dict(
        font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
        fg_color=T.BG_SIDEBAR,
        text_color=T.TEXT_PRIMARY,
        border_color=T.BORDER_COLOR,
        corner_radius=T.BUTTON_CORNER,
        height=34,
        placeholder_text=placeholder,
    )
    opts.update(kw)
    if width:
        opts["width"] = width
    return ctk.CTkEntry(parent, **opts)


def _label(parent, text, color=None, bold=False, small=False) -> ctk.CTkLabel:
    size = T.FONT_SIZE_SMALL if small else T.FONT_SIZE_BODY
    weight = "bold" if bold else "normal"
    return ctk.CTkLabel(
        parent,
        text=text,
        font=(T.FONT_FAMILY, size, weight),
        text_color=color or T.TEXT_PRIMARY,
    )


def _divider(parent):
    ctk.CTkFrame(parent, height=1, fg_color=T.BORDER_COLOR).pack(fill="x", padx=20)


# ══════════════════════════════════════════════════════════════════
# PAGE
# ══════════════════════════════════════════════════════════════════

class STLPresetsPage(ctk.CTkFrame):
    """ Presets page – Result + SW patterns + Variant ↔ SWFL mappings."""

    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self._presets: dict = load_presets()
        # Indices for currently-selected rows (None = no selection / new mode)
        self._sw_sel: int | None = None
        self._var_sel: int | None = None
        # Track row widgets for quick refresh without full rebuild
        self._sw_rows:  list[ctk.CTkFrame] = []
        self._var_rows: list[ctk.CTkFrame] = []
        self._build()

    # ─────────────────────────────────────────────────────────────
    # Build
    # ─────────────────────────────────────────────────────────────
    def _build(self):
        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True)
        self._scroll = scroll

        # ── Page header
        header = ctk.CTkFrame(scroll, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(25, 5))
        _label(header, "Presets", color=T.TEXT_BRIGHT, bold=True).pack(side="left")
        ctk.CTkLabel(
            header,
            text="Result + SW-name patterns and Variant ↔ SWFL mappings for the analyser",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="left", padx=(15, 0), pady=(6, 0))
        RttButton(
            header, text="💾  Save All to File", height=34, width=155,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS, hover_color="#00c853",
            text_color="#000000",
            command=self._save_all,
        ).pack(side="right")

        self._build_pages_card(scroll)
        self._build_sw_card(scroll)
        self._build_sw_comparison_card(scroll)
        self._build_result_card(scroll)
        self._build_variant_card(scroll)
        self._build_library_card(scroll)

    # ════════════════════════════════════════════════════════════
    # Card 0 – Page Numbers
    # ════════════════════════════════════════════════════════════
    def _build_pages_card(self, parent):
        card = ctk.CTkFrame(
            parent, corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD, border_width=1, border_color=T.BORDER_COLOR,
        )
        card.pack(fill="x", padx=30, pady=(20, 15))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        _label(hdr, "PDF Extraction Pages", color=T.TEXT_BRIGHT, bold=True).pack(side="left")
        _label(
            hdr,
            "1-based page numbers used when reading PDFs",
            color=T.TEXT_SECONDARY, small=True,
        ).pack(side="left", padx=(12, 0), pady=(2, 0))

        _divider(card)

        grid = ctk.CTkFrame(card, fg_color="transparent")
        grid.pack(fill="x", padx=30, pady=(14, 18))

        _entry_opts = dict(
            width=70, height=36,
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            fg_color=T.BG_SIDEBAR, text_color=T.TEXT_PRIMARY,
            border_color=T.BORDER_COLOR, corner_radius=T.BUTTON_CORNER,
        )

        # ── Result
        _label(grid, "Result Status", color=T.TEXT_SECONDARY).grid(
            row=0, column=0, sticky="w", padx=(0, 12), pady=6)
        _label(grid, "page:", color=T.TEXT_SECONDARY, small=True).grid(
            row=0, column=1, sticky="e", padx=(0, 6), pady=6)
        self._result_page_var = ctk.StringVar(
            value=str(self._presets["result_extraction"].get("page", 3))
        )
        ctk.CTkEntry(grid, textvariable=self._result_page_var, **_entry_opts).grid(
            row=0, column=2, sticky="w", pady=6)
        _label(grid, "  →  page where result keywords (Passed/Failed/…) appear",
               color=T.TEXT_SECONDARY, small=True).grid(
            row=0, column=3, sticky="w", padx=(10, 0), pady=6)

        # ── SW Name
        _label(grid, "SW Version", color=T.TEXT_SECONDARY).grid(
            row=1, column=0, sticky="w", padx=(0, 12), pady=6)
        _label(grid, "page:", color=T.TEXT_SECONDARY, small=True).grid(
            row=1, column=1, sticky="e", padx=(0, 6), pady=6)
        self._sw_page_var = ctk.StringVar(
            value=str(self._presets["sw_extraction"].get("page", 3))
        )
        ctk.CTkEntry(grid, textvariable=self._sw_page_var, **_entry_opts).grid(
            row=1, column=2, sticky="w", pady=6)
        _label(grid, "  →  page where the SW name string (NNN_NNN_…) appears",
               color=T.TEXT_SECONDARY, small=True).grid(
            row=1, column=3, sticky="w", padx=(10, 0), pady=6)

        # ── Variant
        _label(grid, "Variant (SWFL)", color=T.TEXT_SECONDARY).grid(
            row=2, column=0, sticky="w", padx=(0, 12), pady=6)
        _label(grid, "page:", color=T.TEXT_SECONDARY, small=True).grid(
            row=2, column=1, sticky="e", padx=(0, 6), pady=6)
        self._var_page_var = ctk.StringVar(
            value=str(self._presets["variant_extraction"].get("page", 3))
        )
        ctk.CTkEntry(grid, textvariable=self._var_page_var, **_entry_opts).grid(
            row=2, column=2, sticky="w", pady=6)
        _label(grid, "  →  page where the SWFL code (SWFL-XXXXXXXX) appears",
               color=T.TEXT_SECONDARY, small=True).grid(
            row=2, column=3, sticky="w", padx=(10, 0), pady=6)
        # ── Library
        _label(grid, "Library Version", color=T.TEXT_SECONDARY).grid(
            row=3, column=0, sticky="w", padx=(0, 12), pady=6)
        _label(grid, "page:", color=T.TEXT_SECONDARY, small=True).grid(
            row=3, column=1, sticky="e", padx=(0, 6), pady=6)
        self._lib_page_var = ctk.StringVar(
            value=str(self._presets.get("library_extraction", {}).get("page", 3))
        )
        ctk.CTkEntry(grid, textvariable=self._lib_page_var, **_entry_opts).grid(
            row=3, column=2, sticky="w", pady=6)
        _label(grid, "  \u2192  page where the library version text appears",
               color=T.TEXT_SECONDARY, small=True).grid(
            row=3, column=3, sticky="w", padx=(10, 0), pady=6)
        # ── Save button
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 14))
        RttButton(
            btn_row, text="Save Page Numbers", height=34, width=160,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS, hover_color="#00c853",
            text_color="#000000",
            command=self._save_page_numbers,
        ).pack(side="right")

    # ══════════════════════════════════════════════════════════════
    # Card 1 – SW Pattern
    # ══════════════════════════════════════════════════════════════
    def _build_sw_card(self, parent):
        card = ctk.CTkFrame(
            parent, corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD, border_width=1, border_color=T.BORDER_COLOR,
        )
        card.pack(fill="x", padx=30, pady=(20, 15))

        # ── header row
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        _label(hdr, "SW Name Extraction Patterns", color=T.TEXT_BRIGHT, bold=True).pack(side="left")

        _divider(card)

        # ── scrollable list of patterns
        self._sw_list_frame = ctk.CTkFrame(card, fg_color=T.BG_SIDEBAR, corner_radius=T.BUTTON_CORNER)
        self._sw_list_frame.pack(fill="x", padx=20, pady=(10, 6))
        self._sw_populate_list()

        _divider(card)

        # ── Edit form
        edit = ctk.CTkFrame(card, fg_color="transparent")
        edit.pack(fill="x", padx=20, pady=(10, 0))

        _label(edit, "Label:", small=True, color=T.TEXT_SECONDARY).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=2)
        self._sw_lbl_entry = _entry(edit, placeholder="e.g. Default SW Pattern")
        self._sw_lbl_entry.grid(row=0, column=1, sticky="ew", pady=2)

        _label(edit, "Regex:", small=True, color=T.TEXT_SECONDARY).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=2)
        self._sw_re_entry = _entry(edit, placeholder=r"\d{3}_\d{3}_[^_\s]+_\d{2}_\d{2}_[A-Za-z]\d{2}")
        self._sw_re_entry.grid(row=1, column=1, sticky="ew", pady=2)

        _label(edit, "Test text:", small=True, color=T.TEXT_SECONDARY).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=2)
        test_row = ctk.CTkFrame(edit, fg_color="transparent")
        test_row.grid(row=2, column=1, sticky="ew", pady=2)
        test_row.columnconfigure(0, weight=1)
        self._sw_test_entry = _entry(test_row, placeholder="Paste a line from page 3 to test…")
        self._sw_test_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        RttButton(
            test_row, text="Test", width=60, height=30,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_PRIMARY,
            command=self._sw_test_regex,
        ).grid(row=0, column=1)
        self._sw_test_result = _label(test_row, "", color=T.TEXT_SECONDARY, small=True)
        self._sw_test_result.grid(row=0, column=2, padx=(8, 0))

        edit.columnconfigure(1, weight=1)

        # ── action buttons
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(10, 16))

        RttButton(
            btns, text="New", height=34, width=90,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_SECONDARY,
            command=self._sw_new,
        ).pack(side="left", padx=(0, 6))

        RttButton(
            btns, text="Delete Selected", height=34, width=130,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color="#c0392b",
            text_color=T.TEXT_SECONDARY,
            command=self._sw_delete,
        ).pack(side="left")

        RttButton(
            btns, text="Save Entry", height=34, width=110,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color="#000000",
            command=self._sw_save_entry,
        ).pack(side="right", padx=(6, 0))

        RttButton(
            btns, text="Save All to File", height=34, width=140,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS, hover_color="#00c853",
            text_color="#000000",
            command=self._save_all,
        ).pack(side="right")

    # ── SW list helpers ──────────────────────────────────────────
    def _sw_populate_list(self):
        for w in self._sw_list_frame.winfo_children():
            w.destroy()
        self._sw_rows.clear()

        patterns = self._presets["sw_extraction"].get("patterns", [])
        if not patterns:
            _label(self._sw_list_frame, "  No patterns defined.",
                   color=T.TEXT_SECONDARY, small=True).pack(
                anchor="w", padx=10, pady=6)
            return

        for idx, pat in enumerate(patterns):
            self._sw_add_row(idx, pat)

    def _sw_add_row(self, idx: int, pat: dict):
        row = ctk.CTkFrame(
            self._sw_list_frame, fg_color="transparent", corner_radius=T.BUTTON_CORNER
        )
        row.pack(fill="x", padx=4, pady=2)

        selected = (idx == self._sw_sel)
        bg = T.SIDEBAR_BTN_ACTIVE_BG if selected else "transparent"
        row.configure(fg_color=bg)

        def _select(i=idx):
            self._sw_sel = i
            pat_data = self._presets["sw_extraction"]["patterns"][i]
            self._sw_lbl_entry.delete(0, "end")
            self._sw_lbl_entry.insert(0, pat_data.get("label", ""))
            self._sw_re_entry.delete(0, "end")
            self._sw_re_entry.insert(0, pat_data.get("regex", ""))
            self._sw_populate_list()

        row.bind("<Button-1>", lambda _e, i=idx: _select(i))

        num = _label(row, f"{idx + 1}.", color=T.TEXT_SECONDARY, small=True)
        num.pack(side="left", padx=(8, 6), pady=4)
        num.bind("<Button-1>", lambda _e, i=idx: _select(i))

        lbl = _label(
            row,
            pat.get("label", "—"),
            color=T.ACCENT_PRIMARY if selected else T.TEXT_BRIGHT,
        )
        lbl.pack(side="left", padx=(0, 12), pady=4)
        lbl.bind("<Button-1>", lambda _e, i=idx: _select(i))

        regex_txt = pat.get("regex", "")
        re_lbl = _label(row, regex_txt, color=T.TEXT_SECONDARY, small=True)
        re_lbl.pack(side="left", pady=4)
        re_lbl.bind("<Button-1>", lambda _e, i=idx: _select(i))

        self._sw_rows.append(row)

    def _sw_new(self):
        self._sw_sel = None
        self._sw_lbl_entry.delete(0, "end")
        self._sw_re_entry.delete(0, "end")
        self._sw_populate_list()

    def _sw_save_entry(self):
        label = self._sw_lbl_entry.get().strip()
        regex = self._sw_re_entry.get().strip()

        ok, reason = try_add_sw_pattern(
            self._presets, label, regex,
            update_idx=self._sw_sel,
        )
        if not ok:
            messagebox.showerror("Cannot Save Pattern", reason)
            return

        # After a new addition, point selection at the appended entry
        if self._sw_sel is None:
            self._sw_sel = len(self._presets["sw_extraction"].get("patterns", [])) - 1
        self._sw_populate_list()

    def _sw_delete(self):
        if self._sw_sel is None:
            messagebox.showinfo("Nothing selected", "Click a pattern row first.")
            return
        patterns = self._presets["sw_extraction"].get("patterns", [])
        if 0 <= self._sw_sel < len(patterns):
            patterns.pop(self._sw_sel)
        self._sw_sel = None
        self._sw_lbl_entry.delete(0, "end")
        self._sw_re_entry.delete(0, "end")
        self._sw_populate_list()

    def _sw_test_regex(self):
        regex = self._sw_re_entry.get().strip()
        text = self._sw_test_entry.get().strip()
        if not regex or not text:
            self._sw_test_result.configure(text="—", text_color=T.TEXT_SECONDARY)
            return
        try:
            m = re.search(regex, text)
            if m:
                self._sw_test_result.configure(
                    text=f"✓  {m.group(0)}", text_color=T.ACCENT_SUCCESS)
            else:
                self._sw_test_result.configure(text="✗  No match", text_color=T.ACCENT_DANGER)
        except re.error as exc:
            self._sw_test_result.configure(text=f"Error: {exc}", text_color=T.ACCENT_WARNING)

    # ══════════════════════════════════════════════════════════════
    # Card 1b – SW Comparison Regex
    # ══════════════════════════════════════════════════════════════
    def _build_sw_comparison_card(self, parent):
        cmp = self._presets.get("sw_comparison", {})
        card = ctk.CTkFrame(
            parent, corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD, border_width=1, border_color=T.BORDER_COLOR,
        )
        card.pack(fill="x", padx=30, pady=(0, 15))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        _label(hdr, "SW Version Comparison Regex", color=T.TEXT_BRIGHT, bold=True).pack(side="left")
        _label(
            hdr,
            "Optional – use capturing groups to compare only parts of the SW name",
            color=T.TEXT_SECONDARY, small=True,
        ).pack(side="left", padx=(12, 0), pady=(2, 0))

        _divider(card)

        edit = ctk.CTkFrame(card, fg_color="transparent")
        edit.pack(fill="x", padx=20, pady=(12, 0))
        edit.columnconfigure(1, weight=1)

        _label(edit, "Regex:", small=True, color=T.TEXT_SECONDARY).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self._sw_cmp_regex_var = ctk.StringVar(value=cmp.get("regex", ""))
        ctk.CTkEntry(
            edit, textvariable=self._sw_cmp_regex_var, height=34,
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            fg_color=T.BG_SIDEBAR, text_color=T.TEXT_PRIMARY,
            border_color=T.BORDER_COLOR, corner_radius=T.BUTTON_CORNER,
            placeholder_text=r"e.g. (\d{3}_\d{3})_[^_\s]+_(\d{2}_\d{2}_[A-Za-z]\d{2})",
        ).grid(row=0, column=1, sticky="ew", pady=4)

        _label(
            edit,
            "Leave empty to compare full SW names.  "
            "Use capturing groups () to compare only those parts.",
            color=T.TEXT_SECONDARY, small=True,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(2, 0))

        # ── Test row
        _label(edit, "Test:", small=True, color=T.TEXT_SECONDARY).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        test_row = ctk.CTkFrame(edit, fg_color="transparent")
        test_row.grid(row=2, column=1, sticky="ew", pady=4)
        test_row.columnconfigure(0, weight=1)
        test_row.columnconfigure(1, weight=1)

        self._sw_cmp_test_a = _entry(test_row, placeholder="Expected SW (from Excel tab)")
        self._sw_cmp_test_a.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self._sw_cmp_test_b = _entry(test_row, placeholder="Extracted SW (from PDF)")
        self._sw_cmp_test_b.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        RttButton(
            test_row, text="Test", width=60, height=30,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_PRIMARY,
            command=self._sw_cmp_test,
        ).grid(row=0, column=2)
        self._sw_cmp_test_result = _label(test_row, "", color=T.TEXT_SECONDARY, small=True)
        self._sw_cmp_test_result.grid(row=0, column=3, padx=(8, 0))

        # ── Buttons
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(10, 16))
        RttButton(
            btns, text="Save Entry", height=34, width=110,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color="#000000",
            command=self._sw_cmp_save_entry,
        ).pack(side="right", padx=(6, 0))
        RttButton(
            btns, text="Save All to File", height=34, width=140,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS, hover_color="#00c853",
            text_color="#000000",
            command=self._save_all,
        ).pack(side="right")

    def _sw_cmp_test(self):
        from src.core.systemtestliste.utils import normalize_sw_for_comparison
        regex = self._sw_cmp_regex_var.get().strip()
        a = self._sw_cmp_test_a.get().strip()
        b = self._sw_cmp_test_b.get().strip()
        if not a or not b:
            self._sw_cmp_test_result.configure(text="—", text_color=T.TEXT_SECONDARY)
            return
        if regex:
            try:
                re.compile(regex)
            except re.error as exc:
                self._sw_cmp_test_result.configure(
                    text=f"Regex error: {exc}", text_color=T.ACCENT_WARNING)
                return
        na = normalize_sw_for_comparison(a, regex)
        nb = normalize_sw_for_comparison(b, regex)
        if na == nb:
            self._sw_cmp_test_result.configure(
                text=f"✓ MATCH  ({na})", text_color=T.ACCENT_SUCCESS)
        else:
            self._sw_cmp_test_result.configure(
                text=f"✗ MISMATCH  ({na} ≠ {nb})", text_color=T.ACCENT_DANGER)

    def _sw_cmp_save_entry(self):
        regex = self._sw_cmp_regex_var.get().strip()
        if regex:
            try:
                re.compile(regex)
            except re.error as exc:
                messagebox.showerror("Invalid Regex",
                                     f"Comparison regex compile error:\n{exc}")
                return
        self._presets.setdefault("sw_comparison", {})["regex"] = regex
        messagebox.showinfo("Saved",
                            "SW comparison regex updated.\n"
                            'Click "Save All to File" to persist to presets.json.')

    # ══════════════════════════════════════════════════════════════
    # Card 2 – Result
    # ════════════════════════════════════════════════════════════
    def _build_result_card(self, parent):
        card = ctk.CTkFrame(
            parent, corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD, border_width=1, border_color=T.BORDER_COLOR,
        )
        card.pack(fill="x", padx=30, pady=(0, 15))

        # ── header row
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        _label(hdr, "Result Status Extraction", color=T.TEXT_BRIGHT, bold=True).pack(side="left")

        _divider(card)

        _label(
            card,
            "  Keywords searched in priority order (first match wins, case-insensitive):",
            color=T.TEXT_SECONDARY, small=True,
        ).pack(anchor="w", padx=20, pady=(8, 2))

        # keyword list frame
        self._res_list_frame = ctk.CTkFrame(
            card, fg_color=T.BG_SIDEBAR, corner_radius=T.BUTTON_CORNER
        )
        self._res_list_frame.pack(fill="x", padx=20, pady=(0, 6))
        self._res_sel: int | None = None
        self._res_rows: list = []
        self._res_populate_list()

        _divider(card)

        # ── edit form
        edit = ctk.CTkFrame(card, fg_color="transparent")
        edit.pack(fill="x", padx=20, pady=(10, 0))
        edit.columnconfigure(1, weight=1)

        _label(edit, "Keyword:", small=True, color=T.TEXT_SECONDARY).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=2)
        self._res_kw_entry = _entry(edit, placeholder="e.g. passed")
        self._res_kw_entry.grid(row=0, column=1, sticky="ew", pady=2)

        # ── action buttons
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(10, 16))

        RttButton(
            btns, text="New", height=34, width=90,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_SECONDARY,
            command=self._res_new,
        ).pack(side="left", padx=(0, 6))

        RttButton(
            btns, text="↑ Up", height=34, width=70,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_SECONDARY,
            command=self._res_move_up,
        ).pack(side="left", padx=(0, 4))

        RttButton(
            btns, text="↓ Down", height=34, width=80,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_SECONDARY,
            command=self._res_move_down,
        ).pack(side="left", padx=(0, 6))

        RttButton(
            btns, text="Delete Selected", height=34, width=130,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color="#c0392b",
            text_color=T.TEXT_SECONDARY,
            command=self._res_delete,
        ).pack(side="left")

        RttButton(
            btns, text="Save Entry", height=34, width=110,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color="#000000",
            command=self._res_save_entry,
        ).pack(side="right", padx=(6, 0))

        RttButton(
            btns, text="Save All to File", height=34, width=140,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS, hover_color="#00c853",
            text_color="#000000",
            command=self._save_all,
        ).pack(side="right")

    # ── Result keyword list helpers ─────────────────────────────────
    def _res_populate_list(self):
        for w in self._res_list_frame.winfo_children():
            w.destroy()
        self._res_rows.clear()
        kws = self._presets["result_extraction"].get("keywords", [])
        if not kws:
            _label(self._res_list_frame, "  No keywords defined.",
                   color=T.TEXT_SECONDARY, small=True).pack(
                anchor="w", padx=10, pady=6)
            return
        for idx, kw in enumerate(kws):
            selected = (idx == self._res_sel)
            bg = T.SIDEBAR_BTN_ACTIVE_BG if selected else "transparent"
            row = ctk.CTkFrame(
                self._res_list_frame, fg_color=bg, corner_radius=T.BUTTON_CORNER
            )
            row.pack(fill="x", padx=4, pady=2)

            def _select(i=idx):
                self._res_sel = i
                self._res_kw_entry.delete(0, "end")
                self._res_kw_entry.insert(0, self._presets["result_extraction"]["keywords"][i])
                self._res_populate_list()

            row.bind("<Button-1>", lambda _e, i=idx: _select(i))
            num = _label(row, f"{idx + 1}.", color=T.TEXT_SECONDARY, small=True)
            num.pack(side="left", padx=(8, 6), pady=4)
            num.bind("<Button-1>", lambda _e, i=idx: _select(i))
            kw_lbl = _label(row, kw, color=T.ACCENT_PRIMARY if selected else T.TEXT_BRIGHT)
            kw_lbl.pack(side="left", pady=4)
            kw_lbl.bind("<Button-1>", lambda _e, i=idx: _select(i))
            self._res_rows.append(row)

    def _res_new(self):
        self._res_sel = None
        self._res_kw_entry.delete(0, "end")
        self._res_populate_list()

    def _res_save_entry(self):
        kw = self._res_kw_entry.get().strip().lower()
        if not kw:
            messagebox.showwarning("Empty keyword", "Please enter a keyword.")
            return
        kws = self._presets["result_extraction"].setdefault("keywords", [])
        if self._res_sel is not None and self._res_sel < len(kws):
            kws[self._res_sel] = kw
        else:
            kws.append(kw)
            self._res_sel = len(kws) - 1
        self._res_populate_list()

    def _res_delete(self):
        if self._res_sel is None:
            messagebox.showinfo("Nothing selected", "Click a keyword row first.")
            return
        kws = self._presets["result_extraction"].get("keywords", [])
        if 0 <= self._res_sel < len(kws):
            kws.pop(self._res_sel)
        self._res_sel = None
        self._res_kw_entry.delete(0, "end")
        self._res_populate_list()

    def _res_move_up(self):
        if self._res_sel is None or self._res_sel == 0:
            return
        kws = self._presets["result_extraction"].get("keywords", [])
        i = self._res_sel
        kws[i - 1], kws[i] = kws[i], kws[i - 1]
        self._res_sel = i - 1
        self._res_populate_list()

    def _res_move_down(self):
        kws = self._presets["result_extraction"].get("keywords", [])
        if self._res_sel is None or self._res_sel >= len(kws) - 1:
            return
        i = self._res_sel
        kws[i], kws[i + 1] = kws[i + 1], kws[i]
        self._res_sel = i + 1
        self._res_populate_list()

    # ════════════════════════════════════════════════════════════
    # Card 3 – Variant Info
    # ════════════════════════════════════════════════════════════
    def _build_variant_card(self, parent):
        card = ctk.CTkFrame(
            parent, corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD, border_width=1, border_color=T.BORDER_COLOR,
        )
        card.pack(fill="x", padx=30, pady=(0, 20))

        # ── header row
        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        _label(hdr, "Variant ↔ SWFL Mapping", color=T.TEXT_BRIGHT, bold=True).pack(side="left")

        # Import button
        RttButton(
            hdr, text="Import from .txt file",
            height=30, width=160,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_SECONDARY,
            command=self._var_import_txt,
        ).pack(side="right", padx=(6, 0))

        _divider(card)

        # ── column headers
        col_hdr = ctk.CTkFrame(card, fg_color="transparent")
        col_hdr.pack(fill="x", padx=20, pady=(6, 0))
        col_hdr.columnconfigure(0, weight=1)
        col_hdr.columnconfigure(1, weight=3)
        _label(col_hdr, "Variant", color=T.TEXT_SECONDARY, small=True, bold=True).grid(
            row=0, column=0, sticky="w", padx=(8, 0))
        _label(col_hdr, "SWFL Code", color=T.TEXT_SECONDARY, small=True, bold=True).grid(
            row=0, column=1, sticky="w")

        # ── scrollable entry list
        self._var_list_scroll = ctk.CTkScrollableFrame(
            card, height=220,
            fg_color=T.BG_SIDEBAR, corner_radius=T.BUTTON_CORNER,
        )
        self._var_list_scroll.pack(fill="x", padx=20, pady=(4, 6))
        self._var_list_scroll.columnconfigure(0, weight=1)
        self._var_list_scroll.columnconfigure(1, weight=3)
        self._var_populate_list()

        _divider(card)

        # ── edit form
        edit = ctk.CTkFrame(card, fg_color="transparent")
        edit.pack(fill="x", padx=20, pady=(10, 0))
        edit.columnconfigure(1, weight=1)
        edit.columnconfigure(3, weight=1)

        _label(edit, "Variant:", small=True, color=T.TEXT_SECONDARY).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=2)
        self._var_v_entry = _entry(edit, placeholder="e.g. V35", width=100)
        self._var_v_entry.grid(row=0, column=1, sticky="w", pady=2)

        _label(edit, "SWFL Code:", small=True, color=T.TEXT_SECONDARY).grid(
            row=0, column=2, sticky="w", padx=(20, 8), pady=2)
        self._var_swfl_entry = _entry(edit, placeholder="e.g. SWFL-0000DE16")
        self._var_swfl_entry.grid(row=0, column=3, sticky="ew", pady=2)

        # ── action buttons
        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(10, 16))

        RttButton(
            btns, text="New", height=34, width=90,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_SECONDARY,
            command=self._var_new,
        ).pack(side="left", padx=(0, 6))

        RttButton(
            btns, text="Delete Selected", height=34, width=130,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color="#c0392b",
            text_color=T.TEXT_SECONDARY,
            command=self._var_delete,
        ).pack(side="left")

        RttButton(
            btns, text="Save Entry", height=34, width=110,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color="#000000",
            command=self._var_save_entry,
        ).pack(side="right", padx=(6, 0))

        RttButton(
            btns, text="Save All to File", height=34, width=140,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS, hover_color="#00c853",
            text_color="#000000",
            command=self._save_all,
        ).pack(side="right")

    # ── Variant list helpers ─────────────────────────────────────
    def _var_populate_list(self):
        for w in self._var_list_scroll.winfo_children():
            w.destroy()
        self._var_rows.clear()

        entries = self._presets["variant_extraction"].get("entries", [])
        if not entries:
            _label(self._var_list_scroll, "  No entries.  Import a .txt file or add manually.",
                   color=T.TEXT_SECONDARY, small=True).grid(
                row=0, column=0, columnspan=2, sticky="w", padx=10, pady=6)
            return

        for idx, ent in enumerate(entries):
            self._var_add_row(idx, ent)

    def _var_add_row(self, idx: int, ent: dict):
        selected = (idx == self._var_sel)
        bg = T.SIDEBAR_BTN_ACTIVE_BG if selected else "transparent"

        def _select(i=idx):
            self._var_sel = i
            e = self._presets["variant_extraction"]["entries"][i]
            self._var_v_entry.delete(0, "end")
            self._var_v_entry.insert(0, e.get("variant", ""))
            self._var_swfl_entry.delete(0, "end")
            self._var_swfl_entry.insert(0, e.get("swfl", ""))
            self._var_populate_list()

        # Variant column
        v_lbl = ctk.CTkLabel(
            self._var_list_scroll,
            text=ent.get("variant", ""),
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.ACCENT_PRIMARY if selected else T.TEXT_BRIGHT,
            fg_color=bg, corner_radius=4, anchor="w",
        )
        v_lbl.grid(row=idx, column=0, sticky="ew", padx=(4, 2), pady=1)
        v_lbl.bind("<Button-1>", lambda _e, i=idx: _select(i))

        # SWFL column
        s_lbl = ctk.CTkLabel(
            self._var_list_scroll,
            text=ent.get("swfl", ""),
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_SECONDARY if not selected else T.TEXT_BRIGHT,
            fg_color=bg, corner_radius=4, anchor="w",
        )
        s_lbl.grid(row=idx, column=1, sticky="ew", padx=(2, 4), pady=1)
        s_lbl.bind("<Button-1>", lambda _e, i=idx: _select(i))

        self._var_rows.append((v_lbl, s_lbl))

    def _var_new(self):
        self._var_sel = None
        self._var_v_entry.delete(0, "end")
        self._var_swfl_entry.delete(0, "end")
        self._var_populate_list()

    def _var_save_entry(self):
        variant = self._var_v_entry.get().strip().upper()
        swfl    = self._var_swfl_entry.get().strip().upper()
        if not variant or not swfl:
            messagebox.showwarning("Empty fields", "Both Variant and SWFL Code are required.")
            return

        entries = self._presets["variant_extraction"].setdefault("entries", [])
        entry   = {"variant": variant, "swfl": swfl}
        if self._var_sel is not None and self._var_sel < len(entries):
            entries[self._var_sel] = entry
        else:
            entries.append(entry)
            self._var_sel = len(entries) - 1

        self._var_populate_list()

    def _var_delete(self):
        if self._var_sel is None:
            messagebox.showinfo("Nothing selected", "Click an entry row first.")
            return
        entries = self._presets["variant_extraction"].get("entries", [])
        if 0 <= self._var_sel < len(entries):
            entries.pop(self._var_sel)
        self._var_sel = None
        self._var_v_entry.delete(0, "end")
        self._var_swfl_entry.delete(0, "end")
        self._var_populate_list()

    def _var_import_txt(self):
        path = filedialog.askopenfilename(
            title="Select Variant_Info .txt file",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        new_entries = import_variant_txt(path)
        if not new_entries:
            messagebox.showwarning("No entries found",
                                   "The file contained no parseable Variant - SWFL lines.")
            return
        if messagebox.askyesno(
            "Replace or Append?",
            f"Found {len(new_entries)} entries in the file.\n\n"
            "Click YES to replace the current list.\n"
            "Click NO to append to the current list.",
        ):
            self._presets["variant_extraction"]["entries"] = new_entries
        else:
            self._presets["variant_extraction"].setdefault("entries", []).extend(new_entries)
        self._var_sel = None
        self._var_populate_list()

    # ══════════════════════════════════════════════════════════════    # Save page-numbers only
    # ════════════════════════════════════════════════════════════
    # Card 5 – Library Extraction
    # ════════════════════════════════════════════════════════════
    def _build_library_card(self, parent):
        lib = self._presets.get("library_extraction", {})
        card = ctk.CTkFrame(
            parent, corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD, border_width=1, border_color=T.BORDER_COLOR,
        )
        card.pack(fill="x", padx=30, pady=(0, 15))

        hdr = ctk.CTkFrame(card, fg_color="transparent")
        hdr.pack(fill="x", padx=20, pady=(16, 0))
        _label(hdr, "Library Version Extraction", color=T.TEXT_BRIGHT, bold=True).pack(side="left")

        _divider(card)

        edit = ctk.CTkFrame(card, fg_color="transparent")
        edit.pack(fill="x", padx=20, pady=(12, 0))
        edit.columnconfigure(1, weight=1)

        _label(edit, "Anchor text:", small=True, color=T.TEXT_SECONDARY).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        self._lib_search_var = ctk.StringVar(
            value=lib.get("search_text", "Used version of custom library")
        )
        ctk.CTkEntry(
            edit, textvariable=self._lib_search_var, height=34,
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            fg_color=T.BG_SIDEBAR, text_color=T.TEXT_PRIMARY,
            border_color=T.BORDER_COLOR, corner_radius=T.BUTTON_CORNER,
            placeholder_text="e.g. Used version of custom library",
        ).grid(row=0, column=1, sticky="ew", pady=4)

        _label(edit, "Version regex:", small=True, color=T.TEXT_SECONDARY).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4)
        self._lib_pattern_var = ctk.StringVar(
            value=lib.get("version_pattern", r"[vV]\d+\.\d+")
        )
        ctk.CTkEntry(
            edit, textvariable=self._lib_pattern_var, height=34,
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            fg_color=T.BG_SIDEBAR, text_color=T.TEXT_PRIMARY,
            border_color=T.BORDER_COLOR, corner_radius=T.BUTTON_CORNER,
            placeholder_text=r"e.g. [vV]\d+\.\d+",
        ).grid(row=1, column=1, sticky="ew", pady=4)

        _label(edit, "Test text:", small=True, color=T.TEXT_SECONDARY).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=4)
        test_row = ctk.CTkFrame(edit, fg_color="transparent")
        test_row.grid(row=2, column=1, sticky="ew", pady=4)
        test_row.columnconfigure(0, weight=1)
        self._lib_test_entry = _entry(
            test_row, placeholder="Paste text from the library page to test...")
        self._lib_test_entry.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        RttButton(
            test_row, text="Test", width=60, height=30,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.BG_SIDEBAR, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.TEXT_PRIMARY,
            command=self._lib_test,
        ).grid(row=0, column=1)
        self._lib_test_result = _label(test_row, "", color=T.TEXT_SECONDARY, small=True)
        self._lib_test_result.grid(row=0, column=2, padx=(8, 0))

        btns = ctk.CTkFrame(card, fg_color="transparent")
        btns.pack(fill="x", padx=20, pady=(10, 16))
        RttButton(
            btns, text="Save Entry", height=34, width=110,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY, hover_color=T.SIDEBAR_BTN_HOVER,
            text_color="#000000",
            command=self._lib_save_entry,
        ).pack(side="right", padx=(6, 0))
        RttButton(
            btns, text="Save All to File", height=34, width=140,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS, hover_color="#00c853",
            text_color="#000000",
            command=self._save_all,
        ).pack(side="right")

    def _lib_test(self):
        from src.core.systemtestliste.utils import extract_library_version
        text    = self._lib_test_entry.get().strip()
        anchor  = self._lib_search_var.get().strip()
        pattern = self._lib_pattern_var.get().strip()
        if not text:
            self._lib_test_result.configure(text="—", text_color=T.TEXT_SECONDARY)
            return
        try:
            result = extract_library_version(text, anchor, pattern)
            if result:
                self._lib_test_result.configure(
                    text=f"✓  {result}", text_color=T.ACCENT_SUCCESS)
            else:
                self._lib_test_result.configure(
                    text="✗  No match", text_color=T.ACCENT_DANGER)
        except re.error as exc:
            self._lib_test_result.configure(
                text=f"Regex error: {exc}", text_color=T.ACCENT_WARNING)

    def _lib_save_entry(self):
        search_text     = self._lib_search_var.get().strip()
        version_pattern = self._lib_pattern_var.get().strip()
        if not search_text:
            messagebox.showwarning("Empty", "Anchor text cannot be empty.")
            return
        if version_pattern:
            try:
                re.compile(version_pattern)
            except re.error as exc:
                messagebox.showerror("Invalid Regex",
                                     f"Version pattern compile error:\n{exc}")
                return
        self._presets.setdefault("library_extraction", {}).update({
            "search_text":     search_text,
            "version_pattern": version_pattern or r"[vV]\d+\.\d+",
        })
        messagebox.showinfo("Saved",
                            "Library extraction settings updated.\n"
                            "Click \"Save All to File\" to persist to presets.json.")

    # ════════════════════════════════════════════════════════════
    def _save_page_numbers(self):
        """Persist only the three page numbers immediately."""
        try:
            self._presets["result_extraction"]["page"] = int(self._result_page_var.get())
        except ValueError:
            pass
        try:
            self._presets["sw_extraction"]["page"] = int(self._sw_page_var.get())
        except ValueError:
            pass
        try:
            self._presets["variant_extraction"]["page"] = int(self._var_page_var.get())
        except ValueError:
            pass
        try:
            self._presets.setdefault("library_extraction", {})["page"] = int(self._lib_page_var.get())
        except ValueError:
            pass
        save_presets(self._presets)
        messagebox.showinfo("Saved", "Page numbers saved to config/presets.json")

    # ════════════════════════════════════════════════════════════
    # Persist everything
    # ══════════════════════════════════════════════════════════════
    def _save_all(self):
        """Persist page numbers + all entries/patterns to presets.json."""
        try:
            self._presets["sw_extraction"]["page"] = int(self._sw_page_var.get())
        except ValueError:
            pass
        try:
            self._presets["result_extraction"]["page"] = int(self._result_page_var.get())
        except ValueError:
            pass
        try:
            self._presets["variant_extraction"]["page"] = int(self._var_page_var.get())
        except ValueError:
            pass
        try:
            self._presets.setdefault("library_extraction", {})["page"] = int(self._lib_page_var.get())
        except ValueError:
            pass
        # persist library search_text and version_pattern from the card entries
        if hasattr(self, "_lib_search_var"):
            self._presets.setdefault("library_extraction", {})["search_text"] = self._lib_search_var.get().strip()
        if hasattr(self, "_lib_pattern_var"):
            self._presets.setdefault("library_extraction", {})["version_pattern"] = self._lib_pattern_var.get().strip()
        # SW comparison regex
        if hasattr(self, "_sw_cmp_regex_var"):
            self._presets.setdefault("sw_comparison", {})["regex"] = self._sw_cmp_regex_var.get().strip()

        save_presets(self._presets)

        # Reload from disk so the UI always reflects the persisted state
        self._presets = load_presets()
        self._sw_page_var.set(str(self._presets["sw_extraction"].get("page", 3)))
        self._result_page_var.set(str(self._presets["result_extraction"].get("page", 3)))
        self._var_page_var.set(str(self._presets["variant_extraction"].get("page", 3)))
        self._lib_page_var.set(str(self._presets.get("library_extraction", {}).get("page", 3)))
        if hasattr(self, "_lib_search_var"):
            self._lib_search_var.set(self._presets.get("library_extraction", {}).get("search_text", ""))
        if hasattr(self, "_lib_pattern_var"):
            self._lib_pattern_var.set(self._presets.get("library_extraction", {}).get("version_pattern", ""))
        if hasattr(self, "_sw_cmp_regex_var"):
            self._sw_cmp_regex_var.set(self._presets.get("sw_comparison", {}).get("regex", ""))
        self._sw_sel = None
        self._var_sel = None
        self._sw_populate_list()
        self._var_populate_list()
        if hasattr(self, "_res_list_frame"):
            self._res_sel = None
            self._res_populate_list()

        messagebox.showinfo("Saved", "Presets saved to config/presets.json")
