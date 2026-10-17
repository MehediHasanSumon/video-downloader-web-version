import os
import sys
import time
import uuid
import asyncio
import threading
import urllib.parse
import shutil
from typing import Dict, List, Optional, Any
from concurrent.futures import ThreadPoolExecutor

# Add server directory and project root to sys.path
SERVER_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SERVER_DIR)
for p in (SERVER_DIR, PROJECT_ROOT):
    if p not in sys.path:
        sys.path.insert(0, p)

import yt_dlp
from core.config import (
    DEFAULT_DOWNLOAD_DIR,
    COOKIES_FILE,
    YOUTUBE_FORMAT_PROFILES,
    SOCIAL_FORMAT_PROFILES,
    FILE_RETENTION_SECONDS,
)
from core.models import MediaInfo, FormatOption
from core.detector import PlatformDetector
from core.sanitizer import Sanitizer
from core.logger import AppLogger, YtDlpLogger
from downloader.options import YdlOptionsBuilder, get_available_js_runtimes
from downloader.disk import SmartDiskChecker

try:
    from schemas import JobStatusResponse, DownloadFileInfo
except ImportError:
    from server.schemas import JobStatusResponse, DownloadFileInfo

class DownloadJobManager:
    """Manages active download jobs, progress tracking, and SSE subscribers."""

    _instance: Optional["DownloadJobManager"] = None

    def __init__(self):
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.subscribers: Dict[str, List[asyncio.Queue]] = {}
        self.executor = ThreadPoolExecutor(max_workers=3)
        self.logger = AppLogger.get_logger()

    @classmethod
    def get_instance(cls) -> "DownloadJobManager":
        if cls._instance is None:
            cls._instance = DownloadJobManager()
        return cls._instance

    def create_job(
        self,
        url: str,
        format_id: int,
        is_playlist: bool = False,
        playlist_range: Optional[str] = None,
        playlist_title: Optional[str] = None,
    ) -> str:
        job_id = str(uuid.uuid4())[:8]
        self.jobs[job_id] = {
            "job_id": job_id,
            "url": url,
            "format_id": format_id,
            "is_playlist": is_playlist,
            "playlist_range": playlist_range,
            "playlist_title": playlist_title,
            "status": "queued",
            "percent": 0.0,
            "speed_str": "0 B/s",
            "eta_str": "--:--",
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "downloaded_str": "0 B",
            "total_str": "Calculating...",
            "stream_type": "Media",
            "current_filename": "",
            "completed_files": [],
            "completed_filepaths": [],
            "skipped_files": [],
            "failed_files": [],
            "destination_path": None,
            "elapsed_seconds": 0,
            "error_message": None,
            "start_time": time.time(),
            "completed_time": None,
            "expires_in_seconds": None,
            "download_url": None,
            "zip_url": None,
            "files": [],
        }
        self.subscribers[job_id] = []
        # Submit to background thread pool
        self.executor.submit(self._run_download_task, job_id)
        return job_id

    def get_job(self, job_id: str) -> Optional[JobStatusResponse]:
        data = self.jobs.get(job_id)
        if not data:
            return None
        if data.get("completed_time"):
            elapsed = time.time() - data["completed_time"]
            data["expires_in_seconds"] = max(0, int(FILE_RETENTION_SECONDS - elapsed))
        return JobStatusResponse(**{k: v for k, v in data.items() if k in JobStatusResponse.model_fields})

    def _broadcast_update(self, job_id: str):
        job_data = self.jobs.get(job_id)
        if not job_data:
            return
        if job_data.get("completed_time"):
            elapsed = time.time() - job_data["completed_time"]
            job_data["expires_in_seconds"] = max(0, int(FILE_RETENTION_SECONDS - elapsed))
        queues = list(self.subscribers.get(job_id, []))
        for q in queues:
            try:
                q.put_nowait(dict(job_data))
            except Exception:
                pass

    def subscribe(self, job_id: str) -> asyncio.Queue:
        q = asyncio.Queue()
        if job_id not in self.subscribers:
            self.subscribers[job_id] = []
        self.subscribers[job_id].append(q)
        # Push initial state immediately
        initial = self.jobs.get(job_id)
        if initial:
            q.put_nowait(dict(initial))
        return q

    def unsubscribe(self, job_id: str, q: asyncio.Queue):
        if job_id in self.subscribers and q in self.subscribers[job_id]:
            self.subscribers[job_id].remove(q)

    def _run_download_task(self, job_id: str):
        job = self.jobs[job_id]
        job["status"] = "starting"
        start_time = time.time()
        url = job["url"]
        format_choice = job["format_id"]
        is_playlist = job["is_playlist"]
        playlist_range = job["playlist_range"]

        platform = PlatformDetector.detect(url)
        dest_folder = os.path.join(DEFAULT_DOWNLOAD_DIR, platform.folder)
        os.makedirs(dest_folder, exist_ok=True)
        job["destination_path"] = dest_folder

        completed_files: List[str] = []
        completed_filepaths: List[str] = []
        skipped_files: List[str] = []
        failed_files: List[str] = []
        actual_dest: Optional[str] = None

        def on_skip(fname: str, fsize: str, fpath: str):
            nonlocal actual_dest
            if fname not in skipped_files:
                skipped_files.append(fname)
            if fpath:
                actual_dest = os.path.dirname(fpath)
                if fpath not in completed_filepaths and os.path.isfile(fpath):
                    completed_filepaths.append(fpath)
            job["skipped_files"] = list(skipped_files)
            job["status"] = "downloading"
            self._broadcast_update(job_id)

        def post_hook(filepath: str):
            nonlocal actual_dest
            fname = os.path.basename(filepath) if filepath else "Media"
            if filepath:
                actual_dest = os.path.dirname(filepath)
                if filepath not in completed_filepaths and os.path.isfile(filepath):
                    completed_filepaths.append(filepath)
            if fname not in completed_files:
                completed_files.append(fname)
            job["completed_files"] = list(completed_files)
            self._broadcast_update(job_id)

        def progress_hook(d):
            status = d.get("status")
            if status == "downloading":
                job["status"] = "downloading"
                dl = d.get("downloaded_bytes", 0)
                tot = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                job["downloaded_bytes"] = dl
                job["total_bytes"] = tot
                job["downloaded_str"] = Sanitizer.format_file_size(dl)
                job["total_str"] = Sanitizer.format_file_size(tot) if tot else "Calculating..."
                if tot and tot > 0:
                    pct = min(100.0, (dl / tot) * 100.0)
                    job["percent"] = round(pct, 1)

                speed = d.get("speed")
                if speed:
                    job["speed_str"] = f"{Sanitizer.format_file_size(speed)}/s"

                eta = d.get("eta")
                if eta is not None:
                    job["eta_str"] = Sanitizer.format_duration(eta)

                fname = os.path.basename(d.get("filename", "Media"))
                job["current_filename"] = fname

                info = d.get("info_dict", {})
                vcodec = info.get("vcodec")
                acodec = info.get("acodec")
                if vcodec and vcodec != "none" and (not acodec or acodec == "none"):
                    job["stream_type"] = "Video Stream"
                elif acodec and acodec != "none" and (not vcodec or vcodec == "none"):
                    job["stream_type"] = "Audio Stream"
                else:
                    job["stream_type"] = "Media Stream"

                self._broadcast_update(job_id)

            elif status == "finished":
                job["status"] = "processing"
                job["percent"] = 100.0
                self._broadcast_update(job_id)

        def postprocessor_hook(d):
            status = d.get("status")
            if status == "started":
                job["status"] = "merging"
                job["stream_type"] = "FFmpeg Lossless Muxing"
                self._broadcast_update(job_id)
            elif status == "finished":
                job["status"] = "processing"
                self._broadcast_update(job_id)

        custom_logger = YtDlpLogger(self.logger)
        ydl_opts = YdlOptionsBuilder.build(
            save_path=dest_folder,
            format_choice=format_choice,
            is_playlist=is_playlist,
            progress_hooks=[progress_hook],
            postprocessor_hooks=[postprocessor_hook],
            post_hooks=[post_hook],
            platform_key=platform.key,
            cookies_file=COOKIES_FILE if os.path.isfile(COOKIES_FILE) else None,
            playlist_title=job.get("playlist_title") if is_playlist else None,
            playlist_items=playlist_range if is_playlist else None,
            custom_logger=custom_logger,
        )

        download_ret = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.params["match_filter"] = SmartDiskChecker.create_filter(
                    ydl,
                    format_choice=format_choice,
                    is_playlist=is_playlist,
                    on_skip=on_skip,
                )
                download_ret = ydl.download([url])
        except Exception as e:
            custom_logger.errors.append(str(e))

        # Check search folder to guarantee all completed files are tracked
        search_folder = actual_dest or dest_folder
        if os.path.isdir(search_folder):
            for f in os.listdir(search_folder):
                full_f = os.path.join(search_folder, f)
                if os.path.isfile(full_f) and not f.endswith((".part", ".ytdl", ".temp", ".m3u")):
                    if full_f not in completed_filepaths:
                        try:
                            if os.path.getmtime(full_f) >= (start_time - 5):
                                completed_filepaths.append(full_f)
                                if f not in completed_files:
                                    completed_files.append(f)
                        except Exception:
                            pass

        elapsed_sec = int(time.time() - start_time)
        job["elapsed_seconds"] = elapsed_sec
        job["destination_path"] = actual_dest or dest_folder
        job["completed_filepaths"] = completed_filepaths
        job["completed_files"] = list(completed_files)

        is_success = bool(completed_files or skipped_files or completed_filepaths)
        if is_success:
            job["status"] = "completed"
            job["percent"] = 100.0
            job["completed_time"] = time.time()
            job["expires_in_seconds"] = FILE_RETENTION_SECONDS

            # Build list of files with direct client browser download URLs
            files_info = []
            for fp in completed_filepaths:
                fname = os.path.basename(fp)
                fsize = os.path.getsize(fp) if os.path.isfile(fp) else 0
                enc_name = urllib.parse.quote(fname)
                files_info.append(
                    DownloadFileInfo(
                        filename=fname,
                        size_bytes=fsize,
                        size_str=Sanitizer.format_file_size(fsize),
                        download_url=f"/api/download/file/{job_id}/{enc_name}",
                        stream_url=f"/api/stream/{job_id}/{enc_name}",
                    ).model_dump()
                )
            job["files"] = files_info

            # Primary download URL (single file) and zip URL (multi-file)
            if completed_filepaths:
                job["download_url"] = f"/api/download/file/{job_id}"
            if len(completed_filepaths) > 1:
                job["zip_url"] = f"/api/download/zip/{job_id}"
        else:
            job["status"] = "failed"
            failed_files.append(url)
            job["failed_files"] = failed_files
            err_msg = custom_logger.errors[-1] if custom_logger.errors else (
                f"Download failed with exit code {download_ret}" if download_ret != 0 else "No files were saved."
            )
            job["error_message"] = err_msg

        self._broadcast_update(job_id)

    def cleanup_job_files(self, job_id: str) -> bool:
        """Deletes files associated with a specific job from VPS disk."""
        job = self.jobs.get(job_id)
        if not job:
            return False

        filepaths = list(job.get("completed_filepaths", []))
        dest = job.get("destination_path")

        for fp in filepaths:
            try:
                if os.path.isfile(fp):
                    os.remove(fp)
            except Exception as e:
                self.logger.warning(f"Could not remove {fp}: {e}")

        # If destination folder is inside DEFAULT_DOWNLOAD_DIR and now empty, clean it up
        if dest and os.path.isdir(dest):
            try:
                abs_dest = os.path.abspath(dest)
                abs_root = os.path.abspath(DEFAULT_DOWNLOAD_DIR)
                if abs_dest.startswith(abs_root) and abs_dest != abs_root:
                    if not os.listdir(dest):
                        os.rmdir(dest)
            except Exception:
                pass

        job["completed_filepaths"] = []
        job["files"] = []
        job["download_url"] = None
        job["zip_url"] = None
        job["status"] = "cleaned"
        self._broadcast_update(job_id)
        return True

    def cleanup_expired_files(self, max_age_seconds: int = FILE_RETENTION_SECONDS) -> int:
        """Purges any temporary files older than max_age_seconds from VPS storage."""
        now = time.time()
        purged = 0
        if not os.path.isdir(DEFAULT_DOWNLOAD_DIR):
            return 0

        # Cleanup memory records
        for jid, job in list(self.jobs.items()):
            ctime = job.get("completed_time")
            if ctime and (now - ctime) > max_age_seconds and job.get("status") == "completed":
                self.cleanup_job_files(jid)

        # Walk physical download folder
        for root, dirs, files in os.walk(DEFAULT_DOWNLOAD_DIR, topdown=False):
            for f in files:
                fpath = os.path.join(root, f)
                try:
                    mtime = os.path.getmtime(fpath)
                    if (now - mtime) > max_age_seconds:
                        os.remove(fpath)
                        purged += 1
                except Exception:
                    pass
            for d in dirs:
                dpath = os.path.join(root, d)
                try:
                    if not os.listdir(dpath):
                        os.rmdir(dpath)
                except Exception:
                    pass
        return purged

    def cleanup_all_storage(self) -> int:
        """Manually clears all files in DEFAULT_DOWNLOAD_DIR."""
        purged = 0
        if not os.path.isdir(DEFAULT_DOWNLOAD_DIR):
            return 0
        for root, dirs, files in os.walk(DEFAULT_DOWNLOAD_DIR, topdown=False):
            for f in files:
                fpath = os.path.join(root, f)
                try:
                    os.remove(fpath)
                    purged += 1
                except Exception:
                    pass
            for d in dirs:
                dpath = os.path.join(root, d)
                try:
                    if not os.listdir(dpath):
                        os.rmdir(dpath)
                except Exception:
                    pass
        for jid in list(self.jobs.keys()):
            self.jobs[jid]["status"] = "cleaned"
            self.jobs[jid]["completed_filepaths"] = []
            self.jobs[jid]["files"] = []
            self.jobs[jid]["download_url"] = None
            self.jobs[jid]["zip_url"] = None
            self._broadcast_update(jid)
        return purged

    def get_storage_stats(self) -> Dict[str, Any]:
        """Calculates current temporary storage usage on VPS."""
        total_files = 0
        used_bytes = 0
        if os.path.isdir(DEFAULT_DOWNLOAD_DIR):
            for root, _, files in os.walk(DEFAULT_DOWNLOAD_DIR):
                for f in files:
                    fp = os.path.join(root, f)
                    try:
                        used_bytes += os.path.getsize(fp)
                        total_files += 1
                    except Exception:
                        pass

        try:
            target_dir = DEFAULT_DOWNLOAD_DIR if os.path.isdir(DEFAULT_DOWNLOAD_DIR) else SERVER_DIR
            usage = shutil.disk_usage(target_dir)
            free_bytes = usage.free
        except Exception:
            free_bytes = 0

        return {
            "total_files": total_files,
            "used_bytes": used_bytes,
            "used_str": Sanitizer.format_file_size(used_bytes),
            "free_bytes": free_bytes,
            "free_str": Sanitizer.format_file_size(free_bytes),
        }
