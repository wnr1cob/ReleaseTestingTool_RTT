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
    SIDEBAR_BTN_ACTIVE_BG = "#0f3460"

    # ── Borders / Dividers ───────────────────────────────────────
    BORDER_COLOR = "#233554"
    BORDER_GLOW = "#00d4ff"

    # ── Progress Bar ─────────────────────────────────────────────
    PROGRESS_BG = "#233554"
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

    # ── Sidebar Menu Items (label, icon_char) ────────────────────
    MENU_ITEMS = [
        ("Dashboard",    "📊"),
        ("PDF Analyzer", "📄"),
        ("Excel Tools",  "📗"),
        ("Folder Mgmt",  "📁"),
        ("Reports",      "📈"),
        ("Settings",     "⚙️"),
    ]
