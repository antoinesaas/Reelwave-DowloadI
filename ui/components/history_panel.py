"""Scrollable history panel with search & clear."""
from __future__ import annotations

import os
import tkinter as tk
from pathlib import Path
from typing import Callable

from ui.theme import (
    BG, SURFACE, BORDER, TEXT_1, TEXT_2, TEXT_3,
    SUCCESS, ERROR, WARNING,
    FONT_BODY, FONT_SECONDARY, FONT_SECTION, font,
)
from core import history as hist


class HistoryPanel(tk.Frame):
    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._build()
        self.refresh()

    # ── Build ──────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # Header row
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", pady=(0, 12))

        tk.Label(
            hdr, text="Historique",
            font=FONT_SECTION, bg=BG, fg=TEXT_1,
        ).pack(side="left")

        # Clear button
        self._clear_btn = tk.Button(
            hdr,
            text="Tout effacer",
            font=FONT_SECONDARY,
            bg=BG, fg=TEXT_2,
            activebackground=BG,
            activeforeground=ERROR,
            relief="flat", bd=0,
            cursor="hand2",
            command=self._confirm_clear,
        )
        self._clear_btn.pack(side="right")

        # Search bar
        search_frame = tk.Frame(self, bg=BORDER, padx=1, pady=1)
        search_frame.pack(fill="x", pady=(0, 12))

        search_inner = tk.Frame(search_frame, bg=SURFACE)
        search_inner.pack(fill="both")

        self._search_var = tk.StringVar()
        # trace added after _scroll_frame is created to avoid AttributeError
        self._search_entry = tk.Entry(
            search_inner,
            textvariable=self._search_var,
            font=FONT_BODY,
            bg=SURFACE, fg=TEXT_1,
            insertbackground=TEXT_1,
            relief="flat", bd=8,
        )
        self._search_entry.pack(fill="x", ipady=7)
        self._search_entry.insert(0, "")
        self._placeholder_active = True
        self._search_entry.configure(fg=TEXT_3)
        self._search_entry.insert(0, "Rechercher…")
        self._search_entry.bind("<FocusIn>",  self._search_focus_in)
        self._search_entry.bind("<FocusOut>", self._search_focus_out)

        # Scrollable list
        container = tk.Frame(self, bg=BG)
        container.pack(fill="both", expand=True)

        canvas = tk.Canvas(container, bg=BG, bd=0, highlightthickness=0)
        scrollbar = tk.Scrollbar(container, orient="vertical", command=canvas.yview)

        self._scroll_frame = tk.Frame(canvas, bg=BG)
        self._scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=self._scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))

        # Now safe to add search trace
        self._search_var.trace_add("write", lambda *_: self.refresh())

    # ── Search placeholder ──────────────────────────────────────────────────
    def _search_focus_in(self, _=None) -> None:
        if self._placeholder_active:
            self._placeholder_active = False
            self._search_entry.configure(fg=TEXT_1)
            self._search_entry.delete(0, "end")

    def _search_focus_out(self, _=None) -> None:
        if not self._search_var.get():
            self._placeholder_active = True
            self._search_entry.configure(fg=TEXT_3)
            self._search_entry.delete(0, "end")
            self._search_entry.insert(0, "Rechercher…")

    # ── Refresh ────────────────────────────────────────────────────────────
    def refresh(self) -> None:
        query = "" if self._placeholder_active else self._search_var.get()
        entries = hist.search(query)

        for w in self._scroll_frame.winfo_children():
            w.destroy()

        if not entries:
            tk.Label(
                self._scroll_frame,
                text="Aucun téléchargement pour l'instant.",
                font=FONT_BODY,
                bg=BG, fg=TEXT_3,
            ).pack(pady=40)
            return

        for entry in entries:
            self._make_row(entry)

    # ── Row ────────────────────────────────────────────────────────────────
    def _make_row(self, entry: dict) -> None:
        card = tk.Frame(
            self._scroll_frame,
            bg=SURFACE,
            highlightbackground=BORDER,
            highlightthickness=1,
            padx=14, pady=10,
        )
        card.pack(fill="x", pady=(0, 8))

        # Left col
        left = tk.Frame(card, bg=SURFACE)
        left.pack(side="left", fill="both", expand=True)

        title = entry.get("title") or entry.get("url", "")
        title = title[:62] + "…" if len(title) > 62 else title
        tk.Label(
            left, text=title,
            font=FONT_BODY, bg=SURFACE, fg=TEXT_1,
            anchor="w",
        ).pack(fill="x")

        meta_parts = [
            entry.get("platform", ""),
            entry.get("quality", ""),
            f'{entry.get("size_mb", 0):.1f} MB' if entry.get("size_mb") else "",
            entry.get("date", "")[:10],
        ]
        meta = "  ·  ".join(p for p in meta_parts if p)
        tk.Label(
            left, text=meta,
            font=FONT_SECONDARY, bg=SURFACE, fg=TEXT_2,
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Right col: status + missing-file warning
        right = tk.Frame(card, bg=SURFACE)
        right.pack(side="right")

        filepath = entry.get("filepath", "")
        file_missing = filepath and not Path(filepath).exists()

        status = entry.get("status", "done")
        status_icons = {"done": ("✓", SUCCESS), "error": ("✕", ERROR)}
        icon, col = status_icons.get(status, ("·", TEXT_3))
        tk.Label(
            right, text=icon,
            font=font(14, "bold"),
            bg=SURFACE, fg=col,
        ).pack(side="right", padx=(4, 0))

        if file_missing:
            tk.Label(
                right, text="⚠",
                font=font(13),
                bg=SURFACE, fg=WARNING,
            ).pack(side="right", padx=(0, 4))

        # Click to open folder
        if filepath and not file_missing:
            card.configure(cursor="hand2")
            card.bind("<Button-1>", lambda _e, p=filepath: self._open(p))

    @staticmethod
    def _open(filepath: str) -> None:
        folder = str(Path(filepath).parent)
        try:
            os.startfile(folder)
        except Exception:
            pass

    # ── Clear ──────────────────────────────────────────────────────────────
    def _confirm_clear(self) -> None:
        dialog = tk.Toplevel(self)
        dialog.title("Effacer l'historique")
        dialog.resizable(False, False)
        dialog.configure(bg=BG)
        dialog.grab_set()

        tk.Label(
            dialog,
            text="Effacer tout l'historique ?",
            font=FONT_BODY,
            bg=BG, fg=TEXT_1,
            padx=30, pady=20,
        ).pack()

        btn_row = tk.Frame(dialog, bg=BG, pady=10)
        btn_row.pack()

        tk.Button(
            btn_row, text="Annuler",
            font=FONT_SECONDARY,
            bg=SURFACE, fg=TEXT_1,
            relief="flat", bd=0,
            padx=20, pady=8,
            cursor="hand2",
            command=dialog.destroy,
        ).pack(side="left", padx=6)

        def _do_clear():
            hist.clear()
            dialog.destroy()
            self.refresh()

        tk.Button(
            btn_row, text="Effacer",
            font=FONT_SECONDARY,
            bg=ERROR, fg="white",
            relief="flat", bd=0,
            padx=20, pady=8,
            cursor="hand2",
            command=_do_clear,
        ).pack(side="left", padx=6)
