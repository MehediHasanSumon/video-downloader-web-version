import React from 'react';
import type { MediaInfo } from '../types';
import { Clock, Eye, User, Layers, Video } from 'lucide-react';

interface MediaCardProps {
  media: MediaInfo;
}

export const MediaCard: React.FC<MediaCardProps> = ({ media }) => {
  return (
    <div className="bg-[#12141e] border border-[#222538] rounded-2xl p-5 shadow-xl transition-all">
      <div className="flex flex-col md:flex-row gap-5 items-start">
        {/* Thumbnail Preview */}
        <div className="relative w-full md:w-64 h-36 rounded-xl overflow-hidden bg-[#1a1d2c] border border-[#282c42] shrink-0 group">
          {media.thumbnail ? (
            <img
              src={media.thumbnail}
              alt={media.title}
              className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
            />
          ) : (
            <div className="w-full h-full flex flex-col items-center justify-center text-zinc-500">
              <Video className="w-8 h-8 mb-1" />
              <span className="text-xs">No Preview</span>
            </div>
          )}

          {/* Duration Pill */}
          {media.duration_str && media.duration_str !== 'Unknown' && (
            <div className="absolute bottom-2 right-2 bg-black/80 backdrop-blur-sm text-white text-[11px] font-mono px-2 py-0.5 rounded-md border border-white/10 flex items-center gap-1">
              <Clock className="w-3 h-3 text-[#27d2ed]" />
              <span>{media.duration_str}</span>
            </div>
          )}

          {/* Platform Badge */}
          <div className="absolute top-2 left-2 bg-[#12141e]/90 backdrop-blur-sm px-2.5 py-0.5 rounded-lg border border-[#2b2e46] text-xs font-semibold flex items-center gap-1.5 shadow-sm">
            <span>{media.platform_icon}</span>
            <span style={{ color: media.platform_color }}>{media.platform_name}</span>
          </div>
        </div>

        {/* Media Details */}
        <div className="flex-1 flex flex-col justify-between self-stretch">
          <div>
            <h2 className="text-base sm:text-lg font-bold text-white line-clamp-2 leading-snug">
              {media.title}
            </h2>

            <div className="flex items-center gap-3 mt-2 flex-wrap text-xs text-zinc-400">
              <div className="flex items-center gap-1 font-medium text-[#facc15]">
                <User className="w-3.5 h-3.5" />
                <span>{media.uploader}</span>
              </div>

              {media.views_str !== 'N/A' && (
                <div className="flex items-center gap-1 text-zinc-400">
                  <Eye className="w-3.5 h-3.5" />
                  <span>{media.views_str}</span>
                </div>
              )}

              {media.is_playlist && (
                <div className="flex items-center gap-1 text-[#e778f9] bg-[#e778f9]/10 px-2 py-0.5 rounded-md border border-[#e778f9]/20 font-semibold">
                  <Layers className="w-3.5 h-3.5" />
                  <span>Playlist ({media.playlist_count || 'Multiple'} items)</span>
                </div>
              )}
            </div>
          </div>

          <div className="text-[11px] text-zinc-500 truncate mt-3 pt-3 border-t border-[#1e2133]">
            Source: <span className="text-zinc-400 font-mono">{media.url}</span>
          </div>
        </div>
      </div>
    </div>
  );
};
