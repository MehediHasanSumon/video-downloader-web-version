# Video Downloader Pro (Web GUI Version)

A modern full-stack web downloader with real-time Server-Sent Events (SSE) progress streaming.

### Tech Stack:
- **Frontend**: React 19, TypeScript, Tailwind CSS v4, Lucide Icons, Vite.
- **Backend**: FastAPI, Uvicorn, yt-dlp, FFmpeg.
- **Streaming**: Server-Sent Events (SSE) for instant, lag-free progress updates.

### Project Structure:
```text
web-version/
├── frontend/               # React 19 + TypeScript + Vite + Tailwind CSS Web UI
│   ├── src/                # Components, pages, services, types
│   ├── public/             # Static public assets
│   ├── index.html          # Web entry HTML
│   ├── package.json        # Node dependencies & build scripts
│   └── vite.config.ts      # Vite build & reverse-proxy configuration
│
├── server/                 # FastAPI + yt-dlp Backend Server
│   ├── core/               # Configuration, models, detector, sanitizer, logger
│   ├── downloader/         # Download engine, disk checker, yt-dlp options
│   ├── utils/              # System utilities, clipboard, notifications
│   ├── app.py              # FastAPI REST API & SSE streaming endpoints
│   ├── manager.py          # Download job manager & background worker
│   ├── schemas.py          # Pydantic request / response schemas
│   ├── main.py             # Server runner & Uvicorn entrypoint
│   ├── setup_ffmpeg.py     # Automatic FFmpeg installer
│   ├── requirements.txt    # Python backend dependencies
│   ├── downloads/          # Downloaded media destination folder
│   ├── run.sh / run.bat    # Server-only standalone runner scripts
│   └── venv/               # Python virtual environment
│
├── run.sh                  # Root Linux/macOS full-stack launcher
├── run.bat                 # Root Windows full-stack launcher
└── README.md
```

### Features:
- 🌐 Multi-platform support: YouTube (up to 8K), Facebook (HD/SD reels/watch), Instagram, TikTok, Twitter/X.
- ⚡ Lossless FFmpeg audio/video stream pairing and server-side merging.
- 📊 Exact real-world stream file size calculation and codec badges.
- 🎬 In-browser media preview player with timeline seeking and audio/video auto-detection.
- 🚀 Real-time Server-Sent Events (SSE) progress bar with download speed, ETA, and byte counters.
- 🛡️ Built-in anti-bot client rotation (`web_embedded`, `android`, `mweb`).
- 📦 Full production deployment support: Docker, Docker Compose, Nginx reverse proxy, and 1-click Linux VPS installer.

### Production VPS Deployment:

#### Option 1: 1-Click Native VPS Installer (Recommended for Ubuntu/Debian)
Run this single command on your VPS:
```bash
sudo bash deploy.sh
```
*This automatically configures Python, FFmpeg, Node, Nginx reverse proxy, UFW firewall, and installs the Systemd background service.*

#### Option 2: Docker Compose
```bash
docker compose up -d --build
```
*Runs the containerized stack with auto-restart and isolated dependencies on port 5000.*

---

### How to Run Locally:

#### Linux / macOS:
```bash
./run.sh
```
*(Automatically starts the server on port 5000 and opens your browser)*

#### Windows:
Double-click `run.bat` or run:
```cmd
run.bat
```

#### Frontend Development Mode:
If you want to modify the React frontend:
```bash
cd frontend
npm install
npm run dev
```
*(Runs Vite with hot module replacement at http://localhost:5173, proxying API requests to FastAPI)*
