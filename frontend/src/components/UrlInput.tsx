import React, { useState } from 'react';
import { Link2, ClipboardPaste, ArrowRight, Loader2, X } from 'lucide-react';

interface UrlInputProps {
  onFetch: (url: string) => void;
  isLoading: boolean;
}

export const UrlInput: React.FC<UrlInputProps> = ({ onFetch, isLoading }) => {
  const [url, setUrl] = useState('');

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        setUrl(text.trim());
        onFetch(text.trim());
      }
    } catch {
      // Fallback
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onFetch(url.trim());
    }
  };

  const platforms = [
    { name: 'YouTube', color: '#f87070' },
    { name: 'Facebook', color: '#60a4fa' },
    { name: 'Instagram', color: '#e778f9' },
    { name: 'TikTok', color: '#27d2ed' },
    { name: 'Twitter / X', color: '#f3f4f6' },
  ];

  return (
    <div className="w-full max-w-3xl mx-auto my-8">
      {/* Search Input Container */}
      <form onSubmit={handleSubmit} className="relative group">
        <div className="absolute -inset-1 bg-gradient-to-r from-[#27d2ed] via-[#af91f6] to-[#ed8fba] rounded-2xl blur opacity-25 group-hover:opacity-45 transition duration-500" />
        <div className="relative flex items-center bg-[#13151f] border border-[#232638] rounded-2xl shadow-2xl p-2 pl-4 focus-within:border-[#27d2ed] transition-all">
          <Link2 className="w-5 h-5 text-zinc-400 group-focus-within:text-[#27d2ed] transition-colors shrink-0 mr-3" />
          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="Paste video or audio link (YouTube, Facebook, Reels, TikTok, Twitter...)"
            className="w-full bg-transparent text-sm text-white placeholder-zinc-500 focus:outline-none"
            disabled={isLoading}
          />

          {url && (
            <button
              type="button"
              onClick={() => setUrl('')}
              className="p-2 text-zinc-400 hover:text-white transition-colors cursor-pointer"
            >
              <X className="w-4 h-4" />
            </button>
          )}

          <button
            type="button"
            onClick={handlePaste}
            className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-zinc-300 hover:text-white bg-[#1c1f2e] hover:bg-[#25293d] border border-[#2c3047] rounded-xl transition-all shrink-0 ml-1 cursor-pointer"
          >
            <ClipboardPaste className="w-3.5 h-3.5 text-[#27d2ed]" />
            <span className="hidden sm:inline">Paste</span>
          </button>

          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            className="flex items-center gap-1.5 px-5 py-2.5 ml-2 text-xs font-bold text-[#0c0d12] bg-[#27d2ed] hover:bg-[#34dbf2] disabled:opacity-40 disabled:hover:bg-[#27d2ed] rounded-xl transition-all shrink-0 shadow-lg shadow-[#27d2ed]/20 cursor-pointer disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Fetching...</span>
              </>
            ) : (
              <>
                <span>Inspect</span>
                <ArrowRight className="w-4 h-4" />
              </>
            )}
          </button>
        </div>
      </form>

      {/* Platform Pills */}
      <div className="flex items-center justify-center gap-2 mt-4 flex-wrap">
        <span className="text-xs text-zinc-500 mr-1">Supported:</span>
        {platforms.map((p) => (
          <span
            key={p.name}
            style={{ borderColor: `${p.color}30`, backgroundColor: `${p.color}10`, color: p.color }}
            className="text-[11px] font-semibold border px-2.5 py-0.5 rounded-full"
          >
            {p.name}
          </span>
        ))}
      </div>
    </div>
  );
};
