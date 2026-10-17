import React, { useState, useMemo, useRef } from 'react';
import type { PlaylistEntry } from '../types';
import {
  Check,
  Search,
  X,
  Sparkles,
  CheckCheck,
  RotateCcw,
  SlidersHorizontal,
  Clock,
  Video,
  ExternalLink,
} from 'lucide-react';

interface PlaylistSelectorProps {
  entries: PlaylistEntry[];
  selectedIndices: Set<number>;
  onToggleIndex: (index: number, isShift?: boolean) => void;
  onSelectAll: () => void;
  onDeselectAll: () => void;
  onInvertSelection: () => void;
  onSelectRange: (from: number, to: number) => void;
  onSelectMultiple: (indices: number[]) => void;
}

export const PlaylistSelector: React.FC<PlaylistSelectorProps> = ({
  entries,
  selectedIndices,
  onToggleIndex,
  onSelectAll,
  onDeselectAll,
  onInvertSelection,
  onSelectRange,
  onSelectMultiple,
}) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [showRangeInput, setShowRangeInput] = useState(false);
  const [rangeFrom, setRangeFrom] = useState('');
  const [rangeTo, setRangeTo] = useState('');
  const lastClickedIndexRef = useRef<number | null>(null);

  // Filter entries based on search query
  const filteredEntries = useMemo(() => {
    if (!searchQuery.trim()) return entries;
    const q = searchQuery.toLowerCase().trim();
    return entries.filter(
      (item) =>
        item.title.toLowerCase().includes(q) ||
        String(item.index).includes(q) ||
        (item.uploader && item.uploader.toLowerCase().includes(q))
    );
  }, [entries, searchQuery]);

  // Calculate total duration for selected items
  const selectedDurationStr = useMemo(() => {
    let totalSec = 0;
    for (const item of entries) {
      if (selectedIndices.has(item.index) && item.duration) {
        totalSec += item.duration;
      }
    }
    if (totalSec <= 0) return null;
    const hours = Math.floor(totalSec / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = Math.floor(totalSec % 60);
    if (hours > 0) {
      return `${hours}h ${mins}m`;
    }
    return `${mins}m ${secs}s`;
  }, [entries, selectedIndices]);

  const handleRowClick = (itemIndex: number, e: React.MouseEvent) => {
    if (e.shiftKey && lastClickedIndexRef.current !== null) {
      const start = Math.min(lastClickedIndexRef.current, itemIndex);
      const end = Math.max(lastClickedIndexRef.current, itemIndex);
      const rangeIndices: number[] = [];
      for (let i = start; i <= end; i++) {
        rangeIndices.push(i);
      }
      onSelectMultiple(rangeIndices);
    } else {
      onToggleIndex(itemIndex);
    }
    lastClickedIndexRef.current = itemIndex;
  };

  const handleApplyRange = (e: React.FormEvent) => {
    e.preventDefault();
    const from = parseInt(rangeFrom, 10);
    const to = parseInt(rangeTo, 10);
    if (!isNaN(from) && !isNaN(to) && from > 0 && to >= from) {
      onSelectRange(from, Math.min(to, entries.length));
      setShowRangeInput(false);
    }
  };

  const handleSelectFiltered = () => {
    const indices = filteredEntries.map((e) => e.index);
    onSelectMultiple(indices);
  };

  const isAllSelected = entries.length > 0 && selectedIndices.size === entries.length;
  const isNoneSelected = selectedIndices.size === 0;

  return (
    <div className="bg-[#12141e]/90 border border-[#222538] rounded-2xl p-4 sm:p-5 shadow-2xl backdrop-blur-md transition-all">
      {/* Header with Title & Live Selected Counter */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-[#1f2338]">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-[#27d2ed]/20 to-[#af91f6]/20 border border-[#27d2ed]/30 flex items-center justify-center text-[#27d2ed] shadow-md shadow-[#27d2ed]/10">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-white flex items-center gap-2 tracking-wide uppercase">
              <span>Select Playlist Videos</span>
            </h3>
          </div>
        </div>

        {/* Selected Count Badge & Duration */}
        <div className="flex items-center gap-2 shrink-0">
          <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#171a29] border border-[#2b304c] text-xs">
            <span className="text-zinc-400">Selected:</span>
            <span
              className={`font-mono font-bold ${
                selectedIndices.size > 0 ? 'text-[#27d2ed]' : 'text-zinc-500'
              }`}
            >
              {selectedIndices.size} / {entries.length}
            </span>
          </div>

          {selectedDurationStr && (
            <div className="hidden md:flex items-center gap-1 px-2.5 py-1.5 rounded-xl bg-[#171a29] border border-[#2b304c] text-xs text-amber-300 font-mono">
              <Clock className="w-3 h-3 text-amber-400" />
              <span>{selectedDurationStr}</span>
            </div>
          )}
        </div>
      </div>

      {/* Action Controls & Fast Search Toolbar */}
      <div className="mt-3.5 flex flex-col md:flex-row items-stretch md:items-center justify-between gap-2.5">
        {/* Quick Buttons: Select All / Deselect / Invert */}
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            type="button"
            onClick={onSelectAll}
            className={`flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold transition-all border cursor-pointer ${
              isAllSelected
                ? 'bg-[#27d2ed]/20 text-[#27d2ed] border-[#27d2ed]/40 shadow-sm'
                : 'bg-[#181b29] hover:bg-[#202538] text-zinc-300 hover:text-white border-[#272b42]'
            }`}
          >
            <CheckCheck className="w-3.5 h-3.5" />
            <span>Select All</span>
          </button>

          <button
            type="button"
            onClick={onDeselectAll}
            disabled={isNoneSelected}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-[#181b29] hover:bg-[#202538] text-zinc-300 hover:text-white border border-[#272b42] disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer transition-all"
          >
            <X className="w-3.5 h-3.5 text-[#f87070]" />
            <span>Clear</span>
          </button>

          <button
            type="button"
            onClick={onInvertSelection}
            className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-[#181b29] hover:bg-[#202538] text-zinc-300 hover:text-white border border-[#272b42] cursor-pointer transition-all"
            title="Invert current selection"
          >
            <RotateCcw className="w-3.5 h-3.5 text-[#af91f6]" />
            <span className="hidden sm:inline">Invert</span>
          </button>

          {/* Quick Range Presets */}
          <div className="flex items-center gap-1 ml-1 pl-1.5 border-l border-[#272b42]">
            <button
              type="button"
              onClick={() => onSelectRange(1, Math.min(10, entries.length))}
              className="px-2 py-1 text-[11px] font-mono font-medium rounded-md bg-[#161824] hover:bg-[#1f2336] text-zinc-300 hover:text-white border border-[#23273d] transition-all cursor-pointer"
            >
              1-10
            </button>
            <button
              type="button"
              onClick={() => onSelectRange(1, Math.min(25, entries.length))}
              className="px-2 py-1 text-[11px] font-mono font-medium rounded-md bg-[#161824] hover:bg-[#1f2336] text-zinc-300 hover:text-white border border-[#23273d] transition-all cursor-pointer"
            >
              1-25
            </button>
            <button
              type="button"
              onClick={() => setShowRangeInput(!showRangeInput)}
              className={`p-1 rounded-md border text-xs transition-all cursor-pointer ${
                showRangeInput
                  ? 'bg-[#27d2ed]/20 text-[#27d2ed] border-[#27d2ed]/40'
                  : 'bg-[#161824] text-zinc-400 hover:text-white border-[#23273d]'
              }`}
              title="Custom range selector"
            >
              <SlidersHorizontal className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>

        {/* Real-Time Filter Search Bar */}
        <div className="relative flex-1 max-w-xs">
          <Search className="w-3.5 h-3.5 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search playlist videos..."
            className="w-full bg-[#151724] border border-[#25293d] rounded-xl pl-8 pr-7 py-1.5 text-xs text-white placeholder-zinc-500 focus:outline-none focus:border-[#27d2ed] transition-colors"
          />
          {searchQuery && (
            <button
              type="button"
              onClick={() => setSearchQuery('')}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-zinc-400 hover:text-white p-0.5 cursor-pointer"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Custom Range Popdown */}
      {showRangeInput && (
        <form
          onSubmit={handleApplyRange}
          className="mt-2.5 p-3 rounded-xl bg-[#161826] border border-[#2b304c] flex items-center gap-2.5 text-xs animate-fade-in"
        >
          <span className="text-zinc-400 font-medium">Select items from</span>
          <input
            type="number"
            min={1}
            max={entries.length}
            value={rangeFrom}
            onChange={(e) => setRangeFrom(e.target.value)}
            placeholder="1"
            className="w-16 bg-[#10121c] border border-[#2b3049] rounded-lg px-2 py-1 text-center font-mono text-white focus:outline-none focus:border-[#27d2ed]"
          />
          <span className="text-zinc-400 font-medium">to</span>
          <input
            type="number"
            min={1}
            max={entries.length}
            value={rangeTo}
            onChange={(e) => setRangeTo(e.target.value)}
            placeholder={String(Math.min(10, entries.length))}
            className="w-16 bg-[#10121c] border border-[#2b3049] rounded-lg px-2 py-1 text-center font-mono text-white focus:outline-none focus:border-[#27d2ed]"
          />
          <button
            type="submit"
            className="px-3 py-1 bg-[#27d2ed] hover:bg-[#32dcf5] text-[#0c0d12] font-bold rounded-lg transition-all cursor-pointer"
          >
            Apply Range
          </button>
          <button
            type="button"
            onClick={() => setShowRangeInput(false)}
            className="text-zinc-400 hover:text-white ml-auto cursor-pointer"
          >
            Cancel
          </button>
        </form>
      )}

      {/* Filter notification if search query active */}
      {searchQuery && (
        <div className="mt-2 flex items-center justify-between text-xs px-2.5 py-1.5 rounded-lg bg-[#1a1d2e] border border-[#282d46] text-zinc-300">
          <span>
            Found <span className="font-bold text-[#27d2ed]">{filteredEntries.length}</span> of {entries.length} videos matching "{searchQuery}"
          </span>
          {filteredEntries.length > 0 && (
            <button
              type="button"
              onClick={handleSelectFiltered}
              className="text-[#af91f6] hover:text-[#d3c0ff] font-semibold cursor-pointer underline text-[11px]"
            >
              Select All Filtered
            </button>
          )}
        </div>
      )}

      {/* Videos List Container with Custom Scrollbar */}
      <div className="mt-3 max-h-[380px] overflow-y-auto space-y-1.5 pr-1.5 custom-scrollbar border border-[#1e2236] rounded-xl p-2 bg-[#0d0e15]/50">
        {filteredEntries.length === 0 ? (
          <div className="py-10 text-center text-zinc-500 text-xs">
            No videos matched your search query "{searchQuery}".
          </div>
        ) : (
          filteredEntries.map((item) => {
            const isSelected = selectedIndices.has(item.index);

            return (
              <div
                key={item.index}
                onClick={(e) => handleRowClick(item.index, e)}
                className={`group flex items-center justify-between gap-3 p-2 sm:p-2.5 rounded-xl border cursor-pointer select-none transition-all ${
                  isSelected
                    ? 'bg-[#181b29] border-[#27d2ed]/60 shadow-md shadow-[#27d2ed]/5 ring-1 ring-[#27d2ed]/30'
                    : 'bg-[#131520] border-[#1e2234] hover:bg-[#181a28] hover:border-[#2d324d]'
                }`}
              >
                {/* Left: Checkbox + Number + Thumbnail + Info */}
                <div className="flex items-center gap-3 min-w-0">
                  {/* Custom Checkbox */}
                  <div
                    className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 transition-all duration-150 ${
                      isSelected
                        ? 'border-[#27d2ed] bg-[#27d2ed] text-[#0a0d14] shadow-sm shadow-[#27d2ed]/40'
                        : 'border-zinc-600 bg-[#141624] group-hover:border-[#27d2ed]/60'
                    }`}
                  >
                    {isSelected && (
                      <Check className="w-3.5 h-3.5 stroke-[3.5]" />
                    )}
                  </div>

                  {/* Serial Number Pill */}
                  <span
                    className={`font-mono text-xs font-semibold min-w-[28px] transition-colors ${
                      isSelected ? 'text-[#27d2ed]' : 'text-zinc-400'
                    }`}
                  >
                    #{String(item.index).padStart(2, '0')}
                  </span>

                  {/* Thumbnail with duration overlay */}
                  <div className="relative w-16 h-10 sm:w-20 sm:h-12 rounded-lg overflow-hidden bg-[#1a1d2e] shrink-0 border border-[#272b42]">
                    {item.thumbnail ? (
                      <img
                        src={item.thumbnail}
                        alt=""
                        loading="lazy"
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center text-zinc-600">
                        <Video className="w-4 h-4" />
                      </div>
                    )}

                    {item.duration_str && item.duration_str !== 'Unknown' && (
                      <div className="absolute bottom-0.5 right-0.5 bg-black/85 text-[10px] font-mono text-zinc-200 px-1 py-0.2 rounded border border-white/10 leading-tight">
                        {item.duration_str}
                      </div>
                    )}
                  </div>

                  {/* Video Title & Uploader */}
                  <div className="min-w-0 flex-1">
                    <p
                      className={`text-xs font-semibold line-clamp-2 leading-snug transition-colors ${
                        isSelected ? 'text-white' : 'text-zinc-200 group-hover:text-white'
                      }`}
                      title={item.title}
                    >
                      {item.title}
                    </p>
                    {item.uploader && (
                      <p className="text-[10px] text-zinc-500 truncate mt-0.5">
                        {item.uploader}
                      </p>
                    )}
                  </div>
                </div>

                {/* Right: Direct Watch Link (optional click without toggling checkbox) */}
                {item.url && (
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    title="Open on YouTube"
                    className="p-1.5 text-zinc-500 hover:text-[#27d2ed] hover:bg-[#1f2336] rounded-lg transition-colors shrink-0"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                )}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
