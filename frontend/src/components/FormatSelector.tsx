import React, { useState, useEffect } from 'react';
import type { MediaInfo } from '../types';
import { Download, Sparkles, Music, Film, CheckCircle2 } from 'lucide-react';
import { PlaylistSelector } from './PlaylistSelector';

interface FormatSelectorProps {
  media: MediaInfo;
  onDownload: (
    formatId: number,
    isPlaylist: boolean,
    playlistRange?: string,
    selectedIndices?: number[]
  ) => void;
  isDownloading: boolean;
}

export const FormatSelector: React.FC<FormatSelectorProps> = ({
  media,
  onDownload,
  isDownloading,
}) => {
  const [selectedId, setSelectedId] = useState<number>(0);
  const [mediaTab, setMediaTab] = useState<'all' | 'video' | 'audio'>('all');

  // Playlist selection state
  const [selectedIndices, setSelectedIndices] = useState<Set<number>>(() => {
    if (media.is_playlist && media.playlist_entries && media.playlist_entries.length > 0) {
      return new Set(media.playlist_entries.map((e) => e.index));
    }
    return new Set();
  });

  // Keep selectedIndices in sync if media updates
  useEffect(() => {
    if (media.is_playlist && media.playlist_entries && media.playlist_entries.length > 0) {
      setSelectedIndices(new Set(media.playlist_entries.map((e) => e.index)));
    } else {
      setSelectedIndices(new Set());
    }
  }, [media]);

  const handleToggleIndex = (index: number) => {
    setSelectedIndices((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const handleSelectAll = () => {
    if (media.playlist_entries) {
      setSelectedIndices(new Set(media.playlist_entries.map((e) => e.index)));
    }
  };

  const handleDeselectAll = () => {
    setSelectedIndices(new Set());
  };

  const handleInvertSelection = () => {
    if (!media.playlist_entries) return;
    setSelectedIndices((prev) => {
      const next = new Set<number>();
      for (const item of media.playlist_entries!) {
        if (!prev.has(item.index)) {
          next.add(item.index);
        }
      }
      return next;
    });
  };

  const handleSelectRange = (from: number, to: number) => {
    setSelectedIndices((prev) => {
      const next = new Set(prev);
      for (let i = from; i <= to; i++) {
        next.add(i);
      }
      return next;
    });
  };

  const handleSelectMultiple = (indices: number[]) => {
    setSelectedIndices((prev) => {
      const next = new Set(prev);
      for (const idx of indices) {
        next.add(idx);
      }
      return next;
    });
  };

  const handleStart = () => {
    if (media.is_playlist && media.playlist_entries && media.playlist_entries.length > 0) {
      if (selectedIndices.size === 0) return;
      const totalCount = media.playlist_entries.length;
      const isAll = selectedIndices.size === totalCount;
      const sortedArray = Array.from(selectedIndices).sort((a, b) => a - b);
      onDownload(
        selectedId,
        true,
        isAll ? undefined : sortedArray.join(','),
        isAll ? undefined : sortedArray
      );
    } else {
      onDownload(selectedId, media.is_playlist);
    }
  };

  // Filter format options based on active tab
  const filteredFormats = media.formats.filter((f) => {
    const isAudio = f.ext === 'mp3' || f.ext === 'm4a';
    if (mediaTab === 'video') return !isAudio;
    if (mediaTab === 'audio') return isAudio;
    return true;
  });

  const hasPlaylistItems = Boolean(
    media.is_playlist && media.playlist_entries && media.playlist_entries.length > 0
  );
  const totalPlaylistVideos = media.playlist_entries?.length || media.playlist_count || 0;
  const isSelectionEmpty = media.is_playlist && hasPlaylistItems && selectedIndices.size === 0;

  return (
    <div className="space-y-6">
      {/* 1. Playlist Checkbox Items Selector (Rendered first when it's a playlist) */}
      {hasPlaylistItems && (
        <PlaylistSelector
          entries={media.playlist_entries!}
          selectedIndices={selectedIndices}
          onToggleIndex={handleToggleIndex}
          onSelectAll={handleSelectAll}
          onDeselectAll={handleDeselectAll}
          onInvertSelection={handleInvertSelection}
          onSelectRange={handleSelectRange}
          onSelectMultiple={handleSelectMultiple}
        />
      )}

      {/* 2. Format & Quality Selector Card */}
      <div className="bg-[#12141e]/90 border border-[#222538] rounded-2xl p-5 shadow-2xl backdrop-blur-md">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <h3 className="text-sm font-bold text-white flex items-center gap-2 uppercase tracking-wider">
            <Sparkles className="w-4 h-4 text-[#27d2ed]" />
            <span>Select Quality & Format</span>
          </h3>

          {/* Segmented Filter: All / Video / Audio */}
          <div className="flex items-center gap-1 p-1 bg-[#161826] border border-[#262b42] rounded-xl self-start sm:self-auto">
            <button
              type="button"
              onClick={() => setMediaTab('all')}
              className={`px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                mediaTab === 'all'
                  ? 'bg-[#27d2ed] text-[#0c0d12] shadow-sm'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              All Formats
            </button>
            <button
              type="button"
              onClick={() => setMediaTab('video')}
              className={`flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                mediaTab === 'video'
                  ? 'bg-[#27d2ed] text-[#0c0d12] shadow-sm'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Film className="w-3 h-3" />
              <span>Video</span>
            </button>
            <button
              type="button"
              onClick={() => setMediaTab('audio')}
              className={`flex items-center gap-1 px-3 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                mediaTab === 'audio'
                  ? 'bg-[#af91f6] text-[#0c0d12] shadow-sm'
                  : 'text-zinc-400 hover:text-white'
              }`}
            >
              <Music className="w-3 h-3" />
              <span>Audio</span>
            </button>
          </div>
        </div>

        {/* Format Profiles List */}
        <div className="grid grid-cols-1 gap-2.5">
          {filteredFormats.map((format) => {
            const isSelected = format.id === selectedId;
            const isAudio = format.ext === 'mp3' || format.ext === 'm4a';

            return (
              <div
                key={format.id}
                onClick={() => setSelectedId(format.id)}
                className={`group p-3 sm:px-4 rounded-xl border cursor-pointer transition-all flex items-center justify-between gap-3 ${
                  isSelected
                    ? 'bg-[#181b29] border-[#27d2ed] shadow-lg shadow-[#27d2ed]/10 ring-1 ring-[#27d2ed]'
                    : 'bg-[#141622] border-[#222538] hover:border-[#2f334d] hover:bg-[#181b29]'
                }`}
              >
                <div className="flex items-center gap-3 min-w-0">
                  {/* Radio Indicator */}
                  <div
                    className={`w-4 h-4 rounded-full border flex items-center justify-center shrink-0 transition-colors ${
                      isSelected
                        ? 'border-[#27d2ed] bg-[#27d2ed]'
                        : 'border-zinc-600 bg-transparent group-hover:border-zinc-400'
                    }`}
                  >
                    {isSelected && <div className="w-1.5 h-1.5 rounded-full bg-[#0c0d12]" />}
                  </div>

                  {/* Icon */}
                  <div className="shrink-0">
                    {isAudio ? (
                      <Music
                        className={`w-4 h-4 ${isSelected ? 'text-[#af91f6]' : 'text-zinc-500'}`}
                      />
                    ) : (
                      <Film
                        className={`w-4 h-4 ${isSelected ? 'text-[#27d2ed]' : 'text-zinc-500'}`}
                      />
                    )}
                  </div>

                  {/* Format Name & Badges */}
                  <div className="flex flex-wrap items-center gap-2 min-w-0">
                    <span className="text-xs font-bold text-white group-hover:text-zinc-100">
                      {format.name}
                    </span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-[#1e2336] text-zinc-300 border border-[#2b304a]">
                      {format.badge}
                    </span>
                    {format.desc && (
                      <span className="hidden md:inline text-[11px] text-zinc-400 truncate max-w-xs">
                        {format.desc}
                      </span>
                    )}
                  </div>
                </div>

                {/* Right: Container Format & Estimated Size */}
                <div className="flex items-center gap-3 shrink-0">
                  <span className="text-[11px] font-mono font-semibold uppercase px-2 py-0.5 rounded bg-[#1e2233] text-zinc-300 border border-[#2a2e45]">
                    {format.ext}
                  </span>
                  <span className="text-xs font-bold text-[#4bdd7f] min-w-[75px] text-right font-mono">
                    {format.est_size}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Footer Action: Download Button */}
        <div
          className={`mt-5 pt-4 border-t border-[#1e2236] flex flex-col sm:flex-row items-center gap-3 ${
            media.is_playlist ? 'justify-end' : 'justify-between'
          }`}
        >
          {!media.is_playlist && (
            <div className="text-xs text-zinc-400 text-center sm:text-left">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[#4bdd7f]" />
                <span>Direct lossless single-file extraction</span>
              </div>
            </div>
          )}

          <button
            type="button"
            onClick={handleStart}
            disabled={isDownloading || isSelectionEmpty}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-8 py-3.5 rounded-xl font-bold text-xs bg-gradient-to-r from-[#27d2ed] via-[#af91f6] to-[#ed8fba] text-[#0c0d12] hover:opacity-95 active:scale-98 transition-all shadow-xl shadow-[#27d2ed]/25 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer"
          >
            <Download className="w-4 h-4 stroke-[2.5]" />
            <span>
              {media.is_playlist ? (
                selectedIndices.size === totalPlaylistVideos ? (
                  `Download All Videos (${totalPlaylistVideos})`
                ) : selectedIndices.size > 0 ? (
                  `Download Selected (${selectedIndices.size} Videos)`
                ) : (
                  'Select Videos to Download'
                )
              ) : (
                'Start Lossless Download'
              )}
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};
