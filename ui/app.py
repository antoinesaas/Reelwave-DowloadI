"""Main ReelWave application window."""
from __future__ import annotations

import os
import threading
import tkinter as tk
from pathlib import Path
from typing import Optional

try:
    import pyperclip
    _HAS_CLIP = True
except ImportError:
    _HAS_CLIP = False

from ui.theme import (
    BG, SURFACE, BORDER, TEXT_1, TEXT_2, TEXT_3,
    SUCCESS, ERROR, WARNING,
    FONT_BODY, FONT_SECONDARY, FONT_SECTION, font,
    MARGIN, GAP, SIDEBAR_W,
)
from ui.components.sidebar import Sidebar
from ui.components.url_bar import URLBar
from ui.components.job_card import JobCard
from ui.components.history_panel import HistoryPanel
from ui.components.settings_modal import SettingsView
from ui.components.toast import ToastManager
from core.downloader import Downloader, DownloadJob
from core import settings as cfg
from core.platforms import is_valid_url, detect


class ReelWaveApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("ReelWave")
        self.configure(bg=BG)
        self.minsize(720, 580)
        self.geometry("900x700")

        self._downloader = Downloader()
        self._job_cards: dict[str, JobCard] = {}
        self._active_view = "download"
        self._last_clipboard = ""
        self._auto_paste_after: Optional[str] = None

        self._build_layout()
        self._bind_keys()

        self._toast = ToastManager(self)

        # Start clipboard monitor
        self._poll_clipboard()

    # ── Layout ─────────────────────────────────────────────────────────────
    def _build_layout(self) -> None:
        # Root pane
        pane = tk.Frame(self, bg=BG)
        pane.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = Sidebar(pane, on_nav=self._nav_to)
        self._sidebar.pack(side="left", fill="y")

        # Right area
        self._content = tk.Frame(pane, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

        # Build all views
        self._view_download  = self._build_download_view()
        self._view_history   = HistoryPanel(self._content)
        self._view_settings  = SettingsView(self._content)

        self._nav_to("download")

    # ── Download view ──────────────────────────────────────────────────────
    def _build_download_view(self) -> tk.Frame:
        frame = tk.Frame(self._content, bg=BG, padx=MARGIN, pady=MARGIN)

        # Section title
        tk.Label(
            frame, text="Télécharger",
            font=font(18, "bold"),
            bg=BG, fg=TEXT_1,
            anchor="w",
        ).pack(fill="x", pady=(0, GAP))

        # URL bar
        self._url_bar = URLBar(frame, on_submit=self._on_submit)
        self._url_bar.pack(fill="x")

        # Divider
        tk.Frame(frame, bg=BORDER, height=1).pack(fill="x", pady=(GAP, 0))

        # Active jobs label
        tk.Label(
            frame, text="EN COURS",
            font=font(10, "bold"),
            bg=BG, fg=TEXT_3,
            anchor="w",
        ).pack(fill="x", pady=(12, 6))

        # Scrollable jobs area
        jobs_canvas = tk.Canvas(frame, bg=BG, bd=0, highlightthickness=0)
        jobs_scroll = tk.Scrollbar(
            frame, orient="vertical", command=jobs_canvas.yview
        )
        self._jobs_frame = tk.Frame(jobs_canvas, bg=BG)
        self._jobs_frame.bind(
            "<Configure>",
            lambda e: jobs_canvas.configure(scrollregion=jobs_canvas.bbox("all")),
        )
        jobs_canvas.create_window((0, 0), window=self._jobs_frame, anchor="nw")
        jobs_canvas.configure(yscrollcommand=jobs_scroll.set)
        jobs_scroll.pack(side="right", fill="y")
        jobs_canvas.pack(side="left", fill="both", expand=True)

        jobs_canvas.bind_all("<MouseWheel>", lambda e: jobs_canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))

        self._empty_lbl = tk.Label(
            self._jobs_frame,
            text="Colle un lien pour commencer.",
            font=FONT_BODY, bg=BG, fg=TEXT_3,
        )
        self._empty_lbl.pack(pady=40)

        return frame

    # ── Navigation ──────────────────────────────────────────────────────────
    def _nav_to(self, view: str) -> None:
        # Hide all
        for v in (self._view_download, self._view_history, self._view_settings):
            v.pack_forget()

        self._active_view = view
        self._sidebar.set_active(view)

        if view == "download":
            self._view_download.pack(fill="both", expand=True)
        elif view == "history":
            self._view_history.pack(fill="both", expand=True)
            self._view_history.refresh()
        elif view == "settings":
            self._view_settings.pack(fill="both", expand=True)

    # ── Submit / Download ──────────────────────────────────────────────────
    def _on_submit(self, url: str, quality: str) -> None:
        if not is_valid_url(url):
            self._toast.show("URL invalide.", kind="error")
            return

        out_dir = cfg.get("output_dir", str(Path.home() / "Downloads" / "ReelWave"))

        job = self._downloader.submit(
            url=url,
            quality=quality,
            out_dir=out_dir,
            on_update=lambda j=None: self._schedule_refresh(),
        )
        self._add_job_card(job)
        self._url_bar.set_url("")
        self._update_title()

    def _schedule_refresh(self) -> None:
        self.after(0, self._refresh_cards)

    def _add_job_card(self, job: DownloadJob) -> None:
        if self._empty_lbl.winfo_ismapped():
            self._empty_lbl.pack_forget()

        card = JobCard(self._jobs_frame, job)
        card.pack(fill="x", pady=(0, 8), padx=2)
        self._job_cards[job.id] = card

    def _refresh_cards(self) -> None:
        for job_id, card in list(self._job_cards.items()):
            try:
                card.refresh()
                if card.job.status == "done":
                    self._on_job_done(card.job)
            except tk.TclError:
                del self._job_cards[job_id]
        self._update_title()

    def _on_job_done(self, job: DownloadJob) -> None:
        # Windows notification
        if cfg.get("notify_on_done", True):
            self._toast.show(
                f"✓  {job.title[:50] or 'Téléchargement'} terminé.",
                kind="success",
            )
        # Open folder
        if cfg.get("open_folder_on_done", False) and job.filepath:
            folder = str(Path(job.filepath).parent)
            try:
                os.startfile(folder)
            except Exception:
                pass

    # ── Window title ───────────────────────────────────────────────────────
    def _update_title(self) -> None:
        active = sum(
            1 for j in self._downloader.jobs()
            if j.status == "downloading"
        )
        if active:
            self.title(f"ReelWave — {active} en cours")
        else:
            self.title("ReelWave")

    # ── Keyboard shortcuts ─────────────────────────────────────────────────
    def _bind_keys(self) -> None:
        self.bind_all("<Control-v>", self._shortcut_paste)
        self.bind_all("<Control-d>", self._shortcut_download)
        self.bind_all("<Control-comma>", lambda _: self._nav_to("settings"))
        self.bind_all("<Escape>", self._shortcut_escape)

    def _shortcut_paste(self, _e=None) -> None:
        self._nav_to("download")
        if _HAS_CLIP:
            text = pyperclip.paste().strip()
        else:
            try:
                text = self.clipboard_get().strip()
            except Exception:
                text = ""
        if text:
            self._url_bar.set_url(text)

    def _shortcut_download(self, _e=None) -> None:
        if self._active_view == "download":
            url = self._url_bar.get_url()
            quality = self._url_bar.get_quality()
            if url:
                self._on_submit(url, quality)

    def _shortcut_escape(self, _e=None) -> None:
        pass  # Nothing to close currently

    # ── Auto-paste clipboard monitor ───────────────────────────────────────
    def _poll_clipboard(self) -> None:
        if not cfg.get("auto_paste", False):
            self._auto_paste_after = self.after(500, self._poll_clipboard)
            return

        try:
            if _HAS_CLIP:
                text = pyperclip.paste().strip()
            else:
                text = self.clipboard_get().strip()
        except Exception:
            text = ""

        if text and text != self._last_clipboard and is_valid_url(text):
            self._last_clipboard = text
            platform = detect(text)
            self._url_bar.set_url(text)
            quality = cfg.get("default_quality", "1080p")
            self._url_bar.set_quality(quality)
            self._on_submit(text, quality)
            self._toast.show(
                f"↓  {platform.name} détecté — Téléchargement démarré",
                kind="info",
            )

        self._auto_paste_after = self.after(500, self._poll_clipboard)
