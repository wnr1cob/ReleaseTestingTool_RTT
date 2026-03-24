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
from src.gui.pages.stl_presets import STLPresetsPage
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
        self.root.after(80, self._build_step, 0)

    def _build_step(self, step: int):
        """
        Build one component per call so the splash can update.
        Each step fires after a ~90 ms delay, giving the event loop
        time to repaint the animated splash between steps.
        """
        s     = self._splash
        DELAY = 90   # ms between steps — keeps animation smooth

        try:
            if step == 0:
                s.set_progress(0.03, "Reading configuration files")
                self.root.after(DELAY, self._build_step, 1)

            elif step == 1:
                s.set_progress(0.08, "Applying theme palette")
                self.root.after(DELAY, self._build_step, 2)

            elif step == 2:
                s.set_progress(0.14, "Initializing layout engine")
                self._build_shell()
                self.root.after(DELAY, self._build_step, 3)

            elif step == 3:
                s.set_progress(0.20, "Building navigation sidebar")
                self.root.after(DELAY, self._build_step, 4)

            elif step == 4:
                s.set_progress(0.27, "Mounting header and content area")
                self.root.after(DELAY, self._build_step, 5)

            elif step == 5:
                s.set_progress(0.34, "Loading Dashboard module")
                self._pages[0] = DashboardPage(self._content)
                self.root.after(DELAY, self._build_step, 6)

            elif step == 6:
                s.set_progress(0.44, "Registering event handlers")
                self.root.after(DELAY, self._build_step, 7)

            elif step == 7:
                s.set_progress(0.53, "Loading Report Analyzer module")
                self._pages[1] = PDFAnalyzerPage(self._content)
                self.root.after(DELAY, self._build_step, 8)

            elif step == 8:
                s.set_progress(0.61, "Initializing file I/O handlers")
                self.root.after(DELAY, self._build_step, 9)

            elif step == 9:
                s.set_progress(0.70, "Loading SystemTestListe Analyzer")
                self._pages[2] = SystemTestListePage(self._content)
                self.root.after(DELAY, self._build_step, 10)

            elif step == 10:
                s.set_progress(0.78, "Loading support modules")
                self._pages[3] = PlaceholderPage(self._content, title="Folder Management", icon="")
                self._pages[4] = PlaceholderPage(self._content, title="Reports", icon="")
                self.root.after(DELAY, self._build_step, 11)

            elif step == 11:
                s.set_progress(0.84, "Loading Presets module")
                self._pages[5] = STLPresetsPage(self._content)
                self.root.after(DELAY, self._build_step, 12)

            elif step == 12:
                s.set_progress(0.91, "Loading Settings module")
                self._pages[6] = SettingsPage(self._content, theme_mgr=self._theme_mgr)
                self.root.after(DELAY, self._build_step, 13)

            elif step == 13:
                s.set_progress(0.93, "Verifying component integrity")
                self.root.after(DELAY, self._build_step, 14)

            elif step == 14:
                s.set_progress(0.98, "Finalizing workspace")
                self.root.after(DELAY, self._build_step, 15)

            elif step == 15:
                s.set_progress(1.0, "Workspace ready")
                # Guarantee the splash is shown for at least 3.4 s total —
                # this gives users time to read the loading log.
                s.ensure_min_display(7500, self._finish_build)

        except KeyboardInterrupt:
            self.root.after(DELAY, self._build_step, step)
        except Exception as exc:
            import traceback
            traceback.print_exc()
            s.set_progress(1.0, f"Warning: {exc}")
            s.ensure_min_display(1200, self._finish_build)

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
