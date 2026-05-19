"""64px icon-only sidebar with tooltips."""
from __future__ import annotations

import tkinter as tk
from typing import Callable

from ui.theme import BG, SURFACE, BORDER, TEXT_1, TEXT_2, TEXT_3, font
from ui.components.logomark import LogoMark


class _Tooltip:
    """Simple tooltip that follows the cursor."""

    def __init__(self, widget: tk.Widget, text: str):
        self._widget = widget
        self._text = text
        self._win: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)

    def _show(self, event=None) -> None:
        self._hide()
        x = self._widget.winfo_rootx() + 70
        y = self._widget.winfo_rooty() + 8
        self._win = tk.Toplevel(self._widget)
        self._win.wm_overrideredirect(True)
        self._win.wm_geometry(f"+{x}+{y}")
        self._win.configure(bg=TEXT_1)
        lbl = tk.Label(
            self._win,
            text=self._text,
            font=font(11),
            bg=TEXT_1, fg="white",
            padx=10, pady=5,
        )
        lbl.pack()

    def _hide(self, event=None) -> None:
        if self._win:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None


NAV_ITEMS = [
    ("download", "↓",  "Télécharger"),
    ("history",  "☰",  "Historique"),
    ("settings", "⚙",  "Paramètres"),
]


class Sidebar(tk.Frame):
    """
    64px-wide vertical icon navigation.
    on_nav(view_name) is called when an icon is clicked.
    """

    def __init__(
        self,
        parent: tk.Widget,
        on_nav: Callable[[str], None],
        **kw,
    ):
        super().__init__(parent, bg=SURFACE, width=64, **kw)
        self.pack_propagate(False)
        self._on_nav = on_nav
        self._active = "download"
        self._buttons: dict[str, tk.Label] = {}
        self._build()

    # ── Build ──────────────────────────────────────────────────────────────
    def _build(self) -> None:
        # Separator line on the right edge
        sep = tk.Frame(self, bg=BORDER, width=1)
        sep.place(relx=1.0, rely=0, relheight=1, anchor="ne")

        # Logo at top
        logo_frame = tk.Frame(self, bg=SURFACE, pady=16)
        logo_frame.pack(fill="x")
        logo = LogoMark(logo_frame, size=30, bg=SURFACE)
        logo.pack()

        # Divider
        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=10)

        # Nav items
        for name, icon, label in NAV_ITEMS:
            btn = tk.Label(
                self,
                text=icon,
                font=font(20),
                bg=SURFACE, fg=TEXT_2,
                cursor="hand2",
                pady=16,
            )
            btn.pack(fill="x")
            self._buttons[name] = btn
            _Tooltip(btn, label)
            btn.bind("<Button-1>", lambda e, n=name: self._nav(n))
            btn.bind("<Enter>",    lambda e, b=btn, n=name: self._hover(b, n))
            btn.bind("<Leave>",    lambda e, b=btn, n=name: self._unhover(b, n))

        self._render_active()

    # ── State ──────────────────────────────────────────────────────────────
    def _nav(self, name: str) -> None:
        self._active = name
        self._render_active()
        self._on_nav(name)

    def set_active(self, name: str) -> None:
        self._active = name
        self._render_active()

    def _render_active(self) -> None:
        for name, btn in self._buttons.items():
            if name == self._active:
                btn.configure(fg=TEXT_1, bg=BORDER)
            else:
                btn.configure(fg=TEXT_2, bg=SURFACE)

    def _hover(self, btn: tk.Label, name: str) -> None:
        if name != self._active:
            btn.configure(bg="#EBEBED")

    def _unhover(self, btn: tk.Label, name: str) -> None:
        if name != self._active:
            btn.configure(bg=SURFACE)
        else:
            btn.configure(bg=BORDER)
