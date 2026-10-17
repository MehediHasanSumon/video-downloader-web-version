import React, { useEffect, useRef, useState } from 'react';
import type { JobProgress } from '../types';
import {
  Download,
  Play,
  Trash2,
  CheckCircle,
  AlertTriangle,
  Loader2,
  Gauge,
  Clock,
  HardDrive,
  Check,
  Archive,
  FileCheck,
} from 'lucide-react';
import { triggerBrowserDownload } from '../services/api';

interface ProgressCardProps {
  progress: JobProgress;
  onPreview: (streamUrl: string, title: string, isAudio?: boolean) => void;
  onDeleteJob: (jobId: string) => void;
  onDismiss: () => void;
}

export const ProgressCard: React.FC<ProgressCardProps> = ({
  progress,
  onPreview,
  onDeleteJob,
  onDismiss,
}) => {
  const isCompleted = progress.status === 'completed';
  const isFailed = progress.status === 'failed';
  const isMerging = progress.status === 'merging';
  const isCleaned = progress.status === 'cleaned';

  const autoDownloadedRef = useRef<boolean>(false);
  const [downloadTriggered, setDownloadTriggered] = useState<boolean>(false);

  // Auto-download to user's computer once ready
  useEffect(() => {
    if (isCompleted && progress.download_url && !autoDownloadedRef.current) {
      autoDownloadedRef.current = true;
      setDownloadTriggered(true);
      triggerBrowserDownload(progress.download_url, progress.current_filename);
    }
  }, [isCompleted, progress.download_url, progress.current_filename]);

  const hasMultipleFiles = Boolean(progress.files && progress.files.length > 1);
  const isAudioStream =
    progress.stream_type.toLowerCase().includes('audio') ||
    Boolean(
      progress.current_filename &&
        ['.mp3', '.m4a', '.aac', '.wav', '.opus', '.flac', '.ogg'].some((ext) =>
          progress.current_filename.toLowerCase().endsWith(ext)
        )
    );

  return (
    <div className="bg-[#12141e] border border-[#23273d] rounded-2xl p-5 shadow-2xl mt-6 relative overflow-hidden">
      {/* Top Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          {isCompleted ? (
            <div className="w-7 h-7 rounded-full bg-[#4bdd7f]/20 flex items-center justify-center text-[#4bdd7f]">
              <CheckCircle className="w-4 h-4" />
            </div>
          ) : isCleaned ? (
            <div className="w-7 h-7 rounded-full bg-zinc-800 flex items-center justify-center text-zinc-400">
              <Trash2 className="w-4 h-4" />
            </div>
          ) : isFailed ? (
            <div className="w-7 h-7 rounded-full bg-[#f87070]/20 flex items-center justify-center text-[#f87070]">
              <AlertTriangle className="w-4 h-4" />
            </div>
          ) : (
            <Loader2 className="w-5 h-5 text-[#27d2ed] animate-spin" />
          )}

          <div>
            <h4 className="text-xs font-bold uppercase tracking-wider text-white">
              {isCleaned
                ? 'Files Cleared from VPS'
                : isCompleted
                ? 'Ready for Local Download'
                : isFailed
                ? 'Download Failed'
                : isMerging
                ? 'FFmpeg Lossless Stream Merging...'
                : 'Downloading on Server...'}
            </h4>
            <p className="text-[11px] text-zinc-400 truncate max-w-md">
              {progress.current_filename || 'Processing media streams...'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-mono font-bold px-2.5 py-1 rounded-lg border ${
              isCompleted
                ? 'bg-[#4bdd7f]/10 border-[#4bdd7f]/30 text-[#4bdd7f]'
                : isCleaned
                ? 'bg-zinc-800 border-zinc-700 text-zinc-400'
                : isFailed
                ? 'bg-[#f87070]/10 border-[#f87070]/30 text-[#f87070]'
                : 'bg-[#27d2ed]/10 border-[#27d2ed]/30 text-[#27d2ed]'
            }`}
          >
            {isCompleted || isCleaned ? '100%' : `${progress.percent}%`}
          </span>
        </div>
      </div>

      {/* Progress Bar Container */}
      <div className="w-full bg-[#181b29] h-3 rounded-full overflow-hidden border border-[#252a42] p-[2px] mb-4">
        <div
          style={{ width: `${Math.max(3, progress.percent)}%` }}
          className={`h-full rounded-full transition-all duration-300 relative ${
            isCompleted
              ? 'bg-[#4bdd7f]'
              : isCleaned
              ? 'bg-zinc-600'
              : isFailed
              ? 'bg-[#f87070]'
              : 'bg-gradient-to-r from-[#27d2ed] to-[#af91f6]'
          }`}
        />
      </div>

      {/* Real-Time Metrics Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs py-2 px-3 bg-[#151824] rounded-xl border border-[#202436] mb-4">
        <div className="flex items-center gap-1.5 text-zinc-400">
          <Gauge className="w-3.5 h-3.5 text-[#27d2ed]" />
          <span>Speed:</span>
          <span className="font-semibold text-white font-mono">{progress.speed_str}</span>
        </div>

        <div className="flex items-center gap-1.5 text-zinc-400">
          <Clock className="w-3.5 h-3.5 text-[#facc15]" />
          <span>ETA:</span>
          <span className="font-semibold text-white font-mono">{progress.eta_str}</span>
        </div>

        <div className="flex items-center gap-1.5 text-zinc-400">
          <HardDrive className="w-3.5 h-3.5 text-[#af91f6]" />
          <span>Size:</span>
          <span className="font-semibold text-white font-mono">
            {progress.downloaded_str} / {progress.total_str}
          </span>
        </div>

        <div className="flex items-center gap-1.5 text-zinc-400">
          <Check className="w-3.5 h-3.5 text-[#4bdd7f]" />
          <span>Stream:</span>
          <span className="font-semibold text-white truncate">{progress.stream_type}</span>
        </div>
      </div>

      {/* VPS Temporary Storage Notice & Download Trigger Feedback */}
      {isCompleted && (
        <div className="mb-4 p-3 rounded-xl bg-[#27d2ed]/5 border border-[#27d2ed]/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 text-[11px]">
          <div className="flex items-center gap-2 text-[#27d2ed]">
            <FileCheck className="w-4 h-4 shrink-0" />
            <span>
              {downloadTriggered
                ? 'Download sent to your local machine! Check your browser downloads.'
                : 'Click below to save the file directly to your local computer.'}
            </span>
          </div>
          <span className="text-zinc-500 text-[10px]">
            VPS cache auto-purges in 15 mins to save server disk.
          </span>
        </div>
      )}

      {/* Multi-file / Playlist Items List */}
      {isCompleted && hasMultipleFiles && progress.files && (
        <div className="mb-4 bg-[#161824] border border-[#222538] rounded-xl p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold text-zinc-300">
              Completed Items ({progress.files.length})
            </span>
            {progress.zip_url && (
              <button
                onClick={() => triggerBrowserDownload(progress.zip_url!)}
                className="flex items-center gap-1 text-xs font-semibold text-[#af91f6] hover:text-[#d3c0ff]"
              >
                <Archive className="w-3.5 h-3.5" />
                <span>Save All as ZIP</span>
              </button>
            )}
          </div>
          <div className="max-h-36 overflow-y-auto space-y-1 pr-1 custom-scrollbar">
            {progress.files.map((file, idx) => (
              <div
                key={idx}
                className="flex items-center justify-between text-xs py-1.5 px-2.5 rounded-lg bg-[#1a1d2c] hover:bg-[#202436] transition-colors"
              >
                <span className="text-zinc-300 truncate max-w-[260px] sm:max-w-md">
                  {file.filename}
                </span>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-zinc-500 font-mono text-[10px]">{file.size_str}</span>
                  {file.stream_url && (
                    <button
                      onClick={() => onPreview(file.stream_url!, file.filename, isAudioStream)}
                      className="p-1 text-[#27d2ed] hover:text-white cursor-pointer"
                      title="Preview in browser"
                    >
                      <Play className="w-3.5 h-3.5 fill-current" />
                    </button>
                  )}
                  <button
                    onClick={() => triggerBrowserDownload(file.download_url, file.filename)}
                    className="p-1 text-[#4bdd7f] hover:text-white cursor-pointer"
                    title="Download file"
                  >
                    <Download className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Error Message Display if failed */}
      {isFailed && progress.error_message && (
        <div className="p-3 mb-4 rounded-xl bg-[#f87070]/10 border border-[#f87070]/30 text-xs text-[#f87070]">
          <span className="font-bold">Error: </span>
          {progress.error_message}
        </div>
      )}

      {/* Completion Action Buttons */}
      {isCompleted && (
        <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-[#1e2236]">
          <div className="flex flex-wrap items-center gap-2">
            {/* Primary Download to Local Device Button */}
            {progress.download_url && (
              <button
                onClick={() =>
                  triggerBrowserDownload(progress.download_url!, progress.current_filename)
                }
                className="flex items-center gap-1.5 px-4 py-2 bg-[#4bdd7f] hover:bg-[#56e889] text-[#0c0d12] font-bold text-xs rounded-xl shadow-lg shadow-[#4bdd7f]/20 transition-all active:scale-95 cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Save to Computer</span>
              </button>
            )}

            {/* ZIP Download for Playlists */}
            {progress.zip_url && (
              <button
                onClick={() => triggerBrowserDownload(progress.zip_url!)}
                className="flex items-center gap-1.5 px-3.5 py-2 bg-[#af91f6]/20 hover:bg-[#af91f6]/30 text-[#d3c0ff] border border-[#af91f6]/40 font-semibold text-xs rounded-xl transition-all cursor-pointer"
              >
                <Archive className="w-3.5 h-3.5" />
                <span>Download .ZIP</span>
              </button>
            )}

            {/* In-Browser Preview Button */}
            <button
              onClick={() => {
                const url =
                  (progress.files && progress.files.length > 0 && progress.files[0].stream_url)
                    ? progress.files[0].stream_url
                    : `/api/stream/${progress.job_id}`;
                onPreview(url, progress.current_filename, isAudioStream);
              }}
              className="flex items-center gap-1.5 px-3.5 py-2 bg-[#1b1e2c] hover:bg-[#25293d] border border-[#2b3047] text-white font-semibold text-xs rounded-xl transition-colors cursor-pointer"
            >
              <Play className="w-3.5 h-3.5 text-[#27d2ed] fill-current" />
              <span>Preview in Browser</span>
            </button>

            {/* Immediate VPS Disk Release Button */}
            <button
              onClick={() => onDeleteJob(progress.job_id)}
              title="Delete temporary file from VPS storage now"
              className="flex items-center gap-1 px-3 py-2 text-zinc-400 hover:text-[#f87070] bg-[#161824] hover:bg-[#231b20] border border-[#242738] rounded-xl text-xs transition-colors cursor-pointer"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Delete from Server</span>
            </button>
          </div>

          <button
            onClick={onDismiss}
            className="text-xs text-zinc-400 hover:text-white px-3 py-1.5 cursor-pointer"
          >
            Dismiss
          </button>
        </div>
      )}
    </div>
  );
};
