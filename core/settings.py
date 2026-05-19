import json
from pathlib import Path

SETTINGS_FILE = Path(__file__).parent.parent / "data" / "settings.json"
# Resolve to absolute path relative to the project root (one level up from core/)
SETTINGS_FILE = Path(__file__).resolve().parent.parent / "data" / "settings.json"

DEFAULTS: dict = {
    "output_dir": str(Path.home() / "Downloads" / "ReelWave"),
    "default_quality": "1080p",
    "video_format": "mp4",
    "subfolder_per_platform": False,
    "auto_paste": False,
    "notify_on_done": True,
    "open_folder_on_done": False,
}


def load() -> dict:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        save(DEFAULTS.copy())
        return DEFAULTS.copy()
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Fill missing keys with defaults
        for k, v in DEFAULTS.items():
            if k not in data:
                data[k] = v
        return data
    except (json.JSONDecodeError, OSError):
        return DEFAULTS.copy()


def save(settings: dict) -> None:
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


_cache: dict | None = None


def get(key: str, default=None):
    global _cache
    if _cache is None:
        _cache = load()
    return _cache.get(key, default)


def set(key: str, value) -> None:
    global _cache
    if _cache is None:
        _cache = load()
    _cache[key] = value
    save(_cache)


def reload() -> dict:
    global _cache
    _cache = load()
    return _cache
