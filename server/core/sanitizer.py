"""Title cleaning, time formatting, and parameter parsing."""

import urllib.parse
from typing import Optional, Dict, Any

class Sanitizer:
    """Provides methods for string, duration, size, and title sanitization."""

    @staticmethod
    def format_duration(seconds: Any) -> str:
        if seconds is None:
            return "Unknown"
        try:
            total_sec = int(round(float(seconds)))
        except (ValueError, TypeError):
            return "Unknown"

        if total_sec < 0:
            return "Unknown"
        if total_sec == 0:
            return "00:00"

        hours = total_sec // 3600
        minutes = (total_sec % 3600) // 60
        secs = total_sec % 60
        if hours > 0:
            return f"{hours}h {minutes:02d}m {secs:02d}s"
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def format_views(views: Any) -> str:
        if views is None:
            return "N/A"
        try:
            val = int(round(float(views)))
            return f"{val:,} views"
        except (ValueError, TypeError):
            views_str = str(views).strip()
            return "N/A" if not views_str else f"{views_str} views"

    @staticmethod
    def format_file_size(bytes_val: Any) -> str:
        if not bytes_val:
            return "Unknown size"
        try:
            size = float(bytes_val)
        except (ValueError, TypeError):
            return "Unknown size"

        if size <= 0:
            return "Unknown size"

        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    @staticmethod
    def extract_playlist_id(url: str) -> Optional[str]:
        try:
            parsed = urllib.parse.urlparse(url)
            qs = urllib.parse.parse_qs(parsed.query)
            if "list" in qs and qs["list"]:
                playlist_id = qs["list"][0].strip()
                # Exclude YouTube dynamic radio mix / algorithmic recommendation queues
                if any(playlist_id.startswith(p) for p in ("RD", "UL", "LL", "WL")):
                    return None
                return playlist_id
        except Exception:
            pass
        return None

    @staticmethod
    def clean_media_title(info: Dict[str, Any], platform_key: str) -> str:
        title = (info.get("title") or "").strip()
        desc = (info.get("description") or "").strip()
        uploader = (info.get("uploader") or info.get("channel") or info.get("uploader_id") or "").strip()

        is_generic = False
        if not title:
            is_generic = True
        elif platform_key == "facebook":
            title_lower = title.lower()
            if "facebook video" in title_lower or title_lower.isdigit() or len(title_lower) < 4:
                is_generic = True

        if is_generic and desc:
            lines = [line.strip() for line in desc.splitlines() if line.strip()]
            if lines:
                first_line = lines[0]
                if len(first_line) > 60:
                    first_line = first_line[:57] + "..."
                if uploader and uploader not in first_line:
                    title = f"{uploader} - {first_line}"
                else:
                    title = first_line

        if not title:
            if uploader:
                title = f"{uploader} - {info.get('id', 'Media')}"
            else:
                title = f"Media_{info.get('id', 'video')}"

        # Strip dangerous filename characters for Linux / Windows / macOS
        cleaned = "".join(c for c in title if c not in r'\/:*?"<>|' and ord(c) >= 32).strip()

        # Enforce cross-platform safe filename length (max 100 bytes in UTF-8)
        encoded = cleaned.encode("utf-8", errors="ignore")
        if len(encoded) > 100:
            cleaned = encoded[:100].decode("utf-8", errors="ignore").rstrip() + "..."

        return cleaned or "Media_Download"

    @staticmethod
    def calculate_format_sizes(info: Dict[str, Any], platform_key: str, duration: Optional[float] = None) -> Dict[int, str]:
        """Calculates accurate, real-world file sizes for format profiles from yt-dlp metadata."""
        formats = info.get("formats") or []
        if duration is None:
            raw_duration = info.get("duration")
            try:
                duration = float(raw_duration) if raw_duration is not None else 0.0
            except (ValueError, TypeError):
                duration = 0.0
        else:
            try:
                duration = float(duration)
            except (ValueError, TypeError):
                duration = 0.0

        def get_fmt_size(f: Optional[Dict[str, Any]]) -> int:
            if not f or not isinstance(f, dict):
                return 0
            if f.get("filesize") and f["filesize"] > 0:
                return int(f["filesize"])
            if f.get("filesize_approx") and f["filesize_approx"] > 0:
                return int(f["filesize_approx"])
            tbr = f.get("tbr") or ((f.get("vbr") or 0) + (f.get("abr") or 0))
            if tbr and duration and duration > 0:
                return int(tbr * 1000 / 8 * duration)
            return 0

        # Locate best audio stream
        audio_only = [
            f for f in formats 
            if f.get("vcodec") == "none" and f.get("acodec") and f.get("acodec") != "none"
        ]
        if audio_only:
            best_audio = max(audio_only, key=lambda f: f.get("abr") or f.get("tbr") or 0)
        else:
            with_audio = [f for f in formats if f.get("acodec") and f.get("acodec") != "none"]
            best_audio = max(with_audio, key=lambda f: f.get("abr") or f.get("tbr") or 0) if with_audio else None

        audio_size = get_fmt_size(best_audio)

        # Filter video streams
        video_fmts = [f for f in formats if f.get("vcodec") and f.get("vcodec") != "none"]
        if not video_fmts:
            video_fmts = [f for f in formats if f.get("height") or f.get("resolution")]
        if not video_fmts and formats:
            video_fmts = formats

        def v_sort_key(f: Dict[str, Any]):
            h = f.get("height") or 0
            t = f.get("tbr") or f.get("vbr") or 0
            fs = f.get("filesize") or f.get("filesize_approx") or 0
            return (h, t, fs)

        sorted_videos = sorted(video_fmts, key=v_sort_key) if video_fmts else []

        sizes: Dict[int, str] = {}

        # Profile 0: Max / Best HD Video
        if sorted_videos:
            best_v = sorted_videos[-1]
            v_size = get_fmt_size(best_v)
            needs_audio = (best_v.get("acodec") == "none" or not best_v.get("acodec")) and best_audio is not None
            tot_0 = v_size + (audio_size if needs_audio else 0)
            if tot_0 > 0:
                sizes[0] = Sanitizer.format_file_size(tot_0)
        elif info.get("filesize") or info.get("filesize_approx"):
            root_sz = info.get("filesize") or info.get("filesize_approx")
            sizes[0] = Sanitizer.format_file_size(root_sz)

        # Profile 1: 1080p Full HD Video
        if sorted_videos:
            v_1080 = [f for f in sorted_videos if (f.get("height") or 0) <= 1080]
            match_1 = v_1080[-1] if v_1080 else sorted_videos[-1]
            v_size = get_fmt_size(match_1)
            needs_audio = (match_1.get("acodec") == "none" or not match_1.get("acodec")) and best_audio is not None
            tot_1 = v_size + (audio_size if needs_audio else 0)
            if tot_1 > 0:
                sizes[1] = Sanitizer.format_file_size(tot_1)

        # Profile 2: 720p HD (Generic/YouTube) or 480p SD (Social)
        max_h = 480 if platform_key in ("facebook", "instagram", "tiktok", "twitter") else 720
        if sorted_videos:
            v_target = [f for f in sorted_videos if 0 < (f.get("height") or 0) <= max_h]
            if v_target:
                match_2 = v_target[-1]
            else:
                match_2 = sorted_videos[0]
            v_size = get_fmt_size(match_2)
            needs_audio = (match_2.get("acodec") == "none" or not match_2.get("acodec")) and best_audio is not None
            tot_2 = v_size + (audio_size if needs_audio else 0)
            if tot_2 > 0:
                sizes[2] = Sanitizer.format_file_size(tot_2)

        # Profile 3: High-Fidelity Audio (MP3 320kbps CBR)
        if duration and duration > 0:
            mp3_sz = int(320 * 1000 / 8 * duration)
            sizes[3] = Sanitizer.format_file_size(mp3_sz)
        elif audio_size > 0:
            sizes[3] = Sanitizer.format_file_size(audio_size)

        # Profile 4: Original Raw Audio Stream (M4A / AAC)
        if audio_size > 0:
            sizes[4] = Sanitizer.format_file_size(audio_size)
        elif duration and duration > 0:
            abr = (best_audio.get("abr") if best_audio else None) or 128
            sizes[4] = Sanitizer.format_file_size(int(abr * 1000 / 8 * duration))

        return sizes
