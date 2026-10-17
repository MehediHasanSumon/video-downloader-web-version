import React from 'react';
import { Download } from 'lucide-react';

export const Navbar: React.FC = () => {
  return (
    <header className="border-b border-[#1f2230] bg-[#0f1118]/80 backdrop-blur-md sticky top-0 z-30 px-6 py-4">
      <div className="max-w-6xl mx-auto flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#27d2ed] via-[#af91f6] to-[#ed8fba] p-[2px] shadow-lg shadow-[#27d2ed]/10">
            <div className="w-full h-full bg-[#12141e] rounded-[10px] flex items-center justify-center">
              <Download className="w-5 h-5 text-[#27d2ed]" />
            </div>
          </div>
          <div>
            <span className="font-extrabold text-xl tracking-tight bg-gradient-to-r from-[#af91f6] to-[#ed8fba] bg-clip-text text-transparent">
              VIDEO DOWNLOADER
            </span>
          </div>
        </div>
      </div>
    </header>
  );
};
