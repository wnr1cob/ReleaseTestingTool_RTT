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
from src.gui.pages.settings import SettingsPage
from src.gui.splash import SplashScreen
from src.utils.theme_manager import ThemeManager


class MainWindow:
    """Top-level application window."""

    def __init__(self):
        # ── Load and apply saved theme BEFORE any widget is created ─
        self._theme_mgr = ThemeManager()
        saved_theme = self._theme_mgr.load()
        self._theme_mgr.apply(saved_theme)

        # ── customtkinter global appearance ─────────────────────
        ctk.set_default_color_theme("blue")

        self.root = ctk.CTk()
        self.root.title("Release Testing Tool")
        self.root.minsize(900, 550)
        self.root.configure(fg_color=T.BG_DARK)

        # Hide immediately — prevents any flash before build is complete
        self.root.withdraw()

        # Try to set window icon (ignore if file missing)
        try:
            self.root.iconbitmap("resources/icons/app_icon.ico")
        except Exception:
            pass

        self._pages: dict[int, ctk.CTkFrame] = {}
        self._current_page: ctk.CTkFrame | None = None
        self._splash: SplashScreen | None = None

        # Give Tk a single tick to settle before showing the splash
        self.root.after(50, self._start_build)

    # ── splash-driven incremental build ─────────────────────────
    def _start_build(self):
        """Show splash then kick off incremental page building."""
        self._splash = SplashScreen(self.root)
        self.root.after(20, self._build_step, 0)

    def _build_step(self, step: int):
        """Build one component per call so the splash can update."""
        s = self._splash

        try:
            if step == 0:
                s.set_progress(0.10, "Initializing UI…")
                self._build_shell()
                self.root.after(20, self._build_step, 1)

            elif step == 1:
                s.set_progress(0.35, "Loading Dashboard…")
                self._pages[0] = DashboardPage(self._content)
                self.root.after(20, self._build_step, 2)

            elif step == 2:
                s.set_progress(0.60, "Loading PDF Analyzer…")
                self._pages[1] = PDFAnalyzerPage(self._content)
                self.root.after(20, self._build_step, 3)

            elif step == 3:
                s.set_progress(0.80, "Loading System Test List…")
                self._pages[2] = SystemTestListePage(self._content)
                self.root.after(20, self._build_step, 4)

            elif step == 4:
                s.set_progress(0.95, "Loading remaining pages…")
                self._pages[3] = PlaceholderPage(self._content, title="Folder Management", icon="")
                self._pages[4] = PlaceholderPage(self._content, title="Reports", icon="")
                self._pages[5] = SettingsPage(self._content, theme_mgr=self._theme_mgr)
                self.root.after(20, self._build_step, 5)

            elif step == 5:
                s.set_progress(1.0, "Ready!")
                self.root.after(250, self._finish_build)

        except KeyboardInterrupt:
            # Python 3.14 raises KeyboardInterrupt through tkinter callbacks;
            # swallow it and keep the build chain alive.
            self.root.after(20, self._build_step, step)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            # Don't leave the user stuck on the splash — finish anyway
            s.set_progress(1.0, f"Warning: {exc}")
            self.root.after(800, self._finish_build)

    def _finish_build(self):
        """Close splash, reveal and maximise the main window."""
        if self._splash:
            self._splash.close()
            self._splash = None
        self._show_page(0)
        self.root.deiconify()
        self.root.state("zoomed")

    # ── shell construction (sidebar / header / content) ─────────
    def _build_shell(self):
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
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
