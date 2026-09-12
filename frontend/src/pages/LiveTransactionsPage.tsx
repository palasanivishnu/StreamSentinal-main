import React, { useState, useMemo } from 'react';
import { Activity, Filter, RefreshCw, Eye, ChevronDown, Search } from 'lucide-react';
import { Transaction } from '../api/client';
import { Card, CardHeader } from '../components/ui/Card';
import { DecisionBadge } from '../components/ui/Badge';
import { TransactionId } from '../components/ui/TransactionId';
import { formatUserId, formatMerchantName, normalizeRiskScore } from '../utils/formatters';

export type ConnectionStatus = 'initializing' | 'connected' | 'disconnected';

interface LiveTransactionsPageProps {
  transactions: Transaction[];
  onSelectTransaction: (t: Transaction) => void;
  onRefresh: () => void;
  connectionStatus?: ConnectionStatus;
}

export const LiveTransactionsPage: React.FC<LiveTransactionsPageProps> = ({
  transactions,
  onSelectTransaction,
  onRefresh,
  connectionStatus,
}) => {
  const [decisionFilter, setDecisionFilter] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [sortOrder, setSortOrder] = useState<string>('newest');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [isFilterOpen, setIsFilterOpen] = useState<boolean>(false);

  // Connection health status: initializing | connected | disconnected
  const status: ConnectionStatus = connectionStatus ?? (
    transactions && transactions.length > 0 ? 'connected' : 'initializing'
  );

  // Unified Filtering & Sorting Pipeline
  const displayTransactions = useMemo(() => {
    const query = searchQuery.trim().toLowerCase();

    // 1. Filter
    const filtered = transactions.filter((t) => {
      const riskPct = normalizeRiskScore(t.risk_score);

      // Decision Filter
      const txnDecision = String(t.decision ?? '').trim().toLowerCase();
      const targetDecision = decisionFilter.trim().toLowerCase();
      const matchesDecision = targetDecision === 'all' || txnDecision === targetDecision;

      // Risk Filter
      let matchesRisk = true;
      switch (riskFilter) {
        case 'low':
          matchesRisk = riskPct < 25;
          break;
        case 'medium':
          matchesRisk = riskPct >= 25 && riskPct < 50;
          break;
        case 'high':
          matchesRisk = riskPct >= 50 && riskPct < 75;
          break;
        case 'critical':
          matchesRisk = riskPct >= 75;
          break;
        case 'all':
        default:
          matchesRisk = true;
          break;
      }

      // Search Filter (ID, User ID, Merchant)
      const mName = formatMerchantName(t.merchant, t.merchant_category);
      const matchesSearch =
        !query ||
        String(t.transaction_id ?? '').toLowerCase().includes(query) ||
        String(t.user_id ?? '').toLowerCase().includes(query) ||
        mName.toLowerCase().includes(query) ||
        String(t.merchant_category ?? '').toLowerCase().includes(query);

      return matchesDecision && matchesRisk && matchesSearch;
    });

    // 2. Sort
    filtered.sort((a, b) => {
      switch (sortOrder) {
        case 'highest_risk':
          return normalizeRiskScore(b.risk_score) - normalizeRiskScore(a.risk_score);

        case 'lowest_risk':
          return normalizeRiskScore(a.risk_score) - normalizeRiskScore(b.risk_score);

        case 'largest_amount':
        case 'amount':
          return Number(b.amount ?? 0) - Number(a.amount ?? 0);

        case 'newest':
        default:
          return (
            new Date(String(b.processed_at ?? b.saved_at ?? b.timestamp ?? 0)).getTime() -
            new Date(String(a.processed_at ?? a.saved_at ?? a.timestamp ?? 0)).getTime()
          );
      }
    });

    return filtered;
  }, [transactions, decisionFilter, riskFilter, searchQuery, sortOrder]);

  const formatTimeAgo = (ts?: string): string => {
    if (!ts) return 'just now';
    try {
      const date = new Date(ts);
      const diffSec = Math.floor((new Date().getTime() - date.getTime()) / 1000);
      if (isNaN(diffSec) || diffSec < 5) return 'just now';
      if (diffSec < 60) return `${diffSec}s ago`;
      if (diffSec < 3600) return `${Math.floor(diffSec / 60)}m ago`;
      return `${Math.floor(diffSec / 3600)}h ago`;
    } catch {
      return 'just now';
    }
  };

  return (
    <div className="space-y-6">
      {/* 1. Header Section */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-xl font-bold font-sans text-[#0F172A] tracking-tight">LIVE TRANSACTIONS</h1>
            <div
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-sans font-semibold border ${
                status === 'connected'
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-700'
                  : status === 'initializing'
                  ? 'bg-blue-50 border-blue-200 text-blue-700'
                  : 'bg-rose-50 border-rose-200 text-rose-700'
              }`}
            >
              <span className="relative flex h-2 w-2">
                {status !== 'disconnected' && (
                  <span
                    className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                      status === 'connected' ? 'bg-emerald-400' : 'bg-blue-400'
                    }`}
                  ></span>
                )}
                <span
                  className={`relative inline-flex rounded-full h-2 w-2 ${
                    status === 'connected'
                      ? 'bg-emerald-500'
                      : status === 'initializing'
                      ? 'bg-blue-500'
                      : 'bg-rose-500'
                  }`}
                ></span>
              </span>
              <span>
                {status === 'connected'
                  ? 'LIVE'
                  : status === 'initializing'
                  ? 'CONNECTING...'
                  : 'DISCONNECTED'}
              </span>
            </div>
          </div>
          <p className="text-xs text-[#64748B] mt-0.5 font-sans">Real-time transaction activity</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="h-4 w-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search transaction or user..."
              className="bg-white border border-[#E2E8F0] rounded-xl pl-9 pr-3.5 py-2 text-xs text-[#0F172A] placeholder-slate-400 font-sans focus:outline-none focus:border-[#2563EB] w-64 shadow-xs"
            />
          </div>
          <button
            onClick={onRefresh}
            className="px-3.5 py-2 bg-white border border-[#E2E8F0] hover:bg-slate-50 text-[#0F172A] rounded-xl text-xs flex items-center gap-1.5 cursor-pointer shadow-xs font-sans font-semibold transition-colors"
          >
            <RefreshCw className="h-4 w-4 text-[#2563EB]" />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* 2. Primary Filters & Filter Popover */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        {/* Decision Filter Pills */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {['all', 'allow', 'otp', 'review', 'block'].map((d) => (
            <button
              key={d}
              onClick={() => setDecisionFilter(d)}
              className={`px-3.5 py-1.5 text-xs font-sans rounded-xl border transition-all cursor-pointer font-semibold uppercase tracking-wider ${
                decisionFilter === d
                  ? 'bg-[#2563EB] text-white border-[#2563EB] shadow-xs'
                  : 'bg-white text-[#64748B] border-[#E2E8F0] hover:bg-slate-50 hover:text-[#0F172A]'
              }`}
            >
              {d}
            </button>
          ))}
        </div>

        {/* Filter Popover Dropdown */}
        <div className="relative">
          <button
            onClick={() => setIsFilterOpen(!isFilterOpen)}
            className={`px-3.5 py-1.5 text-xs font-sans rounded-xl border flex items-center gap-2 transition-all cursor-pointer font-semibold bg-white text-[#0F172A] border-[#E2E8F0] hover:bg-slate-50 shadow-xs ${
              riskFilter !== 'all' || sortOrder !== 'newest' ? 'border-[#2563EB] text-[#2563EB] bg-blue-50/50' : ''
            }`}
          >
            <Filter className="h-3.5 w-3.5" />
            <span>Filter</span>
            <ChevronDown className="h-3.5 w-3.5 text-slate-400" />
          </button>

          {isFilterOpen && (
            <div className="absolute right-0 mt-2 w-64 bg-white border border-[#E2E8F0] rounded-2xl shadow-xl p-4 z-30 space-y-4 animate-in fade-in zoom-in-95 duration-100 font-sans">
              <div>
                <p className="text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2 font-sans">Risk Level</p>
                <div className="space-y-1">
                  {[
                    { id: 'all', label: 'All Risks' },
                    { id: 'low', label: 'Low (<25%)' },
                    { id: 'medium', label: 'Medium (25–50%)' },
                    { id: 'high', label: 'High (50–75%)' },
                    { id: 'critical', label: 'Critical (≥75%)' },
                  ].map((r) => (
                    <label
                      key={r.id}
                      className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer text-xs text-[#0F172A]"
                    >
                      <input
                        type="radio"
                        name="riskFilter"
                        checked={riskFilter === r.id}
                        onChange={() => setRiskFilter(r.id)}
                        className="text-[#2563EB] focus:ring-0"
                      />
                      <span>{r.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="border-t border-slate-100 pt-3">
                <p className="text-[10px] font-bold uppercase tracking-wider text-[#64748B] mb-2 font-sans">Sort By</p>
                <div className="space-y-1">
                  {[
                    { id: 'newest', label: 'Newest First' },
                    { id: 'highest_risk', label: 'Highest Risk First' },
                    { id: 'lowest_risk', label: 'Lowest Risk First' },
                    { id: 'largest_amount', label: 'Largest Amount' },
                  ].map((s) => (
                    <label
                      key={s.id}
                      className="flex items-center gap-2.5 px-2 py-1.5 rounded-lg hover:bg-slate-50 cursor-pointer text-xs text-[#0F172A]"
                    >
                      <input
                        type="radio"
                        name="sortOrder"
                        checked={sortOrder === s.id}
                        onChange={() => setSortOrder(s.id)}
                        className="text-[#2563EB] focus:ring-0"
                      />
                      <span>{s.label}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div className="border-t border-slate-100 pt-3 flex justify-between items-center">
                <button
                  onClick={() => {
                    setRiskFilter('all');
                    setSortOrder('newest');
                  }}
                  className="text-[11px] text-slate-500 hover:text-slate-900 underline cursor-pointer"
                >
                  Reset
                </button>
                <button
                  onClick={() => setIsFilterOpen(false)}
                  className="px-3 py-1 bg-[#2563EB] text-white rounded-lg text-[11px] font-semibold cursor-pointer"
                >
                  Apply
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 3. Main Hero Table Card */}
      <Card className="border-[#E2E8F0] bg-white shadow-xs">
        <CardHeader
          title={`Transactions (${displayTransactions.length})`}
          subtitle="Showing 50 most recent transactions — click any row to inspect intelligence drawer"
          icon={<Activity className="h-4 w-4 text-[#2563EB]" />}
        />

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E2E8F0] bg-[#F8FAFC] text-[10px] font-sans uppercase text-[#64748B] font-bold tracking-wider">
                <th className="py-3 px-4">Transaction ID</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Merchant</th>
                <th className="py-3 px-4 text-right">Amount</th>
                <th className="py-3 px-4 text-right">Risk Score</th>
                <th className="py-3 px-4">Decision</th>
                <th className="py-3 px-4 text-right">Latency</th>
                <th className="py-3 px-4 text-right">Time</th>
                <th className="py-3 px-4 text-right">Inspect</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 font-sans text-xs">
              {displayTransactions.length > 0 ? (
                displayTransactions.map((t) => {
                  const mName = formatMerchantName(t.merchant, t.merchant_category);
                  const riskPct = normalizeRiskScore(t.risk_score);
                  const displayTime = formatTimeAgo(t.processed_at || t.saved_at || t.timestamp);

                  return (
                    <tr
                      key={t.transaction_id}
                      onClick={() => onSelectTransaction(t)}
                      className="hover:bg-[#F8FAFC] cursor-pointer transition-colors group"
                    >
                      <td className="py-3.5 px-4">
                        <TransactionId id={t.transaction_id} />
                      </td>
                      <td className="py-3.5 px-4 text-[#0F172A] font-medium">{formatUserId(t.user_id)}</td>
                      <td className="py-3.5 px-4 text-[#0F172A] font-medium">{mName}</td>
                      <td className="py-3.5 px-4 text-[#0F172A] font-sans tabular-nums font-medium text-right">
                        ${Number(t.amount ?? 0).toFixed(2)}
                      </td>
                      <td className="py-3.5 px-4 text-right font-sans tabular-nums">
                        <span
                          className={`font-medium ${
                            riskPct >= 75
                              ? 'text-red-600'
                              : riskPct >= 50
                              ? 'text-orange-600'
                              : riskPct >= 25
                              ? 'text-amber-600'
                              : 'text-emerald-700'
                          }`}
                        >
                          {riskPct.toFixed(1)}%
                        </span>
                      </td>
                      <td className="py-3.5 px-4">
                        <DecisionBadge decision={t.decision} />
                      </td>
                      <td className="py-3.5 px-4 text-[#64748B] font-sans tabular-nums font-medium text-right">
                        {t.latency_ms ? `${t.latency_ms.toFixed(1)} ms` : 'N/A'}
                      </td>
                      <td className="py-3.5 px-4 text-[#64748B] font-sans tabular-nums font-medium text-right text-[11px]">
                        {displayTime}
                      </td>
                      <td className="py-3.5 px-4 text-right">
                        <button className="p-1 text-slate-400 group-hover:text-[#2563EB] rounded-md group-hover:bg-slate-100 transition-colors">
                          <Eye className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500 font-sans text-xs">
                    {status === 'initializing' ? (
                      <div className="flex items-center justify-center gap-2">
                        <RefreshCw className="h-4 w-4 animate-spin text-[#2563EB]" />
                        <span className="font-medium text-slate-700">Connecting to live transaction stream...</span>
                      </div>
                    ) : status === 'disconnected' ? (
                      <div className="space-y-2">
                        <p className="font-semibold text-rose-700">Backend service disconnected.</p>
                        <p className="text-slate-500 text-[11px]">Unable to connect to StreamSentinel API on http://localhost:8000.</p>
                        <button
                          onClick={onRefresh}
                          className="mt-2 px-3.5 py-1.5 bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-200 rounded-lg text-xs font-semibold cursor-pointer transition-colors"
                        >
                          Retry Connection
                        </button>
                      </div>
                    ) : (
                      <>
                        <p className="font-semibold text-slate-700">No transactions match the selected filters.</p>
                        <button
                          onClick={() => {
                            setDecisionFilter('all');
                            setRiskFilter('all');
                            setSearchQuery('');
                            setSortOrder('newest');
                          }}
                          className="mt-3 px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-lg text-xs font-semibold cursor-pointer transition-colors"
                        >
                          Clear Filters
                        </button>
                      </>
                    )}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};