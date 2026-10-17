import os
import sys
import json
import time
import re
import asyncio
import urllib.parse
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles

# Add server directory and project root to sys.path
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SERVER_DIR)
for p in (SERVER_DIR, PROJECT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import yt_dlp
from core.config import (
    ROOT_DIR,
    SERVER_DIR,
    DEFAULT_DOWNLOAD_DIR,
    COOKIES_FILE,
    YOUTUBE_FORMAT_PROFILES,
    SOCIAL_FORMAT_PROFILES,
    FILE_RETENTION_SECONDS,
    PROXY_URL,
    APP_NAME,
    VERSION,
)
from core.detector import PlatformDetector
from core.sanitizer import Sanitizer
from core.models import MediaInfo, FormatOption
from downloader.options import get_available_js_runtimes
from utils.system import SystemUtils

try:
    from schemas import (
        MediaInfoRequest,
        MediaInfoResponse,
        FormatProfileSchema,
        DownloadRequest,
        JobStatusResponse,
        LibraryFileItem,
        ActionResponse,
        CookiesStatusResponse,
        StorageStatsResponse,
    )
    from manager import DownloadJobManager
except ImportError:
    from server.schemas import (
        MediaInfoRequest,
        MediaInfoResponse,
        FormatProfileSchema,
        DownloadRequest,
        JobStatusResponse,
        LibraryFileItem,
        ActionResponse,
        CookiesStatusResponse,
        StorageStatsResponse,
    )
job_manager = DownloadJobManager.get_instance()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Auto-cleanup background task for VPS zero-bloat storage
    stop_event = asyncio.Event()

    async def periodic_cleaner():
        while not stop_event.is_set():
            try:
                await asyncio.sleep(60)
                purged = job_manager.cleanup_expired_files(FILE_RETENTION_SECONDS)
                if purged > 0:
                    print(f"\033[93m[VPS Auto-Cleanup]\033[0m Purged {purged} expired temporary file(s).")
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"[Cleanup Error] {e}")

    cleaner_task = asyncio.create_task(periodic_cleaner())
    yield
    stop_event.set()
    cleaner_task.cancel()

app = FastAPI(
    title=f"{APP_NAME} Web API",
    version=VERSION,
    description="REST & SSE API for Universal Multi-Platform Media Downloader",
    lifespan=lifespan,
)

# Enable CORS for local development (e.g. Vite on port 5173 / localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "app": APP_NAME,
        "version": VERSION,
        "ffmpeg_available": SystemUtils.is_ffmpeg_available(),
    }

