export interface FormatProfile {
  id: number;
  name: string;
  badge: string;
  desc: string;
  ext: string;
  tag: string;
  tag_color: string;
  est_size: string;
  codec: string;
}

export interface PlaylistEntry {
  index: number;
  id: string;
  title: string;
  duration?: number;
  duration_str: string;
  thumbnail?: string;
  url?: string;
  uploader?: string;
}

export interface MediaInfo {
  title: string;
  url: string;
  platform_key: string;
  platform_name: string;
  platform_color: string;
  platform_icon: string;
  uploader: string;
  duration?: number;
  duration_str: string;
  views?: number;
  views_str: string;
  thumbnail?: string;
  is_playlist: boolean;
  playlist_count?: number;
  playlist_entries?: PlaylistEntry[];
  formats: FormatProfile[];
}

export interface DownloadFileInfo {
  filename: string;
  size_bytes: number;
  size_str: string;
  download_url: string;
  stream_url?: string;
}

export interface JobProgress {
  job_id: string;
  status: 'queued' | 'starting' | 'downloading' | 'processing' | 'merging' | 'completed' | 'failed' | 'cleaned';
  percent: number;
  speed_str: string;
  eta_str: string;
  downloaded_bytes: number;
  total_bytes: number;
  downloaded_str: string;
  total_str: string;
  stream_type: string;
  current_filename: string;
  completed_files: string[];
  skipped_files: string[];
  failed_files: string[];
  destination_path?: string;
  elapsed_seconds: number;
  error_message?: string;
  download_url?: string;
  zip_url?: string;
  files?: DownloadFileInfo[];
  expires_in_seconds?: number;
}

export interface LibraryItem {
  filename: string;
  filepath: string;
  relative_path: string;
  platform: string;
  size_bytes: number;
  size_str: string;
  modified_time: number;
  modified_str: string;
  media_type: 'video' | 'audio';
  download_url?: string;
  stream_url?: string;
}

export interface StorageStats {
  total_files: number;
  used_bytes: number;
  used_str: string;
  free_bytes: number;
  free_str: string;
}

export interface CookiesStatus {
  exists: boolean;
  path: string;
  line_count: number;
}
