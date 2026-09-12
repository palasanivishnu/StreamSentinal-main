import React, { useState, useEffect } from 'react';
import { ShieldAlert, RefreshCw } from 'lucide-react';

interface HeaderProps {
  onOpenSearch: () => void;
  onRefresh: () => void;
  isRefreshing?: boolean;
}

export const Header: React.FC<HeaderProps> = ({ onRefresh, isRefreshing }) => {
  const [time, setTime] = useState<string>('');

  useEffect(() => {
    const updateTime = () => setTime(new Date().toLocaleTimeString());
    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="relative h-16 bg-white border-b border-[#E6EAF0] px-6 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      {/* Left: Unchanged Brand Icon / Logo */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-[#2563EB] rounded-xl shadow-xs text-white">
          <ShieldAlert className="h-5 w-5 stroke-[2.5]" />
        </div>
      </div>

      {/* Center: Minimal Enterprise Brand Presentation */}
      <div className="absolute left-1/2 -translate-x-1/2 flex flex-col items-center justify-center text-center">
        <h1 className="text-base font-semibold font-sans text-[#172033] tracking-tight">
          StreamSentinel
        </h1>
        <div className="flex items-center gap-1.5 text-[10px] font-sans font-medium text-[#64748B] mt-0.5">
          <span className="h-1.5 w-1.5 rounded-full bg-[#16A34A] animate-pulse" />
          <span className="uppercase tracking-wider">REAL-TIME FRAUD INTELLIGENCE</span>
        </div>
      </div>

      {/* Right: Time & Refresh Button */}
      <div className="flex items-center gap-4">
        <div className="text-right font-sans text-xs tabular-nums">
          <p className="text-[#172033] font-semibold">{time}</p>
        </div>

        <button
          onClick={onRefresh}
          disabled={isRefreshing}
          className="p-2 bg-white border border-[#E6EAF0] hover:bg-gray-50 text-[#172033] rounded-xl text-xs flex items-center gap-1.5 cursor-pointer shadow-xs transition-all disabled:opacity-50"
          title="Refresh All Data"
        >
          <RefreshCw className={`h-4 w-4 text-[#2563EB] ${isRefreshing ? 'animate-spin' : ''}`} />
        </button>
      </div>
    </header>
  );
};