@app.post("/api/info", response_model=MediaInfoResponse)
async def get_media_info(req: MediaInfoRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    platform = PlatformDetector.detect(url)
    ydl_opts: Dict[str, Any] = {
        "extract_flat": "in_playlist",
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "extractor_args": {
            "youtube": {
                "player_client": ["web_embedded", "android", "mweb", "web"],
            }
        },
    }
    js_runtimes = get_available_js_runtimes()
    if js_runtimes:
        ydl_opts["js_runtimes"] = js_runtimes
        ydl_opts["remote_components"] = ["ejs:github"]

    if os.path.isfile(COOKIES_FILE):
        ydl_opts["cookiefile"] = COOKIES_FILE

    if PROXY_URL:
        ydl_opts["proxy"] = PROXY_URL

    # Run extraction in thread pool to prevent blocking the async event loop
    loop = asyncio.get_event_loop()
    try:
        def extract():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)

        info = await loop.run_in_executor(None, extract)
        if not info:
            raise HTTPException(status_code=404, detail="Could not extract metadata from URL")

        is_playlist = info.get("_type") == "playlist" or "entries" in info
        clean_title = Sanitizer.clean_media_title(info, platform.key)
        uploader = info.get("uploader") or info.get("channel") or info.get("uploader_id") or "Unknown"
        raw_duration = info.get("duration")
        try:
            duration = float(raw_duration) if raw_duration is not None else None
        except (ValueError, TypeError):
            duration = None

        raw_views = info.get("view_count")
        try:
            views = int(raw_views) if raw_views is not None else None
        except (ValueError, TypeError):
            views = None
        thumbnail = info.get("thumbnail")

        # Pick best thumbnail from thumbnails list if not at root
        if not thumbnail and info.get("thumbnails"):
            thumbs = info.get("thumbnails")
            if isinstance(thumbs, list) and thumbs:
                thumbnail = thumbs[-1].get("url")

        playlist_count = None
        if is_playlist:
            entries = list(info.get("entries") or [])
            playlist_count = len(entries) if entries else info.get("playlist_count")

        # Build format options
        raw_profiles = SOCIAL_FORMAT_PROFILES if platform.key in ("facebook", "instagram", "tiktok", "twitter") else YOUTUBE_FORMAT_PROFILES
        real_sizes = Sanitizer.calculate_format_sizes(info, platform.key, duration)
        format_schemas: List[FormatProfileSchema] = []
        for p in raw_profiles:
            opt = FormatOption(**p)
            est = real_sizes.get(opt.id) or opt.estimated_size_str(duration)
            format_schemas.append(
                FormatProfileSchema(
                    id=opt.id,
                    name=opt.name,
                    badge=opt.badge,
                    desc=opt.desc,
                    ext=opt.ext,
                    tag=opt.tag,
                    tag_color=opt.tag_color,
                    est_size=est,
                    codec=opt.codec,
                )
            )

        return MediaInfoResponse(
            title=clean_title,
            url=url,
            platform_key=platform.key,
            platform_name=platform.name,
            platform_color=platform.color,
            platform_icon=platform.icon,
            uploader=uploader,
            duration=duration,
            duration_str=Sanitizer.format_duration(duration),
            views=views,
            views_str=Sanitizer.format_views(views),
            thumbnail=thumbnail,
            is_playlist=is_playlist,
            playlist_count=playlist_count,
            formats=format_schemas,
        )

    except Exception as e:
        raw_msg = str(e)
        ansi_clean = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', raw_msg)
        clean_msg = re.sub(r'^(ERROR:\s*)+', '', ansi_clean.strip())
        err_lower = clean_msg.lower()
        if any(w in err_lower for w in ("sign in", "login", "cookie", "private", "bot")):
            raise HTTPException(
                status_code=403,
                detail=f"This media is private or requires authentication: {clean_msg}",
            )
        raise HTTPException(status_code=400, detail=f"Failed to fetch media: {clean_msg}")

