import React, { useState, useEffect } from 'react';
import { X, Download, Music, Film, AlertTriangle } from 'lucide-react';
import { triggerBrowserDownload } from '../services/api';

interface MediaPreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  streamUrl: string;
  downloadUrl?: string;
  isAudio?: boolean;
}

export const MediaPreviewModal: React.FC<MediaPreviewModalProps> = ({
  isOpen,
  onClose,
  title,
  streamUrl,
  downloadUrl,
  isAudio = false,
}) => {
  const [loadError, setLoadError] = useState<boolean>(false);

  useEffect(() => {
    setLoadError(false);
  }, [streamUrl, isOpen]);

  if (!isOpen) return null;

  const audioExts = ['.mp3', '.m4a', '.aac', '.wav', '.opus', '.flac', '.ogg'];
  const isAudioFile = isAudio || audioExts.some((ext) => (title || '').toLowerCase().endsWith(ext));

  return (
    <div className="fixed inset-0 z-50 bg-black/85 backdrop-blur-md flex items-center justify-center p-4 animate-fade-in">
      <div className="bg-[#12141e] border border-[#23273d] w-full max-w-3xl rounded-2xl overflow-hidden shadow-2xl flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#202438]">
          <div className="flex items-center gap-2 min-w-0 pr-4">
            {isAudioFile ? (
              <Music className="w-4 h-4 text-[#e778f9] shrink-0" />
            ) : (
              <Film className="w-4 h-4 text-[#27d2ed] shrink-0" />
            )}
            <h3 className="text-xs sm:text-sm font-bold text-white truncate">{title || 'Media Preview'}</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 text-zinc-400 hover:text-white rounded-lg hover:bg-zinc-800 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Media Player Container */}
        <div className="p-4 bg-black flex items-center justify-center min-h-[260px] max-h-[480px]">
          {loadError ? (
            <div className="flex flex-col items-center justify-center p-8 text-center max-w-md">
              <div className="w-12 h-12 rounded-full bg-[#f87070]/10 border border-[#f87070]/30 flex items-center justify-center text-[#f87070] mb-3">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <h4 className="text-sm font-bold text-white mb-1">Inline playback not supported by browser</h4>
              <p className="text-xs text-zinc-400 mb-4">
                Your web browser cannot decode this format inline, but the media was successfully merged. You can download and play it locally on any player.
              </p>
              {downloadUrl && (
                <button
                  onClick={() => triggerBrowserDownload(downloadUrl, title)}
                  className="flex items-center gap-1.5 px-4 py-2 bg-[#4bdd7f] hover:bg-[#56e889] text-[#0c0d12] font-bold text-xs rounded-xl shadow-lg cursor-pointer transition-all"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Save File to Computer</span>
                </button>
              )}
            </div>
          ) : isAudioFile ? (
            <div className="w-full max-w-md p-6 bg-[#181b29] border border-[#23273c] rounded-2xl flex flex-col items-center gap-4 shadow-xl">
              <div className="w-16 h-16 rounded-2xl bg-[#e778f9]/10 border border-[#e778f9]/30 flex items-center justify-center text-[#e778f9]">
                <Music className="w-8 h-8 animate-pulse" />
              </div>
              <p className="text-xs text-zinc-300 font-medium text-center truncate w-full">{title}</p>
              <audio
                controls
                autoPlay
                preload="metadata"
                className="w-full mt-2"
                src={streamUrl}
                onError={() => setLoadError(true)}
              >
                Your browser does not support the audio element.
              </audio>
            </div>
          ) : (
            <video
              controls
              autoPlay
              playsInline
              preload="metadata"
              className="max-h-[440px] w-full object-contain rounded-xl"
              src={streamUrl}
              onError={() => setLoadError(true)}
            >
              Your browser does not support the video tag.
            </video>
          )}
        </div>

        {/* Footer Actions */}
        <div className="p-4 border-t border-[#202438] flex items-center justify-between bg-[#151824]">
          <span className="text-[11px] text-zinc-400">
            Playing directly from stream without keeping file on VPS.
          </span>
          <div className="flex items-center gap-2">
            {downloadUrl && (
              <button
                onClick={() => triggerBrowserDownload(downloadUrl, title)}
                className="flex items-center gap-1.5 px-4 py-2 bg-[#4bdd7f] hover:bg-[#56e889] text-[#0c0d12] font-bold text-xs rounded-xl shadow-lg shadow-[#4bdd7f]/20 transition-all cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>Save to Device</span>
              </button>
            )}
            <button
              onClick={onClose}
              className="px-3 py-2 text-xs text-zinc-400 hover:text-white cursor-pointer"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
