"""
Canonical Names Editor dialog.

Performance design
------------------
* Each row is a lightweight ``CTkLabel`` — no per-row CTkEntry widgets.
* Clicking a label swaps it for a single ``CTkEntry`` (edit mode).
  At most ONE row is in edit mode at a time; the previous edit is
  committed automatically before a new one opens.
* Add / Delete are incremental — they only touch the affected row,
  never rebuilding the whole list.
* ``self._entries`` is the single source of truth; widgets reflect it.
"""
from __future__ import annotations

import os
from tkinter import filedialog, messagebox

import customtkinter as ctk

from src.gui.styles.theme import AppTheme as T


class CanonicalNamesDialog(ctk.CTkToplevel):
    """Modal-style dialog for managing the canonical names list."""

    def __init__(self, master, config_path: str, **kwargs):
        super().__init__(master, **kwargs)
        self._config_path = config_path
        self._entries: list[str] = []
        self._row_widgets: list[dict] = []   # [{"frame", "label", "del_btn", "name"}]
        self._editing_row: dict | None = None
        self._empty_label: ctk.CTkLabel | None = None

        self.title("Canonical Names Editor")
        self.geometry("680x560")
        self.resizable(True, True)
        self.configure(fg_color=T.BG_DARK)

        # Keep on top of parent
        self.transient(master)
        self.grab_set()

        self._load_from_file()
        self._build()

    # ── File I/O ────────────────────────────────────────────────
    def _load_from_file(self):
        """Read canonical_names.txt into self._entries."""
        self._entries = []
        if not os.path.isfile(self._config_path):
            return
        with open(self._config_path, encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    self._entries.append(stripped)

    def _save_to_file(self):
        """Write current in-memory entries back to canonical_names.txt."""
        header = (
            "# Canonical test names – one per line.\n"
            "# The test ID (e.g. DPSDC-FC-HILTS-1669) is extracted automatically.\n"
            "# During 'Ignore Duplicates' mode the best-result file is renamed\n"
            "# to <canonical_name>.pdf.\n"
            "#\n"
        )
        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as fh:
            fh.write(header)
            for entry in self._entries:
                fh.write(entry + "\n")

    # ── Build UI ────────────────────────────────────────────────
    def _build(self):
        # ── Title bar ───────────────────────────────────────────
        title_frame = ctk.CTkFrame(self, fg_color=T.BG_HEADER, corner_radius=0)
        title_frame.pack(fill="x")

        ctk.CTkLabel(
            title_frame,
            text="Canonical Names Editor",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkLabel(
            title_frame,
            text=f"  {self._config_path}",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="left", padx=(0, 10), pady=12)

        # ── Scrollable list ──────────────────────────────────────
        list_label = ctk.CTkLabel(
            self,
            text="Current entries  (click a name to edit inline)",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        )
        list_label.pack(anchor="w", padx=20, pady=(14, 4))

        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color=T.BG_SIDEBAR,
            corner_radius=T.CARD_CORNER,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))
        self._scroll_frame = scroll_frame

        self._render_rows()

        # ── Add-new row ──────────────────────────────────────────
        add_frame = ctk.CTkFrame(
            self,
            fg_color=T.BG_CARD,
            corner_radius=T.CARD_CORNER,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        add_frame.pack(fill="x", padx=20, pady=(0, 6))

        self._new_entry_var = ctk.StringVar()
        self._new_entry = ctk.CTkEntry(
            add_frame,
            placeholder_text="e.g. DPSDC-FC-HILTS-1669_CloudDataCollector_TBT_ErrorCounter",
            textvariable=self._new_entry_var,
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            fg_color=T.BG_SIDEBAR,
            text_color=T.TEXT_PRIMARY,
            border_color=T.BORDER_COLOR,
            corner_radius=T.BUTTON_CORNER,
            height=34,
        )
        self._new_entry.pack(side="left", fill="x", expand=True, padx=(12, 8), pady=10)
        self._new_entry.bind("<Return>", lambda _e: self._add_entry())

        ctk.CTkButton(
            add_frame,
            text="Add",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            height=34,
            width=90,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS,
            hover_color="#00c853",
            text_color=T.BG_DARK,
            command=self._add_entry,
        ).pack(side="right", padx=(0, 12), pady=10)

        # ── Bottom action bar ────────────────────────────────────
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_bar,
            text="Import from .txt",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            height=36,
            width=170,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SECONDARY,
            hover_color="#5a1fc0",
            text_color=T.TEXT_BRIGHT,
            command=self._import_from_file,
        ).pack(side="left")

        ctk.CTkButton(
            btn_bar,
            text="Cancel",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            height=36,
            width=110,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_DANGER,
            hover_color="#d50000",
            text_color=T.TEXT_BRIGHT,
            command=self.destroy,
        ).pack(side="right")

        ctk.CTkButton(
            btn_bar,
            text="Save & Close",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            height=36,
            width=140,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.BG_DARK,
            command=self._save_and_close,
        ).pack(side="right", padx=(0, 10))

    # ── Full render (initial load + after import) ────────────────────────────
    def _render_rows(self):
        """Rebuild all row widgets from self._entries (used on open + import)."""
        if self._editing_row:
            self._commit_edit(self._editing_row)
        for widget in self._scroll_frame.winfo_children():
            widget.destroy()
        self._row_widgets.clear()
        self._empty_label = None

        if not self._entries:
            self._show_empty_label()
            return
        for name in self._entries:
            self._append_row_widget(name)

    # ── Incremental row operations ───────────────────────────────────────
    def _append_row_widget(self, name: str) -> dict:
        """Create ONE label row and append it — no full re-render."""
        row_dict: dict = {}

        frame = ctk.CTkFrame(self._scroll_frame, fg_color="transparent")
        frame.pack(fill="x", pady=2)

        lbl = ctk.CTkLabel(
            frame,
            text=name,
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
            anchor="w",
            cursor="hand2",
        )
        lbl.pack(side="left", fill="x", expand=True, padx=(4, 6))
        lbl.bind("<Button-1>", lambda _e, d=row_dict: self._start_edit(d))

        del_btn = ctk.CTkButton(
            frame,
            text="Del",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            width=36,
            height=32,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_DANGER,
            hover_color="#d50000",
            text_color=T.TEXT_BRIGHT,
            command=lambda d=row_dict: self._delete_row(d),
        )
        del_btn.pack(side="right", padx=(0, 4))

        row_dict.update({"frame": frame, "label": lbl, "del_btn": del_btn, "name": name})
        self._row_widgets.append(row_dict)
        return row_dict

    def _show_empty_label(self):
        if self._empty_label is None:
            self._empty_label = ctk.CTkLabel(
                self._scroll_frame,
                text="No entries yet. Use 'Add' or 'Import' below.",
                font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
                text_color=T.TEXT_SECONDARY,
            )
            self._empty_label.pack(pady=20)

    def _hide_empty_label(self):
        if self._empty_label is not None:
            self._empty_label.destroy()
            self._empty_label = None

    # ── Inline edit (one row at a time) ─────────────────────────────────
    def _start_edit(self, row_dict: dict):
        """Swap the clicked label for a CTkEntry (edit mode)."""
        if self._editing_row is row_dict:
            return
        if self._editing_row is not None:
            self._commit_edit(self._editing_row)

        self._editing_row = row_dict
        row_dict["label"].pack_forget()

        var = ctk.StringVar(value=row_dict["name"])
        entry = ctk.CTkEntry(
            row_dict["frame"],
            textvariable=var,
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            fg_color=T.BG_CARD,
            text_color=T.TEXT_PRIMARY,
            border_color=T.ACCENT_PRIMARY,
            corner_radius=T.BUTTON_CORNER,
            height=32,
        )
        # del_btn is already packed side="right"; entry fills remaining left space
        entry.pack(side="left", fill="x", expand=True, padx=(4, 6))
        entry.focus_set()
        entry.select_range(0, "end")

        row_dict["edit_var"]   = var
        row_dict["edit_entry"] = entry

        entry.bind("<Return>",   lambda _e, d=row_dict: self._commit_edit(d))
        entry.bind("<Escape>",   lambda _e, d=row_dict: self._cancel_edit(d))
        entry.bind("<FocusOut>", lambda _e, d=row_dict: self._commit_edit(d))

    def _commit_edit(self, row_dict: dict):
        """Save the edited value and restore the label."""
        if "edit_entry" not in row_dict:
            return
        new_val = row_dict["edit_var"].get().strip()
        if new_val:
            row_dict["name"] = new_val
            idx = self._row_widgets.index(row_dict)
            if idx < len(self._entries):
                self._entries[idx] = new_val

        entry = row_dict.pop("edit_entry")
        row_dict.pop("edit_var")
        entry.destroy()

        row_dict["label"].configure(text=row_dict["name"])
        row_dict["label"].pack(side="left", fill="x", expand=True, padx=(4, 6))
        if self._editing_row is row_dict:
            self._editing_row = None

    def _cancel_edit(self, row_dict: dict):
        """Discard edit and restore the label unchanged."""
        if "edit_entry" not in row_dict:
            return
        entry = row_dict.pop("edit_entry")
        row_dict.pop("edit_var")
        entry.destroy()
        row_dict["label"].pack(side="left", fill="x", expand=True, padx=(4, 6))
        if self._editing_row is row_dict:
            self._editing_row = None

    def _delete_row(self, row_dict: dict):
        """Remove a single row widget — no full re-render."""
        if self._editing_row is row_dict:
            self._cancel_edit(row_dict)
        idx = self._row_widgets.index(row_dict)
        self._entries.pop(idx)
        self._row_widgets.remove(row_dict)
        row_dict["frame"].destroy()
        if not self._entries:
            self._show_empty_label()

    # ── Add ────────────────────────────────────────────────────────────
    def _add_entry(self):
        new_name = self._new_entry_var.get().strip()
        if not new_name or new_name in self._entries:
            self._new_entry_var.set("")
            return
        self._hide_empty_label()
        self._entries.append(new_name)
        self._append_row_widget(new_name)
        self._new_entry_var.set("")

    # ── Import ──────────────────────────────────────────────────────────
    def _import_from_file(self):
        path = filedialog.askopenfilename(
            title="Import canonical names from .txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not path:
            return
        if self._editing_row:
            self._commit_edit(self._editing_row)
        imported = 0
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped and not stripped.startswith("#") and stripped not in self._entries:
                    self._entries.append(stripped)
                    imported += 1
        self._render_rows()
        messagebox.showinfo("Import complete", f"Imported {imported} new entry/entries.", parent=self)

    # ── Save & Close ───────────────────────────────────────────────────
    def _save_and_close(self):
        if self._editing_row:
            self._commit_edit(self._editing_row)
        try:
            self._save_to_file()
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc), parent=self)
            return
        self.destroy()
