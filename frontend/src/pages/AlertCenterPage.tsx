import React, { useState } from 'react';
import { AlertTriangle, CheckCircle, ShieldAlert } from 'lucide-react';
import { Alert, Transaction, acknowledgeAlert } from '../api/client';
import { Card, CardHeader } from '../components/ui/Card';
import { SeverityBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { TransactionId } from '../components/ui/TransactionId';
import { formatUserId, normalizeRiskScore } from '../utils/formatters';

interface AlertCenterPageProps {
  alerts: Alert[];
  onRefresh: () => void;
  onShowToast: (title: string, message?: string, type?: 'success' | 'error' | 'warning' | 'info') => void;
  onSelectTransaction?: (t: Transaction) => void;
}

export const AlertCenterPage: React.FC<AlertCenterPageProps> = ({ alerts, onRefresh, onShowToast }) => {
  const [severityFilter, setSeverityFilter] = useState('all');
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const filtered = alerts.filter((a) => {
    if (severityFilter !== 'all' && a.severity.toUpperCase() !== severityFilter.toUpperCase()) return false;
    return true;
  });

  const handleAcknowledge = async (alert_id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setLoadingId(alert_id);
    try {
      await acknowledgeAlert(alert_id);
      onShowToast('Alert Acknowledged', `Alert ${alert_id} marked as resolved.`, 'success');
      onRefresh();
    } catch (err: any) {
      onShowToast('Acknowledge Failed', err.message, 'error');
    } finally {
      setLoadingId(null);
    }
  };

  const criticalCount = alerts.filter((a) => a.severity === 'CRITICAL').length;
  const highCount = alerts.filter((a) => a.severity === 'HIGH').length;
  const warningCount = alerts.filter((a) => a.severity === 'WARNING' || a.severity === 'MEDIUM').length;

  const renderReasonBadges = (reason: string) => {
    if (!reason) {
      return (
        <span className="px-2 py-0.5 rounded bg-gray-100 text-gray-700 text-[11px] font-mono">
          ELEVATED_RISK_SCORE
        </span>
      );
    }

    const rules = ['HIGH_AMOUNT', 'HIGH_VELOCITY', 'IMPOSSIBLE_TRAVEL', 'NEW_MERCHANT_CATEGORY'];
    const foundRules = rules.filter((r) => reason.includes(r));

    if (foundRules.length > 0) {
      return (
        <div className="space-y-1">
          <div className="flex flex-wrap gap-1">
            {foundRules.map((r) => (
              <span key={r} className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-rose-50 text-rose-700 border border-rose-200">
                ⚠ {r}
              </span>
            ))}
          </div>
          <p className="text-[11px] text-gray-600 font-sans leading-snug">{reason}</p>
        </div>
      );
    }

    return <p className="text-xs text-gray-800 font-sans leading-snug">{reason}</p>;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold font-sans text-[#172033] tracking-tight">Alert Center</h1>
        <p className="text-xs text-[#64748B] mt-0.5 font-sans">Automated security alert management for elevated risk transaction events</p>
      </div>

      {/* Severity Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="border-rose-200 bg-rose-50/50 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-rose-700 font-sans">Critical Severity</span>
            <ShieldAlert className="h-5 w-5 text-rose-600" />
          </div>
          <p className="text-2xl font-semibold text-rose-900 mt-2 font-sans tabular-nums">{criticalCount}</p>
        </Card>
        <Card className="border-orange-200 bg-orange-50/50 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-orange-700 font-sans">High Severity</span>
            <AlertTriangle className="h-5 w-5 text-orange-600" />
          </div>
          <p className="text-2xl font-semibold text-orange-900 mt-2 font-sans tabular-nums">{highCount}</p>
        </Card>
        <Card className="border-amber-200 bg-amber-50/50 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase text-amber-700 font-sans">Warning / Medium</span>
            <AlertTriangle className="h-5 w-5 text-amber-600" />
          </div>
          <p className="text-2xl font-semibold text-amber-900 mt-2 font-sans tabular-nums">{warningCount}</p>
        </Card>
      </div>

      {/* Alert Feed Table */}
      <Card className="border-[#E6EAF0] bg-white shadow-xs">
        <CardHeader
          title={`Alert Feed (${filtered.length})`}
          subtitle="Persisted MongoDB security alert records"
          icon={<AlertTriangle className="h-4 w-4 text-[#D97706]" />}
          action={
            <div className="flex items-center gap-2">
              {['all', 'CRITICAL', 'HIGH', 'WARNING'].map((s) => (
                <button
                  key={s}
                  onClick={() => setSeverityFilter(s)}
                  className={`px-2.5 py-1 text-xs font-sans rounded-lg border transition-all cursor-pointer ${
                    severityFilter === s
                      ? 'bg-amber-600 text-white border-amber-600 font-semibold shadow-xs'
                      : 'bg-gray-50 text-gray-600 border-gray-200 hover:bg-gray-100'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          }
        />

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E6EAF0] bg-[#F6F8FB] text-[10px] font-sans uppercase text-[#64748B] font-semibold">
                <th className="py-3 px-4">Alert ID</th>
                <th className="py-3 px-4">Transaction ID</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Severity</th>
                <th className="py-3 px-4">Reason / Rule Trigger</th>
                <th className="py-3 px-4">Status</th>
                <th className="py-3 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 text-xs font-sans">
              {filtered.map((a) => (
                <tr key={a.alert_id} className="hover:bg-gray-50/80 transition-colors">
                  <td className="py-3 px-4 font-medium text-[11px] text-rose-600 font-mono" style={{ fontFamily: "'JetBrains Mono', monospace" }}>{a.alert_id}</td>
                  <td className="py-3 px-4"><TransactionId id={a.transaction_id} /></td>
                  <td className="py-3 px-4 text-[#172033] font-sans font-medium">{formatUserId(a.user_id)}</td>
                  <td className="py-3 px-4"><SeverityBadge severity={a.severity} /></td>
                  <td className="py-3 px-4 max-w-sm">{renderReasonBadges(a.reason)}</td>
                  <td className="py-3 px-4">
                    {a.acknowledged ? (
                      <span className="text-[#16A34A] font-semibold flex items-center gap-1 font-sans">
                        <CheckCircle className="h-3.5 w-3.5" /> Resolved
                      </span>
                    ) : (
                      <span className="text-[#D97706] font-semibold font-sans">Active</span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    {!a.acknowledged && (
                      <Button
                        variant="secondary"
                        size="sm"
                        isLoading={loadingId === a.alert_id}
                        onClick={(e) => handleAcknowledge(a.alert_id, e)}
                      >
                        Acknowledge
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-8 text-center text-[#64748B] text-xs font-sans">
                    No alerts match the selected severity filter.
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