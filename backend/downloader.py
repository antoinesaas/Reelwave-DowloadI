"""yt-dlp download engine with progress SSE support."""
from __future__ import annotations

import asyncio
import re
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator

import yt_dlp

DOWNLOAD_DIR = Path("/tmp/reelwave")
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

FORMAT_MAP = {
    "4K":    "bestvideo[height<=2160][ext=mp4]+bestaudio[ext=m4a]/best[height<=2160]",
    "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
    "720p":  "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "MP3":   "bestaudio/best",
}


def _friendly_error(msg: str) -> str:
    m = msg.lower()
    if "403" in m or "private" in m:    return "Vidéo privée ou accès refusé."
    if "unavailable" in m or "removed" in m: return "Vidéo supprimée ou indisponible."
    if "sign in" in m or "login" in m:  return "Contenu réservé aux membres connectés."
    if "ffmpeg" in m:  return "FFmpeg requis pour cette qualité."
    if "429" in m or "rate" in m: return "Trop de requêtes. Patientez quelques secondes."
    return msg.split("\n")[0][:120]


@dataclass
class DownloadJob:
    job_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    url: str = ""
    quality: str = "1080p"
    status: str = "pending"   # pending | downloading | done | error | cancelled
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    title: str = ""
    thumbnail: str = ""
    platform: str = "Web"
    filepath: Path | None = None
    filename: str = ""
    error: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    _queue: asyncio.Queue = field(default_factory=asyncio.Queue, repr=False, compare=False)
    _loop: asyncio.AbstractEventLoop | None = field(default=None, repr=False, compare=False)
    _cancelled: bool = field(default=False, repr=False, compare=False)


class DownloadManager:
    def __init__(self) -> None:
        self._jobs: dict[str, DownloadJob] = {}

    def get(self, job_id: str) -> DownloadJob | None:
        return self._jobs.get(job_id)

    def create_job(self, url: str, quality: str) -> DownloadJob:
        job = DownloadJob(url=url, quality=quality)
        self._jobs[job.job_id] = job
        return job

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.status == "downloading":
            job._cancelled = True
            job.status = "cancelled"
            return True
        return False

    async def get_info(self, url: str) -> dict:
        """Extract video metadata without downloading."""
        opts = {"quiet": True, "no_warnings": True, "skip_download": True}
        loop = asyncio.get_running_loop()

        def _extract():
            with yt_dlp.YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await loop.run_in_executor(None, _extract)

        formats: list[dict] = []
        for q, fmt_str in FORMAT_MAP.items():
            formats.append({"quality": q, "format": fmt_str})

        return {
            "title":    info.get("title", ""),
            "thumbnail": info.get("thumbnail", ""),
            "duration": info.get("duration") or 0,
            "uploader": info.get("uploader") or info.get("channel", ""),
            "platform": info.get("extractor_key", "Web"),
            "formats":  formats,
        }

    async def stream_download(self, job: DownloadJob) -> AsyncIterator[dict[str, Any]]:
        """Start download and yield SSE events."""
        loop = asyncio.get_running_loop()
        job._loop = loop

        # Kick off the download in a thread
        thread = threading.Thread(target=self._run_download, args=(job,), daemon=True)
        thread.start()

        # Stream progress events
        while True:
            try:
                event = await asyncio.wait_for(job._queue.get(), timeout=60.0)
            except asyncio.TimeoutError:
                yield {"type": "error", "message": "Timeout"}
                break

            yield event
            if event["type"] in ("done", "error"):
                break

    def _run_download(self, job: DownloadJob) -> None:
        """Thread target: runs yt-dlp, sends updates via queue."""
        loop = job._loop

        def _send(event: dict) -> None:
            if loop and loop.is_running():
                asyncio.run_coroutine_threadsafe(job._queue.put(event), loop)

        def progress_hook(d: dict) -> None:
            if job._cancelled:
                raise yt_dlp.utils.DownloadError("Cancelled")

            if d["status"] == "downloading":
                job.status = "downloading"
                total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                downloaded = d.get("downloaded_bytes", 0)
                job.progress = (downloaded / total) if total else 0.0

                speed = d.get("speed") or 0
                job.speed = (
                    f"{speed/1_048_576:.1f} MB/s" if speed > 1_048_576
                    else f"{speed/1024:.0f} KB/s" if speed > 0 else ""
                )
                eta = d.get("eta")
                if eta is not None:
                    job.eta = f"{eta//60}m {eta%60}s" if eta >= 60 else f"{eta}s"

                _send({
                    "type": "progress",
                    "percent": round(job.progress * 100, 1),
                    "speed": job.speed,
                    "eta": job.eta,
                })

        out_dir = DOWNLOAD_DIR / job.job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        outtmpl = str(out_dir / "%(title)s.%(ext)s")

        ydl_opts: dict = {
            "format":  FORMAT_MAP.get(job.quality, FORMAT_MAP["1080p"]),
            "outtmpl": outtmpl,
            "quiet":   True,
            "no_warnings": True,
            "progress_hooks": [progress_hook],
            "merge_output_format": "mp4",
            "postprocessors": [],
        }

        if job.quality == "MP3":
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(job.url, download=True)
                if info:
                    job.title     = info.get("title", "")
                    job.thumbnail = info.get("thumbnail", "")
                    # Find downloaded file
                    filepath = Path(ydl.prepare_filename(info))
                    if job.quality == "MP3":
                        filepath = filepath.with_suffix(".mp3")
                    job.filepath = filepath
                    job.filename = filepath.name

            job.status   = "done"
            job.progress = 1.0
            _send({
                "type":      "done",
                "job_id":    job.job_id,
                "title":     job.title,
                "thumbnail": job.thumbnail,
                "filename":  job.filename,
            })

        except Exception as exc:
            if not job._cancelled:
                job.status = "error"
                job.error  = _friendly_error(str(exc))
                _send({"type": "error", "message": job.error})


manager = DownloadManager()
