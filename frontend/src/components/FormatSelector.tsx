import React, { useState } from 'react';
import type { MediaInfo } from '../types';
import { Download, Sparkles, Music, Film } from 'lucide-react';

interface FormatSelectorProps {
  media: MediaInfo;
  onDownload: (formatId: number, isPlaylist: boolean, playlistRange?: string) => void;
  isDownloading: boolean;
}

export const FormatSelector: React.FC<FormatSelectorProps> = ({
  media,
  onDownload,
  isDownloading,
}) => {
  const [selectedId, setSelectedId] = useState<number>(0);
  const [downloadPlaylist, setDownloadPlaylist] = useState<boolean>(media.is_playlist);
  const [playlistRange, setPlaylistRange] = useState<string>('');

  const handleStart = () => {
    onDownload(selectedId, downloadPlaylist, playlistRange.trim() || undefined);
  };

  return (
    <div className="bg-[#12141e] border border-[#222538] rounded-2xl p-5 shadow-xl mt-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-bold text-white flex items-center gap-2 uppercase tracking-wider">
          <Sparkles className="w-4 h-4 text-[#27d2ed]" />
          <span>Select Quality & Format</span>
        </h3>
        <span className="text-xs text-zinc-400">
          Target: <span className="font-semibold text-[#af91f6]">{media.platform_name}</span>
        </span>
      </div>

      {/* Format Options List */}
      <div className="flex flex-col gap-2">
        {media.formats.map((format) => {
          const isSelected = format.id === selectedId;
          const isAudio = format.ext === 'mp3' || format.ext === 'm4a';

          return (
            <div
              key={format.id}
              onClick={() => setSelectedId(format.id)}
              className={`p-3 px-4 rounded-xl border cursor-pointer transition-all flex items-center justify-between gap-3 ${
                isSelected
                  ? 'bg-[#181b29] border-[#27d2ed] shadow-md shadow-[#27d2ed]/10 ring-1 ring-[#27d2ed]'
                  : 'bg-[#141622] border-[#222538] hover:border-[#2f334d] hover:bg-[#181b29]'
              }`}
            >
              <div className="flex items-center gap-3 min-w-0">
                {/* Radio indicator */}
                <div
                  className={`w-4 h-4 rounded-full border flex items-center justify-center shrink-0 transition-colors ${
                    isSelected
                      ? 'border-[#27d2ed] bg-[#27d2ed]'
                      : 'border-zinc-600 bg-transparent'
                  }`}
                >
                  {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-[#0c0d12]" />}
                </div>

                {/* Media Icon */}
                <div className="shrink-0">
                  {isAudio ? (
                    <Music className={`w-4 h-4 ${isSelected ? 'text-[#e778f9]' : 'text-zinc-500'}`} />
                  ) : (
                    <Film className={`w-4 h-4 ${isSelected ? 'text-[#27d2ed]' : 'text-zinc-500'}`} />
                  )}
                </div>

                {/* Title & Badge */}
                <div className="flex flex-wrap items-center gap-2 min-w-0">
                  <span className="text-xs font-bold text-white">
                    {format.name}
                  </span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-zinc-800 text-zinc-300">
                    {format.badge}
                  </span>
                </div>
              </div>

              {/* Right: Format Ext & Real Size */}
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-[11px] font-mono font-semibold uppercase px-2 py-0.5 rounded bg-[#1e2233] text-zinc-400">
                  {format.ext}
                </span>
                <span className="text-xs font-bold text-[#4bdd7f] min-w-[70px] text-right">
                  {format.est_size}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Playlist Controls (if playlist) */}
      {media.is_playlist && (
        <div className="mt-5 p-4 bg-[#161826] border border-[#262a40] rounded-xl flex flex-col sm:flex-row items-center justify-between gap-3">
          <label className="flex items-center gap-2 text-xs font-semibold text-white cursor-pointer">
            <input
              type="checkbox"
              checked={downloadPlaylist}
              onChange={(e) => setDownloadPlaylist(e.target.checked)}
              className="rounded bg-[#12141e] border-zinc-700 text-[#27d2ed] focus:ring-[#27d2ed]"
            />
            <span>Download All Playlist Videos ({media.playlist_count || 'Multiple'})</span>
          </label>

          {downloadPlaylist && (
            <input
              type="text"
              value={playlistRange}
              onChange={(e) => setPlaylistRange(e.target.value)}
              placeholder="Range e.g. 1-10 or 5"
              className="bg-[#12141e] border border-[#2b3049] text-xs text-white px-3 py-1.5 rounded-lg focus:outline-none focus:border-[#27d2ed] w-full sm:w-44"
            />
          )}
        </div>
      )}

      {/* Action Footer */}
      <div className="mt-5 flex items-center justify-end pt-4 border-t border-[#1e2133]">
        <button
          onClick={handleStart}
          disabled={isDownloading}
          className="w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-bold text-xs bg-gradient-to-r from-[#27d2ed] to-[#af91f6] text-[#0c0d12] hover:opacity-90 transition-all shadow-lg shadow-[#27d2ed]/25 disabled:opacity-50 cursor-pointer"
        >
          <Download className="w-4 h-4" />
          <span>Start Lossless Download</span>
        </button>
      </div>
    </div>
  );
};
