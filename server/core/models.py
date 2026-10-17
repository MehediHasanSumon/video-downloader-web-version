"""Data models and representations for media, formats, and results."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union

@dataclass
class Platform:
    key: str
    name: str
    badge: str
    color: str
    icon: str
    folder: str
    is_social: bool = False

@dataclass
class FormatOption:
    id: int
    name: str
    badge: str
    desc: str
    ext: str
    tag: str
    tag_color: str
    est_mb_per_min: float = 15.0
    codec: str = "MP4 / Best"

    def estimated_size_str(self, duration_seconds: Optional[Union[int, float]]) -> str:
        if not duration_seconds or duration_seconds <= 0:
            return "Varies"
        est_mb = (float(duration_seconds) / 60.0) * self.est_mb_per_min
        if est_mb >= 1024:
            return f"~{est_mb / 1024:.1f} GB"
        return f"~{int(est_mb)} MB"

@dataclass
class MediaInfo:
    title: str
    url: str
    platform: Platform
    is_playlist: bool = False
    duration: Optional[Union[int, float]] = None
    views: Optional[int] = None
    uploader: str = "Unknown"
    playlist_count: Optional[int] = None
    playlist_items_range: Optional[str] = None
    raw_info: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DownloadResult:
    title: str
    destination_path: str
    elapsed_seconds: int = 0
    is_playlist: bool = False
    completed_files: List[str] = field(default_factory=list)
    skipped_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    success: bool = True
    error_message: Optional[str] = None
