# ReelWave ✦

> Download anything. No ads. No limits.

A premium video downloader with an animated 3D particle sphere UI.  
Supports YouTube · TikTok · Instagram · Pinterest · Twitter/X · Vimeo.

---

## Stack

| Layer    | Tech                                        |
|----------|---------------------------------------------|
| Frontend | React 18 · Vite · Tailwind · Framer Motion · Three.js |
| Backend  | FastAPI · yt-dlp · SSE streaming            |
| 4K       | Server-side FFmpeg (Docker) — zero client install |

---

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
> Requires **FFmpeg** installed on the server for 4K merging.  
> Or use Docker: `docker build -t reelwave-api . && docker run -p 8000:8000 reelwave-api`

### Frontend
```bash
cd frontend
npm install
npm run dev       # → http://localhost:5173
npm run build     # → dist/
```

---

## UX Flow

```
[3D Particle Sphere] ──click──► [Explode → Ring → Logo orb]
      ↓
[Paste URL panel]  ──valid URL──►  [Quality bubbles: 4K / 1080p / 720p / 480p / MP3]
      ↓
[Télécharger →]  ──SSE stream──►  [Progress card: speed · ETA · %]
      ↓
[File saved to browser downloads ✓]
```

---

## API Endpoints

| Method | Path                  | Description                         |
|--------|-----------------------|-------------------------------------|
| POST   | `/api/info`           | Get video metadata                  |
| POST   | `/api/start`          | Create download job → `{job_id}`    |
| GET    | `/api/download/:id`   | SSE stream: progress / done / error |
| GET    | `/api/file/:id`       | Serve the downloaded file           |
| POST   | `/api/cancel/:id`     | Cancel in-progress download         |

---

## Deploy

**Frontend → Vercel**
```bash
cd frontend && npx vercel --prod
```

**Backend → Railway / Render**  
Push to GitHub and connect the `/backend` folder.  
Set env var `PORT=8000`.  
The `Dockerfile` handles FFmpeg installation automatically.

**CORS**: Set `VITE_API_URL=https://api.reelwave.com` in Vercel env vars.

---

## File Structure

```
reelwave/
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ParticleSphere.jsx   ← Three.js 4200-particle sphere
│   │   │   ├── PastePanel.jsx       ← Glass URL input card
│   │   │   ├── QualityBubbles.jsx   ← iOS 26 floating quality pills
│   │   │   ├── DownloadCard.jsx     ← SSE progress card
│   │   │   ├── HistoryPanel.jsx     ← Drawer history
│   │   │   └── CustomCursor.jsx     ← Magnetic dot cursor
│   │   ├── hooks/
│   │   │   ├── useDownload.js       ← SSE + job state
│   │   │   └── useClipboard.js
│   │   └── App.jsx                  ← State machine orchestrator
│   └── vite.config.js
└── backend/
    ├── main.py                      ← FastAPI routes
    ├── downloader.py                ← yt-dlp engine + SSE
    ├── platforms.py                 ← URL detection
    ├── Dockerfile                   ← FFmpeg included
    └── requirements.txt
```
