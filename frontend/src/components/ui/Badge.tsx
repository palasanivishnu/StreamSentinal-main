import React from 'react';

interface DecisionBadgeProps {
  decision: 'allow' | 'otp' | 'review' | 'block' | string;
  size?: 'sm' | 'md' | 'lg';
}

export const DecisionBadge: React.FC<DecisionBadgeProps> = ({ decision, size = 'md' }) => {
  const d = (decision || '').toLowerCase();
  let bg = 'bg-slate-100 text-slate-700 border-slate-200';
  let label = d.toUpperCase();

  if (d === 'allow') {
    bg = 'bg-emerald-50 text-[#16A34A] border-emerald-200';
  } else if (d === 'otp') {
    bg = 'bg-amber-50 text-[#D97706] border-amber-200';
  } else if (d === 'review') {
    bg = 'bg-orange-50 text-[#EA580C] border-orange-200';
  } else if (d === 'block') {
    bg = 'bg-rose-50 text-[#DC2626] border-rose-200';
  }

  const py =
    size === 'sm'
      ? 'py-0.5 px-2 text-[10px]'
      : size === 'lg'
      ? 'py-1 px-3 text-xs'
      : 'py-0.5 px-2.5 text-[11px]';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-sans font-bold tracking-wider uppercase ${py} ${bg}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current opacity-80" />
      {label}
    </span>
  );
};

export const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const s = (severity || '').toUpperCase();
  let bg = 'bg-slate-100 text-slate-700 border-slate-200';

  if (s === 'CRITICAL') {
    bg = 'bg-rose-50 text-[#DC2626] border-rose-200 font-bold';
  } else if (s === 'HIGH') {
    bg = 'bg-orange-50 text-[#EA580C] border-orange-200 font-semibold';
  } else if (s === 'WARNING' || s === 'MEDIUM') {
    bg = 'bg-amber-50 text-[#D97706] border-amber-200 font-medium';
  } else {
    bg = 'bg-blue-50 text-[#2563EB] border-blue-200 font-medium';
  }

  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[10px] font-sans uppercase font-bold tracking-wider ${bg}`}>
      {s}
    </span>
  );
};

export const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const st = (status || '').toLowerCase();
  let bg = 'bg-slate-100 text-slate-700 border-slate-200';

  if (st === 'healthy' || st === 'up' || st === 'running') {
    bg = 'bg-emerald-50 text-[#16A34A] border-emerald-200';
  } else if (st === 'degraded' || st === 'warning') {
    bg = 'bg-amber-50 text-[#D97706] border-amber-200';
  } else if (st === 'unhealthy' || st === 'down' || st === 'failed') {
    bg = 'bg-rose-50 text-[#DC2626] border-rose-200';
  }

  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-sans font-bold tracking-wider uppercase ${bg}`}>
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {st.toUpperCase()}
    </span>
  );
};