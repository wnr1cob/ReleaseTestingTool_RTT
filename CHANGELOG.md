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
