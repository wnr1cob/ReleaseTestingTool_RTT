"""
Splash screen shown while the main window builds.

Professional animated splash with:
  • Theme-aware palette (reads saved theme from settings.json)
  • Canvas particle-field background animation (~33 fps)
  • Accent border lines + corner glow dots
  • Pulsing title glow via color oscillation
  • Shimmer / highlight sweep on the progress bar
  • Animated loading dots on the status message
  • Percentage readout
  • Photoshop-style scrolling loading log (history of completed steps)
  • Guaranteed minimum display time via ensure_min_display()
  • Alpha fade-in on open, fade-out on close
"""
from __future__ import annotations

import ctypes
import ctypes.wintypes
import json
import math
import random
import time
from pathlib import Path
import tkinter as tk
import customtkinter as ctk
from src.gui.styles.theme import AppTheme as T

# ── icon path (relative to this file) ─────────────────────────────────────────
_ICON_PATH = Path(__file__).parent / "icon" / "icon.ico"

# ── settings path ─────────────────────────────────────────────────────────────
_SETTINGS_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "settings.json"
)


def _get_largest_monitor_rect() -> tuple[int, int, int, int] | None:
    """
    Return (left, top, right, bottom) of the monitor with the largest pixel
    area using the Win32 EnumDisplayMonitors API.
    Returns None on non-Windows platforms or if enumeration fails.
    """
    try:
        monitors: list[tuple[int, int, int, int]] = []

        _MONITORENUMPROC = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            ctypes.c_void_p,                           # HMONITOR
            ctypes.c_void_p,                           # HDC
            ctypes.POINTER(ctypes.wintypes.RECT),      # lprcMonitor
            ctypes.c_void_p,                           # LPARAM
        )

        def _cb(hMon, hdcMon, lprc, data):
            r = lprc.contents
            monitors.append((r.left, r.top, r.right, r.bottom))
            return 1   # TRUE – continue enumeration

        ctypes.windll.user32.EnumDisplayMonitors(
            None, None, _MONITORENUMPROC(_cb), 0
        )

        if monitors:
            return max(monitors, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))
    except Exception:
        pass
    return None


def _load_saved_theme() -> str:
    """Return 'dark' or 'light' from settings.json (default: dark)."""
    try:
        data = json.loads(_SETTINGS_PATH.read_text(encoding="utf-8"))
        t = data.get("theme", "dark").lower()
        return t if t in ("light", "dark") else "dark"
    except Exception:
        return "dark"


# ── per-theme colour palettes ──────────────────────────────────────────────────
_PALETTE: dict[str, dict[str, str]] = {
    "dark": {
        "bg":          "#0d1117",
        "panel":       "#131922",
        "border":      "#00d4ff",
        "accent":      "#00d4ff",
        "accent2":     "#7b2ff7",
        "text_bright": "#ffffff",
        "text_sub":    "#8892b0",
        "bar_track":   "#1e2d40",
        "particle":    "#00d4ff",
        "badge_fg":    "#0d1117",
        "log_bg":      "#090d12",   # darker console bg for log panel
    },
    "light": {
        "bg":          "#f0f4f8",
        "panel":       "#ffffff",
        "border":      "#0077aa",
        "accent":      "#0077aa",
        "accent2":     "#6d28d9",
        "text_bright": "#0d1117",
        "text_sub":    "#526070",
        "bar_track":   "#c5d0dc",
        "particle":    "#0077aa",
        "badge_fg":    "#ffffff",
        "log_bg":      "#dce5ef",   # console-style bg for log panel
    },
}


# ── colour helpers ─────────────────────────────────────────────────────────────
def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _lerp_color(c1: str, c2: str, t: float) -> str:
    """Linear interpolate between two hex colours."""
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    r = int(r1 + (r2 - r1) * t)
    g = int(g1 + (g2 - g1) * t)
    b = int(b1 + (b2 - b1) * t)
    return f"#{r:02x}{g:02x}{b:02x}"


