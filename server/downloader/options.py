"""Factory for yt-dlp parameter dictionaries."""

import os
import shutil
from typing import Optional, List, Dict, Any
from core.config import CONCURRENT_FRAGMENTS, SOCKET_BUFFER_SIZE, PROXY_URL
from core.logger import AppLogger, YtDlpLogger
from core.sanitizer import Sanitizer

def get_available_js_runtimes() -> Dict[str, Dict[str, Any]]:
    """Detects available system JavaScript runtimes for yt-dlp challenge solving."""
    runtimes: Dict[str, Dict[str, Any]] = {}
    for rt in ("node", "deno", "bun", "quickjs"):
        path = shutil.which(rt)
        if not path and rt == "node":
            home = os.path.expanduser("~")
            nvm_dir = os.path.join(home, ".nvm", "versions", "node")
            if os.path.isdir(nvm_dir):
                for v in sorted(os.listdir(nvm_dir), reverse=True):
                    cand = os.path.join(nvm_dir, v, "bin", "node")
                    if os.path.isfile(cand) and os.access(cand, os.X_OK):
                        path = cand
                        break
        if path:
            runtimes[rt] = {"path": path}
    return runtimes

class YdlOptionsBuilder:
    """Constructs tailored yt-dlp configuration dictionaries."""

    @staticmethod
    def build(
        save_path: str,
        format_choice: int,
        is_playlist: bool,
        progress_hooks: List[Any],
        postprocessor_hooks: List[Any],
        post_hooks: List[Any],
        platform_key: str = "generic",
        cookies_file: Optional[str] = None,
        cookies_from_browser: Optional[str] = None,
        playlist_title: Optional[str] = None,
        playlist_items: Optional[str] = None,
        custom_logger: Optional[Any] = None,
    ) -> Dict[str, Any]:
        os.makedirs(save_path, exist_ok=True)

        if is_playlist:
            # 1. Folder named after the playlist
            clean_folder = None
            if playlist_title:
                clean_folder = Sanitizer.clean_media_title({"title": playlist_title}, "generic")

            if clean_folder:
                folder_path = os.path.join(save_path, clean_folder)
                try:
                    os.makedirs(folder_path, exist_ok=True)
                except Exception:
                    pass
            else:
                folder_path = os.path.join(save_path, "%(playlist_title,playlist|Playlist)s")

            # 2. Numbered serial prefix: 01. , 02. , 03. etc.
            file_part = "%(playlist_index,playlist_autonumber,autonumber)02d. %(title,id).100B.%(ext)s"
            out_template = os.path.join(folder_path, file_part)
        else:
            out_template = os.path.join(save_path, "%(title,id).100B.%(ext)s")

        ydl_opts: Dict[str, Any] = {
            "outtmpl": {"default": out_template},
            "autonumber_start": 1,
            "windowsfilenames": True,
            "trim_file_name": 100,
            "ignoreerrors": True,
            "retries": 15,
            "fragment_retries": 15,
            "concurrent_fragment_downloads": CONCURRENT_FRAGMENTS,
            "buffersize": SOCKET_BUFFER_SIZE,
            "progress_hooks": progress_hooks,
            "postprocessor_hooks": postprocessor_hooks,
            "post_hooks": post_hooks,
            "continuedl": True,
            "nooverwrites": True,
            "noplaylist": not is_playlist,
            "logger": custom_logger or YtDlpLogger(AppLogger.get_logger()),
            "noprogress": True,
            "quiet": True,
            "no_warnings": True,
        }

        # Anti-ban rotating proxy configuration
        if PROXY_URL:
            ydl_opts["proxy"] = PROXY_URL

        # Auto-configure JS runtimes if installed (fixes YouTube JS challenge solver warnings)
        js_runtimes = get_available_js_runtimes()
        if js_runtimes:
            ydl_opts["js_runtimes"] = js_runtimes
            ydl_opts["remote_components"] = ["ejs:github"]

        # Anti-bot bypass player clients for YouTube
        ydl_opts["extractor_args"] = {
            "youtube": {
                "player_client": ["web_embedded", "android", "mweb", "web"],
            }
        }

        if is_playlist and playlist_items:
            ydl_opts["playlist_items"] = str(playlist_items).strip()

        if cookies_file and os.path.isfile(cookies_file):
            ydl_opts["cookiefile"] = cookies_file
        elif cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (cookies_from_browser, None, None, None)

        if platform_key in ("facebook", "instagram", "tiktok", "twitter"):
            if format_choice == 0:
                ydl_opts.update({
                    "format": "bestvideo+bestaudio/best",
                    "merge_output_format": "mp4",
                    "final_ext": "mp4",
                })
            elif format_choice == 1:
                ydl_opts.update({
                    "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                    "merge_output_format": "mp4",
                    "final_ext": "mp4",
                })
            elif format_choice == 2:
                ydl_opts.update({
                    "format": "bestvideo[height<=480]+bestaudio/best[height<=480]/best",
                    "merge_output_format": "mp4",
                    "final_ext": "mp4",
                })
            elif format_choice == 3:
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "final_ext": "mp3",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "320",
                        }
                    ],
                })
            elif format_choice == 4:
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "final_ext": "m4a",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "m4a",
                        }
                    ],
                })
        else:
            # YouTube & Standard Web Media
            if format_choice == 0:
                ydl_opts.update({
                    "format": "bestvideo+bestaudio/best",
                    "format_sort": ["res", "fps", "hdr:12", "vcodec", "channels", "br", "asr"],
                    "merge_output_format": "mp4",
                    "final_ext": "mp4",
                })
            elif format_choice == 1:
                ydl_opts.update({
                    "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best",
                    "merge_output_format": "mp4",
                    "final_ext": "mp4",
                })
            elif format_choice == 2:
                ydl_opts.update({
                    "format": "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                    "merge_output_format": "mp4",
                    "final_ext": "mp4",
                })
            elif format_choice == 3:
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "final_ext": "mp3",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "mp3",
                            "preferredquality": "320",
                        }
                    ],
                })
            elif format_choice == 4:
                ydl_opts.update({
                    "format": "bestaudio/best",
                    "final_ext": "m4a",
                    "postprocessors": [
                        {
                            "key": "FFmpegExtractAudio",
                            "preferredcodec": "m4a",
                        }
                    ],
                })

        return ydl_opts
