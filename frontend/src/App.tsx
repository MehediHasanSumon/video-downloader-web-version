import { useState, useEffect, useRef } from 'react';
import { Navbar } from './components/Navbar';
import { UrlInput } from './components/UrlInput';
import { MediaCard } from './components/MediaCard';
import { FormatSelector } from './components/FormatSelector';
import { ProgressCard } from './components/ProgressCard';
import { MediaPreviewModal } from './components/MediaPreviewModal';
import type { MediaInfo, JobProgress } from './types';
import {
  fetchMediaInfo,
  startDownload,
  subscribeToProgress,
  deleteJobFiles,
} from './services/api';
import { AlertCircle } from 'lucide-react';

function App() {
  const [media, setMedia] = useState<MediaInfo | null>(null);
  const [isFetching, setIsFetching] = useState<boolean>(false);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [currentJob, setCurrentJob] = useState<JobProgress | null>(null);
  const [isDownloading, setIsDownloading] = useState<boolean>(false);

  // In-Browser Media Preview Modal State
  const [preview, setPreview] = useState<{
    isOpen: boolean;
    title: string;
    streamUrl: string;
    isAudio?: boolean;
  }>({
    isOpen: false,
    title: '',
    streamUrl: '',
    isAudio: false,
  });

  const unsubscribeRef = useRef<(() => void) | null>(null);

  useEffect(() => {
    return () => {
      if (unsubscribeRef.current) {
        unsubscribeRef.current();
      }
    };
  }, []);

  const handleFetchMedia = async (url: string) => {
    setIsFetching(true);
    setFetchError(null);
    setMedia(null);
    try {
      const data = await fetchMediaInfo(url);
      setMedia(data);
    } catch (err: any) {
      setFetchError(err.message || 'Failed to inspect link. Please verify URL or check cookies.');
    } finally {
      setIsFetching(false);
    }
  };

  const handleStartDownload = async (
    formatId: number,
    isPlaylist: boolean,
    playlistRange?: string
  ) => {
    if (!media) return;

    if (unsubscribeRef.current) {
      unsubscribeRef.current();
      unsubscribeRef.current = null;
    }

    setIsDownloading(true);
    setCurrentJob(null);

    try {
      const { job_id } = await startDownload(
        media.url,
        formatId,
        isPlaylist,
        playlistRange,
        isPlaylist ? media.title : undefined
      );

      // Initial progress dummy
      setCurrentJob({
        job_id,
        status: 'starting',
        percent: 0,
        speed_str: '0 KB/s',
        eta_str: '--:--',
        downloaded_bytes: 0,
        total_bytes: 0,
        downloaded_str: '0 MB',
        total_str: 'Calculating...',
        stream_type: 'Initializing',
        current_filename: media.title,
        completed_files: [],
        skipped_files: [],
        failed_files: [],
        elapsed_seconds: 0,
      });

      // Stream progress live
      unsubscribeRef.current = subscribeToProgress(
        job_id,
        (progress) => {
          setCurrentJob(progress);
          if (progress.status === 'completed' || progress.status === 'failed') {
            setIsDownloading(false);
          }
        },
        (err) => {
          console.error('SSE Error:', err);
          setIsDownloading(false);
        }
      );
    } catch (err: any) {
      alert(`Download failed: ${err.message || 'Network error'}`);
      setIsDownloading(false);
    }
  };

  const handlePreview = (streamUrl: string, title: string, isAudio = false) => {
    setPreview({
      isOpen: true,
      title,
      streamUrl,
      isAudio,
    });
  };

  const handleDeleteJob = async (jobId: string) => {
    try {
      await deleteJobFiles(jobId);
      setCurrentJob((prev) =>
        prev && prev.job_id === jobId
          ? { ...prev, status: 'cleaned', download_url: undefined, zip_url: undefined, files: [] }
          : prev
      );
    } catch (err: any) {
      alert(`Could not delete files: ${err.message}`);
    }
  };

  return (
    <div className="min-h-screen bg-[#0a0b10] text-[#e0e2ec] flex flex-col selection:bg-[#27d2ed]/30 selection:text-white">
      {/* Top Navbar */}
      <Navbar />

      {/* Main Content Area */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-4 py-6">
        <div>
          {/* Hero / Tagline */}
          <div className="text-center my-6 space-y-2">
            <h1 className="text-2xl sm:text-4xl font-extrabold tracking-tight text-white">
              Download lossless media to your device
            </h1>
            <p className="text-xs sm:text-sm text-zinc-400 max-w-xl mx-auto">
              Automatic best stream pairing, server-side lossless merging, and instant browser
              downloads directly to your local computer.
            </p>
          </div>

          {/* URL Input Form */}
          <UrlInput onFetch={handleFetchMedia} isLoading={isFetching} />

          {/* Error Message */}
          {fetchError && (
            <div className="max-w-3xl mx-auto mb-6 p-4 rounded-2xl bg-[#f87070]/10 border border-[#f87070]/30 flex items-start gap-3 text-xs text-[#f87070]">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <div>
                <span className="font-bold">Inspection Error: </span>
                {fetchError}
              </div>
            </div>
          )}

          {/* Download Progress Card (if job running or completed) */}
          {currentJob && (
            <div className="max-w-3xl mx-auto mb-6">
              <ProgressCard
                progress={currentJob}
                onPreview={handlePreview}
                onDeleteJob={handleDeleteJob}
                onDismiss={() => setCurrentJob(null)}
              />
            </div>
          )}

          {/* Media Information Card */}
          {media && (
            <div className="max-w-3xl mx-auto space-y-6 animate-fade-in">
              <MediaCard media={media} />

              <FormatSelector
                media={media}
                onDownload={handleStartDownload}
                isDownloading={isDownloading}
              />
            </div>
          )}
        </div>
      </main>

      {/* In-Browser Media Preview Modal */}
      <MediaPreviewModal
        isOpen={preview.isOpen}
        onClose={() => setPreview((prev) => ({ ...prev, isOpen: false }))}
        title={preview.title}
        streamUrl={preview.streamUrl}
        downloadUrl={preview.streamUrl.replace('/api/stream/', '/api/download/file/')}
        isAudio={preview.isAudio}
      />


      {/* Footer */}
      <footer className="border-t border-[#181b28] py-5 text-center text-xs text-zinc-500">
        <p>
          Developed by{' '}
          <span className="text-zinc-300 font-medium">Md Mehedi Hasan</span>
        </p>
      </footer>
    </div>
  );
}

export default App;
