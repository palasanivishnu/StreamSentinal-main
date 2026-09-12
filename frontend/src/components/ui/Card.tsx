import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
}

export const Card: React.FC<CardProps> = ({ children, className = '', onClick }) => (
  <div
    onClick={onClick}
    className={`bg-white border border-[#E2E8F0] rounded-xl p-5 shadow-xs text-[#0F172A] transition-all ${className}`}
  >
    {children}
  </div>
);

export const CardHeader: React.FC<{
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  icon?: React.ReactNode;
}> = ({ title, subtitle, action, icon }) => (
  <div className="flex items-center justify-between border-b border-[#E2E8F0] pb-3.5 mb-4">
    <div className="flex items-center gap-2.5">
      {icon && <div className="text-[#2563EB] p-1.5 bg-blue-50 rounded-lg border border-blue-100">{icon}</div>}
      <div>
        <h3 className="text-xs font-bold text-[#0F172A] tracking-wider uppercase font-sans">{title}</h3>
        {subtitle && <p className="text-[11px] text-[#64748B] mt-0.5 font-sans leading-tight">{subtitle}</p>}
      </div>
    </div>
    {action && <div>{action}</div>}
  </div>
);