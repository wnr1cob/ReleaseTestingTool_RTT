"""
PDF Analyzer page – browse a directory and analyze PDF files.
"""
import os
import subprocess
import threading
from tkinter import filedialog
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T
from src.gui.widgets.segmented_progress import SegmentedProgressBar
from src.core.pdf_analyzer.file_copier import copy_pdfs, load_canonical_map, smart_deduplicate
from src.gui.dialogs.canonical_names_dialog import CanonicalNamesDialog

# Resolve config path so it works both in dev and when packaged as a .exe.
# When frozen by PyInstaller, write next to the .exe (sys.executable).
# In dev, fall back to the project-root config/ folder.
import sys as _sys
if getattr(_sys, "frozen", False):
    # Running as a PyInstaller bundle – place config next to the .exe
    _BASE_DIR = os.path.dirname(_sys.executable)
else:
    # Running from source
    _BASE_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_CANONICAL_NAMES_PATH = os.path.join(_BASE_DIR, "config", "canonical_names.txt")
from src.core.pdf_analyzer.module_separator import separate_by_module
from src.core.pdf_analyzer.result_separator import separate_by_result
from src.core.pdf_analyzer.report_generator import generate_report


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
            text="Select Directory",
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
            text="Browse",
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
            text="Copy Options",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(anchor="w", padx=20, pady=(18, 12))

        # Duplicate handling radio buttons
        self._dup_mode = ctk.StringVar(value="ignore_duplicates")

        self._radio_copy_dup = ctk.CTkRadioButton(
            self._copy_card,
            text="Copy Duplicates (rename with _Dup suffix)",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            variable=self._dup_mode,
            value="copy_duplicates",
            command=self._toggle_canonical_row,
        )
        self._radio_copy_dup.pack(anchor="w", padx=20, pady=(0, 6))

        self._radio_ignore_dup = ctk.CTkRadioButton(
            self._copy_card,
            text="Consolidate Duplicates (compares and keeps best result)",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_PRIMARY,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            variable=self._dup_mode,
            value="ignore_duplicates",
            command=self._toggle_canonical_row,
        )
        self._radio_ignore_dup.pack(anchor="w", padx=20, pady=(0, 10))

        # Edit canonical names row (shown only when Ignore Duplicates is selected)
        self._edit_names_row = ctk.CTkFrame(self._copy_card, fg_color="transparent")
        # Packed/hidden dynamically via _toggle_canonical_row
        self._edit_names_row.pack(fill="x", padx=20, pady=(0, 18))

        ctk.CTkLabel(
            self._edit_names_row,
            text="Canonical names are used to rename the best result file uniformly.",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL),
            text_color=T.TEXT_SECONDARY,
        ).pack(side="left")

        ctk.CTkButton(
            self._edit_names_row,
            text="Edit Canonical Names",
            font=(T.FONT_FAMILY, T.FONT_SIZE_SMALL, "bold"),
            height=28,
            width=180,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SECONDARY,
            hover_color="#5a1fc0",
            text_color=T.TEXT_BRIGHT,
            command=self._open_canonical_names_editor,
        ).pack(side="right")

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
            text="Separator Selection",
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
        if (0): # Use SystemTestListe Switch (hidden for now, can be enabled when STL integration is ready)
            # ── SystemTestListe option card ────────────────────────
            self._stl_card = ctk.CTkFrame(
                self,
                corner_radius=T.CARD_CORNER,
                fg_color=T.BG_CARD,
                border_width=1,
                border_color=T.BORDER_COLOR,
            )
            self._stl_card.pack(fill="x", padx=30, pady=(0, 15))

            self._use_stl_var = ctk.BooleanVar(value=False)

            self._chk_use_stl = ctk.CTkCheckBox(
                self._stl_card,
                text="Use SystemTestListe",
                font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
                text_color=T.TEXT_PRIMARY,
                fg_color=T.ACCENT_PRIMARY,
                hover_color=T.SIDEBAR_BTN_HOVER,
                variable=self._use_stl_var,
                onvalue=True,
                offvalue=False,
            )
            self._chk_use_stl.pack(anchor="w", padx=20, pady=(18, 18))

        # ── Bottom bar: progress + status + Start button ──────────
        self._bottom_card = ctk.CTkFrame(
            self,
            corner_radius=T.CARD_CORNER,
            fg_color=T.BG_CARD,
            border_width=1,
            border_color=T.BORDER_COLOR,
        )
        self._bottom_card.pack(fill="x", side="bottom", padx=30, pady=(0, 20))

        # Status label
        self._status_label = ctk.CTkLabel(
            self._bottom_card,
            text="  No directory selected. Click 'Browse' to choose a folder.",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY),
            text_color=T.TEXT_SECONDARY,
            anchor="w",
        )
        self._status_label.pack(anchor="w", padx=20, pady=(14, 6))

        # Segmented progress bar
        self._progress = SegmentedProgressBar(
            self._bottom_card,
            segments=[
                {"label": "Copying",     "color": T.ACCENT_PRIMARY},
                {"label": "Separating",  "color": T.ACCENT_WARNING},
            ],
        )
        self._progress.pack(fill="x", padx=20, pady=(0, 10))

        # Start button row (right-aligned)
        btn_row = ctk.CTkFrame(self._bottom_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 14))

        self._start_btn = ctk.CTkButton(
            btn_row,
            text="Start",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            height=40,
            width=140,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS,
            hover_color="#00c853",
            text_color=T.BG_DARK,
            command=self._start_process,
        )
        self._start_btn.pack(side="right")

        self._close_btn = ctk.CTkButton(
            btn_row,
            text="Close",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            height=40,
            width=140,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_DANGER,
            hover_color="#d50000",
            text_color=T.TEXT_BRIGHT,
            command=self._close_app,
        )
        # Hidden initially – shown after process completes

        self._open_btn = ctk.CTkButton(
            btn_row,
            text="Open Folder",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            height=40,
            width=150,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_PRIMARY,
            hover_color=T.SIDEBAR_BTN_HOVER,
            text_color=T.BG_DARK,
            command=self._open_result_folder,
        )
        # Hidden initially – shown after process completes
        self._result_folder: str = ""

        self._open_excel_btn = ctk.CTkButton(
            btn_row,
            text="Open Excel",
            font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
            height=40,
            width=150,
            corner_radius=T.BUTTON_CORNER,
            fg_color=T.ACCENT_SUCCESS,
            hover_color="#00c853",
            text_color=T.BG_DARK,
            command=self._open_excel_report,
        )
        # Hidden initially – shown after process completes
        self._report_path: str = ""

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
        else:
            self._status_label.configure(
                text=f"  No PDF files found in: {directory}",
                text_color=T.ACCENT_WARNING,
            )

    # ── unified start process ───────────────────────────────────
    def _start_process(self):
        """Copy PDFs then run the selected separator in sequence (threaded)."""
        if not self._selected_dir:
            self._status_label.configure(
                text="  Please select a directory first.",
                text_color=T.ACCENT_WARNING,
            )
            return
        if not self._pdf_files:
            self._status_label.configure(
                text="  No PDF files found. Browse a folder with PDFs.",
                text_color=T.ACCENT_WARNING,
            )
            return

        # Disable button to prevent double-clicks
        self._start_btn.configure(state="disabled", text="Processing...")
        self._progress.reset()

        # Launch work on a background thread
        thread = threading.Thread(target=self._run_worker, daemon=True)
        thread.start()

    # ── thread-safe GUI helpers ─────────────────────────────────
    def _ui(self, fn):
        """Schedule *fn* on the main thread."""
        self.after(0, fn)

    def _set_status(self, text: str, color: str = T.TEXT_PRIMARY):
        self._ui(lambda: self._status_label.configure(text=text, text_color=color))

    def _set_seg(self, idx: int, value: float):
        self._ui(lambda: self._progress.set_segment(idx, value))

    # ── background worker ───────────────────────────────────────
    def _run_worker(self):
        """Heavy I/O work – runs on a daemon thread."""
        total_files = len(self._pdf_files)

        # ── Step 1: Copy PDFs to All_Available_Reports ──────────
        parent_dir = os.path.dirname(self._selected_dir)
        dest_dir = os.path.join(parent_dir, "All_Available_Reports")

        mode = self._dup_mode.get()
        # For ignore_duplicates, copy ALL files first (with _Dup suffix for
        # same-name conflicts) so every variant lands in dest_dir for comparison.
        copy_mode = "copy_duplicates" if mode == "ignore_duplicates" else mode

        def _copy_progress(processed: int, total: int) -> None:
            self._set_seg(0, processed / total)
            self._set_status(f"  Copying... {processed}/{total} files")

        # Load canonical map early so copy_pdfs can use it for dest filename
        canonical_map = load_canonical_map(_CANONICAL_NAMES_PATH)

        copy_result = copy_pdfs(
            self._pdf_files, dest_dir, mode=copy_mode,
            on_progress=_copy_progress, canonical_map=canonical_map
        )
        copied = copy_result["copied"]
        skipped = copy_result["skipped"]

        # ── Step 1b: Smart deduplication (ignore_duplicates mode) ──────────
        dedup_summary = ""
        if mode == "ignore_duplicates":
            self._set_status("  Deduplicating by test ID (keeping best result)...")
            # canonical_map already loaded above

            def _dedup_progress(cur: int, tot: int, test_id: str) -> None:
                self._set_seg(0, cur / tot)
                self._set_status(f"  Deduplicating... {cur}/{tot} — {test_id}")

            dedup_result = smart_deduplicate(
                dest_dir, canonical_map, on_progress=_dedup_progress
            )
            parts = []
            if dedup_result["removed"]:
                parts.append(f"removed {dedup_result['removed']} duplicate(s)")
            if dedup_result["renamed"]:
                parts.append(f"renamed {dedup_result['renamed']} to canonical")
            if dedup_result["unmatched"]:
                parts.append(f"{dedup_result['unmatched']} unmatched")
            dedup_summary = " | ".join(parts) if parts else "no duplicates found"
        else:
            pass  # canonical_map already loaded above (before copy step)

        # ── Step 2: Run selected separator ──────────────────────
        self._set_status("  Running separator...")
        self._set_seg(1, 0.05)

        sep_mode = self._sep_mode.get()
        sep_msg = ""
        file_results: list[dict[str, str]] = []
        results_count: dict[str, int] = {}

        if sep_mode == "module_separator":
            try:
                # Detect results for the Excel report (per-file progress)
                from src.core.pdf_analyzer.result_separator import _detect_result

                for i, pdf_path in enumerate(self._pdf_files):
                    fname = os.path.basename(pdf_path)
                    target = os.path.join(dest_dir, fname)
                    path_to_read = target if os.path.exists(target) else pdf_path
                    detected = _detect_result(path_to_read)
                    status = detected or "Unknown"
                    file_results.append({"name": fname, "result": status})
                    results_count[status] = results_count.get(status, 0) + 1
                    pct = (i + 1) / total_files * 0.7
                    self._set_seg(1, pct)
                    self._set_status(f"  Detecting results... {i + 1}/{total_files} — {fname}")

                # Module separation with per-file progress
                def _mod_progress(cur, tot, name):
                    self._set_seg(1, 0.7 + 0.3 * cur / tot)
                    self._set_status(f"  Module separator... {cur}/{tot} — {name}")

                result = separate_by_module(dest_dir, on_progress=_mod_progress)
                parts = [f"Moved {result['moved']} PDF(s) into {len(result['modules'])} module folder(s)"]
                if result["skipped"]:
                    parts.append(f"({result['skipped']} skipped – no '-' in name)")
                sep_msg = " | ".join(parts)
                self._set_seg(1, 1.0)
            except Exception as e:
                self._set_status(f"  Separator error: {e}", T.ACCENT_DANGER)
                self._ui(lambda: self._start_btn.configure(state="normal", text="▶  Start"))
                return
        else:
            try:
                # Result separation with per-file progress
                def _res_progress(cur, tot, name):
                    pct = cur / tot * 0.5
                    self._set_seg(1, pct)
                    self._set_status(f"  Result separator... {cur}/{tot} — {name}")

                result = separate_by_result(dest_dir, on_progress=_res_progress)
                self._set_seg(1, 0.5)

                breakdown = ", ".join(
                    f"{k}: {v}" for k, v in sorted(result["results"].items())
                )
                parts = [f"Moved {result['moved']} PDF(s) → {breakdown or 'none'}"]
                if result["skipped"]:
                    parts.append(f"({result['skipped']} skipped – no result on page 2)")
                sep_msg = " | ".join(parts)
                file_results = result.get("file_results", [])
                results_count = result.get("results", {})

                # Module separation inside each result folder
                folders_todo = ["Passed", "Failed", "Error", "Undefined"]
                for fi, folder_name in enumerate(folders_todo):
                    sub_dir = os.path.join(result["dest_root"], folder_name)
                    if os.path.isdir(sub_dir):
                        base_pct = 0.5 + 0.5 * fi / len(folders_todo)
                        chunk = 0.5 / len(folders_todo)

                        def _sub_mod_progress(cur, tot, name, _base=base_pct, _chunk=chunk):
                            self._set_seg(1, _base + _chunk * cur / tot)
                            self._set_status(
                                f"  Module separator ({folder_name})... {cur}/{tot} — {name}"
                            )

                        mod_result = separate_by_module(sub_dir, on_progress=_sub_mod_progress)
                        if mod_result["moved"]:
                            sep_msg += (
                                f" | {folder_name} → {mod_result['moved']} PDF(s) into "
                                f"{len(mod_result['modules'])} module folder(s)"
                            )
                    self._set_seg(1, 0.5 + 0.5 * (fi + 1) / len(folders_todo))
            except Exception as e:
                self._set_status(f"  Separator error: {e}", T.ACCENT_DANGER)
                self._ui(lambda: self._start_btn.configure(state="normal", text="▶  Start"))
                return

        # ── Step 3: Generate Excel report ──────────────────────
        self._set_status("  Generating Excel report...")

        # Apply canonical names to file_results so the Excel shows uniform names
        from src.core.pdf_analyzer.file_copier import _extract_test_id
        file_summaries: list[dict[str, str]] = []
        def _apply_canonical(results: list[dict[str, str]]) -> list[dict[str, str]]:
            mapped = []
            for entry in results:
                name = entry["name"]
                stem = os.path.splitext(name)[0]
                tid = _extract_test_id(stem)
                canonical = canonical_map.get(tid) if tid else None
                final = canonical if canonical else stem
                action = "Renamed" if canonical and canonical != stem else "As-Is"
                file_summaries.append({
                    "original": stem,
                    "final": final,
                    "action": action,
                    "result": entry["result"],
                })
                mapped.append({"name": final, "result": entry["result"]})
            return mapped
        file_results = _apply_canonical(file_results)

        report_name = ""
        try:
            report_path = generate_report(dest_dir, file_results, results_count, file_summaries)
            report_name = os.path.basename(report_path)
            self._report_path = report_path
        except Exception as e:
            report_name = f"Report error: {e}"

        # ── Finish on the main thread ───────────────────────────
        copy_summary = f"Copied {copied}"
        if skipped:
            copy_summary += f", skipped {skipped}"
        if dedup_summary:
            copy_summary += f" | 🔍 {dedup_summary}"

        final_msg = f"  ✅  {copy_summary} PDF(s) → {dest_dir}  |  {sep_msg}  |  📊 {report_name}"
        self._result_folder = dest_dir

        def _finish():
            self._status_label.configure(text=final_msg, text_color=T.ACCENT_SUCCESS)
            self._start_btn.configure(state="normal", text="Start")
            self._open_btn.pack(side="left")
            self._open_excel_btn.pack(side="left", padx=(10, 0))
            self._close_btn.pack(side="right", padx=(0, 10))

        self._ui(_finish)

    def _toggle_canonical_row(self):
        """Show or hide the canonical names row based on the selected dup mode."""
        if self._dup_mode.get() == "ignore_duplicates":
            self._edit_names_row.pack(fill="x", padx=20, pady=(0, 18))
        else:
            self._edit_names_row.pack_forget()

    def _open_canonical_names_editor(self):
        """Open the canonical names editor dialog."""
        CanonicalNamesDialog(self.winfo_toplevel(), config_path=_CANONICAL_NAMES_PATH)

    def _close_app(self):
        """Close the application window."""
        self.winfo_toplevel().destroy()

    def _open_result_folder(self):
        """Open the result folder in the system file explorer."""
        folder = self._result_folder
        if folder and os.path.isdir(folder):
            subprocess.Popen(["explorer", os.path.normpath(folder)])

    def _open_excel_report(self):
        """Open the generated Excel report."""
        if self._report_path and os.path.isfile(self._report_path):
            os.startfile(self._report_path)
