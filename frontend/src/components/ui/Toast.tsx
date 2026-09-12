import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, Info, X } from 'lucide-react';

export interface ToastMessage {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message?: string;
}

interface ToastContainerProps {
  toasts: ToastMessage[];
  onDismiss: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onDismiss }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2.5 max-w-md w-full pointer-events-none">
      {toasts.map((t) => {
        let border = 'border-gray-200 bg-white text-gray-900 shadow-lg';
        let icon = <Info className="h-5 w-5 text-blue-600 shrink-0" />;

        if (t.type === 'success') {
          border = 'border-emerald-200 bg-emerald-50 text-emerald-900 shadow-lg';
          icon = <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />;
        } else if (t.type === 'error') {
          border = 'border-rose-200 bg-rose-50 text-rose-900 shadow-lg';
          icon = <XCircle className="h-5 w-5 text-rose-600 shrink-0" />;
        } else if (t.type === 'warning') {
          border = 'border-amber-200 bg-amber-50 text-amber-900 shadow-lg';
          icon = <AlertTriangle className="h-5 w-5 text-amber-600 shrink-0" />;
        }

        return (
          <div
            key={t.id}
            className={`pointer-events-auto flex items-start gap-3 rounded-xl border p-4 backdrop-blur-md transition-all duration-200 animate-in slide-in-from-bottom-3 ${border}`}
          >
            {icon}
            <div className="flex-1 text-xs">
              <p className="font-semibold text-gray-900 font-mono">{t.title}</p>
              {t.message && <p className="mt-0.5 text-gray-600 leading-relaxed">{t.message}</p>}
            </div>
            <button
              onClick={() => onDismiss(t.id)}
              className="text-gray-400 hover:text-gray-600 p-0.5 rounded-md hover:bg-gray-100 cursor-pointer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
};