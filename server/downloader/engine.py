"""High-level media downloader engine with rich progress tracking."""

import os
import time
from typing import Optional, Dict, Any, List
import yt_dlp
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)
from core.config import COOKIES_FILE
from core.models import MediaInfo, DownloadResult
from core.detector import PlatformDetector
from core.sanitizer import Sanitizer
from core.logger import AppLogger, YtDlpLogger
from downloader.options import YdlOptionsBuilder, get_available_js_runtimes
from downloader.disk import SmartDiskChecker
from utils.notify import NotificationManager

class MediaDownloader:
    """Manages metadata fetching and live download execution via yt-dlp."""

    def __init__(self, console: Console):
        self.console = console
        self.logger = AppLogger.get_logger()

    def fetch_media_info(self, url: str, cookies_from_browser: Optional[str] = None) -> Optional[MediaInfo]:
        platform = PlatformDetector.detect(url)
        ydl_opts: Dict[str, Any] = {
            "extract_flat": "in_playlist",
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "logger": YtDlpLogger(self.logger),
        }
        js_runtimes = get_available_js_runtimes()
        if js_runtimes:
            ydl_opts["js_runtimes"] = js_runtimes
            ydl_opts["remote_components"] = ["ejs:github"]

        if os.path.isfile(COOKIES_FILE):
            ydl_opts["cookiefile"] = COOKIES_FILE
            self.logger.info(f"Using local cookies.txt from: {COOKIES_FILE}")
        elif cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (cookies_from_browser, None, None, None)
            self.logger.info(f"Using browser cookies from: {cookies_from_browser}")

        with self.console.status(f"[bold #27d2ed]⠋ Fetching media information from {platform.name}...", spinner="dots"):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    if not info:
                        return None

                    is_playlist = info.get("_type") == "playlist" or "entries" in info
                    clean_title = Sanitizer.clean_media_title(info, platform.key)
                    uploader = info.get("uploader") or info.get("channel") or info.get("uploader_id") or "Unknown"

                    playlist_count = None
                    if is_playlist:
                        entries = list(info.get("entries") or [])
                        playlist_count = len(entries) if entries else info.get("playlist_count")

                    return MediaInfo(
                        title=clean_title,
                        url=url,
                        platform=platform,
                        is_playlist=is_playlist,
                        duration=info.get("duration"),
                        views=info.get("view_count"),
                        uploader=uploader,
                        playlist_count=playlist_count,
                        raw_info=info,
                    )
            except Exception as e:
                err_msg = str(e)
                self.logger.error(f"Failed to fetch media metadata for URL: {url} | Error: {err_msg}")
                self.console.print(f"\n  [bold red][ERROR][/bold red] Could not fetch media info: [dim]{err_msg}[/dim]\n")
                if any(term in err_msg.lower() for term in ("login", "sign in", "private", "account", "cookies", "restricted")):
                    self.console.print("  [bold yellow]💡 Authentication / Cookie Tip:[/bold yellow]")
                    self.console.print("  This video might be private, friends-only, or requires login.")
                    self.console.print(f"  You can place an exported [bold white]cookies.txt[/bold white] file in: [cyan]{COOKIES_FILE}[/cyan]\n")
                return None

    def execute_download(
        self,
        media: MediaInfo,
        save_path: str,
        format_choice: int,
        cookies_from_browser: Optional[str] = None,
    ) -> DownloadResult:
        start_time = time.time()
        self.logger.info(f"Starting download execution for: '{media.title}' | Format choice: {format_choice}")

        progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold #27d2ed]{task.description}"),
            BarColumn(bar_width=26, complete_style="#27d2ed", finished_style="#4bdd7f"),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
            transient=False,
        )

        playlist_task_id = None
        stream_task_id = None
        completed_files: List[str] = []
        skipped_files: List[str] = []
        failed_files: List[str] = []
        processed_count = 0
        total_videos = media.playlist_count if media.is_playlist else 1
        if media.is_playlist and media.playlist_items_range:
            rng = media.playlist_items_range.strip()
            if "-" in rng:
                parts = rng.split("-")
                try:
                    start_i = int(parts[0]) if parts[0] else 1
                    end_i = int(parts[1]) if parts[1] else (media.playlist_count or 1)
                    if end_i >= start_i:
                        total_videos = end_i - start_i + 1
                except Exception:
                    pass
            elif "," in rng:
                total_videos = len([p for p in rng.split(",") if p.strip()])
            elif rng.isdigit():
                total_videos = 1
        actual_destination_dir: Optional[str] = None

        def on_skip_callback(fname: str, fsize: str, fpath: str):
            nonlocal processed_count, actual_destination_dir
            if fname in skipped_files:
                return
            processed_count += 1
            skipped_files.append(fname)
            if fpath:
                actual_destination_dir = os.path.dirname(fpath)
            self.logger.info(f"[SKIPPED] Already exists: '{fname}' ({fsize}) at '{fpath}'")

            if media.is_playlist and total_videos and total_videos > 1:
                progress.console.print(
                    f"  [bold yellow]⚡ Skipped ({processed_count}/{total_videos}):[/bold yellow] [bright_white]{fname}[/bright_white] [dim]({fsize} - exists)[/dim]"
                )
                if playlist_task_id is not None:
                    progress.advance(playlist_task_id, 1)
            else:
                progress.console.print(
                    f"  [bold yellow]⚡ Skipped:[/bold yellow] [bright_white]{fname}[/bright_white] [dim]({fsize} - exists)[/dim]"
                )

        def post_hook_callback(filepath: str):
            nonlocal stream_task_id, processed_count, actual_destination_dir
            fname = os.path.basename(filepath) if filepath else "Media"
            if filepath:
                actual_destination_dir = os.path.dirname(filepath)
            if fname in completed_files:
                return
            processed_count += 1
            fsize = Sanitizer.format_file_size(os.path.getsize(filepath)) if filepath and os.path.isfile(filepath) else "Completed"
            completed_files.append(fname)
            self.logger.info(f"[COMPLETED] Download finished: '{fname}' | Size: {fsize} | Path: '{filepath}'")

            if stream_task_id is not None:
                try:
                    progress.remove_task(stream_task_id)
                except Exception:
                    pass
                stream_task_id = None

            if media.is_playlist and total_videos and total_videos > 1:
                progress.console.print(
                    f"  [bold #4bdd7f]✓ Completed ({processed_count}/{total_videos}):[/bold #4bdd7f] [bold bright_white]{fname}[/bold bright_white] [bold #4bdd7f]({fsize})[/bold #4bdd7f]"
                )
                if playlist_task_id is not None:
                    progress.advance(playlist_task_id, 1)
            else:
                progress.console.print(
                    f"  [bold #4bdd7f]✓ Completed:[/bold #4bdd7f] [bold bright_white]{fname}[/bold bright_white] [bold #4bdd7f]({fsize})[/bold #4bdd7f]"
                )

        def progress_hook(d):
            nonlocal stream_task_id
            status = d.get("status")

            if status == "downloading":
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                info = d.get("info_dict", {})
                vcodec = info.get("vcodec")
                acodec = info.get("acodec")

                if vcodec is not None and vcodec != "none" and (acodec is None or acodec == "none"):
                    stream_type = "Video Stream"
                elif acodec is not None and acodec != "none" and (vcodec is None or vcodec == "none"):
                    stream_type = "Audio Stream"
                else:
                    stream_type = "Media Stream"

                fname = os.path.basename(d.get("filename", "Media"))
                short_name = fname[:24] + "..." if len(fname) > 24 else fname

                if stream_task_id is None:
                    stream_task_id = progress.add_task(f"Downloading {stream_type} ({short_name})", total=total, completed=downloaded)
                else:
                    progress.update(
                        stream_task_id,
                        description=f"Downloading {stream_type} ({short_name})",
                        completed=downloaded,
                        total=total,
                    )
            elif status == "finished":
                if stream_task_id is not None:
                    progress.update(stream_task_id, description="[bold #4bdd7f]Stream download finished[/bold #4bdd7f]")

        def postprocessor_hook(d):
            nonlocal stream_task_id
            status = d.get("status")

            if status == "started":
                if stream_task_id is not None:
                    progress.update(stream_task_id, description="[bold bright_yellow]⚡ Merging streams with FFmpeg...[/bold bright_yellow]")
            elif status == "finished":
                if stream_task_id is not None:
                    progress.update(stream_task_id, description="[bold #4bdd7f]✓ Lossless merge completed[/bold #4bdd7f]")

        dl_logger = YtDlpLogger(self.logger)
        ydl_opts = YdlOptionsBuilder.build(
            save_path=save_path,
            format_choice=format_choice,
            is_playlist=media.is_playlist,
            progress_hooks=[progress_hook],
            postprocessor_hooks=[postprocessor_hook],
            post_hooks=[post_hook_callback],
            platform_key=media.platform.key,
            cookies_file=COOKIES_FILE if os.path.isfile(COOKIES_FILE) else None,
            cookies_from_browser=cookies_from_browser,
            playlist_title=media.title if media.is_playlist else None,
            playlist_items=media.playlist_items_range if media.is_playlist else None,
            custom_logger=dl_logger,
        )

        download_ret = None
        with progress:
            if media.is_playlist and total_videos and total_videos > 1:
                playlist_task_id = progress.add_task(
                    f"[bold #e778f9]Playlist Progress (0/{total_videos})[/bold #e778f9]",
                    total=total_videos,
                )

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.params["match_filter"] = SmartDiskChecker.create_filter(
                    ydl,
                    format_choice=format_choice,
                    is_playlist=media.is_playlist,
                    on_skip=on_skip_callback,
                )
                try:
                    download_ret = ydl.download([media.url])
                except Exception as dl_err:
                    self.logger.warning(f"Download execution encountered warning/error: {dl_err}")
                    if str(dl_err) not in dl_logger.errors:
                        dl_logger.errors.append(str(dl_err))

        elapsed_sec = int(time.time() - start_time)

        # Check whether download succeeded or failed
        is_success = bool(completed_files or skipped_files)
        error_msg = None
        if not is_success:
            if dl_logger.errors:
                error_msg = dl_logger.errors[-1]
            elif download_ret is not None and download_ret != 0:
                error_msg = f"Download failed with exit code {download_ret}"
            else:
                error_msg = "No media files were downloaded. The video stream may be unavailable or restricted."
            failed_files.append(media.title)
            self.logger.error(f"[FAILED] Download failed for '{media.title}': {error_msg}")

        # Determine target final directory for playlist
        final_dir = actual_destination_dir
        if not final_dir:
            if media.is_playlist:
                clean_folder = Sanitizer.clean_media_title({"title": media.title}, "generic")
                final_dir = os.path.join(save_path, clean_folder)
            else:
                final_dir = save_path

        # Generate M3U playlist file for audio playlists (format 3: MP3, format 4: M4A)
        if media.is_playlist and format_choice in (3, 4) and final_dir and os.path.isdir(final_dir):
            try:
                audio_files = sorted([
                    f for f in os.listdir(final_dir)
                    if f.endswith((".mp3", ".m4a", ".opus", ".aac", ".flac", ".wav"))
                ])
                if audio_files:
                    m3u_file = os.path.join(final_dir, f"{Sanitizer.clean_media_title({'title': media.title}, 'generic')}.m3u")
                    with open(m3u_file, "w", encoding="utf-8") as m3u:
                        m3u.write("#EXTM3U\n")
                        for af in audio_files:
                            m3u.write(f"{af}\n")
                    self.logger.info(f"Generated M3U playlist file at: {m3u_file}")
            except Exception as m3u_err:
                self.logger.warning(f"Could not write M3U playlist: {m3u_err}")

        # Trigger desktop system notification
        if is_success:
            NotificationManager.notify(
                title="Download Completed",
                message=f"{media.title} ({len(completed_files)} new, {len(skipped_files)} skipped)",
            )
        else:
            NotificationManager.notify(
                title="Download Failed",
                message=f"{media.title}: {error_msg or 'Download could not be completed'}",
            )

        return DownloadResult(
            title=media.title,
            destination_path=final_dir,
            elapsed_seconds=elapsed_sec,
            is_playlist=media.is_playlist,
            completed_files=completed_files,
            skipped_files=skipped_files,
            failed_files=failed_files,
            success=is_success,
            error_message=error_msg,
        )
