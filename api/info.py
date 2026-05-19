"""Vercel serverless function — extract video metadata via yt-dlp."""
from http.server import BaseHTTPRequestHandler
import json
import yt_dlp

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

PLATFORM_MAP = {
    "youtube": "YouTube", "youtu": "YouTube",
    "tiktok": "TikTok", "instagram": "Instagram",
    "pinterest": "Pinterest", "twitter": "Twitter/X", "x.com": "Twitter/X",
}

def detect_platform(url: str) -> str:
    u = url.lower()
    for k, v in PLATFORM_MAP.items():
        if k in u:
            return v
    return "Web"

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
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))
            url    = body.get("url", "").strip()
            if not url:
                raise ValueError("URL manquante")

            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "skip_download": True,
                "socket_timeout": 8,
                "extract_flat": False,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            result = {
                "title":     info.get("title") or "Vidéo",
                "thumbnail": info.get("thumbnail") or "",
                "duration":  info.get("duration") or 0,
                "platform":  detect_platform(url),
                "uploader":  info.get("uploader") or "",
            }
            self._send(200, json.dumps(result).encode())

        except Exception as e:
            self._send(400, json.dumps({"detail": str(e)}).encode())

    def log_message(self, *_):
        pass
