import React, { useState } from 'react';
import { FileCheck2, CheckCircle2, ShieldOff, ShieldCheck, Clock, Layers } from 'lucide-react';
import { Transaction, approveReview, blockReview } from '../api/client';
import { Card, CardHeader } from '../components/ui/Card';
import { DecisionBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';
import { TransactionId } from '../components/ui/TransactionId';
import { formatUserId, formatMerchantName, getCategoryBadgeInfo, normalizeRiskScore } from '../utils/formatters';

interface ReviewQueuePageProps {
  reviews: Transaction[];
  onRefresh: () => void;
  onShowToast: (title: string, message?: string, type?: 'success' | 'error' | 'warning' | 'info') => void;
}

export const ReviewQueuePage: React.FC<ReviewQueuePageProps> = ({ reviews, onRefresh, onShowToast }) => {
  const [loadingId, setLoadingId] = useState<string | null>(null);

  const handleApprove = async (transaction_id: string) => {
    setLoadingId(transaction_id);
    try {
      await approveReview(transaction_id);
      onShowToast('Transaction Approved', `Transaction ${transaction_id} decision updated to ALLOW.`, 'success');
      onRefresh();
    } catch (err: any) {
      onShowToast('Approve Failed', err.message, 'error');
    } finally {
      setLoadingId(null);
    }
  };

  const handleBlock = async (transaction_id: string) => {
    setLoadingId(transaction_id);
    try {
      await blockReview(transaction_id);
      onShowToast('Transaction Blocked', `Transaction ${transaction_id} decision updated to BLOCK.`, 'warning');
      onRefresh();
    } catch (err: any) {
      onShowToast('Block Failed', err.message, 'error');
    } finally {
      setLoadingId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold font-sans text-[#172033] tracking-tight">Analyst Review Queue</h1>
        <p className="text-xs text-[#64748B] mt-0.5 font-sans">
          Manual inspection workstation for high-risk transactions requiring human analyst decisioning (decision == REVIEW)
        </p>
      </div>

      <Card className="border-[#E6EAF0] bg-white shadow-xs">
        <CardHeader
          title={`Pending Review Items (${reviews.length})`}
          subtitle="Inspect rule triggers and machine learning explanations before taking action"
          icon={<FileCheck2 className="h-4 w-4 text-[#EA580C]" />}
        />

        <div className="p-4 space-y-4">
          {reviews.map((r) => {
            const riskPct = normalizeRiskScore(r.risk_score);
            const mlPct = r.ml_fraud_score !== undefined ? normalizeRiskScore(r.ml_fraud_score) : null;
            const mName = formatMerchantName(r.merchant, r.merchant_category);
            const catInfo = getCategoryBadgeInfo(r.merchant_category);

            return (
              <div key={r.transaction_id} className="p-4 bg-[#F6F8FB] border border-[#E6EAF0] rounded-xl space-y-4 shadow-xs">
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 border-b border-[#E6EAF0] pb-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <TransactionId id={r.transaction_id} />
                      <DecisionBadge decision={r.decision} size="sm" />
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-sans bg-gray-100 text-gray-700">
                        <span>{catInfo.emoji}</span>
                        <span>{catInfo.label}</span>
                      </span>
                    </div>
                    <p className="text-xs text-[#64748B] mt-1 font-sans">
                      User: <strong className="text-[#172033] font-sans">{formatUserId(r.user_id)}</strong> | Amount:{' '}
                      <strong className="text-[#172033] font-sans tabular-nums font-medium">${r.amount.toFixed(2)}</strong> | Merchant:{' '}
                      <strong className="text-[#172033] font-sans">{mName}</strong>
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="success"
                      size="sm"
                      icon={<CheckCircle2 className="h-3.5 w-3.5" />}
                      isLoading={loadingId === r.transaction_id}
                      onClick={() => handleApprove(r.transaction_id)}
                    >
                      APPROVE
                    </Button>
                    <Button
                      variant="danger"
                      size="sm"
                      icon={<ShieldOff className="h-3.5 w-3.5" />}
                      isLoading={loadingId === r.transaction_id}
                      onClick={() => handleBlock(r.transaction_id)}
                    >
                      REJECT / BLOCK
                    </Button>
                  </div>
                </div>

                {/* Risk Details & Rationale */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                  <div className="bg-white border border-[#E6EAF0] p-3.5 rounded-xl space-y-2">
                    <p className="text-[10px] text-[#64748B] uppercase font-bold font-sans">Risk Evaluation Breakdown</p>
                    <div className="flex justify-between items-center">
                      <span className="text-[#64748B] font-sans">Combined Risk Score:</span>
                      <span className="text-[#EA580C] font-sans tabular-nums font-medium">{riskPct.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-[#64748B] font-sans">XGBoost ML Score:</span>
                      <span className="text-purple-600 font-sans tabular-nums font-medium">{mlPct !== null ? `${mlPct.toFixed(1)}%` : 'N/A'}</span>
                    </div>
                    <div className="pt-1 border-t border-gray-100">
                      <span className="text-[#64748B] font-sans block mb-1">Triggered Heuristics:</span>
                      <div className="flex flex-wrap gap-1">
                        {(r.rule_flags && r.rule_flags.length > 0 ? r.rule_flags : ['HIGH_AMOUNT']).map((flag) => (
                          <span key={flag} className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-amber-50 text-[#D97706] border border-amber-200">
                            ⚠ {flag}
                          </span>
                        ))}
                      </div>
                    </div>
                  </div>

                  <div className="bg-white border border-[#E6EAF0] p-3.5 rounded-xl">
                    <p className="text-[10px] text-[#64748B] uppercase font-bold font-sans mb-1.5">Explainability Rationale</p>
                    <p className="text-[#172033] leading-relaxed font-sans text-xs">
                      {r.human_readable_reason || 'Transaction amount exceeds user historical baseline with elevated risk score.'}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}

          {reviews.length === 0 && (
            <div className="py-12 px-4 text-center bg-[#F6F8FB] border border-dashed border-[#E6EAF0] rounded-2xl max-w-lg mx-auto my-6 space-y-3">
              <div className="h-12 w-12 rounded-full bg-emerald-50 text-[#16A34A] border border-emerald-200 flex items-center justify-center mx-auto">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <div>
                <h3 className="font-bold text-[#172033] font-sans text-sm">Review Queue Clear</h3>
                <p className="text-xs text-[#64748B] font-sans mt-1">
                  No transactions currently require human analyst review.
                </p>
              </div>
              <div className="pt-2 border-t border-[#E6EAF0] flex justify-around text-[11px] font-sans text-[#64748B]">
                <span><Clock className="h-3 w-3 inline mr-1" /> Last reviewed: 2 mins ago</span>
                <span><Layers className="h-3 w-3 inline mr-1" /> Queue status: 0 Pending</span>
              </div>
            </div>
          )}
        </div>
      </Card>
    </div>
  );
};