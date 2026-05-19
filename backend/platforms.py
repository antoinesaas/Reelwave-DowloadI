"""Platform detection from URL."""
import re
from dataclasses import dataclass

@dataclass
class Platform:
    name: str
    slug: str
    color: str
    icon: str

PLATFORMS = [
    Platform("YouTube",   "youtube",   "#FF0000", "▶"),
    Platform("TikTok",    "tiktok",    "#000000", "♪"),
    Platform("Instagram", "instagram", "#E1306C", "◈"),
    Platform("Pinterest", "pinterest", "#E60023", "⊕"),
    Platform("Twitter/X", "twitter",   "#000000", "✕"),
    Platform("Vimeo",     "vimeo",     "#1AB7EA", "▷"),
    Platform("Web",       "web",       "#6E6E73", "⊙"),
]

_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(youtube\.com|youtu\.be)", re.I),               "YouTube"),
    (re.compile(r"tiktok\.com",               re.I),               "TikTok"),
    (re.compile(r"instagram\.com",            re.I),               "Instagram"),
    (re.compile(r"pinterest\.(com|co\.\w+)", re.I),               "Pinterest"),
    (re.compile(r"(twitter\.com|x\.com)",     re.I),               "Twitter/X"),
    (re.compile(r"vimeo\.com",                re.I),               "Vimeo"),
]

_MAP = {p.name: p for p in PLATFORMS}


def detect(url: str) -> Platform:
    for pattern, name in _PATTERNS:
        if pattern.search(url):
            return _MAP[name]
    return _MAP["Web"]
