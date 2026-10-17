import React from 'react';
import type { MediaInfo } from '../types';
import { Clock, Eye, User, Layers, Video } from 'lucide-react';

interface MediaCardProps {
  media: MediaInfo;
}

export const MediaCard: React.FC<MediaCardProps> = ({ media }) => {
  const itemCount = media.playlist_entries?.length || media.playlist_count || 0;

  return (
    <div className="relative group">
      {/* Background Neon Ambient Glow */}
      <div className="absolute -inset-0.5 bg-gradient-to-r from-[#27d2ed]/20 via-[#af91f6]/20 to-[#ed8fba]/20 rounded-3xl blur-md opacity-50 group-hover:opacity-80 transition duration-500 pointer-events-none" />

      <div className="relative bg-[#12141e]/95 border border-[#23273e] rounded-2xl p-5 shadow-2xl backdrop-blur-md transition-all">
        <div className="flex flex-col md:flex-row gap-5 items-center">
          {/* Thumbnail Preview */}
          <div className="relative w-full md:w-64 h-36 rounded-xl overflow-hidden bg-[#1a1d2c] border border-[#282c42] shrink-0 group/thumb shadow-inner">
            {media.thumbnail ? (
              <img
                src={media.thumbnail}
                alt={media.title}
                className="w-full h-full object-cover group-hover/thumb:scale-105 transition-transform duration-300"
              />
            ) : (
              <div className="w-full h-full flex flex-col items-center justify-center text-zinc-500">
                <Video className="w-8 h-8 mb-1" />
                <span className="text-xs">No Preview</span>
              </div>
            )}

            {/* Duration Pill */}
            {media.duration_str && media.duration_str !== 'Unknown' && (
              <div className="absolute bottom-2 right-2 bg-black/85 backdrop-blur-md text-white text-[11px] font-mono px-2 py-0.5 rounded-md border border-white/15 flex items-center gap-1 shadow-lg">
                <Clock className="w-3 h-3 text-[#27d2ed]" />
                <span>{media.duration_str}</span>
              </div>
            )}

            {/* Platform Badge */}
            <div className="absolute top-2 left-2 bg-[#12141e]/95 backdrop-blur-md px-2.5 py-1 rounded-lg border border-[#2e334e] text-xs font-semibold flex items-center gap-1.5 shadow-md">
              <span>{media.platform_icon}</span>
              <span style={{ color: media.platform_color }}>{media.platform_name}</span>
            </div>
          </div>

          {/* Media Details */}
          <div className="flex-1 flex flex-col justify-center gap-3 w-full">
            <div>
              {media.url ? (
                <a
                  href={media.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  title="Open on YouTube"
                  className="text-base sm:text-lg font-bold text-white hover:text-[#27d2ed] transition-colors line-clamp-2 leading-snug cursor-pointer block"
                >
                  {media.title}
                </a>
              ) : (
                <h2 className="text-base sm:text-lg font-bold text-white line-clamp-2 leading-snug">
                  {media.title}
                </h2>
              )}
            </div>

            <div className="flex items-center gap-2.5 flex-wrap text-xs text-zinc-400">
              {media.uploader && media.uploader !== 'Unknown' && (
                <div className="flex items-center gap-1.5 font-medium text-amber-300 bg-[#24211a] px-2.5 py-1 rounded-lg border border-amber-500/20">
                  <User className="w-3.5 h-3.5 text-amber-400" />
                  <span>{media.uploader}</span>
                </div>
              )}

              {media.views_str !== 'N/A' && (
                <div className="flex items-center gap-1 text-zinc-400 bg-[#161826] px-2.5 py-1 rounded-lg border border-[#252a40]">
                  <Eye className="w-3.5 h-3.5 text-zinc-400" />
                  <span>{media.views_str}</span>
                </div>
              )}

              {media.is_playlist && (
                <div className="flex items-center gap-1.5 text-[#e778f9] bg-[#e778f9]/10 px-2.5 py-1 rounded-lg border border-[#e778f9]/30 font-semibold shadow-sm">
                  <Layers className="w-3.5 h-3.5" />
                  <span>Playlist ({itemCount} videos)</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
