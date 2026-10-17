import type { MediaInfo, JobProgress, LibraryItem, CookiesStatus } from '../types';

const API_BASE = '/api';

export async function fetchMediaInfo(url: string): Promise<MediaInfo> {
  const res = await fetch(`${API_BASE}/info`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to fetch media' }));
    throw new Error(errorData.detail || 'Could not load media info');
  }
  return res.json();
}

export async function startDownload(
  url: string,
  formatId: number,
  isPlaylist = false,
  playlistRange?: string,
  playlistTitle?: string,
  selectedIndices?: number[]
): Promise<{ job_id: string; status: string }> {
  const res = await fetch(`${API_BASE}/download`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      format_id: formatId,
      is_playlist: isPlaylist,
      playlist_range: playlistRange,
      playlist_title: playlistTitle,
      selected_indices: selectedIndices,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Download failed to start' }));
    throw new Error(errorData.detail || 'Could not initiate download');
  }
  return res.json();
}

export function subscribeToProgress(
  jobId: string,
  onMessage: (data: JobProgress) => void,
  onError: (err: any) => void
): () => void {
  const eventSource = new EventSource(`${API_BASE}/progress/${jobId}/stream`);

  eventSource.onmessage = (event) => {
    try {
      const data: JobProgress = JSON.parse(event.data);
      onMessage(data);
      if (data.status === 'completed' || data.status === 'failed') {
        eventSource.close();
      }
    } catch (e) {
      console.error('Error parsing SSE event', e);
    }
  };

  eventSource.onerror = (err) => {
    eventSource.close();
    onError(err);
  };

  return () => {
    eventSource.close();
  };
}

export async function listDownloads(): Promise<LibraryItem[]> {
  const res = await fetch(`${API_BASE}/downloads`);
  if (!res.ok) throw new Error('Failed to load library');
  return res.json();
}

export async function playMedia(filepath: string): Promise<void> {
  const res = await fetch(`${API_BASE}/play`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ filepath }),
  });
  if (!res.ok) throw new Error('Could not open media player');
}

export async function openFolder(folderPath?: string): Promise<void> {
  const res = await fetch(`${API_BASE}/open-folder`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ folder_path: folderPath }),
  });
  if (!res.ok) throw new Error('Could not open folder');
}

export async function getCookiesStatus(): Promise<CookiesStatus> {
  const res = await fetch(`${API_BASE}/cookies`);
  if (!res.ok) throw new Error('Could not check cookies');
  return res.json();
}

export async function saveCookies(content: string): Promise<void> {
  const res = await fetch(`${API_BASE}/cookies`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content }),
  });
  if (!res.ok) throw new Error('Could not save cookies file');
}

export function triggerBrowserDownload(url: string, filename?: string) {
  const a = document.createElement('a');
  a.href = url;
  if (filename) a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

export async function deleteJobFiles(jobId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/download/file/${jobId}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Could not delete job files');
}

export async function deleteCachedFile(path: string): Promise<void> {
  const res = await fetch(`${API_BASE}/downloads/file?path=${encodeURIComponent(path)}`, {
    method: 'DELETE',
  });
  if (!res.ok) throw new Error('Could not delete file');
}

export async function clearVpsStorage(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/cleanup`, { method: 'POST' });
  if (!res.ok) throw new Error('Could not clear VPS storage');
  return res.json();
}

export async function getStorageStats(): Promise<import('../types').StorageStats> {
  const res = await fetch(`${API_BASE}/storage`);
  if (!res.ok) throw new Error('Could not fetch storage stats');
  return res.json();
}
