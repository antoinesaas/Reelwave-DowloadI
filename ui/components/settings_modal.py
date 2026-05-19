"""Settings view — all user preferences."""
from __future__ import annotations

import shutil
import subprocess
import sys
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import filedialog

from ui.theme import (
    BG, SURFACE, BORDER, TEXT_1, TEXT_2, TEXT_3,
    SUCCESS, ERROR, WARNING,
    FONT_BODY, FONT_SECONDARY, FONT_SECTION, font,
)
from core import settings as cfg

QUALITIES  = ["4K", "1080p", "720p", "480p", "Audio MP3"]
FORMATS    = ["mp4", "mkv", "webm"]
FORMAT_LBL = {"mp4": "MP4 (recommandé)", "mkv": "MKV", "webm": "WebM"}


class SettingsView(tk.Frame):
    def __init__(self, parent: tk.Widget, **kw):
        super().__init__(parent, bg=BG, **kw)
        self._settings = cfg.load()
        self._build()

    # ── Build ──────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # Scrollable container
        canvas = tk.Canvas(self, bg=BG, bd=0, highlightthickness=0)
        scroll = tk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)

        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=BG, padx=40)
        inner.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(
            int(-1 * (e.delta / 120)), "units"
        ))

        tk.Label(
            inner, text="Paramètres",
            font=font(18, "bold"),
            bg=BG, fg=TEXT_1,
            anchor="w",
        ).pack(fill="x", pady=(0, 20))

        self._build_output_dir(inner)
        self._divider(inner)
        self._build_quality(inner)
        self._divider(inner)
        self._build_format(inner)
        self._divider(inner)
        self._build_behavior(inner)
        self._divider(inner)
        self._build_ffmpeg(inner)
        self._divider(inner)
        self._build_about(inner)
        tk.Frame(inner, bg=BG, height=40).pack()

    def _divider(self, parent: tk.Widget) -> None:
        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=16)

    def _section_label(self, parent: tk.Widget, text: str) -> None:
        tk.Label(
            parent, text=text.upper(),
            font=font(10, "bold"),
            bg=BG, fg=TEXT_3,
            anchor="w",
        ).pack(fill="x", pady=(0, 10))

    # ── Output directory ───────────────────────────────────────────────────
    def _build_output_dir(self, parent: tk.Widget) -> None:
        self._section_label(parent, "Dossier de téléchargement")

        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=(0, 8))

        self._dir_lbl = tk.Label(
            row,
            text=self._settings.get("output_dir", ""),
            font=FONT_BODY,
            bg=SURFACE, fg=TEXT_1,
            anchor="w", padx=12, pady=8,
        )
        self._dir_lbl.pack(side="left", fill="x", expand=True, padx=(0, 8))

        tk.Button(
            row, text="Changer…",
            font=FONT_SECONDARY,
            bg=BORDER, fg=TEXT_1,
            activebackground=TEXT_3,
            relief="flat", bd=0,
            padx=14, pady=8,
            cursor="hand2",
            command=self._choose_dir,
        ).pack(side="right")

        self._subfolder_var = tk.BooleanVar(
            value=self._settings.get("subfolder_per_platform", False)
        )
        self._checkbox(
            parent,
            "Créer un sous-dossier par plateforme (YouTube/, TikTok/…)",
            self._subfolder_var,
            "subfolder_per_platform",
        )

    def _choose_dir(self) -> None:
        d = filedialog.askdirectory(
            title="Choisir le dossier de téléchargement",
            initialdir=self._settings.get("output_dir", str(Path.home())),
        )
        if d:
            self._settings["output_dir"] = d
            self._dir_lbl.configure(text=d)
            cfg.save(self._settings)

    # ── Quality ────────────────────────────────────────────────────────────
    def _build_quality(self, parent: tk.Widget) -> None:
        self._section_label(parent, "Qualité par défaut")
        self._quality_var = tk.StringVar(
            value=self._settings.get("default_quality", "1080p")
        )
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x")
        for q in QUALITIES:
            rb = tk.Radiobutton(
                row, text=q,
                variable=self._quality_var, value=q,
                font=FONT_BODY,
                bg=BG, fg=TEXT_1,
                activebackground=BG,
                selectcolor=BG,
                indicatoron=True,
                relief="flat",
                cursor="hand2",
                command=lambda: self._save("default_quality", self._quality_var.get()),
            )
            rb.pack(side="left", padx=(0, 16))

    # ── Format ─────────────────────────────────────────────────────────────
    def _build_format(self, parent: tk.Widget) -> None:
        self._section_label(parent, "Format vidéo")
        self._format_var = tk.StringVar(
            value=self._settings.get("video_format", "mp4")
        )
        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x")
        for fmt in FORMATS:
            rb = tk.Radiobutton(
                row, text=FORMAT_LBL[fmt],
                variable=self._format_var, value=fmt,
                font=FONT_BODY,
                bg=BG, fg=TEXT_1,
                activebackground=BG,
                selectcolor=BG,
                relief="flat",
                cursor="hand2",
                command=lambda: self._save("video_format", self._format_var.get()),
            )
            rb.pack(side="left", padx=(0, 20))

    # ── Behaviour ──────────────────────────────────────────────────────────
    def _build_behavior(self, parent: tk.Widget) -> None:
        self._section_label(parent, "Comportement")

        self._autopaste_var = tk.BooleanVar(
            value=self._settings.get("auto_paste", False)
        )
        self._notify_var = tk.BooleanVar(
            value=self._settings.get("notify_on_done", True)
        )
        self._openfolder_var = tk.BooleanVar(
            value=self._settings.get("open_folder_on_done", False)
        )

        self._checkbox(
            parent,
            "Télécharger automatiquement si URL valide collée",
            self._autopaste_var,
            "auto_paste",
        )
        self._checkbox(
            parent,
            "Notification Windows quand terminé",
            self._notify_var,
            "notify_on_done",
        )
        self._checkbox(
            parent,
            "Ouvrir le dossier après téléchargement",
            self._openfolder_var,
            "open_folder_on_done",
        )

    # ── FFmpeg ─────────────────────────────────────────────────────────────
    def _build_ffmpeg(self, parent: tk.Widget) -> None:
        self._section_label(parent, "FFmpeg")

        row = tk.Frame(parent, bg=BG)
        row.pack(fill="x", pady=(0, 8))

        has_ffmpeg = bool(shutil.which("ffmpeg"))
        icon = "✓" if has_ffmpeg else "⚠"
        icon_col = SUCCESS if has_ffmpeg else WARNING
        msg = "FFmpeg détecté" if has_ffmpeg else "FFmpeg non trouvé (requis pour la 4K)"

        tk.Label(
            row, text=icon,
            font=font(14, "bold"),
            bg=BG, fg=icon_col,
        ).pack(side="left", padx=(0, 6))

        tk.Label(
            row, text=msg,
            font=FONT_BODY,
            bg=BG, fg=TEXT_1,
        ).pack(side="left")

        if not has_ffmpeg:
            tk.Button(
                row, text="Installer FFmpeg",
                font=FONT_SECONDARY,
                bg=BORDER, fg=TEXT_1,
                activebackground=TEXT_3,
                relief="flat", bd=0,
                padx=12, pady=6,
                cursor="hand2",
                command=lambda: webbrowser.open("https://ffmpeg.org/download.html"),
            ).pack(side="left", padx=(16, 0))

    # ── About ──────────────────────────────────────────────────────────────
    def _build_about(self, parent: tk.Widget) -> None:
        self._section_label(parent, "À propos")

        tk.Label(
            parent, text="ReelWave v1.0.0",
            font=font(15, "bold"),
            bg=BG, fg=TEXT_1,
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            parent, text="Download anything. No ads. No limits.",
            font=FONT_BODY,
            bg=BG, fg=TEXT_2,
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

    # ── Helpers ────────────────────────────────────────────────────────────
    def _checkbox(
        self,
        parent: tk.Widget,
        label: str,
        var: tk.BooleanVar,
        key: str,
    ) -> None:
        row = tk.Frame(parent, bg=BG, pady=4)
        row.pack(fill="x")

        cb = tk.Checkbutton(
            row, text=label,
            variable=var,
            font=FONT_BODY,
            bg=BG, fg=TEXT_1,
            activebackground=BG,
            selectcolor=BG,
            relief="flat",
            cursor="hand2",
            command=lambda: self._save(key, var.get()),
        )
        cb.pack(side="left")

    def _save(self, key: str, value) -> None:
        self._settings[key] = value
        cfg.save(self._settings)
