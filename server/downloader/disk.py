"""Smart disk pre-check and auto-resume filter."""

import os
from typing import Callable, Optional
from core.sanitizer import Sanitizer

class SmartDiskChecker:
    """Checks disk for already downloaded complete media files and resumes partial streams."""

    @staticmethod
    def create_filter(ydl, format_choice: int, is_playlist: bool = False, on_skip: Optional[Callable] = None):
        if format_choice in (3, 4):
            valid_exts = {".mp3", ".m4a", ".opus", ".aac", ".flac", ".wav", ".ogg"}
        else:
            valid_exts = {".mp4", ".mkv", ".webm", ".avi", ".mov", ".ts"}

        def disk_check_filter(info_dict, *, incomplete=False):
            if info_dict.get("_type") == "playlist":
                return None

            try:
                target = ydl.prepare_filename(info_dict)
                dir_name = os.path.dirname(target)
                if not os.path.isdir(dir_name):
                    return None

                base, _ = os.path.splitext(target)

                # 1. Exact base filename match
                for ext in valid_exts:
                    cand = base + ext
                    if os.path.isfile(cand) and os.path.getsize(cand) > 1024 and not cand.endswith(".part") and not cand.endswith(".ytdl"):
                        fname = os.path.basename(cand)
                        fsize = Sanitizer.format_file_size(os.path.getsize(cand))
                        if on_skip:
                            on_skip(fname, fsize, cand)
                        return f"Skipping '{fname}': already exists on disk"

                # 2. Numbered index prefix match for playlist videos
                index = info_dict.get("playlist_index") or info_dict.get("playlist_autonumber")
                if is_playlist and index is not None:
                    try:
                        idx_num = int(index)
                        prefixes = (f"{idx_num:02d}. ", f"{idx_num:02d} - ", f"{idx_num}. ")
                        for f in os.listdir(dir_name):
                            if any(f.startswith(p) for p in prefixes) and any(f.endswith(e) for e in valid_exts):
                                full = os.path.join(dir_name, f)
                                if os.path.isfile(full) and os.path.getsize(full) > 1024 and not f.endswith(".part") and not f.endswith(".ytdl"):
                                    fsize = Sanitizer.format_file_size(os.path.getsize(full))
                                    if on_skip:
                                        on_skip(f, fsize, full)
                                    return f"Skipping '{f}': already exists on disk"
                    except Exception:
                        pass
            except Exception:
                pass

            return None

        return disk_check_filter
