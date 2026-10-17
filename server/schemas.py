"""Pydantic data schemas for Web REST API."""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

class MediaInfoRequest(BaseModel):
    url: str = Field(..., description="Target media URL (YouTube, Facebook, Instagram, TikTok, etc.)")

class FormatProfileSchema(BaseModel):
    id: int
    name: str
    badge: str
    desc: str
    ext: str
    tag: str
    tag_color: str
    est_size: str
    codec: str

class MediaInfoResponse(BaseModel):
    title: str
    url: str
    platform_key: str
    platform_name: str
    platform_color: str
    platform_icon: str
    uploader: str
    duration: Optional[float] = None
    duration_str: str = "Unknown"
    views: Optional[Union[int, float]] = None
    views_str: str = "N/A"
    thumbnail: Optional[str] = None
    is_playlist: bool = False
    playlist_count: Optional[int] = None
    formats: List[FormatProfileSchema] = []

class DownloadRequest(BaseModel):
    url: str
    format_id: int = 0
    is_playlist: bool = False
    playlist_range: Optional[str] = None
    playlist_title: Optional[str] = None

class DownloadFileInfo(BaseModel):
    filename: str
    size_bytes: int = 0
    size_str: str = "Unknown"
    download_url: str
    stream_url: Optional[str] = None

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    percent: float = 0.0
    speed_str: str = "0 B/s"
    eta_str: str = "--:--"
    downloaded_bytes: int = 0
    total_bytes: int = 0
    downloaded_str: str = "0 B"
    total_str: str = "Unknown"
    stream_type: str = "Media"
    current_filename: str = ""
    completed_files: List[str] = []
    skipped_files: List[str] = []
    failed_files: List[str] = []
    destination_path: Optional[str] = None
    elapsed_seconds: int = 0
    error_message: Optional[str] = None
    download_url: Optional[str] = None
    zip_url: Optional[str] = None
    files: List[DownloadFileInfo] = []
    expires_in_seconds: Optional[int] = None

class LibraryFileItem(BaseModel):
    filename: str
    filepath: str
    relative_path: str
    platform: str
    size_bytes: int
    size_str: str
    modified_time: float
    modified_str: str
    media_type: str
    download_url: str
    stream_url: str

class StorageStatsResponse(BaseModel):
    total_files: int
    used_bytes: int
    used_str: str
    free_bytes: int
    free_str: str

class ActionResponse(BaseModel):
    success: bool
    message: str

class CookiesStatusResponse(BaseModel):
    exists: bool
    path: str
    line_count: int = 0