# ── particle class ─────────────────────────────────────────────────────────────
class _Particle:
    """A single drifting dot in the background canvas."""

    def __init__(self, width: int, height: int, color: str, bg: str):
        self.w = width
        self.h = height
        self.color = color
        self.bg    = bg
        self._spawn(initial=True)

    def _spawn(self, initial: bool = False) -> None:
        self.x  = random.uniform(0, self.w)
        self.y  = random.uniform(0, self.h) if initial else self.h + 4
        self.vx = random.uniform(-0.35, 0.35)
        self.vy = random.uniform(-0.55, -0.08)
        self.r  = random.uniform(1.1, 2.6)
        self.alpha = random.uniform(0.25, 0.85)
        self.ttl   = random.randint(150, 450)

    def step(self) -> None:
        self.x += self.vx
        self.y += self.vy
        self.ttl -= 1
        if self.ttl < 70:
            self.alpha = max(0.0, self.alpha - 0.012)
        if self.ttl <= 0 or self.y < -8:
            self._spawn()

    def draw_color(self) -> str:
        """Blend particle colour toward the bg colour by (1-alpha)."""
        pr, pg, pb = _hex_to_rgb(self.color)
        br, bg_, bb = _hex_to_rgb(self.bg)
        a = max(0.0, min(1.0, self.alpha))
        r = int(pr * a + br * (1 - a))
        g = int(pg * a + bg_ * (1 - a))
        b = int(pb * a + bb * (1 - a))
        return f"#{r:02x}{g:02x}{b:02x}"


