"""Vercel serverless function — get direct download URL via yt-dlp (no FFmpeg needed)."""
from http.server import BaseHTTPRequestHandler
import json
import re
import yt_dlp

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

# Pre-muxed formats only (no FFmpeg needed). Falls back gracefully.
FORMATS = {
    "4K":    "best[height<=2160][vcodec!=none][acodec!=none]/best[height<=2160]/best",
    "1080p": "best[height<=1080][vcodec!=none][acodec!=none]/best[height<=1080]/best",
    "720p":  "best[height<=720][vcodec!=none][acodec!=none]/best[height<=720]/best",
    "480p":  "best[height<=480][vcodec!=none][acodec!=none]/best[height<=480]/best",
    "MP3":   "bestaudio[ext=m4a]/bestaudio",
}

def safe_filename(title: str, ext: str) -> str:
    name = re.sub(r'[\\/*?:"<>|]', "", title)[:80]
    return f"{name}.{ext}" if name else f"reelwave-download.{ext}"

class handler(BaseHTTPRequestHandler):

    def _send(self, code: int, body: bytes, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(200, b"")

    def do_POST(self):
        try:
            length  = int(self.headers.get("Content-Length", 0))
            body    = json.loads(self.rfile.read(length))
            url     = body.get("url", "").strip()
            quality = body.get("quality", "720p")
            if not url:
                raise ValueError("URL manquante")

            fmt = FORMATS.get(quality, FORMATS["720p"])

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "format": fmt,
                "socket_timeout": 8,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            # Resolve the actual download URL
            if "url" in info:
                dl_url = info["url"]
                ext    = info.get("ext", "mp4")
            elif info.get("formats"):
                # Pick last (best) format that has a URL
                for f in reversed(info["formats"]):
                    if f.get("url"):
                        dl_url = f["url"]
                        ext    = f.get("ext", "mp4")
                        break
                else:
                    raise ValueError("Aucun lien de téléchargement trouvé")
            else:
                raise ValueError("Aucun lien de téléchargement trouvé")

            title    = info.get("title") or "video"
            filename = safe_filename(title, "mp3" if quality == "MP3" else ext)

            result = {
                "url":      dl_url,
                "filename": filename,
                "title":    title,
                "ext":      ext,
                "thumbnail": info.get("thumbnail") or "",
            }
            self._send(200, json.dumps(result).encode())

        except Exception as e:
            self._send(400, json.dumps({"detail": str(e)}).encode())

    def log_message(self, *_):
        pass
