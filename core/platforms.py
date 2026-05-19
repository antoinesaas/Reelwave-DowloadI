import re
from dataclasses import dataclass

@dataclass
class Platform:
    name: str
    icon: str
    max_quality: str  # "4K" | "1080p"
    color: str = "#1D1D1F"


PLATFORMS = [
    Platform("YouTube",    "▶",  "4K",   "#1D1D1F"),
    Platform("TikTok",     "♪",  "1080p","#1D1D1F"),
    Platform("Instagram",  "◈",  "1080p","#1D1D1F"),
    Platform("Pinterest",  "⊕",  "1080p","#1D1D1F"),
    Platform("Twitter/X",  "✕",  "1080p","#1D1D1F"),
    Platform("Vimeo",      "▷",  "4K",   "#1D1D1F"),
    Platform("Web",        "⊙",  "4K",   "#1D1D1F"),
]

_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"(youtube\.com|youtu\.be)", re.I),  "YouTube"),
    (re.compile(r"tiktok\.com",              re.I),  "TikTok"),
    (re.compile(r"instagram\.com",           re.I),  "Instagram"),
    (re.compile(r"pinterest\.(com|co\.uk|fr|de|es|it)", re.I), "Pinterest"),
    (re.compile(r"(twitter\.com|x\.com)",    re.I),  "Twitter/X"),
    (re.compile(r"vimeo\.com",               re.I),  "Vimeo"),
]

_URL_RE = re.compile(
    r"https?://[^\s/$.?#].[^\s]*", re.I
)

_PLATFORM_MAP: dict[str, Platform] = {p.name: p for p in PLATFORMS}


def detect(url: str) -> Platform:
    for pattern, name in _PATTERNS:
        if pattern.search(url):
            return _PLATFORM_MAP[name]
    if _URL_RE.match(url):
        return _PLATFORM_MAP["Web"]
    return _PLATFORM_MAP["Web"]


def is_valid_url(url: str) -> bool:
    return bool(_URL_RE.match(url.strip()))


def get_platform(name: str) -> Platform:
    return _PLATFORM_MAP.get(name, _PLATFORM_MAP["Web"])
