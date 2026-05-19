import json
import uuid
from datetime import datetime
from pathlib import Path

HISTORY_FILE = Path(__file__).resolve().parent.parent / "data" / "history.json"
MAX_ENTRIES = 500


def _ensure() -> None:
    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)


def load() -> list[dict]:
    _ensure()
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _write(entries: list[dict]) -> None:
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False, default=str)


def save(job) -> None:
    """Accepts a DownloadJob dataclass or a plain dict."""
    _ensure()
    entries = load()

    if hasattr(job, "__dict__"):
        data = {
            "id": job.id,
            "url": job.url,
            "platform": job.platform,
            "title": job.title or job.url,
            "quality": job.quality,
            "filename": job.filename or "",
            "filepath": job.filepath or "",
            "size_mb": round(job.size_mb, 2) if job.size_mb else 0,
            "date": job.finished_at.isoformat() if job.finished_at else datetime.now().isoformat(),
            "duration_sec": job.duration_sec or 0,
            "status": job.status,
        }
    else:
        data = dict(job)

    # Prepend, keep max 500
    entries = [data] + [e for e in entries if e.get("id") != data.get("id")]
    entries = entries[:MAX_ENTRIES]
    _write(entries)


def clear() -> None:
    _ensure()
    _write([])


def search(query: str) -> list[dict]:
    if not query:
        return load()
    q = query.lower()
    return [
        e for e in load()
        if q in e.get("title", "").lower()
        or q in e.get("url", "").lower()
        or q in e.get("platform", "").lower()
        or q in e.get("filename", "").lower()
    ]


def remove(entry_id: str) -> None:
    entries = [e for e in load() if e.get("id") != entry_id]
    _write(entries)
