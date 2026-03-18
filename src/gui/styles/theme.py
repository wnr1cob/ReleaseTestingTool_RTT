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
    ACCENT_PRIMARY = "#00d4ff"    # Cyan / electric blue
    ACCENT_SECONDARY = "#7b2ff7"  # Purple accent
    ACCENT_SUCCESS = "#00e676"    # Green success
    ACCENT_WARNING = "#ffab00"    # Amber warning
    ACCENT_DANGER = "#ff1744"     # Red danger

    # ── Text ─────────────────────────────────────────────────────
    TEXT_PRIMARY = "#e0e0e0"      # Primary text
    TEXT_SECONDARY = "#8892b0"    # Muted text
    TEXT_BRIGHT = "#ffffff"       # Bright / heading text
    TEXT_ACCENT = "#00d4ff"       # Accent coloured text

    # ── Sidebar ──────────────────────────────────────────────────
    SIDEBAR_WIDTH = 220
    SIDEBAR_BTN_HOVER = "#1b3a5c"
    SIDEBAR_BTN_ACTIVE = "#00d4ff"
    SIDEBAR_BTN_ACTIVE_BG = "#152d50"

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
    LIGHT = {
        "BG_DARK":               "#f0f2f5",
        "BG_SIDEBAR":            "#e2e6ea",
        "BG_CARD":               "#ffffff",
        "BG_HEADER":             "#dde1e7",
        "TEXT_PRIMARY":          "#1a1a2e",
        "TEXT_SECONDARY":        "#555b6e",
        "TEXT_BRIGHT":           "#000000",
        "BORDER_COLOR":          "#c9cdd4",
        "SIDEBAR_BTN_HOVER":     "#d0d4da",
        "SIDEBAR_BTN_ACTIVE_BG": "#dce3f0",
        "PROGRESS_BG":           "#d4d8de",
    }

    DARK = {
        "BG_DARK":               "#1a1a2e",
        "BG_SIDEBAR":            "#16213e",
        "BG_CARD":               "#1a1a40",
        "BG_HEADER":             "#0d1b2a",
        "TEXT_PRIMARY":          "#e0e0e0",
        "TEXT_SECONDARY":        "#8892b0",
        "TEXT_BRIGHT":           "#ffffff",
        "BORDER_COLOR":          "#233554",
        "SIDEBAR_BTN_HOVER":     "#1b3a5c",
        "SIDEBAR_BTN_ACTIVE_BG": "#152d50",
        "PROGRESS_BG":           "#1e2e44",
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
