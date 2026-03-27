# Changelog

All notable changes to **Release Testing Tool (RTT)** are recorded here.

Follow the versioning rules documented in [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md#12-versioning-policy).

Format per entry:

```
## vX.Y.Z — YYYY-MM-DD
### Added / Changed / Fixed / Removed
- Description
```

---

## v3.2.1 — 2026-03-27
### Fixed
- **Settings "Apply & Restart" crash on Windows**: Replaced POSIX-only `os.execv()` with `subprocess.Popen()` + `sys.exit(0)` for cross-platform restart support

- **HoverButton IndexError on empty color value**: Added guard against empty list/tuple returned by `cget("text_color")`, preventing `IndexError` during hover events

- **StatusBar timer resource leak**: Timer callback (`_tick`) was never cancelled on widget destruction, leading to infinite `after()` chain; added timer-ID tracking and `destroy()` override with `after_cancel()`

- **SystemTestListe PDF matcher shared-dict reference bug**: `[{}] * total` created N references to the same dict object; replaced with list comprehension `[{} for _ in range(total)]`

- **PDF Analyzer negative page-index guard**: When preset page numbers are 0, `page - 1` yields −1 (valid Python index = last element); added explicit `< 0` early-return guards in `_detect_result_priority()` and `_detect_result()`

---

## v3.2.0 — 2026-03-27
### Fixed
- **Progress bar percentage display stuck at 99%**:
  - Changed `int()` to `round()` for all percentage display calculations in SegmentedProgressBar widget
  - Eliminates asymptotic behavior where lerp animation approaches 1.0 but `int(0.997*100)` = 99

- **Progress bar animation never reaches full completion**:
  - Raised lerp snap threshold from 0.004 to 0.015 to properly snap bars to final values
  - Cleaned up stale targets in `_seg_targets` dictionary after snapping to prevent lingering state

- **Progress bar segment labels cropping and shifting**:
  - Added fixed-width labels with right-alignment (`width=44` for segments, `width=54` for overall percentage)
  - Reordered label packing so percentage label is packed first to prevent child pushes off-screen
  - Applied `fill="x"` expansion to step labels for graceful text truncation

- **PDF analyzer progress bar stayed empty during report generation**:
  - Added explicit `_set_seg(2, 1.0)` call after report PDF is written
  - Added midpoint progress `_set_seg(2, 0.3)` before report generation starts

- **PDF analyzer copy segment went backward during deduplication**:
  - Added explicit `_set_seg(0, 1.0)` call after copy and deduplication complete

- **SystemTestListe report segment showed no progress during Excel write**:
  - Added midpoint progress `_set_seg(2, 0.3)` before Excel write begins

- **Redundant widget redraws causing jerky animation**:
  - Implemented `_bar_colors` tracking to skip `configure()` calls when bar color unchanged
  - Eliminated duplicate `configure()` calls in `_update_overall()` method

- **Progress bar jumping instead of gradually filling**:
  - Implemented target-based lerp animation system with `_seg_targets` dictionary
  - Progress now interpolates 35% of remaining gap per 50ms tick for smooth visual progression

### Added
- **"Don't Minimize" warning dialog** before processing begins on both analyzers:
  - Blocks processing start with modal CTkToplevel dialog
  - Centered over parent window with single OK button
  - Reminds user that minimizing window during processing may cause freezing
  - Enter key bound to dismiss dialog

- **Item completion counter in progress bar card**:
  - Progress bar now displays "Processing — X of Y items" showing current item count and total
  - PDF Analyzer: Updates for each file copied, deduplicated, detected, and separated
  - SystemTestListe Analyzer: Updates for each PDF scanned during analysis
  - Counter increments in real-time as processing advances through each phase

### Changed
- **Overall percentage label** now displays with fixed width and right-alignment for consistent layout
- **Segment percentage labels** now display with fixed width and right-alignment for consistent layout
- **Segmented progress bar update frequency**: All batch updates consolidated via `set_segments_batch()` for reduced overhead
- **SegmentedProgressBar widget**: Added `set_item_counter(completed, total)` method to display item completion statistics

---

## v3.1.0 — 2026-03-27
### Added
- **Software version comparison feature** with configurable regex patterns:
  - New presets section `sw_comparison` with extraction and comparison regexes
  - `normalize_sw_for_comparison()` utility function extracts regex capture groups
  - UI card in Presets page for entering/testing comparison regexes (e.g., compare
    `120_240_A_01_02_T12` vs `120_240_B_01_02_T12` by ignoring the 3rd segment
    letter and focusing on build/variant/test info).
  - SystemTestListe Analyzer now compares SW versions using normalized forms for
    more flexible matching (e.g., prefix match on build part).

- **Preset save button in header** for quick access to save all preset changes
  to `config/presets.json` without requiring a manual save dialog.

- **Auto-reload of presets** after saving — all UI instances (`_presets` dict,
  bound variables, extracted regexes) are immediately refreshed so changes take
  effect without restarting the application.

- **Elapsed time formatting** with human-readable display across both analyzers:
  - Subsecond times display as decimal (e.g., `"0.4s"`, `"12.3s"`)
  - Minute-scale times display as `"Xm YYs"` (e.g., `"2m 05s"`)
  - Hour-scale times display as `"Xh YYm ZZs"` (e.g., `"1h 02m 09s"`)
  - Applied to all 3 progress segments in both PDF Analyzer and SystemTestListe
    Analyzer (6 elapsed-time labels total).

### Changed
- **PDF Analyzer progress bar now includes a "Report" segment** so the full
  workflow is visible: "Copy" → "Separate" → "Report" (was previously showing
  only 2 segments; the report generation step runs but was unlabeled).

### Fixed
- **SystemTestListe tab list scroll position** now auto-resets to the top after
  selecting a tab or clearing filters, improving UX when switching between tabs
  with long content.

- **PDF Analyzer worker thread crash** on step label updates:
  - Root cause: code was calling non-existent `set_step_label()` method on the
    progress bar, causing an `AttributeError` that crashed the worker thread
    and froze the UI with the Start button never re-enabling.
  - Fixed by introducing `_set_seg_label()` helper method that thread-safely
    buffers label updates in `_pending_seg_labels` and applies them during
    the 50 ms poll cycle.

- **Progress bar flickering and jitter** during file processing:
  - Root cause: multiple overlapping calls to `set_segment()` were each triggering
    a full widget configure() and GUI redraw, causing visible visual artifacts.
  - Fixed by introducing `set_segments_batch()` method that accepts multiple
    segment updates in one dict and batches all configure() calls into a single
    per-widget operation. Both `_do_poll()` loops now use this batched approach
    instead of per-segment updates, eliminating jitter altogether.

---

## v3.0.0 — 2026-03-26
### Fixed
- **Progress bars no longer hang or show random percentages during processing**:
  - Root cause: every file processed called `self.after(0, fn)`, flooding the
    Tkinter event queue with hundreds of callbacks simultaneously. The main
    thread drained them all in a burst, causing UI freezes and flickering
    intermediate values.
  - Replaced the per-call `after(0, ...)` dispatch with a **50 ms poll loop**
    (`_start_poll` / `_do_poll`) on both `PDFAnalyzerPage` and
    `SystemTestListeAnalyzerPage`. The worker thread writes to plain instance
    variables (`_pending_status`, `_pending_segs`, `_pending_seg_labels`);
    the main thread reads and applies them at a controlled rate (max 20
    updates/s), keeping the UI fully responsive regardless of workload size.
  - `_ui()` is retained only for infrequent one-shot events (button re-enable,
    show/hide buttons) which are unaffected by the queue-flood problem.
  - `_poll_running = False` is set at every worker exit path (success + all
    error returns) so the poll loop terminates cleanly.

### Changed
- **PDF page selection now strictly follows presets — no silent fallbacks**:
  - `pdf_matcher.py` (`_read_pdf_pages`): removed fallback-to-page-`[1]` /
    page-`[0]` logic. If the preset page index exceeds the PDF page count, the
    result is an empty string for that page — no redirect to a different page.
  - `result_separator.py` (`_detect_result`, `separate_by_result`): hardcoded
    `pages[1]` replaced with a `page_idx` parameter. When not provided,
    `result_extraction.page` is read from `config/presets.json` (1-based →
    0-based conversion). Only the specified page is accessed; returns `None`
    if it doesn’t exist in the PDF.
  - `file_copier.py` (`_detect_result_priority`, `smart_deduplicate`):
    same treatment — `page_idx` parameter, preset-driven default, no
    `len(pages) < 2` guard with a hardcoded `pages[1]` fallback.
  - `pdf_analyzer.py` (`_run_worker`): presets are loaded once at the start;
    `result_page_idx` is derived and forwarded explicitly to
    `smart_deduplicate`, `_detect_result`, and `separate_by_result`.

- **Logging infrastructure removed; replaced with crash-only traceback writer**:
  - The always-on `RotatingFileHandler` that wrote to `logs/crash_YYYYMMDD.log`
    on every run has been removed. A new `_write_crash_log(tb)` helper in
    `main.py` opens and appends to the log file **only when an unhandled
    exception actually occurs** — zero file I/O during normal operation.
  - `import logging` and all `logging.*` calls removed from `main.py` and
    `src/gui/main_window.py`.
  - `.gitignore` updated: `logs/*.log` / `logs/*.txt` patterns replaced with
    `logs/*` (ignores all runtime-generated files in the folder, preserving
    `logs/README.txt` via the existing `!` exception rule).

---

## v2.5.0 — 2026-03-25
### Added
- **Per-step processing time display** in the SystemTestListe Analyzer:
  - Each progress segment label updates with its elapsed wall-clock time once
    that step completes (e.g. `Reading Excel (0.4s)`, `Scanning PDFs (12.3s)`,
    `Report (0.8s)`).
  - Timing uses `time.perf_counter()` for high-resolution measurement.
  - Labels are updated thread-safely via the existing `_ui()` dispatcher.
  - `SegmentedProgressBar` gains a new `set_segment_label(index, text)` public
    method; `reset()` now also restores all segment labels to their original
    values so re-runs show a clean state.

### Changed
- **Performance optimisations** across the core analyser layer:
  - `utils.py` — `_VER_RE` regex moved to module level (compiled once, not per
    PDF call); `_SW_PATTERN_CACHE` dict introduced so user-supplied SW regex
    patterns are compiled only on first use and reused on every subsequent call.
  - `report_writer.py` — style objects (`PatternFill`, `Font`, `Border`,
    `Alignment`) pre-created once before data loops; the same instances are
    reused across all rows and all tabs, reducing per-cell object allocation
    from O(rows×cols) to O(distinct\_styles).
  - `excel_reader.py` — header-candidate lookup converted from `list` to `set`
    for O(1) membership test in `find_header_row`.
  - `pdf_matcher.py` — parallel PDF scanning via `ThreadPoolExecutor` (up to 8
    workers); `gc.collect()` called after each PDF worker and after the full
    batch to release pdfplumber page objects promptly.

---

## v2.4.0 — 2026-03-25
### Changed
- **`utils.py` — `extract_library_version()` rewritten**:
  - Replaces the collapsed-whitespace + 6-line-fallback strategy with a strict
    line-based approach: finds the line containing the anchor phrase (case-insensitive)
    and inspects that line plus the next **3 lines only** (4-line window).
  - Version token pattern is now fixed as `[vV] ?\d+(?:\.\d+)?` — matches
    `V2`, `v 2`, `V114.0`, `v 2.5`, etc.
  - Result is **normalised**: spaces removed and uppercased (`"V 2"` → `"V2"`).
  - Returns `None` (instead of `""`) when not found; callers are unaffected
    since both are falsy.
- **`report_writer.py` — MainSheet & detail tabs overhaul**:
  - New **`Report`** column added to MainSheet immediately after `PDFResult`;
    shows `✓ Available` (green) or `✗ No Report` (grey/bold) per row.
  - No-report rows receive a distinct light-grey row tint (`F2F2F2`).
  - Detail tabs follow an explicit **three-step** creation order:
    1. **No Reports** tab — created only when at least one test case has no
       matched PDF; lists Test Case ID and Name.
    2. **Result Mismatches**, **SW Mismatches**, **Variant Mismatches**,
       **Library — Not Linked** — populated with mismatches only, all
       no-report test cases excluded from these tabs.
    3. **Empty tabs are never created** — tabs with no qualifying rows are
       skipped entirely.
- **`systemtestliste_analyzer.py` — folder Browse button gating**:
  - The **Browse** button in the PDF Reports Directory card is now hidden on
    page load; it appears only after a SW tab has been selected from the list.
  - Resetting the tab selection hides the button again.

---

## v2.3.0 — 2026-03-24
### Added
- **Library Check** — new end-to-end feature for extracting and validating the
  custom library version from PDF test reports:
  - `config/presets.json`: new `library_extraction` section (`page`, `search_text`,
    `version_pattern`) with sensible defaults.
  - `presets.py`: `library_extraction` added to `DEFAULT_PRESETS`; `load_presets()`
    merges the new section; new `library_settings_from_presets()` helper.
  - `utils.py`: new `extract_library_version(text, search_text, version_pattern)` —
    collapses whitespace, locates an anchor phrase, and extracts a version token
    (e.g. `v114.0`) via regex; falls back to a 6-line sliding window.
  - `pdf_matcher.py`: all three extraction paths (`_extract_page3_full`,
    `match_pdf_result`, `match_all_rows`) accept `library_page_idx`,
    `library_search_text`, `library_version_pattern` and return `library_version`
    in every result dict.
  - `report_writer.py`: `write_stl_helper()` accepts `library_version_list`;
    appends a **Library Version** column; rows where the version is absent are
    highlighted amber (`FFF2CC` row / `FFC000` cell); a dedicated **"Library —
    Not Linked"** summary sheet is created when any versions are missing.
  - `stl_presets.py`: new **Library** card (Card 5) with Anchor text entry,
    Version regex entry, live-test field, and Save Entry / Save All buttons;
    Library Version page number added to the PDF Extraction Pages card.
  - `systemtestliste_analyzer.py`: **Library Check** checkbox (default: checked)
    added beside Variant Information; worker reads the checkbox, derives library
    extraction parameters from presets, passes them to `match_all_rows()`, and
    forwards `library_version_list` to `write_stl_helper()`; summary message
    includes `Library: N/total linked` count.

---

## v2.2.0 — 2026-03-24
### Added
- **`presets.py` — SW pattern management utilities**:
  - `try_add_sw_pattern(presets, label, regex, update_idx)` — validates and
    adds or replaces a SW name regex pattern; enforces duplicate-regex and
    duplicate-label checks with human-readable error messages.
  - `detect_unmatched_sw(text, presets)` — scans arbitrary text for SW name
    candidates (via `SW_NAME_RE`) and returns which are already covered by
    existing patterns (`matched`) and which are not (`unmatched`), each with
    an auto-generated suggested regex.
  - `_generalize_sw_name(sw_value)` — private helper that converts a concrete
    SW name string into a generalised regex (digit segments → `\d{N}`,
    alpha-digit suffixes → `[A-Za-z]\d{N}`, other segments escaped verbatim).
### Changed
- **STL Presets — `_sw_save_entry()`** refactored to delegate all validation
  and persistence to `try_add_sw_pattern()`; inline `re.compile` / duplicate
  logic removed; error surfaced via `messagebox.showerror("Cannot Save
  Pattern", reason)` for consistent UX.
- Selection pointer after a new SW pattern addition now correctly points to the
  last appended entry (`_sw_sel = len(patterns) - 1`).

---

## v2.1.2 — 2026-03-24
### Changed
- **STL Presets — PDF Extraction Pages card**: consolidated all page-number
  entries (Result Status / SW Version / Variant SWFL) into a single dedicated
  card at the top of the Presets page; removed inline "Extract from page:"
  spinners from the SW Name, Result, and Variant individual cards.
- Added `_save_page_numbers()` method — saves only page numbers without
  touching patterns or entries.
- Stale page-number writes removed from `_sw_save_entry` and `_res_save_entry`
  (now managed exclusively through Card 0 / `_save_all()`).

---

## v2.1.1 — 2026-03-24
### Changed
- **SystemTestListe Analyzer — UI improvements**:
  - "Open Result" button is hidden at run start and revealed only after a
    successful analysis (Excel file ready).
  - Selecting a tab row collapses the filter + list area and shows a name chip
    with a Reset button; Reset restores the filter row and list.
  - `_filter_var` is cleared on Reset.
  - Variant Information checkbox now defaults to **unchecked**.
  - Variant checkbox is auto-hidden when the SW name's second segment is `200`
    (pattern `NNN_200_*`) and restored on Reset.
- **Menu order** updated to: Dashboard, Report Analyzer, SystemTestListe
  Analyzer, Folder Mgmt, Reports, Presets, Settings (page index 5 = Presets).

---

## v2.1.0 — 2026-03-24
### Added
- **STL Presets system**:
  - `config/presets.json` — persistent config with three sections:
    `sw_extraction` (page + regex patterns), `result_extraction` (page +
    keywords), `variant_extraction` (page + SWFL entries).
  - `src/core/systemtestliste/presets.py` — backend: `load_presets()`,
    `save_presets()`, `variant_map_from_presets()`, `sw_patterns_from_presets()`,
    `result_keywords_from_presets()`, `import_variant_txt()`.
  - `src/gui/pages/stl_presets.py` — new `STLPresetsPage` UI with four cards:
    **PDF Extraction Pages**, **SW Name Extraction Patterns**,
    **Result Status Extraction**, and **Variant ↔ SWFL Mapping**.
    Each card supports add / edit / delete with live list view.
- **Presets** menu item (🔧) added to sidebar; wired to `STLPresetsPage` in
  `main_window.py`.
- `_run_worker()` in `systemtestliste_analyzer.py` now loads live presets at
  runtime: derives `variant_map`, `sw_patterns`, `keywords`,
  `result_page_idx`, `sw_page_idx`, `variant_page_idx` from `presets.json`
  before each analysis run.

---

## v2.0.0 — 2026-03-24
### Changed — **Breaking: core extraction API**
- `pdf_matcher.match_pdf_result()` now returns a `dict` (`result`,
  `page3_sw`, `page3_variant`) instead of a plain `str`.
- `pdf_matcher.match_all_rows()` now returns `list[dict]` with the same keys.
- Both functions accept new keyword parameters: `keywords`, `result_page_idx`,
  `sw_page_idx`, `variant_page_idx` — all fully configurable.
- `_extract_page3_full()` reads result, SW name, and variant from independently
  configurable page indices.
### Added
- `utils.SW_NAME_RE` — compiled regex for NNN_NNN_…_NN_NN_ANN SW name format.
- `utils.load_variant_map(path)` — loads `Variant_Info.txt`; returns
  `{SWFL_hex_upper: variant_label}`.
- `utils.extract_sw_name(text, patterns)` — tries preset regex patterns list,
  falls back to `SW_NAME_RE`.
- `utils.extract_variant_from_swfl(text, variant_map)` — extracts SWFL code and
  maps it to a variant label.
- `report_writer.py` gains six new output columns (added when the corresponding
  check is enabled): `PDFResult`, `ResultMatch`, `Page3_SW`, `SWMatch`,
  `Page3_Variant`, `VariantMatch`.

---

## v1.3.4 — 2026-03-23
### Changed
- Versioning policy updated: **logic changes and major code restructuring now
  classify as Major (X.0.0)**, not Minor.  Decision guide in
  `DEVELOPER_GUIDE.md` updated with two new rules:
  - "Does it change business logic or core algorithms? → Major"
  - "Is it a large code restructure / refactor? → Major"

---

## v1.3.3 — 2026-03-23
### Added
- `DEVELOPER_GUIDE.md` — single reference file for co-workers covering color
  presets, widget catalogue, page-wiring recipe, splash config, versioning
  policy, coding conventions, and common pitfalls.

---

## v1.3.2 — 2026-03-23
### Added
- Multi-monitor splash centering: `_get_largest_monitor_rect()` uses
  `ctypes.windll.user32.EnumDisplayMonitors` to find the monitor with the
  largest pixel area and centers the splash on it.  Falls back to
  `winfo_screenwidth/height` on non-Windows.

---

## v1.3.1 — 2026-03-23
### Changed
- Splash minimum display time raised to **7 500 ms** via `ensure_min_display()`.
- Replaced `CTkToplevel` with plain `tk.Toplevel` for the splash window;
  eliminates the hidden CTk internal frame that was covering the canvas and
  causing the "two area / empty" visual bug.
- Window enlarged to **780 × 560 px**; all fonts, padding, bar, and log
  elements scaled up proportionally.

---

## v1.3.0 — 2026-03-23
### Added
- **Photoshop-style loading log panel** inside splash — 6-line scrolling history
  with recency-based opacity fading and an accent `▶` arrow on the newest entry.
- `SplashScreen.log(text)` public method for manual log entries.
- `SplashScreen.ensure_min_display(ms, callback)` — guarantees the splash is
  visible for at least `ms` milliseconds regardless of how fast modules load.
- `set_progress()` now automatically appends its message to the loading log.
### Changed
- Build steps expanded from **6 → 15** granular steps with 90 ms delay between
  each, providing descriptive messages ("Reading configuration files", "Applying
  theme palette", "Building navigation sidebar", etc.).

---

## v1.2.2 — 2026-03-22
### Added
- `RttButton` widget (`src/gui/widgets/hover_button.py`) — `CTkButton` subclass
  that brightens button text to `T.BTN_HOVER_TEXT` on hover and restores it on
  leave.  All page and sidebar buttons migrated from `ctk.CTkButton`.
- `AppTheme.BTN_HOVER_TEXT` class constant + entry in both `LIGHT` and `DARK`
  dicts so `ThemeManager` remaps it on theme switch.

---

## v1.2.1 — 2026-03-22
### Changed
- Dark-theme button/sidebar hover colour raised from `#1b3a5c` to `#1e4d80`
  (mid-blue) — visibly distinct from the sidebar background without being harsh.
  Updated in both the class-level constant and the `DARK` dict.

---

## v1.2.0 — 2026-03-22
### Fixed — WCAG contrast failures in light theme
- `ACCENT_PRIMARY` light: `#00d4ff` (1.4:1 ❌) → `#0077aa` (9.0:1 ✅ AAA)
- `ACCENT_SECONDARY` dark: `#7b2ff7` (2.9:1 ❌) → `#a371f7` (5.1:1 ✅ AA);
  light: new `#6d28d9` (8.3:1 ✅ AAA)
- `SIDEBAR_BTN_ACTIVE` (was absent from dicts) — added to both palettes.
- `TEXT_ACCENT`, `BORDER_GLOW`, `PROGRESS_FG`, all semantic accents
  (`ACCENT_SUCCESS/WARNING/DANGER`) — added to both `LIGHT` and `DARK` dicts so
  `ThemeManager` remaps them on theme switch (previously unremapped).
### Added
- Full `LIGHT` / `DARK` palette dicts now cover every token that differs between
  themes — surfaces, text, accents, sidebar states, borders, progress bar.

---

## v1.1.0 — 2026-03-22
### Changed
- Splash screen fully redesigned with professional animation suite:
  - Canvas particle field (46 drifting dots, alpha-blended, respawn from bottom)
  - Title colour pulse via sine-wave oscillation (`text_bright` ↔ `accent`)
  - Shimmer sweep across the filled portion of the progress bar
  - Animated loading dots (`.` → `..` → `...` cycle)
  - Percentage readout label
  - Alpha fade-in on open, fade-out on close
  - `[RTT]` coloured badge, hairline divider, footer with theme indicator dot
  - Theme-aware palette (reads `config/settings.json` before `ThemeManager` runs)

---

## v1.0.0 — initial
### Added
- Initial release: main window with sidebar navigation, header, status bar.
- Pages: Dashboard, Report Analyzer (PDF), SystemTestListe Analyzer, Excel Tools,
  Settings (theme toggle).
- `ThemeManager` — load / apply / save light/dark preference to `settings.json`.
- Splash screen (basic progress bar, static text).
