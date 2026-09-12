import React from 'react';
import {
  LayoutDashboard,
  Activity,
  AlertTriangle,
  FileCheck2,
  KeyRound,
  BarChart3,
  Cpu,
  ShieldAlert,
} from 'lucide-react';

interface SidebarProps {
  currentPage: string;
  onNavigate: (page: string) => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentPage, onNavigate }) => {
  const menuItems = [
    { id: 'overview', label: 'Command Center', icon: <LayoutDashboard className="h-4 w-4" /> },
    { id: 'transactions', label: 'Live Transactions', icon: <Activity className="h-4 w-4" /> },
    { id: 'alerts', label: 'Alerts', icon: <AlertTriangle className="h-4 w-4" /> },
    { id: 'reviews', label: 'Review Queue', icon: <FileCheck2 className="h-4 w-4" /> },
    { id: 'otp', label: 'OTP Verification', icon: <KeyRound className="h-4 w-4" /> },
    { id: 'analytics', label: 'Analytics', icon: <BarChart3 className="h-4 w-4" /> },
    { id: 'engine', label: 'Detection Engine', icon: <Cpu className="h-4 w-4" /> },
  ];

  return (
    <aside className="w-64 bg-[#0F172A] border-r border-[#1E293B] flex flex-col justify-between shrink-0 select-none">
      <div className="p-4 space-y-1">
        <div className="px-3 py-2 mb-3 border-b border-[#1E293B] flex items-center gap-2.5">
          <ShieldAlert className="h-4 w-4 text-[#2563EB]" />
          <span className="font-sans font-bold text-xs tracking-wider text-white uppercase">StreamSentinel</span>
        </div>

        <p className="text-[10px] font-sans font-bold uppercase tracking-wider text-slate-400 px-3 mb-2">OPERATIONS MENU</p>
        
        {menuItems.map((item) => {
          const isActive = currentPage === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onNavigate(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-xs font-sans font-medium transition-all cursor-pointer ${
                isActive
                  ? 'bg-[#2563EB] text-white font-semibold shadow-xs'
                  : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
              }`}
            >
              <span className={isActive ? 'text-white' : 'text-slate-400'}>{item.icon}</span>
              <span>{item.label}</span>
            </button>
          );
        })}
      </div>

      {/* System Footer Info */}
      <div className="p-4 border-t border-[#1E293B] bg-[#090D16] text-[11px] text-slate-400 space-y-1.5 font-sans">
        <div className="flex justify-between items-center text-slate-400">
          <span className="font-sans">Detection Model:</span>
          <span className="text-purple-400 font-mono font-semibold">XGBoost v2</span>
        </div>
        <div className="flex justify-between items-center text-slate-400">
          <span className="font-sans">Backend Status:</span>
          <span className="text-emerald-400 font-sans font-semibold">Online</span>
        </div>
      </div>
    </aside>
  );
};