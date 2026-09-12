import React, { useState } from 'react';
import { Search, X } from 'lucide-react';
import { globalSearch, SearchResult, Transaction } from '../api/client';
import { DecisionBadge, SeverityBadge } from './ui/Badge';

interface SearchModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectTransaction: (t: Transaction) => void;
}

export const SearchModal: React.FC<SearchModalProps> = ({ isOpen, onClose, onSelectTransaction }) => {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<SearchResult | null>(null);

  if (!isOpen) return null;

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await globalSearch(query);
      setResults(res);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-start justify-center pt-20 p-4">
      <div className="bg-white border border-slate-200 rounded-2xl max-w-2xl w-full shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-150">
        {/* Search Input */}
        <form onSubmit={handleSearch} className="flex items-center border-b border-slate-200 p-4 gap-3 bg-slate-50">
          <Search className="h-5 w-5 text-blue-600 shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search by Transaction ID, User ID, or Alert ID..."
            className="w-full bg-transparent text-slate-900 placeholder-slate-400 text-sm focus:outline-none font-sans"
            autoFocus
          />
          <button type="button" onClick={onClose} className="p-1 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-200 cursor-pointer transition-colors">
            <X className="h-5 w-5" />
          </button>
        </form>

        {/* Search Results */}
        <div className="p-5 max-h-[60vh] overflow-y-auto space-y-4">
          {loading && <p className="text-xs text-slate-500 font-sans text-center py-6">Searching StreamSentinel backend database...</p>}

          {results && !loading && (
            <>
              {results.transactions.length > 0 && (
                <div>
                  <p className="text-xs font-sans font-medium text-slate-500 uppercase tracking-wider mb-2">Transactions ({results.transactions.length})</p>
                  <div className="space-y-1.5">
                    {results.transactions.map((t) => (
                      <div
                        key={t.transaction_id}
                        onClick={() => {
                          onSelectTransaction(t);
                          onClose();
                        }}
                        className="flex items-center justify-between p-3 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl cursor-pointer transition-all"
                      >
                        <div>
                          <p className="text-xs font-mono font-semibold text-blue-600 hover:underline">{t.transaction_id}</p>
                          <p className="text-[11px] text-slate-500 font-mono mt-0.5">User: {t.user_id} | ${t.amount.toFixed(2)}</p>
                        </div>
                        <DecisionBadge decision={t.decision} />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {results.alerts.length > 0 && (
                <div>
                  <p className="text-xs font-sans font-medium text-slate-500 uppercase tracking-wider mb-2">Security Alerts ({results.alerts.length})</p>
                  <div className="space-y-1.5">
                    {results.alerts.map((a) => (
                      <div key={a.alert_id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs font-sans">
                        <div>
                          <p className="font-mono font-semibold text-red-600">{a.alert_id}</p>
                          <p className="text-slate-600 text-[11px] mt-0.5 font-sans">{a.reason}</p>
                        </div>
                        <SeverityBadge severity={a.severity} />
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {results.transactions.length === 0 && results.alerts.length === 0 && (
                <p className="text-xs text-slate-500 font-sans text-center py-6">No matching records found for "{results.query}".</p>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
};