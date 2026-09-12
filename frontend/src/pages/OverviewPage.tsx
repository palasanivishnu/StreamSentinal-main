import React from 'react';
import {
  Activity,
  CheckCircle2,
  KeyRound,
  FileCheck2,
  XCircle,
  ArrowUpRight,
  TrendingUp,
  Play,
  AlertTriangle,
} from 'lucide-react';
import { AnalyticsSummary, Transaction, Alert, ServicesHealthResponse } from '../api/client';
import { Card, CardHeader } from '../components/ui/Card';
import { DecisionBadge, SeverityBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { TransactionId } from '../components/ui/TransactionId';
import { formatUserId, formatMerchantName, getCategoryBadgeInfo, normalizeRiskScore } from '../utils/formatters';

interface OverviewPageProps {
  summary: AnalyticsSummary | null;
  transactions: Transaction[];
  alerts: Alert[];
  health: ServicesHealthResponse | null;
  onSelectTransaction: (t: Transaction) => void;
  onNavigate: (page: string) => void;
  onRunDemo: () => void;
}

export const OverviewPage: React.FC<OverviewPageProps> = ({
  summary,
  transactions,
  alerts,
  onSelectTransaction,
  onNavigate,
  onRunDemo,
}) => {
  const totalCount = summary?.total_transactions ?? 0;
  const allowCount = summary?.allow_count ?? 0;
  const otpCount = summary?.otp_count ?? 0;
  const reviewCount = summary?.review_count ?? 0;
  const blockCount = summary?.block_count ?? 0;
  const avgRisk = normalizeRiskScore(summary?.avg_risk_score ?? 0);

  const kpis = [
    {
      title: 'TOTAL PROCESSED',
      value: totalCount.toLocaleString(),
      icon: <Activity className="h-4 w-4 text-[#2563EB]" />,
      iconBg: 'bg-blue-50 border-blue-100',
      sub: 'Real-time telemetry stream',
    },
    {
      title: 'ALLOWED',
      value: allowCount.toLocaleString(),
      icon: <CheckCircle2 className="h-4 w-4 text-[#16A34A]" />,
      iconBg: 'bg-emerald-50 border-emerald-100',
      sub: 'Legitimate activity',
    },
    {
      title: 'OTP CHALLENGES',
      value: otpCount.toLocaleString(),
      icon: <KeyRound className="h-4 w-4 text-[#D97706]" />,
      iconBg: 'bg-amber-50 border-amber-100',
      sub: 'Step-up authentication',
    },
    {
      title: 'IN REVIEW',
      value: reviewCount.toLocaleString(),
      icon: <FileCheck2 className="h-4 w-4 text-[#EA580C]" />,
      iconBg: 'bg-orange-50 border-orange-100',
      sub: 'Pending analyst action',
    },
    {
      title: 'BLOCKED FRAUD',
      value: blockCount.toLocaleString(),
      icon: <XCircle className="h-4 w-4 text-[#DC2626]" />,
      iconBg: 'bg-rose-50 border-rose-100',
      sub: 'High-risk blocked',
    },
    {
      title: 'AVERAGE RISK',
      value: `${avgRisk.toFixed(1)}%`,
      icon: <TrendingUp className="h-4 w-4 text-purple-600" />,
      iconBg: 'bg-purple-50 border-purple-100',
      sub: 'Combined risk score',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold font-sans text-[#0F172A] tracking-tight">Command Center</h1>
          <p className="text-xs text-[#64748B] mt-0.5 font-sans">
            Real-Time Financial Transaction Fraud Detection & Operational Telemetry
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="primary" icon={<Play className="h-3.5 w-3.5" />} onClick={onRunDemo}>
            Stream Demo Transactions (10 Txns)
          </Button>
        </div>
      </div>

      {/* Unified Standardized KPI Cards Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3.5">
        {kpis.map((kpi, idx) => (
          <Card key={idx} className="p-4 flex flex-col justify-between border-[#E2E8F0] bg-white shadow-xs rounded-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-sans font-bold uppercase tracking-wider text-[#64748B]">{kpi.title}</span>
              <div className={`p-1.5 rounded-lg border ${kpi.iconBg}`}>{kpi.icon}</div>
            </div>
            <div>
              <p className="text-2xl font-semibold font-sans tabular-nums text-[#0F172A]">{kpi.value}</p>
              <p className="text-[10px] text-[#64748B] mt-0.5 font-sans">{kpi.sub}</p>
            </div>
          </Card>
        ))}
      </div>

      {/* Main Stream & Alerts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Transaction Stream (2 Cols) */}
        <Card className="lg:col-span-2 border-[#E2E8F0] bg-white shadow-xs">
          <CardHeader
            title="Live Transaction Stream"
            subtitle="Scored real-time telemetry feed with merchant classification"
            icon={<Activity className="h-4 w-4 text-[#2563EB]" />}
            action={
              <Button variant="ghost" size="sm" onClick={() => onNavigate('transactions')}>
                View All <ArrowUpRight className="h-3 w-3 ml-1" />
              </Button>
            }
          />
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="border-b border-[#E2E8F0] bg-[#F8FAFC] text-[10px] font-sans uppercase text-[#64748B] font-bold tracking-wider">
                  <th className="py-3 px-3.5">Transaction ID</th>
                  <th className="py-3 px-3.5">User</th>
                  <th className="py-3 px-3.5 text-right">Amount</th>
                  <th className="py-3 px-3.5">Merchant</th>
                  <th className="py-3 px-3.5">Category</th>
                  <th className="py-3 px-3.5 text-right">Risk Score</th>
                  <th className="py-3 px-3.5">Decision</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-sans text-xs">
                {transactions.slice(0, 10).map((t) => {
                  const mName = formatMerchantName(t.merchant, t.merchant_category);
                  const catInfo = getCategoryBadgeInfo(t.merchant_category);
                  const riskPct = normalizeRiskScore(t.risk_score);

                  return (
                    <tr
                      key={t.transaction_id}
                      onClick={() => onSelectTransaction(t)}
                      className="hover:bg-[#F8FAFC] cursor-pointer transition-colors"
                    >
                      <td className="py-3 px-3.5"><TransactionId id={t.transaction_id} /></td>
                      <td className="py-3 px-3.5 text-[#0F172A] font-sans font-medium">{formatUserId(t.user_id)}</td>
                      <td className="py-3 px-3.5 text-[#0F172A] font-sans tabular-nums font-medium text-right">${t.amount.toFixed(2)}</td>
                      <td className="py-3 px-3.5 text-[#0F172A] font-sans font-medium">{mName}</td>
                      <td className="py-3 px-3.5">
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-sans bg-slate-100 text-slate-700">
                          <span>{catInfo.emoji}</span>
                          <span>{catInfo.label}</span>
                        </span>
                      </td>
                      <td className="py-3 px-3.5 text-[#0F172A] font-sans tabular-nums font-medium text-right">{riskPct.toFixed(1)}%</td>
                      <td className="py-3 px-3.5"><DecisionBadge decision={t.decision} size="sm" /></td>
                    </tr>
                  );
                })}

                {transactions.length === 0 && (
                  <tr>
                    <td colSpan={7} className="py-8 text-center text-[#64748B] font-sans text-xs">
                      No live transactions ingested yet. Click "Stream Demo Transactions" to populate stream.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </Card>

        {/* Security Alert Feed (1 Col) */}
        <div className="space-y-6">
          <Card className="border-[#E2E8F0] bg-white shadow-xs">
            <CardHeader
              title="Recent Fraud Alerts"
              subtitle="Automated rule & ML triggers"
              icon={<AlertTriangle className="h-4 w-4 text-[#D97706]" />}
              action={
                <Button variant="ghost" size="sm" onClick={() => onNavigate('alerts')}>
                  Alerts <ArrowUpRight className="h-3 w-3 ml-1" />
                </Button>
              }
            />
            <div className="space-y-2.5">
              {alerts.slice(0, 5).map((a) => (
                <div
                  key={a.alert_id}
                  onClick={() => {
                    const txn = transactions.find((t) => t.transaction_id === a.transaction_id);
                    if (txn) onSelectTransaction(txn);
                  }}
                  className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl space-y-1.5 text-xs cursor-pointer hover:border-slate-300 transition-all"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-mono font-medium text-[11px] text-[#0F172A]" style={{ fontFamily: "'JetBrains Mono', monospace" }}>{a.alert_id}</span>
                    <SeverityBadge severity={a.severity} />
                  </div>
                  <p className="text-[#64748B] text-[11px] font-sans leading-snug">{a.reason}</p>
                  <div className="flex justify-between items-center text-[10px] font-sans text-[#64748B] pt-1">
                    <span className="flex items-center gap-1">Txn: <TransactionId id={a.transaction_id} /></span>
                    <span className="font-medium text-amber-700 tabular-nums">Risk: {normalizeRiskScore(a.risk_score).toFixed(0)}%</span>
                  </div>
                </div>
              ))}
              {alerts.length === 0 && (
                <p className="py-6 text-center text-[#64748B] font-sans text-xs">No active security alerts.</p>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};