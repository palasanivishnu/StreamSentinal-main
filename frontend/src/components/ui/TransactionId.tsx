import React, { useState } from 'react';

interface TransactionIdProps {
  id: string;
  className?: string;
  showFull?: boolean;
}

export const TransactionId: React.FC<TransactionIdProps> = ({ id, className = '', showFull = false }) => {
  const [copied, setCopied] = useState(false);

  if (!id) return null;

  // Deliberate compact representation: first 23 chars ("00000006-0000-0000-0000" / "a7915132-c7c4-2409-96ba") without any "..."
  const compactDisplay = showFull || id.length <= 23 ? id : id.slice(0, 23);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (navigator.clipboard) {
      navigator.clipboard.writeText(id);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    }
  };

  return (
    <span
      onClick={handleCopy}
      title={`Transaction ID:\n${id}\n(Click to copy full ID)`}
      className={`inline-flex items-center gap-1 font-mono font-medium text-[11px] text-[#2563EB] hover:text-blue-700 whitespace-nowrap cursor-pointer select-none tracking-normal ${className}`}
      style={{ fontFamily: "'JetBrains Mono', monospace" }}
    >
      <span>{compactDisplay}</span>
      {copied && (
        <span className="text-[9px] bg-emerald-100 text-emerald-800 font-sans px-1 py-0.2 rounded font-bold transition-all animate-in fade-in">
          Copied!
        </span>
      )}
    </span>
  );
};
