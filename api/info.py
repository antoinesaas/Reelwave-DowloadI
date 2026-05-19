"""Vercel serverless — extract video metadata via yt-dlp."""
from http.server import BaseHTTPRequestHandler
import json

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}

PLATFORM_MAP = {
    "youtube": "YouTube", "youtu.be": "YouTube",
    "tiktok":  "TikTok",  "instagram": "Instagram",
    "pinterest": "Pinterest", "twitter": "Twitter/X", "x.com": "Twitter/X",
}

def detect_platform(url: str) -> str:
    u = url.lower()
    for k, v in PLATFORM_MAP.items():
        if k in u:
            return v
    return "Web"

def friendly_error(e: Exception) -> str:
    msg = str(e)
    if "Unsupported URL" in msg or "unsupported url" in msg.lower():
        return "URL non supportée. Essaie YouTube, TikTok, Instagram, Pinterest ou Twitter/X."
    if "Private video" in msg or "private" in msg.lower():
        return "Cette vidéo est privée."
    if "age" in msg.lower() or "sign in" in msg.lower() or "login" in msg.lower():
        return "Cette vidéo est restreinte par YouTube. Essaie avec une autre vidéo ou une URL TikTok/Instagram."
    if "not available" in msg.lower() or "unavailable" in msg.lower():
        return "Cette vidéo n'est pas disponible."
    if "HTTP Error 403" in msg:
        return "Accès refusé par la plateforme (403)."
    if "HTTP Error 404" in msg:
        return "Vidéo introuvable (404)."
    if "timeout" in msg.lower() or "timed out" in msg.lower():
        return "Délai dépassé. Réessaie dans quelques secondes."
    return f"Erreur : {msg[:120]}"

class handler(BaseHTTPRequestHandler):

    def _send(self, code: int, body: bytes, content_type="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        for k, v in CORS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(200, b"{}")

    def do_POST(self):
        try:
            import yt_dlp
        except ImportError:
            self._send(500, json.dumps({"detail": "yt-dlp non installé sur le serveur."}).encode())
            return

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
                "socket_timeout": 10,
                # Use Android client — bypasses most YouTube age/login restrictions
                "extractor_args": {
                    "youtube": {
                        "player_client": ["android", "web"],
                        "skip": ["hls"],
                    }
                },
                "http_headers": {
                    "User-Agent": "com.google.android.youtube/19.09.37 (Linux; U; Android 11) gzip"
                },
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
            self._send(400, json.dumps({"detail": friendly_error(e)}).encode())

    def log_message(self, *_):
        pass
