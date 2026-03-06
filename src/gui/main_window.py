"""
Main application window – CCleaner-style futuristic layout.

Layout
──────
┌──────────┬──────────────────────────────────────────────┐
│          │  Header bar                                  │
│ Sidebar  ├──────────────────────────────────────────────┤
│          │  Content area (swapped per page)             │
│          │                                              │
│          │                                              │
│          ├──────────────────────────────────────────────┤
│          │  Status bar                                  │
└──────────┴──────────────────────────────────────────────┘
"""
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T
from src.gui.widgets.sidebar import Sidebar
from src.gui.widgets.status_bar import StatusBar
from src.gui.pages.dashboard import DashboardPage
from src.gui.pages.placeholder import PlaceholderPage
from src.gui.pages.pdf_analyzer import PDFAnalyzerPage
from src.gui.pages.excel_tools import ExcelToolsPage
from src.gui.pages.systemtestliste_analyzer import SystemTestListePage


class MainWindow:
    """Top-level application window."""

    def __init__(self):
        # ── customtkinter global appearance ─────────────────────
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("⚡ Release Testing Tool")
        self.root.minsize(900, 550)
        self.root.configure(fg_color=T.BG_DARK)

        # Dynamically set geometry to the full screen resolution
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"{screen_w}x{screen_h}+0+0")
        self.root.state("zoomed")

        # Try to set window icon (ignore if file missing)
        try:
            self.root.iconbitmap("resources/icons/app_icon.ico")
        except Exception:
            pass

        self._pages: dict[int, ctk.CTkFrame] = {}
        self._current_page: ctk.CTkFrame | None = None

        self._build_layout()
        self._show_page(0)  # start on Dashboard

        # Kick off a demo progress animation after the window renders
        self.root.after(600, self._pages[0].demo_progress)

    # ── layout construction ─────────────────────────────────────
    def _build_layout(self):
        # Sidebar (left)
        self._sidebar = Sidebar(self.root, on_select_callback=self._show_page)
        self._sidebar.pack(side="left", fill="y")

        # Right-hand container
        right = ctk.CTkFrame(self.root, fg_color=T.BG_DARK, corner_radius=0)
        right.pack(side="right", fill="both", expand=True)

        # Header bar
        header = ctk.CTkFrame(right, height=48, corner_radius=0, fg_color=T.BG_HEADER)
        header.pack(fill="x")
        header.pack_propagate(False)

        self._header_title = ctk.CTkLabel(
            header,
            text="Dashboard",
            font=(T.FONT_FAMILY, T.FONT_SIZE_HEADING, "bold"),
            text_color=T.TEXT_BRIGHT,
        )
        self._header_title.pack(side="left", padx=20)

        # Accent line under header
        ctk.CTkFrame(right, height=2, corner_radius=0, fg_color=T.ACCENT_PRIMARY).pack(fill="x")

        # Content area
        self._content = ctk.CTkFrame(right, fg_color=T.BG_DARK, corner_radius=0)
        self._content.pack(fill="both", expand=True)

        # Status bar (bottom)
        self._status_bar = StatusBar(right)
        self._status_bar.pack(fill="x", side="bottom")

        # Pre-build pages
        self._pages[0] = DashboardPage(self._content)
        self._pages[1] = PDFAnalyzerPage(self._content)
        self._pages[2] = SystemTestListePage(self._content)

        page_defs = [
            (3, "Folder Management", "📁"),
            (4, "Reports", "📈"),
            (5, "Settings", "⚙️"),
        ]
        for idx, title, icon in page_defs:
            self._pages[idx] = PlaceholderPage(self._content, title=title, icon=icon)

    # ── page switching ──────────────────────────────────────────
    def _show_page(self, index: int):
        if self._current_page is not None:
            self._current_page.pack_forget()

        page = self._pages.get(index)
        if page:
            page.pack(fill="both", expand=True)
            self._current_page = page

        # update header text
        labels = [item[0] for item in T.MENU_ITEMS]
        if index < len(labels):
            self._header_title.configure(text=labels[index])
            self._status_bar.set_status(f"Viewing: {labels[index]}")

    # ── run ─────────────────────────────────────────────────────
    def run(self):
        """Launch the main event loop."""
        self.root.mainloop()
