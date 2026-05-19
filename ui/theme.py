"""Centralized design tokens for ReelWave."""

# ── Colours ──────────────────────────────────────────────────────────────────
BG       = "#FFFFFF"
SURFACE  = "#F5F5F7"
BORDER   = "#D2D2D7"
TEXT_1   = "#1D1D1F"
TEXT_2   = "#6E6E73"
TEXT_3   = "#AEAEB2"
ACCENT   = "#1D1D1F"
SUCCESS  = "#34C759"
ERROR    = "#FF3B30"
WARNING  = "#FF9F0A"
HOVER    = "#3A3A3C"

# ── Typography ────────────────────────────────────────────────────────────────
FONT_FAMILY = "Segoe UI"
FONT_MONO   = "Consolas"

def font(size: int = 13, weight: str = "normal") -> tuple:
    return (FONT_FAMILY, size, weight)

def mono(size: int = 12) -> tuple:
    return (FONT_MONO, size, "normal")

FONT_TITLE     = font(22, "bold")
FONT_SECTION   = font(13, "bold")
FONT_BODY      = font(13)
FONT_SECONDARY = font(11)
FONT_SMALL     = font(10)
FONT_LARGE_BTN = font(15, "bold")

# ── Spacing ───────────────────────────────────────────────────────────────────
MARGIN      = 40
GAP         = 24
PAD_CARD    = 16
RADIUS_CARD = 14
RADIUS_BTN  = 10
RADIUS_IN   = 14
SIDEBAR_W   = 64