# ── main splash class ──────────────────────────────────────────────────────────
class SplashScreen:
    """
    Centered, borderless splash window with full animation suite.

    Public API
    ----------
    set_progress(value, message)   — update bar (0.0–1.0) and status text
    close()                        — fade out and destroy
    """

    WIDTH      = 780
    HEIGHT     = 560          # taller to accommodate the loading log
    _TICK_MS   = 30           # ≈ 33 fps
    _N_PARTS   = 64
    _LOG_LINES = 6           # how many log entries are visible at once

    def __init__(self, root: ctk.CTk):
        self._root = root
        self._theme = _load_saved_theme()
        self._pal   = _PALETTE[self._theme]

        # animation state
        self._progress  = 0.0
        self._msg       = "Initializing"
        self._dot_frame = 0
        self._pulse_t   = 0.0
        self._shimmer_x = -60.0
        self._alpha     = 0.0
        self._closing   = False

        # log / timing state
        self._log_entries: list[str]  = []
        self._log_labels:  list[tk.Label] = []
        self._start_ms: float = time.monotonic() * 1000

        # Use plain tk.Toplevel — CTkToplevel injects its own internal frame
        # which sits on top and hides the canvas layer.  tk.Toplevel gives a
        # clean blank window where .place() stacking works exactly as expected.
        win = tk.Toplevel(root)
        win.overrideredirect(True)
        win.configure(bg=self._pal["bg"])
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.attributes("-alpha", 0.0)          # start transparent for fade-in

        # Set taskbar / titlebar icon on the splash window
        try:
            win.iconbitmap(str(_ICON_PATH))
        except Exception:
            pass

        # Set size first, then let Tk settle before reading screen dimensions.
        # Using win.winfo_screen* after update_idletasks gives the correct
        # primary-monitor values even when the root window is still withdrawn.
        win.geometry(f"{self.WIDTH}x{self.HEIGHT}")
        win.update_idletasks()

        # Pick the monitor with the largest pixel area and centre on it.
        # _get_largest_monitor_rect() enumerates all connected monitors via
        # Win32 and returns the bounding rect of the biggest one.
        mon = _get_largest_monitor_rect()
        if mon:
            ml, mt, mr, mb = mon
            x = ml + (mr - ml - self.WIDTH)  // 2
            y = mt + (mb - mt - self.HEIGHT) // 2
        else:
            # Fallback for non-Windows or if enumeration failed
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()
            x  = (sw - self.WIDTH)  // 2
            y  = (sh - self.HEIGHT) // 2
        win.geometry(f"{self.WIDTH}x{self.HEIGHT}+{x}+{y}")

        self._win  = win
        self._particles: list[_Particle] = []
        self._build()
        self._win.after(10, self._tick)
        self._start_ms = time.monotonic() * 1000  # reset after window creates

    # ── UI build ──────────────────────────────────────────────────────────────
    def _build(self) -> None:
        pal = self._pal
        W, H = self.WIDTH, self.HEIGHT

        # ── Layer 0: full-window canvas (bg + particles + accents + border) ──
        self._bg_canvas = tk.Canvas(
            self._win,
            width=W, height=H,
            bg=pal["bg"],
            highlightthickness=0,
        )
        self._bg_canvas.place(x=0, y=0)

        # seed particles with staggered lifetimes
        for _ in range(self._N_PARTS):
            p = _Particle(W, H, pal["particle"], pal["bg"])
            p.ttl = random.randint(1, 450)
            self._particles.append(p)

        # 1-px border rectangle drawn on the canvas (no extra Frame needed)
        self._bg_canvas.create_rectangle(
            0, 0, W - 1, H - 1,
            outline=pal["border"], width=2, fill="",
        )

        # top accent bar
        self._bg_canvas.create_rectangle(
            2, 0, W - 2, 4, fill=pal["accent"], outline="",
        )
        # bottom accent bar (secondary colour)
        self._bg_canvas.create_rectangle(
            2, H - 4, W - 2, H, fill=pal["accent2"], outline="",
        )
        # corner glow dots
        gr = 10
        for cx, cy in ((0, 0), (W, 0), (0, H), (W, H)):
            self._bg_canvas.create_oval(
                cx - gr, cy - gr, cx + gr, cy + gr,
                fill=pal["accent"], outline="",
            )

        # ── Layer 1: solid inner panel (2 px inset so border shows) ──────────
        panel = tk.Frame(self._win, bg=pal["panel"])
        panel.place(x=2, y=2, width=W - 4, height=H - 4)

        # ── Logo row ──────────────────────────────────────────────────────────
        logo_row = tk.Frame(panel, bg=pal["panel"])
        logo_row.pack(pady=(40, 0))

        # TODO: add logo image here when ready

        # App title — fg updated each tick for pulsing glow
        self._title_lbl = tk.Label(
            logo_row,
            text="Release Testing Tool",
            font=("Segoe UI", 30, "bold"),
            fg=pal["text_bright"],
            bg=pal["panel"],
        )
        self._title_lbl.pack()

        # ── Subtitle ──────────────────────────────────────────────────────────
        tk.Label(
            panel,
            text="Test Execution Analysis Suite",
            font=("Segoe UI", 13),
            fg=pal["accent"],
            bg=pal["panel"],
        ).pack(pady=(7, 0))

        # ── Hairline divider ──────────────────────────────────────────────────
        tk.Frame(panel, bg=pal["border"], height=1).pack(
            fill="x", padx=50, pady=(20, 14),
        )

        # ── Animated status message ───────────────────────────────────────────
        self._msg_lbl = tk.Label(
            panel,
            text=self._msg + "...",
            font=("Segoe UI", 11),
            fg=pal["text_sub"],
            bg=pal["panel"],
        )
        self._msg_lbl.pack(pady=(0, 10))

        # ── Custom shimmer progress bar (Canvas-drawn) ────────────────────────
        BAR_W, BAR_H = 640, 9
        bar_host = tk.Frame(panel, bg=pal["panel"])
        bar_host.pack()

        self._bar_cv = tk.Canvas(
            bar_host,
            width=BAR_W, height=BAR_H,
            bg=pal["panel"],
            highlightthickness=0,
        )
        self._bar_cv.pack()
        self._bar_w = BAR_W
        self._bar_h = BAR_H

        # track
        self._bar_cv.create_rectangle(
            0, 0, BAR_W, BAR_H, fill=pal["bar_track"], outline="",
        )
        # fill
        self._bar_fill = self._bar_cv.create_rectangle(
            0, 0, 0, BAR_H, fill=pal["accent"], outline="",
        )
        # shimmer highlight
        self._bar_shimmer = self._bar_cv.create_rectangle(
            0, 0, 0, 0,
            fill=_lerp_color(pal["accent"], "#ffffff", 0.55),
            outline="",
            stipple="gray50",
        )

        # ── Percentage label ──────────────────────────────────────────────────
        self._pct_lbl = tk.Label(
            panel,
            text="0 %",
            font=("Segoe UI", 10),
            fg=pal["text_sub"],
            bg=pal["panel"],
        )
        self._pct_lbl.pack(pady=(5, 0))

        # ── Photoshop-style loading log ───────────────────────────────────────
        log_outer = tk.Frame(
            panel,
            bg=pal["log_bg"],
            bd=0,
            highlightthickness=1,
            highlightbackground=_lerp_color(pal["border"], pal["panel"], 0.7),
        )
        log_outer.pack(fill="x", padx=50, pady=(12, 0))

        # header row inside the log panel
        log_header = tk.Frame(log_outer, bg=pal["log_bg"])
        log_header.pack(fill="x", padx=10, pady=(6, 3))

        tk.Label(
            log_header,
            text="►  Loading log",
            font=("Consolas", 9),
            fg=pal["accent"],
            bg=pal["log_bg"],
        ).pack(side="left")

        # one label per visible log line
        for _ in range(self._LOG_LINES):
            lbl = tk.Label(
                log_outer,
                text="",
                font=("Consolas", 10),
                fg=pal["text_sub"],
                bg=pal["log_bg"],
                anchor="w",
            )
            lbl.pack(fill="x", padx=14, pady=1)
            self._log_labels.append(lbl)

        # bottom padding inside log panel
        tk.Frame(log_outer, bg=pal["log_bg"], height=6).pack()

        # ── Footer ────────────────────────────────────────────────────────────
        foot = tk.Frame(panel, bg=pal["panel"])
        foot.pack(side="bottom", fill="x", pady=(0, 10))

        tk.Label(
            foot,
            text="v3.2.1",
            font=("Segoe UI", 10),
            fg=pal["text_sub"],
            bg=pal["panel"],
        ).pack(side="right", padx=26)

        # Theme indicator dot
        theme_col = pal["accent"] if self._theme == "dark" else pal["accent2"]
        tk.Label(
            foot,
            text=f"\u25cf  {self._theme.title()} Theme",
            font=("Segoe UI", 10),
            fg=theme_col,
            bg=pal["panel"],
        ).pack(side="left", padx=26)

    # ── animation tick ────────────────────────────────────────────────────────
    def _tick(self) -> None:
        try:
            if not self._win.winfo_exists():
                return
        except Exception:
            return

        self._pulse_t   += 0.055
        self._dot_frame += 1
        self._shimmer_x += 4.5

        # ── fade-in ───────────────────────────────────────────────────────────
        if not self._closing and self._alpha < 1.0:
            self._alpha = min(1.0, self._alpha + 0.08)
            try:
                self._win.attributes("-alpha", self._alpha)
            except Exception:
                pass

        # ── fade-out ──────────────────────────────────────────────────────────
        if self._closing:
            self._alpha -= 0.12
            if self._alpha <= 0.0:
                try:
                    self._win.destroy()
                except Exception:
                    pass
                return
            try:
                self._win.attributes("-alpha", max(0.0, self._alpha))
            except Exception:
                pass

        # ── particles ─────────────────────────────────────────────────────────
        self._bg_canvas.delete("particle")
        for p in self._particles:
            p.step()
            r = p.r
            col = p.draw_color()
            self._bg_canvas.create_oval(
                p.x - r, p.y - r, p.x + r, p.y + r,
                fill=col, outline="", tags="particle",
            )

        # ── title pulse (colour oscillation) ──────────────────────────────────
        t_osc = (math.sin(self._pulse_t) + 1.0) / 2.0   # 0 → 1
        title_col = _lerp_color(
            self._pal["text_bright"],
            self._pal["accent"],
            t_osc * 0.38,
        )
        try:
            self._title_lbl.configure(fg=title_col)
        except Exception:
            pass

        # ── animated loading dots ─────────────────────────────────────────────
        dot_count = 1 + (self._dot_frame // 12 % 3)
        try:
            self._msg_lbl.configure(text=self._msg.rstrip(".") + "." * dot_count)
        except Exception:
            pass

        # ── shimmer progress bar ──────────────────────────────────────────────
        fill_w = int(self._progress * self._bar_w)
        if fill_w > 0:
            self._bar_cv.coords(self._bar_fill, 0, 0, fill_w, self._bar_h)
            sh_w = 45
            sx   = int(self._shimmer_x % (fill_w + sh_w)) - sh_w
            sx   = max(0, sx)
            ex   = min(sx + sh_w, fill_w)
            if ex > sx:
                self._bar_cv.coords(self._bar_shimmer, sx, 0, ex, self._bar_h)
            else:
                self._bar_cv.coords(self._bar_shimmer, 0, 0, 0, 0)
        else:
            self._bar_cv.coords(self._bar_fill,    0, 0, 0, self._bar_h)
            self._bar_cv.coords(self._bar_shimmer, 0, 0, 0, 0)

        # reset shimmer sweep when it overtakes fill
        if self._shimmer_x > fill_w + 50:
            self._shimmer_x = -60.0

        # ── schedule next frame ───────────────────────────────────────────────
        try:
            self._win.after(self._TICK_MS, self._tick)
        except Exception:
            pass

    # ── public API ────────────────────────────────────────────────────────────
    def set_progress(self, value: float, message: str = "") -> None:
        """Update the progress bar (0.0 – 1.0) and status message.

        Also appends the message to the loading log automatically.
        """
        self._progress = max(0.0, min(1.0, value))
        if message:
            self._msg = message
            self.log(message)          # auto-populate loading history
        try:
            self._pct_lbl.configure(text=f"{int(self._progress * 100)} %")
        except Exception:
            pass

    def log(self, text: str) -> None:
        """Append a line to the Photoshop-style loading log."""
        if text:
            self._log_entries.append(text)
        self._refresh_log()

    def _refresh_log(self) -> None:
        """Re-render the log label rows with recency-based fading."""
        pal = self._pal
        # Take the last N entries (oldest at top, newest at bottom)
        entries = self._log_entries[-self._LOG_LINES:]
        n       = len(entries)

        # Opacity steps: oldest line is most faded, newest is full brightness
        # Lerp from bg toward text_sub; t=0 most faded, t=1 full
        fade_levels = [0.18, 0.35, 0.52, 0.68, 0.84, 1.0][-self._LOG_LINES:]

        for i, lbl in enumerate(self._log_labels):
            idx = i - (self._LOG_LINES - n)  # index into entries
            try:
                if idx < 0 or idx >= n:
                    lbl.configure(text="")
                else:
                    fade = fade_levels[i] if i < len(fade_levels) else 1.0
                    color = _lerp_color(pal["log_bg"], pal["text_sub"], fade)
                    # Newest line gets a small arrow prefix in accent
                    if idx == n - 1:
                        lbl.configure(
                            text=f"  ▶  {entries[idx]}",
                            fg=_lerp_color(pal["log_bg"], pal["accent"], 0.9),
                        )
                    else:
                        lbl.configure(
                            text=f"      {entries[idx]}",
                            fg=color,
                        )
            except Exception:
                pass

    def ensure_min_display(self, min_ms: int, callback) -> None:
        """
        Schedule callback after at least min_ms milliseconds have elapsed
        since the splash window was created.  If the build finished faster
        than min_ms, the remaining delay is added so the user has time to
        read the loading log.  If already past min_ms, fires immediately.
        """
        elapsed   = (time.monotonic() * 1000) - self._start_ms
        remaining = max(0, int(min_ms - elapsed))
        try:
            self._win.after(remaining, callback)
        except Exception:
            callback()

    def close(self) -> None:
        """Fade out and destroy the splash window."""
        self._closing = True
