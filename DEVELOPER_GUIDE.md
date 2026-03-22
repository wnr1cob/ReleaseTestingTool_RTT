# RTT — Developer Guide & Team Reference

> **Audience:** Every developer or co-worker who contributes to or maintains the
> Release Testing Tool (RTT).  This file is the single source of truth for
> presets, conventions, component APIs, and best practices.

---

## Table of Contents

1. [Project Layout](#1-project-layout)
2. [Running the App](#2-running-the-app)
3. [Architecture Overview](#3-architecture-overview)
4. [Theme System — Presets & Colours](#4-theme-system--presets--colours)
5. [Widget Catalogue](#5-widget-catalogue)
6. [Adding a New Page](#6-adding-a-new-page)
7. [Splash Screen Configuration](#7-splash-screen-configuration)
8. [Config Files](#8-config-files)
9. [Coding Conventions](#9-coding-conventions)
10. [Dependencies](#10-dependencies)
11. [Common Pitfalls](#11-common-pitfalls)
12. [Versioning Policy](#12-versioning-policy)

---

## 1. Project Layout

```
ReleaseTestingTool_RTT/
│
├── main.py                        ← Entry point — run this
├── requirements.txt
├── DEVELOPER_GUIDE.md             ← You are here
├── README.md
│
├── config/
│   ├── settings.json              ← Theme preference + user settings
│   └── canonical_names.json       ← Test-case name normalisation map
│
├── src/
│   ├── core/                      ← Pure business logic (no GUI)
│   │   ├── pdf_analyzer/          ← PDF copy, split, dedup, report gen
│   │   └── systemtestliste/       ← Excel reader, PDF matcher, report writer
│   │
│   ├── gui/
│   │   ├── main_window.py         ← Top-level window + splash build chain
│   │   ├── splash.py              ← Animated splash screen
│   │   ├── dialogs/               ← Modal dialogs (canonical names, etc.)
│   │   ├── pages/                 ← One file per sidebar page
│   │   │   ├── dashboard.py
│   │   │   ├── pdf_analyzer.py
│   │   │   ├── systemtestliste_analyzer.py
│   │   │   ├── excel_tools.py
│   │   │   ├── settings.py
│   │   │   └── placeholder.py     ← Stub for unreleased pages
│   │   ├── styles/
│   │   │   └── theme.py           ← ALL colour/font/dimension constants
│   │   └── widgets/               ← Reusable custom widgets
│   │       ├── hover_button.py    ← RttButton (hover-text-colour support)
│   │       ├── sidebar.py
│   │       ├── status_bar.py
│   │       ├── progress_bar.py
│   │       ├── segmented_progress.py
│   │       └── stat_card.py
│   │
│   └── utils/
│       └── theme_manager.py       ← Load / apply / save theme preference
│
├── tests/
├── data/                          ← Input files (PDFs, Excel)
├── output/                        ← Generated reports
└── logs/
```

---

## 2. Running the App

```powershell
# Create and activate a virtual environment (one-time)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Launch
python main.py
```

Minimum Python version: **3.10** (uses `X | Y` union types and `match` syntax).

---

## 3. Architecture Overview

```
main.py
  └── MainWindow.__init__
        ├── ThemeManager.load()          ← reads config/settings.json
        ├── ThemeManager.apply()         ← sets AppTheme class attrs + ctk mode
        ├── root.withdraw()              ← window stays hidden during build
        └── root.after(50, _start_build)
              └── SplashScreen(root)     ← animated splash appears
                    └── _build_step(0..14)   ← incremental page construction
                          └── _finish_build()
                                ├── splash.close()   ← fade-out
                                └── root.deiconify() ← main window appears
```

**Key rule:** The root window is always hidden (`withdraw`) while the splash is
visible.  Never call `root.deiconify()` before `_finish_build()`.

### Page wiring

Each page is a `ctk.CTkFrame` subclass placed inside `self._content`.
`_show_page(index)` calls `pack_forget()` on the previous page and `pack()` on
the new one — no destroy/recreate cycle.

---

## 4. Theme System — Presets & Colours

### 4.1 The single source: `AppTheme`

`src/gui/styles/theme.py` — `AppTheme` class.  
**Import it everywhere as:**

```python
from src.gui.styles.theme import AppTheme as T
```

Never hardcode hex strings in page or widget files.

---

### 4.2 Colour Presets

#### Dark Theme (default)

| Token | Hex | Use |
|---|---|---|
| `T.BG_DARK` | `#1a1a2e` | Main window background |
| `T.BG_SIDEBAR` | `#16213e` | Sidebar background |
| `T.BG_CARD` | `#1a1a40` | Card / panel background |
| `T.BG_HEADER` | `#0d1b2a` | Header strip |
| `T.ACCENT_PRIMARY` | `#00d4ff` | Primary cyan — 16:1 contrast ✅ |
| `T.ACCENT_SECONDARY` | `#a371f7` | Violet — 5.1:1 contrast ✅ |
| `T.ACCENT_SUCCESS` | `#00e676` | Green |
| `T.ACCENT_WARNING` | `#ffab00` | Amber |
| `T.ACCENT_DANGER` | `#ff5370` | Red |
| `T.TEXT_PRIMARY` | `#e0e0e0` | Body text |
| `T.TEXT_SECONDARY` | `#8892b0` | Muted / placeholder text |
| `T.TEXT_BRIGHT` | `#ffffff` | Headings |
| `T.BORDER_COLOR` | `#233554` | Card / input borders |
| `T.SIDEBAR_BTN_HOVER` | `#1e4d80` | Hover bg — mid-blue |
| `T.SIDEBAR_BTN_ACTIVE_BG` | `#152d50` | Active item bg |
| `T.BTN_HOVER_TEXT` | `#ffffff` | Button text on hover |

#### Light Theme

| Token | Hex | Use |
|---|---|---|
| `T.BG_DARK` | `#f0f4f8` | Main window background |
| `T.BG_SIDEBAR` | `#e2e8ef` | Sidebar background |
| `T.BG_CARD` | `#ffffff` | Card / panel background |
| `T.ACCENT_PRIMARY` | `#0077aa` | Deep teal — 9.0:1 ✅ |
| `T.ACCENT_SECONDARY` | `#6d28d9` | Deep violet — 8.3:1 ✅ |
| `T.ACCENT_SUCCESS` | `#15803d` | Dark green — 6.0:1 ✅ |
| `T.ACCENT_WARNING` | `#b45309` | Dark amber — 4.8:1 ✅ |
| `T.ACCENT_DANGER` | `#dc2626` | Dark red — 5.5:1 ✅ |
| `T.BTN_HOVER_TEXT` | `#0d1117` | Near-black button text on hover |

> **Contrast rule (WCAG):** AA requires ≥ 4.5:1 for normal text, AAA ≥ 7:1.
> Every accent above is verified.  Do **not** use a custom colour for text on a
> coloured background without checking contrast first.

---

### 4.3 Font Presets

```python
T.FONT_FAMILY      = "Segoe UI"   # base family for all text
T.FONT_SIZE_TITLE   = 20
T.FONT_SIZE_HEADING = 14
T.FONT_SIZE_BODY    = 12
T.FONT_SIZE_SMALL   = 10
T.FONT_SIZE_SIDEBAR = 13
```

Always compose as a tuple: `(T.FONT_FAMILY, T.FONT_SIZE_BODY)` or
`(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold")`.

---

### 4.4 Dimension Presets

```python
T.WINDOW_WIDTH   = 1100
T.WINDOW_HEIGHT  = 700
T.SIDEBAR_WIDTH  = 220
T.CORNER_RADIUS  = 12    # CTkFrame
T.BUTTON_CORNER  = 8     # CTkButton / RttButton
T.CARD_CORNER    = 10    # card frames
T.PROGRESS_HEIGHT = 6    # progress bar height
```

---

### 4.5 How ThemeManager applies a theme switch

`ThemeManager.apply(theme, root)` does three things in order:

1. Builds a `{old_hex: new_hex}` map by comparing the **old** and **new**
   palette dicts.
2. Updates every `AppTheme` class attribute with the new palette values
   (so newly-created widgets use correct colours automatically).
3. Walks the **entire live widget tree** via `_restyle_widgets()` and remaps
   `fg_color`, `text_color`, `button_color`, `hover_color`, `progress_color`,
   etc. on every widget.

**Rule:** Every colour token that differs between light and dark **must** be
present in **both** `AppTheme.LIGHT` and `AppTheme.DARK` dicts.  A key missing
from either side will not be remapped on theme switch.

---

## 5. Widget Catalogue

### `RttButton` — `src/gui/widgets/hover_button.py`

Drop-in replacement for `ctk.CTkButton` that brightens button text on hover.

```python
from src.gui.widgets.hover_button import RttButton

btn = RttButton(
    parent,
    text="Run Analysis",
    font=(T.FONT_FAMILY, T.FONT_SIZE_BODY, "bold"),
    height=40,
    corner_radius=T.BUTTON_CORNER,
    fg_color=T.ACCENT_PRIMARY,
    hover_color=T.SIDEBAR_BTN_HOVER,
    text_color=T.TEXT_BRIGHT,
    command=self._start,
)
```

**Optional kwarg:** `hover_text_color="#ff0000"` overrides `T.BTN_HOVER_TEXT`
for a specific button.

> ⚠️ Use `RttButton` for **all** buttons in the app — never `ctk.CTkButton`
> directly — so hover-text behaviour and theme remapping stay consistent.

---

### `Sidebar` — `src/gui/widgets/sidebar.py`

```python
Sidebar(master, on_select_callback=self._show_page)
```

Menu items are driven entirely by `AppTheme.MENU_ITEMS` list of `(label, icon)`
tuples.  To add a sidebar entry, add to that list **and** register a
corresponding page in `MainWindow._pages`.

---

### `StatusBar` — `src/gui/widgets/status_bar.py`

```python
self._status_bar.set_status("Processing file…")
self._status_bar.set_status("Error occurred", color=T.ACCENT_DANGER)
```

---

### `SegmentedProgressBar` — `src/gui/widgets/segmented_progress.py`

Multi-segment progress bar used on analyzer pages.

```python
bar = SegmentedProgressBar(
    parent,
    segments=[
        {"label": "Reading Excel",  "color": T.ACCENT_SUCCESS},
        {"label": "Scanning PDFs",  "color": T.ACCENT_PRIMARY},
        {"label": "Report",         "color": T.ACCENT_SECONDARY},
    ],
)
bar.set_segment(0, 0.65)   # 65% complete on segment 0
bar.set_segment(1, 1.0)    # segment 1 done
bar.reset()                # clear all segments
```

---

### `StatCard` — `src/gui/widgets/stat_card.py`

Dashboard summary card:

```python
StatCard(parent, title="Total PDFs", value="142", icon="📄")
```

---

## 6. Adding a New Page

Follow these steps exactly — they keep the build chain, sidebar, theming, and
splash loading log in sync.

### Step 1 — Create the page file

```python
# src/gui/pages/my_new_page.py
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T
from src.gui.widgets.hover_button import RttButton


class MyNewPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=T.BG_DARK, corner_radius=0, **kwargs)
        self._build()

    def _build(self):
        ctk.CTkLabel(
            self,
            text="My New Page",
            font=(T.FONT_FAMILY, T.FONT_SIZE_TITLE, "bold"),
            text_color=T.TEXT_BRIGHT,
        ).pack(pady=30)

    # Optional: called by ThemeManager after a theme switch
    def _on_theme_refresh(self) -> None:
        pass
```

### Step 2 — Register the menu item

In `src/gui/styles/theme.py`, append to `MENU_ITEMS`:

```python
MENU_ITEMS = [
    ...
    ("My New Page", "🆕"),   # ← add here
]
```

### Step 3 — Wire it into `MainWindow`

In `src/gui/main_window.py`:

**a) Import:**
```python
from src.gui.pages.my_new_page import MyNewPage
```

**b) Add a build step** (pick the next available `step` number, currently after
step 11):

```python
elif step == 12:
    s.set_progress(0.88, "Loading My New Page")
    self._pages[6] = MyNewPage(self._content)
    self.root.after(DELAY, self._build_step, 13)
```

**c) Renumber** the subsequent steps and progress values accordingly.

---

## 7. Splash Screen Configuration

All splash knobs live at the top of `SplashScreen` class in
`src/gui/splash.py`:

| Constant | Default | Description |
|---|---|---|
| `WIDTH` | `780` | Window width in px |
| `HEIGHT` | `560` | Window height in px |
| `_TICK_MS` | `30` | Animation frame interval (≈33 fps) |
| `_N_PARTS` | `64` | Number of floating particles |
| `_LOG_LINES` | `6` | Visible lines in the loading log panel |

**Minimum display time** is set in `main_window.py`:

```python
# step 14 — always >= 7.5 s regardless of how fast modules load
s.ensure_min_display(7500, self._finish_build)
```

Change `7500` (milliseconds) to adjust how long the splash stays.

**Multi-monitor centering:** Uses `ctypes.windll.user32.EnumDisplayMonitors`
to find the monitor with the largest pixel area and centres the splash on it.
Falls back to `winfo_screenwidth/height` on non-Windows.

---

## 8. Config Files

### `config/settings.json`

```json
{
    "theme": "dark"
}
```

| Key | Values | Notes |
|---|---|---|
| `theme` | `"dark"` / `"light"` | Written by Settings page on Apply |

### `config/canonical_names.json`

Maps raw test-case names (from PDF filenames) to a normalised canonical name.
Edited via the **Edit TestCase Names** dialog on the Report Analyzer page.

```json
{
  "TC_001_Login_v2_FINAL": "TC_001_Login",
  "SomeLongVariantName":   "ShortCanonical"
}
```

---

## 9. Coding Conventions

### Imports

```python
# stdlib first
import os, threading

# third-party
import customtkinter as ctk
from tkinter import filedialog

# project — always use full package path
from src.gui.styles.theme import AppTheme as T
from src.gui.widgets.hover_button import RttButton
```

### Page structure template

```python
class MyPage(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color=T.BG_DARK, corner_radius=0, **kwargs)
        self._build()

    # ── builders (one private method per card / section) ────────
    def _build(self):
        self._build_header_card()
        self._build_content_card()
        self._build_bottom_bar()

    def _build_header_card(self): ...
    def _build_content_card(self): ...
    def _build_bottom_bar(self): ...

    # ── event handlers ───────────────────────────────────────────
    def _on_browse(self): ...
    def _on_start(self): ...

    # ── theme refresh hook ────────────────────────────────────────
    def _on_theme_refresh(self) -> None:
        """Called by ThemeManager after a live theme switch."""
        ...
```

### Background threads

All heavy I/O (reading PDFs, Excel, copying files) must run in a
`threading.Thread` to keep the GUI responsive.

```python
def _start_process(self):
    self._start_btn.configure(state="disabled")
    threading.Thread(target=self._run_worker, daemon=True).start()

def _run_worker(self):
    try:
        result = do_heavy_work()
        self.after(0, self._on_done, result)      # ← always marshal back to main thread
    except Exception as exc:
        self.after(0, self._on_error, str(exc))

def _on_done(self, result): ...
def _on_error(self, msg): ...
```

> **Rule:** Never touch a tkinter widget from a background thread.
> Use `widget.after(0, callback, *args)` to post work back to the main thread.

### Card layout pattern

```python
card = ctk.CTkFrame(
    self,
    corner_radius=T.CARD_CORNER,
    fg_color=T.BG_CARD,
    border_width=1,
    border_color=T.BORDER_COLOR,
)
card.pack(fill="x", padx=30, pady=(0, 15))
```

### Bottom action bar pattern

```python
bottom = ctk.CTkFrame(
    self,
    corner_radius=T.CARD_CORNER,
    fg_color=T.BG_CARD,
    border_width=1,
    border_color=T.BORDER_COLOR,
)
bottom.pack(fill="x", side="bottom", padx=30, pady=(0, 20))

btn_row = ctk.CTkFrame(bottom, fg_color="transparent")
btn_row.pack(fill="x", padx=20, pady=(0, 14))

RttButton(btn_row, text="Start", fg_color=T.ACCENT_SUCCESS,
          hover_color="#00c853", ...).pack(side="right")
```

---

## 10. Dependencies

| Package | Min version | Purpose |
|---|---|---|
| `customtkinter` | 5.2.1 | Modern themed tkinter widgets |
| `PyPDF2` | 3.0.1 | Read / split / merge PDFs |
| `pdfplumber` | 0.10.3 | Extract text and tables from PDFs |
| `reportlab` | 4.1.0 | Generate PDF reports |
| `openpyxl` | 3.1.2 | Read / write `.xlsx` files |
| `xlrd` | 2.0.1 | Read legacy `.xls` files |
| `pandas` | 2.0.3 | Data manipulation + Excel I/O |
| `Pillow` | 10.0.0 | Image handling |

Install all: `pip install -r requirements.txt`

---

## 11. Common Pitfalls

| Pitfall | ✅ Correct approach |
|---|---|
| Hardcoding a hex colour in a widget | Use `T.ACCENT_PRIMARY` etc. |
| Adding a colour only to `DARK` dict | Add it to **both** `LIGHT` and `DARK` dicts |
| Using `ctk.CTkButton` directly | Use `RttButton` so hover text works |
| Updating a widget inside a thread | Use `widget.after(0, fn)` to marshal to main thread |
| Creating a `CTkToplevel` as a bare canvas host | Use `tk.Toplevel` — CTkToplevel injects an internal frame that covers the canvas |
| Adding a sidebar item without a page | Register a `PlaceholderPage` at minimum |
| Forgetting `_on_theme_refresh` | Implement it if your page has dynamic list items or manually coloured widgets |
| Calling `root.deiconify()` early | Only call it inside `_finish_build()` after splash closes |

---

## 12. Versioning Policy

RTT uses **Semantic Versioning** with three numeric segments: `MAJOR.MINOR.PATCH`

| Change type | What qualifies | Version bump |
|---|---|---|
| **Patch** (x.x.Z) | Bug fixes, typo corrections, minor UI tweaks, config / doc updates | `0.0.1` |
| **Minor** (x.Y.0) | New features, new widgets, new pages, theme overhauls, animation enhancements — backward-compatible | `0.1.0` |
| **Major** (X.0.0) | Breaking changes, full architectural refactor, removal of existing features, **logic changes, major code restructuring** | `1.0.0` |

### Rules every contributor must follow

1. **Every PR / commit that ships to `main` must bump the version** in all three
   places: `APP_VERSION` constant (see below), `CHANGELOG.md`, and `README.md`.

2. **Update `CHANGELOG.md`** — add a new `## vX.Y.Z — YYYY-MM-DD` block at the
   top of the file describing what was Added / Changed / Fixed / Removed.

3. **Version string locations** — keep these three in sync:
   - `src/gui/splash.py` — footer label: `text="vX.Y.Z"`
   - `src/gui/widgets/sidebar.py` — bottom label: `text="vX.Y.Z"`
   - `README.md` — `**Current version: vX.Y.Z**` line

4. **Do not skip versions.** If two patches and one minor feature land together,
   bump to the minor version only (e.g. `1.2.0` → `1.3.0`, not `1.2.2` then
   `1.3.0`).

### Quick decision guide

```
Is it a docs / comment / config change only?     → Patch  (x.x.Z)
Is it a new widget, page, or feature?             → Minor  (x.Y.0)
Does it change business logic or core algorithms? → Major  (X.0.0)
Is it a large code restructure / refactor?        → Major  (X.0.0)
Does it break something that worked before?       → Major  (X.0.0)
Is it a bug fix with no behaviour change?         → Patch  (x.x.Z)
Is it a visual / UX improvement to an existing
  feature (new animation, colour, layout tweak)?  → Minor  (x.Y.0)
```

### Current version: v1.3.4

See [CHANGELOG.md](CHANGELOG.md) for the full history.
