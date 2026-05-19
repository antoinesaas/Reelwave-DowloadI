"""Toast notification system — slide-up, auto-dismiss, stacked."""
from __future__ import annotations

import tkinter as tk
from typing import Literal

from ui.theme import TEXT_1, SUCCESS, ERROR, TEXT_2, font

ToastType = Literal["success", "error", "info"]

_ICONS = {"success": "✓", "error": "✕", "info": "ℹ"}
_COLORS = {"success": SUCCESS, "error": ERROR, "info": TEXT_2}

_MAX_TOASTS = 3
_DURATION_MS = 3000
_SLIDE_STEPS = 12
_SLIDE_INTERVAL = 16  # ms per frame ≈ 60fps


class ToastManager:
    """
    Manages a stack of toast notifications anchored to a root window.
    Usage: ToastManager(root).show("message", type="success")
    """

    def __init__(self, root: tk.Tk | tk.Toplevel):
        self._root = root
        self._toasts: list["_Toast"] = []

    def show(self, message: str, kind: ToastType = "info") -> None:
        if len(self._toasts) >= _MAX_TOASTS:
            oldest = self._toasts.pop(0)
            oldest.dismiss(animate=False)

        t = _Toast(self._root, message, kind, on_dismiss=self._on_dismiss)
        self._toasts.append(t)
        self._restack()

    def _on_dismiss(self, toast: "_Toast") -> None:
        if toast in self._toasts:
            self._toasts.remove(toast)
        self._restack()

    def _restack(self) -> None:
        margin_x = 20
        margin_y = 20
        gap = 8
        base_y = self._root.winfo_height() - margin_y
        for i, t in enumerate(reversed(self._toasts)):
            t.target_y = base_y - (i * (t.height + gap))


class _Toast(tk.Toplevel):
    height = 48

    def __init__(
        self,
        root: tk.Tk | tk.Toplevel,
        message: str,
        kind: ToastType,
        on_dismiss,
    ):
        super().__init__(root)
        self._root = root
        self._on_dismiss = on_dismiss
        self._dismissed = False

        self.wm_overrideredirect(True)
        self.configure(bg=TEXT_1)
        self.attributes("-topmost", True)
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass

        self._build(message, kind)
        self.update_idletasks()
        self.height = self.winfo_reqheight()

        self.target_y: int = 0
        self._place_initial()
        self._fade_in()
        self.after(_DURATION_MS, self.dismiss)

    def _build(self, message: str, kind: ToastType) -> None:
        icon = _ICONS.get(kind, "ℹ")
        col  = _COLORS.get(kind, TEXT_2)

        frame = tk.Frame(self, bg=TEXT_1, padx=16, pady=12)
        frame.pack()

        tk.Label(
            frame, text=icon,
            font=font(13, "bold"),
            bg=TEXT_1, fg=col,
        ).pack(side="left", padx=(0, 8))

        tk.Label(
            frame, text=message,
            font=font(12),
            bg=TEXT_1, fg="white",
            wraplength=340,
            justify="left",
        ).pack(side="left")

    def _place_initial(self) -> None:
        self.update_idletasks()
        w = self.winfo_reqwidth()
        rx = self._root.winfo_rootx()
        ry = self._root.winfo_rooty()
        rh = self._root.winfo_height()
        rw = self._root.winfo_width()
        x = rx + rw - w - 20
        y = ry + rh + 10  # start below the window
        self.geometry(f"+{x}+{y}")
        self._cur_y = y
        self.target_y = ry + rh - 60

    def _fade_in(self) -> None:
        try:
            self.attributes("-alpha", 0.0)
        except Exception:
            pass
        self._animate_in(0)

    def _animate_in(self, step: int) -> None:
        if step > _SLIDE_STEPS:
            return
        progress = step / _SLIDE_STEPS
        # ease-out cubic
        t = 1 - (1 - progress) ** 3

        self.update_idletasks()
        w = self.winfo_reqwidth()
        rx = self._root.winfo_rootx()
        rw = self._root.winfo_width()
        x  = rx + rw - w - 20

        start_y = self.target_y + 30
        cur_y = int(start_y + (self.target_y - start_y) * t)
        self.geometry(f"+{x}+{cur_y}")
        try:
            self.attributes("-alpha", t)
        except Exception:
            pass
        self.after(_SLIDE_INTERVAL, lambda: self._animate_in(step + 1))

    def dismiss(self, animate: bool = True) -> None:
        if self._dismissed:
            return
        self._dismissed = True
        if animate:
            self._animate_out(0)
        else:
            try:
                self.destroy()
            except Exception:
                pass
            self._on_dismiss(self)

    def _animate_out(self, step: int) -> None:
        if step > _SLIDE_STEPS:
            try:
                self.destroy()
            except Exception:
                pass
            self._on_dismiss(self)
            return
        progress = step / _SLIDE_STEPS
        t = progress ** 2  # ease-in
        try:
            self.attributes("-alpha", max(0.0, 1.0 - t))
        except Exception:
            pass
        self.after(_SLIDE_INTERVAL, lambda: self._animate_out(step + 1))
