"""
Canonical Names Editor dialog.

Behaviour
---------
* Entries are loaded from canonical_names.json (or auto-migrated from .txt).
* Each row is a read-only ``CTkLabel``.  Click to edit inline.
* Use "Import .txt / .json" to load entries from an external file.
* "Save & Close" persists changes back to canonical_names.json.
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
        self._row_widgets: list[dict] = []   # [{"frame", "label", "name"}]
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
        """Read canonical_names.json (or legacy .txt) into self._entries."""
        self._entries = []

        # ── JSON (preferred) ─────────────────────────────────────
        if self._config_path.endswith(".json") and os.path.isfile(self._config_path):
            try:
                import json
                with open(self._config_path, encoding="utf-8") as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    self._entries = list(data.values())
                    return
            except Exception:
                pass  # fall through to .txt

        # ── Legacy .txt fallback ──────────────────────────────────
        txt_path = (
            os.path.splitext(self._config_path)[0] + ".txt"
            if self._config_path.endswith(".json")
            else self._config_path
        )
        if not os.path.isfile(txt_path):
            return
        with open(txt_path, encoding="utf-8") as fh:
            for line in fh:
                stripped = line.strip()
                if stripped and not stripped.startswith("#"):
                    self._entries.append(stripped)

    def _save_to_file(self):
        """Write current in-memory entries to canonical_names.json."""
        import json, re

        # Rebuild {test_id: full_name} dict preserving order
        def _extract_id(name: str) -> str:
            """Extract leading TEST-ID token (e.g. AEC-FC-HILTS-1004)."""
            first = name.split("_")[0]
            parts = first.split("-")
            if len(parts) >= 2 and parts[-1].isdigit():
                return first
            # fallback: use the whole name as key
            return re.sub(r"[^\w\-]", "_", name)

        data: dict[str, str] = {}
        for entry in self._entries:
            key = _extract_id(entry)
            # avoid silent key collisions – append suffix when duplicate
            if key in data:
                key = f"{key}_{sum(1 for k in data if k.startswith(key))}"
            data[key] = entry

        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
        with open(self._config_path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=4, ensure_ascii=False)

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

        # ── Bottom action bar ────────────────────────────────────
        btn_bar = ctk.CTkFrame(self, fg_color="transparent")
        btn_bar.pack(fill="x", padx=20, pady=(0, 16))

        ctk.CTkButton(
            btn_bar,
            text="Import .txt / .json",
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
        lbl.pack(fill="x", expand=True, padx=(4, 6))
        lbl.bind("<Button-1>", lambda _e, d=row_dict: self._start_edit(d))

        row_dict.update({"frame": frame, "label": lbl, "name": name})
        self._row_widgets.append(row_dict)
        return row_dict

    def _show_empty_label(self):
        if self._empty_label is None:
            self._empty_label = ctk.CTkLabel(
                self._scroll_frame,
                text="No entries yet. Use 'Import' below to load a file.",
                font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
                text_color=T.TEXT_SECONDARY,
            )
            self._empty_label.pack(pady=20)

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
        entry.pack(fill="x", expand=True, padx=(4, 6))
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
        row_dict["label"].pack(fill="x", expand=True, padx=(4, 6))
        if self._editing_row is row_dict:
            self._editing_row = None

    def _cancel_edit(self, row_dict: dict):
        """Discard edit and restore the label unchanged."""
        if "edit_entry" not in row_dict:
            return
        entry = row_dict.pop("edit_entry")
        row_dict.pop("edit_var")
        entry.destroy()
        row_dict["label"].pack(fill="x", expand=True, padx=(4, 6))
        if self._editing_row is row_dict:
            self._editing_row = None

    # ── Import ──────────────────────────────────────────────────────────
    def _import_from_file(self):
        import json
        path = filedialog.askopenfilename(
            title="Import canonical names",
            filetypes=[
                ("JSON files", "*.json"),
                ("Text files", "*.txt"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        if self._editing_row:
            self._commit_edit(self._editing_row)
        imported = 0

        if path.endswith(".json"):
            # ── JSON input: merge values into current list ───────
            try:
                with open(path, encoding="utf-8") as fh:
                    data = json.load(fh)
                for v in (data.values() if isinstance(data, dict) else data):
                    v = str(v).strip()
                    if v and v not in self._entries:
                        self._entries.append(v)
                        imported += 1
            except Exception as exc:
                messagebox.showerror("Import failed", str(exc), parent=self)
                return
            self._render_rows()
            messagebox.showinfo(
                "Import complete",
                f"Imported {imported} new entry/entries from JSON.",
                parent=self,
            )

        else:
            # ── .txt input: read, merge, then immediately convert ─
            # and save as canonical_names.json so everything from
            # this point forward runs purely on JSON.
            before = len(self._entries)
            with open(path, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    stripped = line.strip()
                    if stripped and not stripped.startswith("#") and stripped not in self._entries:
                        self._entries.append(stripped)
                        imported += 1

            self._render_rows()

            # Immediately write JSON – .txt is now fully converted
            json_saved = False
            try:
                self._save_to_file()
                json_saved = True
            except Exception as exc:
                messagebox.showwarning(
                    "JSON save failed",
                    f"Entries loaded into memory but could not write JSON:\n{exc}",
                    parent=self,
                )

            msg = (
                f"Imported {imported} new entry/entries from .txt file.\n\n"
                + (
                    f"Converted and saved as:\n{self._config_path}"
                    if json_saved
                    else "Could not save JSON — entries are in memory only."
                )
            )
            messagebox.showinfo("Import & Convert complete", msg, parent=self)

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
