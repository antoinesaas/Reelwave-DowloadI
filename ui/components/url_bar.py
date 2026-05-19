"""URL input bar with live platform detection."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

try:
    import pyperclip
    _HAS_CLIP = True
except ImportError:
    _HAS_CLIP = False

from ui.theme import (
    BG, SURFACE, BORDER, TEXT_1, TEXT_2, TEXT_3,
    FONT_BODY, FONT_SECONDARY, font,
)
from core.platforms import detect, is_valid_url, Platform

# Quality options
QUALITIES = ["4K", "1080p", "720p", "480p", "Audio MP3"]
# Platforms that cap at 1080p
CAPPED_PLATFORMS = {"TikTok", "Instagram", "Pinterest", "Twitter/X"}


class URLBar(tk.Frame):
    """
    URL input + platform icon + paste button.
    Emits on_submit(url, quality) when Enter is pressed or download triggered.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_submit: Callable[[str, str], None],
        **kw,
    ):
        super().__init__(parent, bg=BG, **kw)
        self._on_submit = on_submit
        self._quality = tk.StringVar(value="1080p")
        self._platform: Platform | None = None
        self._build()

    # ── Build ──────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # ── Input row ──────────────────────────────────────────────────────
        row = tk.Frame(self, bg=BG)
        row.pack(fill="x")

        # Platform icon
        self._icon_lbl = tk.Label(
            row, text="⊙",
            font=font(18), bg=SURFACE, fg=TEXT_3,
            width=2,
        )
        self._icon_lbl.pack(side="left")

        # Text entry container (rounded appearance via Frame bg)
        entry_frame = tk.Frame(
            row,
            bg=BORDER,
            padx=1, pady=1,
        )
        entry_frame.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self._entry_inner = tk.Frame(entry_frame, bg=SURFACE)
        self._entry_inner.pack(fill="both", expand=True)

        self._var = tk.StringVar()
        self._entry = tk.Entry(
            self._entry_inner,
            textvariable=self._var,
            font=FONT_BODY,
            bg=SURFACE, fg=TEXT_1,
            insertbackground=TEXT_1,
            relief="flat",
            bd=8,
        )
        self._entry.pack(fill="both", expand=True, ipady=10)
        self._entry.insert(0, "")
        self._set_placeholder()

        self._entry.bind("<FocusIn>",  self._on_focus_in)
        self._entry.bind("<FocusOut>", self._on_focus_out)
        self._entry.bind("<Return>",   self._on_return)
        self._var.trace_add("write",   self._on_text_change)

        # Paste button
        self._paste_btn = tk.Button(
            row,
            text="Coller",
            font=FONT_SECONDARY,
            bg=BORDER, fg=TEXT_1,
            activebackground=TEXT_3,
            activeforeground=TEXT_1,
            relief="flat",
            bd=0,
            padx=12, pady=6,
            cursor="hand2",
            command=self._paste,
        )
        self._paste_btn.pack(side="left")

        # ── FFmpeg warning ─────────────────────────────────────────────────
        self._ffmpeg_warn = tk.Label(
            self, text="",
            font=FONT_SECONDARY, bg=BG, fg="#FF9F0A",
            anchor="w",
        )
        self._ffmpeg_warn.pack(fill="x", pady=(4, 0))

        # ── Quality selectors ──────────────────────────────────────────────
        q_row = tk.Frame(self, bg=BG)
        q_row.pack(fill="x", pady=(12, 0))

        self._q_buttons: dict[str, tk.Frame] = {}
        for q in QUALITIES:
            btn_frame = tk.Frame(q_row, bg=BG, cursor="hand2")
            btn_frame.pack(side="left", padx=(0, 16))

            dot = tk.Canvas(
                btn_frame, width=16, height=16,
                bg=BG, bd=0, highlightthickness=0,
            )
            dot.pack(side="left", padx=(0, 4))

            lbl = tk.Label(
                btn_frame, text=q,
                font=FONT_BODY, bg=BG, fg=TEXT_1,
            )
            lbl.pack(side="left")

            self._q_buttons[q] = btn_frame
            btn_frame._dot = dot
            btn_frame._lbl = lbl

            for w in (btn_frame, dot, lbl):
                w.bind("<Button-1>", lambda e, _q=q: self._select_quality(_q))

        self._render_quality()

        # ── Download button ────────────────────────────────────────────────
        self._dl_btn = tk.Button(
            self,
            text="Télécharger",
            font=font(15, "bold"),
            bg=TEXT_1, fg="white",
            activebackground="#3A3A3C",
            activeforeground="white",
            relief="flat",
            bd=0,
            pady=14,
            cursor="hand2",
            command=self._on_return,
        )
        self._dl_btn.pack(fill="x", pady=(16, 0))

    # ── Placeholder ────────────────────────────────────────────────────────
    def _set_placeholder(self) -> None:
        self._placeholder_active = True
        self._entry.config(fg=TEXT_3)
        self._entry.delete(0, "end")
        self._entry.insert(0, "Colle un lien YouTube, TikTok, Instagram…")

    def _clear_placeholder(self) -> None:
        if self._placeholder_active:
            self._placeholder_active = False
            self._entry.config(fg=TEXT_1)
            self._entry.delete(0, "end")

    def _on_focus_in(self, _e=None) -> None:
        self._clear_placeholder()
        self._entry_inner.configure(bg=SURFACE)
        self._entry_inner.master.configure(bg=TEXT_1)

    def _on_focus_out(self, _e=None) -> None:
        if not self._var.get():
            self._set_placeholder()
        self._entry_inner.master.configure(bg=BORDER)

    # ── Text change / platform detection ──────────────────────────────────
    def _on_text_change(self, *_) -> None:
        if self._placeholder_active:
            return
        url = self._var.get().strip()
        platform = detect(url)
        self._platform = platform
        self._icon_lbl.configure(text=platform.icon, fg=TEXT_1 if url else TEXT_3)

        # Update 4K availability
        self._render_quality()
        self._update_ffmpeg_warn()

    # ── Quality render ─────────────────────────────────────────────────────
    def _select_quality(self, q: str) -> None:
        if not self._is_quality_enabled(q):
            return
        self._quality.set(q)
        self._render_quality()
        self._update_ffmpeg_warn()

    def _is_quality_enabled(self, q: str) -> bool:
        if q == "4K" and self._platform and self._platform.name in CAPPED_PLATFORMS:
            return False
        return True

    def _render_quality(self) -> None:
        selected = self._quality.get()
        for q, frame in self._q_buttons.items():
            enabled = self._is_quality_enabled(q)
            dot: tk.Canvas = frame._dot
            lbl: tk.Label = frame._lbl
            dot.delete("all")
            active = (q == selected) and enabled
            if active:
                dot.create_oval(2, 2, 14, 14, fill=TEXT_1, outline=TEXT_1)
            else:
                border = BORDER if enabled else TEXT_3
                dot.create_oval(2, 2, 14, 14, fill="", outline=border, width=2)
            lbl.configure(fg=TEXT_1 if enabled else TEXT_3)

    def _update_ffmpeg_warn(self) -> None:
        import shutil
        if self._quality.get() == "4K" and shutil.which("ffmpeg") is None:
            self._ffmpeg_warn.configure(
                text="⚠  FFmpeg non détecté — requis pour la 4K. ffmpeg.org"
            )
        else:
            self._ffmpeg_warn.configure(text="")

    # ── Actions ────────────────────────────────────────────────────────────
    def _paste(self) -> None:
        if _HAS_CLIP:
            text = pyperclip.paste().strip()
        else:
            try:
                text = self.clipboard_get().strip()
            except Exception:
                text = ""
        if text:
            self._clear_placeholder()
            self._var.set(text)
            self._entry.focus_set()
            self._entry.select_range(0, "end")

    def _on_return(self, _e=None) -> None:
        url = self.get_url()
        if not url:
            return
        quality = self._quality.get()
        self._dl_btn.configure(state="disabled")
        self.after(300, lambda: self._dl_btn.configure(state="normal"))
        self._on_submit(url, quality)

    # ── Public API ─────────────────────────────────────────────────────────
    def get_url(self) -> str:
        if self._placeholder_active:
            return ""
        return self._var.get().strip()

    def set_url(self, url: str) -> None:
        self._clear_placeholder()
        self._var.set(url)
        self._entry.focus_set()

    def get_quality(self) -> str:
        return self._quality.get()

    def set_quality(self, q: str) -> None:
        self._quality.set(q)
        self._render_quality()