@app.post("/api/download")
async def start_download(req: DownloadRequest):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL cannot be empty")

    job_id = job_manager.create_job(
        url=url,
        format_id=req.format_id,
        is_playlist=req.is_playlist,
        playlist_range=req.playlist_range,
        playlist_title=req.playlist_title,
    )
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/progress/{job_id}", response_model=JobStatusResponse)
async def get_progress(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/progress/{job_id}/stream")
async def stream_progress(job_id: str, request: Request):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    queue = job_manager.subscribe(job_id)

    async def event_generator():
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=1.0)
                    # Convert to JSON event
                    payload = json.dumps(data)
                    yield f"data: {payload}\n\n"
                    if data.get("status") in ("completed", "failed"):
                        break
                except asyncio.TimeoutError:
                    # Keep-alive heartbeat ping
                    yield ": ping\n\n"
        finally:
            job_manager.unsubscribe(job_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

@app.get("/api/download/file/{job_id}")
async def download_single_file(job_id: str, background_tasks: BackgroundTasks, auto_delete: bool = False):
    job = job_manager.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Download job not found")

    filepaths = job.get("completed_filepaths", [])
    if not filepaths:
        raise HTTPException(status_code=404, detail="No files available for this download")

    target_file = filepaths[0]
    if not os.path.isfile(target_file):
        raise HTTPException(status_code=404, detail="File has already been cleaned or expired")

    filename = os.path.basename(target_file)

    if auto_delete:
        def delay_delete(p: str, jid: str):
            time.sleep(30)
            job_manager.cleanup_job_files(jid)
        background_tasks.add_task(delay_delete, target_file, job_id)

    return FileResponse(
        target_file,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{urllib.parse.quote(filename)}"'}
    )

@app.get("/api/download/file/{job_id}/{filename}")
async def download_specific_file(job_id: str, filename: str):
    job = job_manager.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Download job not found")

    filepaths = job.get("completed_filepaths", [])
    target = None
    for fp in filepaths:
        if os.path.basename(fp) == filename:
            target = fp
            break

    if not target or not os.path.isfile(target):
        dest = job.get("destination_path")
        if dest and os.path.isfile(os.path.join(dest, filename)):
            target = os.path.join(dest, filename)
        else:
            raise HTTPException(status_code=404, detail="File not found or expired")

    return FileResponse(
        target,
        filename=filename,
        headers={"Content-Disposition": f'attachment; filename="{urllib.parse.quote(filename)}"'}
    )

@app.get("/api/download/zip/{job_id}")
async def download_zip_archive(job_id: str):
    import zipfile
    job = job_manager.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Download job not found")

    filepaths = [fp for fp in job.get("completed_filepaths", []) if os.path.isfile(fp)]
    if not filepaths:
        raise HTTPException(status_code=404, detail="No files available to package")

    safe_title = Sanitizer.clean_filename(job.get("playlist_title") or "media_bundle")
    zip_filename = f"{safe_title}_{job_id}.zip"
    zip_path = os.path.join(DEFAULT_DOWNLOAD_DIR, zip_filename)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for fp in filepaths:
            zipf.write(fp, arcname=os.path.basename(fp))

    return FileResponse(
        zip_path,
        filename=zip_filename,
        headers={"Content-Disposition": f'attachment; filename="{urllib.parse.quote(zip_filename)}"'}
    )

@app.delete("/api/download/file/{job_id}", response_model=ActionResponse)
async def delete_job_files_endpoint(job_id: str):
    success = job_manager.cleanup_job_files(job_id)
    if not success:
        raise HTTPException(status_code=404, detail="Job not found or already cleaned")
    return ActionResponse(success=True, message=f"Temporary files for job {job_id} deleted from VPS.")

@app.get("/api/stream/{job_id}")
@app.get("/api/stream/{job_id}/{filename}")
async def stream_media_in_browser(job_id: str, filename: Optional[str] = None):
    job = job_manager.jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Download job not found")

    filepaths = [fp for fp in job.get("completed_filepaths", []) if os.path.isfile(fp)]
    target = None
    if filename:
        unquoted = urllib.parse.unquote(filename)
        for fp in filepaths:
            if os.path.basename(fp) in (filename, unquoted):
                target = fp
                break
    if not target and filepaths:
        target = filepaths[0]

    if not target or not os.path.isfile(target):
        dest = job.get("destination_path")
        if dest and os.path.isdir(dest):
            for root, _, files in os.walk(dest):
                for f in files:
                    if not f.endswith((".part", ".ytdl", ".temp", ".zip")):
                        cand = os.path.join(root, f)
                        if os.path.isfile(cand):
                            target = cand
                            break
                if target:
                    break

    if not target or not os.path.isfile(target):
        raise HTTPException(status_code=404, detail="Media file not found or expired")

    ext = os.path.splitext(target)[1].lower()
    mime_map = {
        ".mp4": "video/mp4",
        ".webm": "video/webm",
        ".mkv": "video/webm",
        ".mov": "video/quicktime",
        ".mp3": "audio/mpeg",
        ".m4a": "audio/mp4",
        ".aac": "audio/aac",
        ".wav": "audio/wav",
        ".opus": "audio/opus",
        ".ogg": "audio/ogg",
    }
    media_type = mime_map.get(ext, "video/mp4")
    return FileResponse(
        target,
        media_type=media_type,
        content_disposition_type="inline",
        headers={
            "Accept-Ranges": "bytes",
            "Cache-Control": "public, max-age=3600",
        }
    )

@app.get("/api/storage", response_model=StorageStatsResponse)
async def get_storage_stats_endpoint():
    return StorageStatsResponse(**job_manager.get_storage_stats())

@app.post("/api/cleanup", response_model=ActionResponse)
async def manual_cleanup_endpoint():
    count = job_manager.cleanup_all_storage()
    return ActionResponse(success=True, message=f"Purged {count} temporary files from VPS storage.")

@app.get("/api/raw-download")
async def raw_file_download(path: str):
    full_path = os.path.abspath(os.path.join(DEFAULT_DOWNLOAD_DIR, path))
    if not full_path.startswith(os.path.abspath(DEFAULT_DOWNLOAD_DIR)) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    fname = os.path.basename(full_path)
    return FileResponse(
        full_path,
        filename=fname,
        headers={"Content-Disposition": f'attachment; filename="{urllib.parse.quote(fname)}"'}
    )

@app.get("/api/raw-stream")
async def raw_file_stream(path: str):
    full_path = os.path.abspath(os.path.join(DEFAULT_DOWNLOAD_DIR, path))
    if not full_path.startswith(os.path.abspath(DEFAULT_DOWNLOAD_DIR)) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(full_path)

@app.delete("/api/downloads/file", response_model=ActionResponse)
async def delete_cached_file(path: str):
    full_path = os.path.abspath(os.path.join(DEFAULT_DOWNLOAD_DIR, path))
    if not full_path.startswith(os.path.abspath(DEFAULT_DOWNLOAD_DIR)) or not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="File not found")
    try:
        os.remove(full_path)
        return ActionResponse(success=True, message="File deleted from VPS cache")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/downloads", response_model=List[LibraryFileItem])
