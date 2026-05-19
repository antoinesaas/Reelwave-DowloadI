"""JobCard — animated download progress card."""
from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from typing import TYPE_CHECKING

from ui.theme import (
    SURFACE, BORDER, TEXT_1, TEXT_2, TEXT_3,
    SUCCESS, ERROR, WARNING,
    FONT_BODY, FONT_SECONDARY, FONT_SECTION, font,
)

if TYPE_CHECKING:
    from core.downloader import DownloadJob


class JobCard(tk.Frame):
    """A single card representing one download job."""

    BAR_H = 4
    BAR_RADIUS = 2
    PULSE_FRAMES = [1.0, 0.6, 0.3, 0.6, 1.0]

    def __init__(self, parent: tk.Widget, job: "DownloadJob", **kw):
        super().__init__(parent, bg=SURFACE, **kw)
        self.job = job
        self._pulse_idx = 0
        self._pulse_after: str | None = None
        self._build()
        self.bind("<Button-1>", self._on_click)
        self._update_display()

    # ── Build ──────────────────────────────────────────────────────────────
    def _build(self) -> None:
        self.configure(
            bd=1, relief="flat",
            padx=16, pady=14,
            highlightbackground=BORDER,
            highlightthickness=1,
            highlightcolor=BORDER,
        )

        # Top row
        top = tk.Frame(self, bg=SURFACE)
        top.pack(fill="x")

        # Platform badge
        self._badge = tk.Label(
            top, text=self.job.platform[0].upper(),
            font=font(11, "bold"),
            bg=BORDER, fg=TEXT_1,
            width=2, height=1,
        )
        self._badge.pack(side="left", padx=(0, 10))

        # URL / title label
        self._title_lbl = tk.Label(
            top, text=self._short_url(),
            font=FONT_BODY, bg=SURFACE, fg=TEXT_1,
            anchor="w",
        )
        self._title_lbl.pack(side="left", fill="x", expand=True)

        # Quality tag
        self._quality_lbl = tk.Label(
            top, text=self.job.quality,
            font=FONT_SECONDARY, bg=SURFACE, fg=TEXT_2,
        )
        self._quality_lbl.pack(side="left", padx=(8, 6))

        # Status icon
        self._status_lbl = tk.Label(
            top, text="⏳",
            font=font(16), bg=SURFACE, fg=TEXT_3,
        )
        self._status_lbl.pack(side="left")

        # Progress bar container
        bar_frame = tk.Frame(self, bg=SURFACE)
        bar_frame.pack(fill="x", pady=(10, 4))

        self._bar_bg = tk.Canvas(
            bar_frame, height=self.BAR_H, bg=BORDER,
            bd=0, highlightthickness=0,
        )
        self._bar_bg.pack(fill="x")

        # Meta row
        meta = tk.Frame(self, bg=SURFACE)
        meta.pack(fill="x")

        self._meta_lbl = tk.Label(
            meta, text="",
            font=FONT_SECONDARY, bg=SURFACE, fg=TEXT_2,
            anchor="w",
        )
        self._meta_lbl.pack(side="left")

        self._bind_children(self)

    def _bind_children(self, widget: tk.Widget) -> None:
        widget.bind("<Button-1>", self._on_click)
        for child in widget.winfo_children():
            self._bind_children(child)

    # ── Helpers ────────────────────────────────────────────────────────────
    def _short_url(self) -> str:
        title = self.job.title or self.job.url
        return title[:58] + "…" if len(title) > 58 else title

    # ── Public update ──────────────────────────────────────────────────────
    def refresh(self) -> None:
        """Called from the main thread whenever job state changes."""
        self._update_display()

    # ── Internal rendering ─────────────────────────────────────────────────
    def _update_display(self) -> None:
        status = self.job.status

        # Title / URL
        self._title_lbl.configure(text=self._short_url())

        # Status icon & colour
        icons = {
            "pending":     ("⏳", TEXT_3),
            "downloading": ("↓",  TEXT_1),
            "done":        ("✓",  SUCCESS),
            "error":       ("✕",  ERROR),
            "cancelled":   ("◌",  TEXT_3),
        }
        icon, colour = icons.get(status, ("⏳", TEXT_3))
        self._status_lbl.configure(text=icon, fg=colour)

        # Progress bar
        self._draw_bar()

        # Meta info
        if status == "downloading":
            parts = []
            if self.job.speed:
                parts.append(self.job.speed)
            if self.job.eta:
                parts.append(f"ETA {self.job.eta}")
            pct = int(self.job.progress * 100)
            parts.append(f"{pct}%")
            self._meta_lbl.configure(text="  ·  ".join(parts), fg=TEXT_2)
        elif status == "done":
            size = f"{self.job.size_mb:.1f} MB" if self.job.size_mb else ""
            dur  = self._fmt_dur(self.job.duration_sec)
            info = "  ·  ".join(filter(None, [size, dur, "Terminé"]))
            self._meta_lbl.configure(text=info, fg=TEXT_2)
        elif status == "error":
            self._meta_lbl.configure(text=self.job.error or "Erreur", fg=ERROR)
        else:
            self._meta_lbl.configure(text="En attente…", fg=TEXT_3)

        # Pulse animation for downloading
        if status == "downloading":
            self._start_pulse()
        else:
            self._stop_pulse()

    def _draw_bar(self) -> None:
        self._bar_bg.update_idletasks()
        w = self._bar_bg.winfo_width()
        if w < 2:
            self.after(50, self._draw_bar)
            return

        self._bar_bg.delete("all")
        h = self.BAR_H

        status = self.job.status
        fill_w = int(w * self.job.progress)

        if status == "done":
            fill_col = SUCCESS
        elif status == "error":
            fill_col = ERROR
            fill_w = w
        else:
            fill_col = TEXT_1

        # Background track
        self._bar_bg.configure(bg=BORDER)

        # Filled portion
        if fill_w > 0:
            self._bar_bg.create_rectangle(0, 0, fill_w, h, fill=fill_col, outline="")

    def _start_pulse(self) -> None:
        if self._pulse_after is not None:
            return
        self._pulse_tick()

    def _pulse_tick(self) -> None:
        if self.job.status != "downloading":
            self._stop_pulse()
            return
        alpha = self.PULSE_FRAMES[self._pulse_idx % len(self.PULSE_FRAMES)]
        # Simulate pulse by changing text colour opacity using a grey blend
        grey_val = int(0x1D + (0xFF - 0x1D) * (1 - alpha))
        hex_col = f"#{grey_val:02X}{grey_val:02X}{grey_val:02X}"
        try:
            self._status_lbl.configure(fg=hex_col)
        except tk.TclError:
            return
        self._pulse_idx += 1
        self._pulse_after = self.after(200, self._pulse_tick)

    def _stop_pulse(self) -> None:
        if self._pulse_after is not None:
            try:
                self.after_cancel(self._pulse_after)
            except Exception:
                pass
            self._pulse_after = None

    @staticmethod
    def _fmt_dur(secs: int) -> str:
        if not secs:
            return ""
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h}:{m:02d}:{s:02d}"
        return f"{m}:{s:02d}"

    # ── Interaction ────────────────────────────────────────────────────────
    def _on_click(self, _event=None) -> None:
        if self.job.status == "done" and self.job.filepath:
            folder = str(Path(self.job.filepath).parent)
            try:
                os.startfile(folder)
            except Exception:
                pass
