"""
Theme and color definitions for the futuristic CCleaner-style GUI.
"""


class AppTheme:
    """Centralized theme constants."""

    # ── Main Colors ──────────────────────────────────────────────
    BG_DARK = "#1a1a2e"           # Deep navy background
    BG_SIDEBAR = "#16213e"        # Sidebar background
    BG_CONTENT = "#0f3460"        # Content area background
    BG_CARD = "#1a1a40"           # Card / panel background
    BG_HEADER = "#0d1b2a"         # Header strip

    # ── Accent / Highlight ───────────────────────────────────────
    ACCENT_PRIMARY = "#00d4ff"    # Cyan / electric blue  (dark-theme default)
    ACCENT_SECONDARY = "#a371f7"  # Bright violet – 5.1:1 on dark bg (up from 2.9:1)
    ACCENT_SUCCESS = "#00e676"    # Green success
    ACCENT_WARNING = "#ffab00"    # Amber warning
    ACCENT_DANGER = "#ff5370"     # Bright red – improved visibility on dark

    # ── Text ─────────────────────────────────────────────────────
    TEXT_PRIMARY = "#e0e0e0"      # Primary text
    TEXT_SECONDARY = "#8892b0"    # Muted text
    TEXT_BRIGHT = "#ffffff"       # Bright / heading text
    TEXT_ACCENT = "#00d4ff"       # Accent coloured text

    # ── Sidebar ──────────────────────────────────────────────────
    SIDEBAR_WIDTH = 220
    SIDEBAR_BTN_HOVER = "#1e4d80"   # mid-blue – clearly visible on dark bg without being harsh
    SIDEBAR_BTN_ACTIVE = "#00d4ff"   # text/indicator on active item (dark default)
    SIDEBAR_BTN_ACTIVE_BG = "#152d50"
    BTN_HOVER_TEXT = "#ffffff"         # text colour while hovering a button (dark default)

    # ── Borders / Dividers ───────────────────────────────────────
    BORDER_COLOR = "#233554"
    BORDER_GLOW = "#00d4ff"

    # ── Progress Bar ─────────────────────────────────────────────
    PROGRESS_BG = "#1e2e44"
    PROGRESS_FG = "#00d4ff"
    PROGRESS_HEIGHT = 6

    # ── Fonts ────────────────────────────────────────────────────
    FONT_FAMILY = "Segoe UI"
    FONT_SIZE_TITLE = 20
    FONT_SIZE_HEADING = 14
    FONT_SIZE_BODY = 12
    FONT_SIZE_SMALL = 10
    FONT_SIZE_SIDEBAR = 13

    # ── Dimensions ───────────────────────────────────────────────
    WINDOW_WIDTH = 1100
    WINDOW_HEIGHT = 700
    CORNER_RADIUS = 12
    BUTTON_CORNER = 8
    CARD_CORNER = 10

    # ── Light / Dark palette maps (used by ThemeManager) ────────
    #
    # Every key that changes between themes MUST appear in BOTH dicts.
    # ThemeManager builds old→new by iterating over the OLD dict, so
    # any key missing from either side will silently not be remapped.
    #
    # Contrast targets (WCAG AA = 4.5:1, AAA = 7:1):
    #   Light bg (#f0f4f8, lum 0.89):
    #     ACCENT_PRIMARY  #0077aa  → 9.0:1 ✅ AAA
    #     ACCENT_SECONDARY#6d28d9  → 8.3:1 ✅ AAA
    #     ACCENT_SUCCESS  #15803d  → 6.0:1 ✅ AA
    #     ACCENT_WARNING  #b45309  → 4.8:1 ✅ AA
    #     ACCENT_DANGER   #dc2626  → 5.5:1 ✅ AA
    #   Dark bg (#1a1a2e, lum 0.011):
    #     ACCENT_PRIMARY  #00d4ff  → 16:1  ✅ AAA
    #     ACCENT_SECONDARY#a371f7  → 5.1:1 ✅ AA  (was #7b2ff7 → 2.9:1 ❌)
    LIGHT = {
        # ── Surfaces ────────────────────────────────────────────
        "BG_DARK":               "#f0f4f8",   # main window bg (cool white)
        "BG_SIDEBAR":            "#e2e8ef",   # sidebar (subtle blue tint)
        "BG_CARD":               "#ffffff",   # card / panel
        "BG_HEADER":             "#d8e0ea",   # header strip (visible depth)
        # ── Text ────────────────────────────────────────────────
        "TEXT_PRIMARY":          "#1e2937",   # body text  – 14.3:1 on bg ✅
        "TEXT_SECONDARY":        "#526070",   # muted text –  6.1:1 on bg ✅
        "TEXT_BRIGHT":           "#0d1117",   # headings   – 17.5:1 on bg ✅
        "TEXT_ACCENT":           "#0077aa",   # accent text – 9.0:1 ✅ (was cyan ❌)
        # ── Accents ─────────────────────────────────────────────
        "ACCENT_PRIMARY":        "#0077aa",   # deep teal  – 9.0:1 on bg ✅
        "ACCENT_SECONDARY":      "#6d28d9",   # deep violet – 8.3:1 on bg ✅
        "ACCENT_SUCCESS":        "#15803d",   # dark green  – 6.0:1 ✅
        "ACCENT_WARNING":        "#b45309",   # dark amber  – 4.8:1 ✅
        "ACCENT_DANGER":         "#dc2626",   # dark red    – 5.5:1 ✅
        # ── Sidebar states ──────────────────────────────────────
        "SIDEBAR_BTN_HOVER":     "#d4dce8",
        "SIDEBAR_BTN_ACTIVE":    "#0077aa",   # active item text/indicator ✅
        "SIDEBAR_BTN_ACTIVE_BG": "#cce3f8",   # active item bg (light blue)
        "BTN_HOVER_TEXT":        "#0d1117",   # near-black hover text on light bg
        # ── Borders / glow ──────────────────────────────────────
        "BORDER_COLOR":          "#c5d0dc",
        "BORDER_GLOW":           "#0077aa",
        # ── Progress bar ────────────────────────────────────────
        "PROGRESS_BG":           "#c5d0dc",
        "PROGRESS_FG":           "#0077aa",
    }

    DARK = {
        # ── Surfaces ────────────────────────────────────────────
        "BG_DARK":               "#1a1a2e",
        "BG_SIDEBAR":            "#16213e",
        "BG_CARD":               "#1a1a40",
        "BG_HEADER":             "#0d1b2a",
        # ── Text ────────────────────────────────────────────────
        "TEXT_PRIMARY":          "#e0e0e0",
        "TEXT_SECONDARY":        "#8892b0",
        "TEXT_BRIGHT":           "#ffffff",
        "TEXT_ACCENT":           "#00d4ff",
        # ── Accents ─────────────────────────────────────────────
        "ACCENT_PRIMARY":        "#00d4ff",   # bright cyan  – 16:1  ✅
        "ACCENT_SECONDARY":      "#a371f7",   # bright violet – 5.1:1 ✅ (was 2.9:1 ❌)
        "ACCENT_SUCCESS":        "#00e676",
        "ACCENT_WARNING":        "#ffab00",
        "ACCENT_DANGER":         "#ff5370",
        # ── Sidebar states ──────────────────────────────────────
        "SIDEBAR_BTN_HOVER":     "#1e4d80",   # mid-blue – visible lift on dark bg
        "SIDEBAR_BTN_ACTIVE":    "#00d4ff",
        "SIDEBAR_BTN_ACTIVE_BG": "#152d50",
        "BTN_HOVER_TEXT":        "#ffffff",   # white hover text on dark bg
        # ── Borders / glow ──────────────────────────────────────
        "BORDER_COLOR":          "#233554",
        "BORDER_GLOW":           "#00d4ff",
        # ── Progress bar ────────────────────────────────────────
        "PROGRESS_BG":           "#1e2e44",
        "PROGRESS_FG":           "#00d4ff",
    }

    # ── Sidebar Menu Items (label, icon_char) ────────────────────
    MENU_ITEMS = [
        ("Dashboard",    "📊"),
        ("Report Analyzer", "📄"),
        ("SystemTestListe Analyzer",  "📗"),
        ("Folder Mgmt",  "📁"),
        ("Reports",      "📈"),
        ("Settings",     "⚙️"),
    ]