async def list_downloaded_files():
    items: List[LibraryFileItem] = []
    if not os.path.isdir(DEFAULT_DOWNLOAD_DIR):
        return items

    valid_exts = {
        ".mp4": "video",
        ".mkv": "video",
        ".webm": "video",
        ".avi": "video",
        ".mov": "video",
        ".mp3": "audio",
        ".m4a": "audio",
        ".opus": "audio",
        ".aac": "audio",
        ".flac": "audio",
        ".wav": "audio",
    }

    for root, _, files in os.walk(DEFAULT_DOWNLOAD_DIR):
        for f in files:
            if f.endswith((".part", ".ytdl", ".m3u")):
                continue
            _, ext = os.path.splitext(f.lower())
            if ext in valid_exts:
                full_path = os.path.join(root, f)
                try:
                    st = os.stat(full_path)
                    rel = os.path.relpath(full_path, DEFAULT_DOWNLOAD_DIR)
                    plat = rel.split(os.sep)[0] if os.sep in rel else "Direct"
                    items.append(
                        LibraryFileItem(
                            filename=f,
                            filepath=full_path,
                            relative_path=rel,
                            platform=plat,
                            size_bytes=st.st_size,
                            size_str=Sanitizer.format_file_size(st.st_size),
                            modified_time=st.st_mtime,
                            modified_str=time.strftime("%Y-%m-%d %H:%M", time.localtime(st.st_mtime)),
                            media_type=valid_exts[ext],
                            download_url=f"/api/raw-download?path={urllib.parse.quote(rel)}",
                            stream_url=f"/api/raw-stream?path={urllib.parse.quote(rel)}",
                        )
                    )
                except Exception:
                    pass

    # Sort descending by modified time (newest first)
    items.sort(key=lambda x: x.modified_time, reverse=True)
    return items

@app.post("/api/play", response_model=ActionResponse)
async def play_media_file(payload: Dict[str, str]):
    fpath = payload.get("filepath", "")
    if not fpath or not os.path.isfile(fpath):
        raise HTTPException(status_code=404, detail="File does not exist")
    # For headless VPS environment, safely return success
    SystemUtils.play_media(fpath)
    return ActionResponse(success=True, message=f"Playing {os.path.basename(fpath)}")

@app.post("/api/open-folder", response_model=ActionResponse)
async def open_download_folder(payload: Dict[str, Optional[str]] = {}):
    target = payload.get("folder_path") or DEFAULT_DOWNLOAD_DIR
    SystemUtils.open_folder(target)
    return ActionResponse(success=True, message=f"Storage directory: {target}")

@app.get("/api/cookies", response_model=CookiesStatusResponse)
async def get_cookies_status():
    exists = os.path.isfile(COOKIES_FILE)
    count = 0
    if exists:
        try:
            with open(COOKIES_FILE, "r", encoding="utf-8", errors="ignore") as cf:
                count = sum(1 for line in cf if line.strip() and not line.startswith("#"))
        except Exception:
            pass
    return CookiesStatusResponse(exists=exists, path=COOKIES_FILE, line_count=count)

@app.post("/api/cookies", response_model=ActionResponse)
async def save_cookies_file(payload: Dict[str, str]):
    content = payload.get("content", "")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Cookie content cannot be empty")
    try:
        with open(COOKIES_FILE, "w", encoding="utf-8") as cf:
            cf.write(content.strip() + "\n")
        return ActionResponse(success=True, message="cookies.txt saved successfully")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save cookies file: {e}")

# Mount built React web app if frontend/dist or web/dist exists
FRONTEND_DIST = os.path.join(ROOT_DIR, "frontend", "dist")
WEB_DIST = os.path.join(ROOT_DIR, "web", "dist")
DIST_DIR = FRONTEND_DIST if os.path.isdir(FRONTEND_DIST) else WEB_DIST
if os.path.isdir(DIST_DIR):
    assets_dir = os.path.join(DIST_DIR, "assets")
    if os.path.isdir(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse(os.path.join(DIST_DIR, "index.html"))

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        # Don't intercept API calls if an undefined /api path is requested
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = os.path.join(DIST_DIR, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(DIST_DIR, "index.html"))
