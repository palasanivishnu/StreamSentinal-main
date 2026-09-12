import React, { useState } from 'react';
import { Users, Search, Activity } from 'lucide-react';
import { Transaction, fetchUserTransactions } from '../api/client';
import { Card, CardHeader } from '../components/ui/Card';
import { DecisionBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { formatUserId, formatMerchantName, getCategoryBadgeInfo, normalizeRiskScore } from '../utils/formatters';

interface UsersPageProps {
  onSelectTransaction: (t: Transaction) => void;
  onShowToast: (title: string, message?: string, type?: 'success' | 'error' | 'warning' | 'info') => void;
}

export const UsersPage: React.FC<UsersPageProps> = ({ onSelectTransaction, onShowToast }) => {
  const [userId, setUserId] = useState('');
  const [loading, setLoading] = useState(false);
  const [userTxns, setUserTxns] = useState<Transaction[] | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!userId.trim()) return;

    setLoading(true);
    try {
      const res = await fetchUserTransactions(userId.trim());
      setUserTxns(res.transactions);
      if (res.transactions.length === 0) {
        onShowToast('User Search', `No transactions found for user ${userId}.`, 'info');
      }
    } catch (err: any) {
      onShowToast('Search Failed', err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold font-sans text-[#0F172A] tracking-tight">User Profile Risk Intelligence</h1>
        <p className="text-xs text-[#64748B] mt-0.5 font-sans">Inspect user transaction history, risk profiles, and behavioral scoring outputs</p>
      </div>

      <Card className="border-[#E2E8F0] bg-white shadow-xs">
        <CardHeader title="Search User Identifier" icon={<Users className="h-4 w-4 text-[#2563EB]" />} />
        <form onSubmit={handleSearch} className="flex gap-3">
          <input
            type="text"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            placeholder="Enter User ID (e.g. 4908846471916297)..."
            className="flex-1 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl px-4 py-2.5 text-xs text-[#0F172A] font-sans focus:outline-none focus:border-[#2563EB] focus:bg-white"
            required
          />
          <Button type="submit" variant="primary" isLoading={loading} icon={<Search className="h-4 w-4" />}>
            Search User Profile
          </Button>
        </form>
      </Card>

      {userTxns && (
        <Card className="border-[#E2E8F0] bg-white shadow-xs">
          <CardHeader
            title={`User Transactions History (${userTxns.length})`}
            subtitle={`Telemetry records for user ${formatUserId(userId)}`}
            icon={<Activity className="h-4 w-4 text-[#2563EB]" />}
          />
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#E2E8F0] bg-[#F8FAFC] text-[10px] font-sans uppercase text-[#64748B] font-bold tracking-wider">
                  <th className="py-3 px-3.5">Transaction ID</th>
                  <th className="py-3 px-3.5 text-right">Amount</th>
                  <th className="py-3 px-3.5">Merchant</th>
                  <th className="py-3 px-3.5">Category</th>
                  <th className="py-3 px-3.5 text-right">Risk Score</th>
                  <th className="py-3 px-3.5 text-right">ML Score</th>
                  <th className="py-3 px-3.5">Decision</th>
                  <th className="py-3 px-3.5 text-right">Processed At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans text-xs">
                {userTxns.map((t) => {
                  const mName = formatMerchantName(t.merchant, t.merchant_category);
                  const catInfo = getCategoryBadgeInfo(t.merchant_category);
                  const riskPct = normalizeRiskScore(t.risk_score);
                  const mlPct = t.ml_fraud_score !== undefined ? normalizeRiskScore(t.ml_fraud_score) : null;

                  return (
                    <tr
                      key={t.transaction_id}
                      onClick={() => onSelectTransaction(t)}
                      className="hover:bg-[#F8FAFC] cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-3.5 text-[#2563EB] font-mono font-semibold">{t.transaction_id.slice(0, 16)}...</td>
                      <td className="py-3 px-3.5 text-[#0F172A] font-mono tabular-nums font-bold text-right">${t.amount.toFixed(2)}</td>
                      <td className="py-3 px-3.5 text-[#0F172A] font-medium">{mName}</td>
                      <td className="py-3 px-3.5">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] bg-slate-100 text-slate-700">
                          <span>{catInfo.emoji}</span>
                          <span>{catInfo.label}</span>
                        </span>
                      </td>
                      <td className="py-3 px-3.5 text-[#0F172A] font-mono tabular-nums font-semibold text-right">{riskPct.toFixed(1)}%</td>
                      <td className="py-3 px-3.5 text-purple-600 font-mono tabular-nums font-semibold text-right">
                        {mlPct !== null ? `${mlPct.toFixed(1)}%` : 'N/A'}
                      </td>
                      <td className="py-3 px-3.5"><DecisionBadge decision={t.decision} size="sm" /></td>
                      <td className="py-3 px-3.5 text-[#64748B] font-mono tabular-nums text-right">{t.processed_at || t.saved_at || 'N/A'}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  );
};