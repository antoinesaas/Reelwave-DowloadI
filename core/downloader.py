from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal

import yt_dlp

from core import history as hist
from core import settings as cfg
from core.platforms import detect

# ---------------------------------------------------------------------------
# Quality → yt-dlp format string
# ---------------------------------------------------------------------------
FORMAT_MAP: dict[str, str] = {
    "4K":       "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=2160]+bestaudio/best",
    "1080p":    "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=1080]+bestaudio/best",
    "720p":     "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/bestvideo[height<=720]+bestaudio/best",
    "480p":     "bestvideo[height<=480]+bestaudio/best",
    "Audio MP3": "bestaudio/best",
}

StatusType = Literal["pending", "downloading", "done", "error", "cancelled"]


def _friendly_error(raw: str) -> str:
    r = raw.lower()
    if "403" in r or "forbidden" in r:
        return "Vidéo privée ou accès refusé."
    if "unavailable" in r or "removed" in r or "deleted" in r:
        return "Vidéo supprimée ou indisponible."
    if "sign in" in r or "login" in r or "members" in r:
        return "Cette vidéo est réservée aux membres connectés."
    if "ffmpeg" in r:
        return "FFmpeg requis pour cette qualité. Installe-le depuis ffmpeg.org"
    if "rate" in r or "too many" in r or "429" in r:
        return "Trop de téléchargements. Attends quelques secondes."
    first_line = raw.strip().split("\n")[0]
    return first_line[:100] if first_line else "Erreur inconnue."


# ---------------------------------------------------------------------------
# DownloadJob dataclass
# ---------------------------------------------------------------------------
@dataclass
class DownloadJob:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    url: str = ""
    quality: str = "1080p"
    out_dir: str = ""
    platform: str = "Web"

    status: StatusType = "pending"
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    title: str = ""
    filename: str = ""
    filepath: str = ""
    size_mb: float = 0.0
    duration_sec: int = 0
    error: str = ""

    started_at: datetime | None = None
    finished_at: datetime | None = None

    on_update: Callable[[], None] | None = field(default=None, repr=False, compare=False)


# ---------------------------------------------------------------------------
# Downloader engine
# ---------------------------------------------------------------------------
class Downloader:
    def __init__(self) -> None:
        self._jobs: dict[str, DownloadJob] = {}
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    def submit(
        self,
        url: str,
        quality: str,
        out_dir: str | None = None,
        on_update: Callable[[], None] | None = None,
    ) -> DownloadJob:
        if out_dir is None:
            out_dir = cfg.get("output_dir", str(Path.home() / "Downloads" / "ReelWave"))

        platform = detect(url).name
        job = DownloadJob(
            url=url,
            quality=quality,
            out_dir=out_dir,
            platform=platform,
            status="pending",
            started_at=datetime.now(),
            on_update=on_update,
        )

        with self._lock:
            self._jobs[job.id] = job

        t = threading.Thread(target=self._run, args=(job,), daemon=True)
        t.start()
        return job

    # ------------------------------------------------------------------
    def cancel(self, job_id: str) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
        if job:
            job.status = "cancelled"
            if job.on_update:
                job.on_update()

    # ------------------------------------------------------------------
    def jobs(self) -> list[DownloadJob]:
        with self._lock:
            return list(self._jobs.values())

    # ------------------------------------------------------------------
    def _run(self, job: DownloadJob) -> None:
        job.status = "downloading"
        if job.on_update:
            job.on_update()

        # Build output path
        out_dir = Path(job.out_dir)
        if cfg.get("subfolder_per_platform", False):
            out_dir = out_dir / job.platform
        out_dir.mkdir(parents=True, exist_ok=True)

        outtmpl = str(out_dir / "%(title)s.%(ext)s")

        ydl_opts: dict = {
            "format": FORMAT_MAP.get(job.quality, FORMAT_MAP["1080p"]),
            "outtmpl": outtmpl,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._make_hook(job)],
            "postprocessors": [],
            "merge_output_format": cfg.get("video_format", "mp4"),
        }

        if job.quality == "Audio MP3":
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                if job.status == "cancelled":
                    return
                info = ydl.extract_info(job.url, download=True)
                if info:
                    job.title = info.get("title", "")
                    job.duration_sec = int(info.get("duration") or 0)
                    # Resolve actual filename
                    filepath = ydl.prepare_filename(info)
                    if job.quality == "Audio MP3":
                        filepath = str(Path(filepath).with_suffix(".mp3"))
                    job.filepath = filepath
                    job.filename = Path(filepath).name
                    try:
                        job.size_mb = Path(filepath).stat().st_size / 1_048_576
                    except OSError:
                        pass

            if job.status != "cancelled":
                job.status = "done"
                job.progress = 1.0
                job.finished_at = datetime.now()
                hist.save(job)

        except Exception as exc:
            if job.status != "cancelled":
                job.status = "error"
                job.error = _friendly_error(str(exc))
                job.progress = 1.0
                job.finished_at = datetime.now()

        if job.on_update:
            job.on_update()

    # ------------------------------------------------------------------
    def _make_hook(self, job: DownloadJob):
        def hook(d: dict) -> None:
            if job.status == "cancelled":
                raise yt_dlp.utils.DownloadError("Cancelled by user")

            if d["status"] == "downloading":
                job.status = "downloading"
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                job.progress = (downloaded / total) if total else 0.0

                speed = d.get("speed") or 0
                if speed:
                    if speed > 1_048_576:
                        job.speed = f"{speed / 1_048_576:.1f} MB/s"
                    else:
                        job.speed = f"{speed / 1024:.0f} KB/s"
                else:
                    job.speed = ""

                eta = d.get("eta")
                if eta is not None:
                    if eta >= 60:
                        job.eta = f"{eta // 60}m {eta % 60}s"
                    else:
                        job.eta = f"{eta}s"
                else:
                    job.eta = ""

                if job.on_update:
                    job.on_update()

            elif d["status"] == "finished":
                job.progress = 1.0
                job.speed = ""
                job.eta = ""
                if job.on_update:
                    job.on_update()

        return hook
