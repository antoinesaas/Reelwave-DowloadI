"""RW monogram logo drawn on a tkinter Canvas."""
from __future__ import annotations

import tkinter as tk
from ui.theme import TEXT_1


class LogoMark(tk.Canvas):
    """
    RW monogram — black rounded square, white strokes.
    size: side length in pixels (24, 38, 80 …)
    """

    def __init__(self, parent: tk.Widget, size: int = 38, bg: str = "white", **kw):
        super().__init__(
            parent,
            width=size, height=size,
            bd=0, highlightthickness=0,
            bg=bg,
            **kw,
        )
        self._size = size
        self._bg_colour = bg
        self.bind("<Configure>", lambda _: self._draw())
        self.after(10, self._draw)

    def _draw(self) -> None:
        s = self._size
        self.delete("all")

        # Rounded square background
        r = int(s * 0.22)
        self.create_rounded_rect(0, 0, s, s, r, fill=TEXT_1, outline="")

        # White strokes
        sw = max(1, int(s * 0.09))
        pad = int(s * 0.18)
        mid = s // 2

        # ── R ───────────────────────────────────────────────────────────────
        # Vertical stem: x1 at pad, full height minus padding
        rx = pad
        ry_top = pad
        ry_bot = s - pad
        r_mid_y = pad + (s - 2 * pad) * 0.45  # where the bump ends

        # Stem
        self.create_line(
            rx, ry_top, rx, ry_bot,
            fill="white", width=sw, capstyle="round",
        )
        # Bump (semi-circle approximated with arc)
        arc_x2 = mid - int(s * 0.05)
        arc_cy = ry_top + (r_mid_y - ry_top) / 2
        bump_r = (r_mid_y - ry_top) / 2
        self.create_arc(
            rx, ry_top,
            arc_x2, ry_top + (r_mid_y - ry_top),
            start=90, extent=-180,
            style="arc",
            outline="white", width=sw,
        )
        # Leg (diagonal from bump junction to bottom right area)
        leg_x2 = mid + int(s * 0.02)
        self.create_line(
            arc_x2 - sw, r_mid_y,
            leg_x2, ry_bot,
            fill="white", width=sw, capstyle="round",
        )

        # ── W ───────────────────────────────────────────────────────────────
        wx_start = mid + int(s * 0.04)
        wx_end   = s - pad
        wy_top   = pad
        wy_bot   = s - pad
        wy_mid   = wy_top + (wy_bot - wy_top) * 0.55
        wx_m1    = wx_start + (wx_end - wx_start) * 0.33
        wx_m2    = wx_start + (wx_end - wx_start) * 0.67

        self.create_line(
            wx_start, wy_top,
            wx_m1,    wy_bot,
            fill="white", width=sw, capstyle="round", joinstyle="round",
        )
        self.create_line(
            wx_m1,  wy_bot,
            (wx_m1 + wx_m2) / 2, wy_mid,
            fill="white", width=sw, capstyle="round", joinstyle="round",
        )
        self.create_line(
            (wx_m1 + wx_m2) / 2, wy_mid,
            wx_m2,  wy_bot,
            fill="white", width=sw, capstyle="round", joinstyle="round",
        )
        self.create_line(
            wx_m2,  wy_bot,
            wx_end, wy_top,
            fill="white", width=sw, capstyle="round", joinstyle="round",
        )

    def create_rounded_rect(
        self, x1, y1, x2, y2, r, **kw
    ) -> int:
        points = [
            x1 + r, y1,
            x2 - r, y1,
            x2,     y1,
            x2,     y1 + r,
            x2,     y2 - r,
            x2,     y2,
            x2 - r, y2,
            x1 + r, y2,
            x1,     y2,
            x1,     y2 - r,
            x1,     y1 + r,
            x1,     y1,
        ]
        return self.create_polygon(points, smooth=True, **kw)
