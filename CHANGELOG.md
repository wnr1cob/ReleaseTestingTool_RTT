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
