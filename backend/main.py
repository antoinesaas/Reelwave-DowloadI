"""ReelWave FastAPI backend."""
from __future__ import annotations

import json
from pathlib import Path

import aiofiles
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from downloader import manager
from platforms import detect

app = FastAPI(title="ReelWave API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://reelwave.com",
        "https://www.reelwave.com",
        "http://localhost:5173",
        "http://localhost:4173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Models ───────────────────────────────────────────────────────────────────

class InfoRequest(BaseModel):
    url: str


class DownloadRequest(BaseModel):
    url: str
    quality: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "service": "ReelWave API"}


@app.post("/api/info")
async def get_info(body: InfoRequest):
    """Return video metadata without downloading."""
    try:
        info = await manager.get_info(body.url)
        platform = detect(body.url)
        info["platform"]      = platform.name
        info["platform_slug"] = platform.slug
        info["platform_color"] = platform.color
        return info
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)[:200])


@app.post("/api/start")
async def start_download(body: DownloadRequest):
    """Create a download job and return the job_id for SSE subscription."""
    job = manager.create_job(url=body.url, quality=body.quality)
    return {"job_id": job.job_id}


@app.get("/api/download/{job_id}")
async def download_sse(job_id: str):
    """SSE stream — emits progress/done/error events."""
    job = manager.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    async def event_gen():
        async for event in manager.stream_download(job):
            yield {"data": json.dumps(event)}

    return EventSourceResponse(event_gen())


@app.get("/api/file/{job_id}")
async def serve_file(job_id: str):
    """Serve the downloaded file for the browser to save."""
    job = manager.get(job_id)
    if not job or not job.filepath or not job.filepath.exists():
        raise HTTPException(status_code=404, detail="File not found")

    media_type = "audio/mpeg" if str(job.filepath).endswith(".mp3") else "video/mp4"
    return FileResponse(
        path=str(job.filepath),
        filename=job.filename,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{job.filename}"'},
    )


@app.post("/api/cancel/{job_id}")
async def cancel_download(job_id: str):
    """Cancel an in-progress download."""
    success = manager.cancel(job_id)
    return {"cancelled": success}


@app.delete("/api/file/{job_id}")
async def cleanup_file(job_id: str, background_tasks: BackgroundTasks):
    """Remove temp files for a completed job."""
    job = manager.get(job_id)
    if job and job.filepath:
        background_tasks.add_task(_delete_job_dir, job_id)
    return {"ok": True}


def _delete_job_dir(job_id: str) -> None:
    import shutil
    job_dir = Path("/tmp/reelwave") / job_id
    shutil.rmtree(job_dir, ignore_errors=True)
