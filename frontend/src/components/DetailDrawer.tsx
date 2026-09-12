import React, { useState, useEffect, useRef } from 'react';
import { X, ShieldAlert, Cpu, AlertTriangle, CheckCircle2, Info, KeyRound, Sparkles, RefreshCw, XCircle } from 'lucide-react';
import { Transaction, fetchPendingOtps, verifyOTP, PendingOTP } from '../api/client';
import { DecisionBadge } from './ui/Badge';
import { Button } from './ui/Button';
import { TransactionId } from './ui/TransactionId';
import { formatUserId, formatMerchantName, normalizeRiskScore } from '../utils/formatters';

interface DetailDrawerProps {
  transaction: Transaction | null;
  onClose: () => void;
  onRefresh?: () => void;
}

export const DetailDrawer: React.FC<DetailDrawerProps> = ({ transaction, onClose, onRefresh }) => {
  if (!transaction) return null;

  const [currentDecision, setCurrentDecision] = useState<string>(transaction.decision);
  const [pendingOtp, setPendingOtp] = useState<PendingOTP | null>(null);
  const [loadingOtp, setLoadingOtp] = useState<boolean>(false);
  const [digits, setDigits] = useState<string[]>(['', '', '', '', '', '']);
  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [verifyResult, setVerifyResult] = useState<{ success: boolean; message: string } | null>(null);

  const inputRefs = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    setCurrentDecision(transaction.decision);
    setDigits(['', '', '', '', '', '']);
    setVerifyResult(null);

    const loadOtpRecord = async () => {
      setLoadingOtp(true);
      try {
        const res = await fetchPendingOtps(50);
        if (res && res.otps) {
          const match = res.otps.find(
            (o) => o.transaction_id === transaction.transaction_id || o.user_id === transaction.user_id
          );
          setPendingOtp(match || null);
        }
      } catch (e) {
        console.error('Failed to load pending OTP:', e);
      } finally {
        setLoadingOtp(false);
      }
    };

    loadOtpRecord();
  }, [transaction.transaction_id, transaction.decision, transaction.user_id]);

  const handleDigitChange = (idx: number, val: string) => {
    const cleanVal = val.replace(/\D/g, '');
    if (!cleanVal && val !== '') return;

    const nextDigits = [...digits];
    nextDigits[idx] = cleanVal ? cleanVal.slice(-1) : '';
    setDigits(nextDigits);

    if (cleanVal && idx < 5) {
      inputRefs.current[idx + 1]?.focus();
    }
  };

  const handleKeyDown = (idx: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !digits[idx] && idx > 0) {
      inputRefs.current[idx - 1]?.focus();
    }
  };

  const handlePaste = (e: React.ClipboardEvent<HTMLDivElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (!pasted) return;

    const nextDigits = ['', '', '', '', '', ''];
    for (let i = 0; i < pasted.length; i++) {
      nextDigits[i] = pasted[i];
    }
    setDigits(nextDigits);

    const targetIdx = Math.min(pasted.length, 5);
    inputRefs.current[targetIdx]?.focus();
  };

  const handleAutofill = (code: string) => {
    const cleanCode = code.replace(/\D/g, '').slice(0, 6);
    const nextDigits = ['', '', '', '', '', ''];
    for (let i = 0; i < cleanCode.length; i++) {
      nextDigits[i] = cleanCode[i];
    }
    setDigits(nextDigits);
    inputRefs.current[5]?.focus();
  };

  const handleVerifySubmit = async () => {
    const code = digits.join('');
    if (code.length < 6) return;

    setIsVerifying(true);
    setVerifyResult(null);

    try {
      const res = await verifyOTP(transaction.user_id, code, transaction.transaction_id);
      if (res.success) {
        setVerifyResult({ success: true, message: '✓ OTP verified successfully! Transaction approved (ALLOW).' });
        setCurrentDecision('allow');
        onRefresh?.();
      } else {
        setVerifyResult({ success: false, message: res.message || '✕ Invalid OTP code. Transaction blocked (BLOCK).' });
        setCurrentDecision('block');
        onRefresh?.();
      }
    } catch (err: any) {
      setVerifyResult({ success: false, message: err.message || 'OTP verification failed' });
      setCurrentDecision('block');
      onRefresh?.();
    } finally {
      setIsVerifying(false);
    }
  };

  const rulesList = [
    { key: 'HIGH_AMOUNT', label: 'HIGH_AMOUNT', desc: 'Transaction amount > $1,000 or 5x user average' },
    { key: 'HIGH_VELOCITY', label: 'HIGH_VELOCITY', desc: 'Velocity > 5 transactions in 5 minutes' },
    { key: 'IMPOSSIBLE_TRAVEL', label: 'IMPOSSIBLE_TRAVEL', desc: 'Physical displacement > 500 km in short window' },
    { key: 'NEW_MERCHANT_CATEGORY', label: 'NEW_MERCHANT_CATEGORY', desc: 'Transaction category never previously used' },
  ];

  const triggeredFlags = transaction.rule_flags || [];

  const combinedRiskPct = Math.round(normalizeRiskScore(transaction.risk_score));
  const mlRiskPct =
    transaction.ml_fraud_score !== undefined
      ? Math.round(normalizeRiskScore(transaction.ml_fraud_score))
      : Math.round(combinedRiskPct * 0.6);
  const ruleRiskPct = Math.min(100, Math.max(0, combinedRiskPct - Math.round(mlRiskPct * 0.5)));
  const mName = formatMerchantName(transaction.merchant, transaction.merchant_category);

  return (
    <div className="fixed inset-0 z-50 overflow-hidden bg-slate-900/40 backdrop-blur-xs flex justify-end animate-in fade-in duration-200">
      <div className="w-full max-w-2xl bg-white border-l border-[#E2E8F0] h-full flex flex-col shadow-2xl overflow-y-auto font-sans">
        {/* Header */}
        <div className="p-5 border-b border-[#E2E8F0] flex items-center justify-between bg-[#F8FAFC] sticky top-0 z-10">
          <div>
            <div className="flex items-center gap-2">
              <ShieldAlert className="h-5 w-5 text-[#2563EB]" />
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#0F172A] font-sans">Transaction Intelligence</h2>
            </div>
            <div className="mt-1">
              <TransactionId id={transaction.transaction_id} showFull />
            </div>
          </div>
          <div className="flex items-center gap-3">
            <DecisionBadge decision={currentDecision} size="lg" />
            <button onClick={onClose} className="p-1 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-200 cursor-pointer">
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6 flex-1 text-xs">
          {/* Key Detection Metrics */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3 text-center">
              <p className="text-[10px] text-[#64748B] uppercase font-bold font-sans">Amount</p>
              <p className="text-base font-bold text-[#0F172A] mt-1 font-sans tabular-nums">${transaction.amount.toFixed(2)}</p>
            </div>
            <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3 text-center">
              <p className="text-[10px] text-[#64748B] uppercase font-bold font-sans">Overall Risk</p>
              <p className="text-base font-bold text-[#2563EB] mt-1 font-sans tabular-nums">{combinedRiskPct}%</p>
            </div>
            <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3 text-center">
              <p className="text-[10px] text-[#64748B] uppercase font-bold font-sans">ML Fraud Score</p>
              <p className="text-base font-bold text-purple-600 mt-1 font-sans tabular-nums">{mlRiskPct}%</p>
            </div>
            <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-3 text-center">
              <p className="text-[10px] text-[#64748B] uppercase font-bold font-sans">Latency</p>
              <p className="text-base font-bold text-[#0F172A] mt-1 font-sans tabular-nums">
                {transaction.latency_ms ? `${transaction.latency_ms.toFixed(1)} ms` : 'N/A'}
              </p>
            </div>
          </div>

          {/* 2FA OTP Workstation Panel (shown when transaction requires OTP or is pending OTP) */}
          {(currentDecision === 'otp' || pendingOtp) && (
            <div className="bg-amber-50/80 border border-amber-200 rounded-xl p-4 space-y-3.5 shadow-xs">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-amber-900 font-bold text-xs font-sans">
                  <KeyRound className="h-4 w-4 text-amber-600 shrink-0" />
                  <span>2FA OTP VERIFICATION WORKSTATION</span>
                </div>
                <span className="text-[10px] text-amber-700 bg-amber-200/70 font-mono px-2 py-0.5 rounded font-bold uppercase">
                  Real Backend Challenge
                </span>
              </div>

              {pendingOtp?.otp_code ? (
                <div className="bg-white border border-amber-200 rounded-lg p-3 flex items-center justify-between">
                  <div>
                    <p className="text-[10px] text-slate-500 uppercase font-bold font-sans">Backend Demo OTP Code</p>
                    <p className="text-2xl font-black text-amber-700 tracking-widest font-mono mt-0.5">
                      {pendingOtp.otp_code}
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleAutofill(pendingOtp.otp_code!)}
                    className="px-3 py-1.5 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-bold transition flex items-center gap-1.5 cursor-pointer shadow-xs font-sans"
                  >
                    <Sparkles className="h-3.5 w-3.5" />
                    Autofill Demo OTP
                  </button>
                </div>
              ) : (
                <div className="text-[11px] text-amber-800 bg-amber-100/50 p-2.5 rounded-lg border border-amber-200 font-sans">
                  {loadingOtp ? 'Fetching real backend OTP challenge...' : 'Enter 6-digit OTP assigned to this user/transaction.'}
                </div>
              )}

              {/* 6-Digit Passcode Input */}
              {currentDecision === 'otp' && (
                <div className="space-y-2 pt-1">
                  <label className="text-[11px] font-bold text-slate-700 font-sans block">
                    Enter 6-Digit Verification Code:
                  </label>
                  <div className="flex items-center gap-2 justify-center" onPaste={handlePaste}>
                    {digits.map((digit, idx) => (
                      <input
                        key={idx}
                        ref={(el) => { inputRefs.current[idx] = el; }}
                        type="text"
                        inputMode="numeric"
                        maxLength={1}
                        value={digit}
                        onChange={(e) => handleDigitChange(idx, e.target.value)}
                        onKeyDown={(e) => handleKeyDown(idx, e)}
                        className="w-11 h-12 text-center text-xl font-bold font-mono border-2 border-amber-300 focus:border-blue-600 focus:bg-blue-50/50 rounded-lg text-slate-900 shadow-xs focus:outline-none transition-all"
                      />
                    ))}
                  </div>

                  <button
                    type="button"
                    disabled={isVerifying || digits.join('').length < 6}
                    onClick={handleVerifySubmit}
                    className="w-full mt-2 py-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition shadow-xs flex items-center justify-center gap-2 cursor-pointer font-sans"
                  >
                    {isVerifying ? (
                      <>
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        Verifying 2FA Challenge...
                      </>
                    ) : (
                      <>
                        <KeyRound className="h-4 w-4" />
                        VERIFY OTP PASSCODE
                      </>
                    )}
                  </button>
                </div>
              )}

              {/* Result Banner */}
              {verifyResult && (
                <div
                  className={`p-3 rounded-lg border text-xs font-semibold flex items-center gap-2 font-sans ${
                    verifyResult.success
                      ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                      : 'bg-rose-50 border-rose-200 text-rose-800'
                  }`}
                >
                  {verifyResult.success ? (
                    <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                  ) : (
                    <XCircle className="h-4 w-4 text-rose-600 shrink-0" />
                  )}
                  <span>{verifyResult.message}</span>
                </div>
              )}
            </div>
          )}

          {/* Explainable AI Reason */}
          <div className="bg-blue-50/60 border border-blue-200 rounded-xl p-4 space-y-2">
            <div className="flex items-center gap-2 text-[#2563EB] font-bold">
              <Info className="h-4 w-4 shrink-0" />
              <span className="uppercase text-xs font-sans">Why did the system make this decision?</span>
            </div>
            <p className="text-xs text-[#0F172A] leading-relaxed font-sans pl-6">
              {transaction.human_readable_reason || 'Transaction scored automatically by hybrid ML model and heuristic rule engine.'}
            </p>
          </div>

          {/* Risk Contribution Visualization */}
          <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-4 space-y-3">
            <h3 className="text-xs font-bold uppercase text-[#0F172A] font-sans">📊 Risk Contribution Breakdown</h3>

            <div className="space-y-2 text-xs">
              <div>
                <div className="flex justify-between text-[11px] text-[#64748B] mb-1 font-sans">
                  <span>Rule-Based Risk</span>
                  <span className="font-bold text-[#D97706] font-sans tabular-nums">{ruleRiskPct}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div className="bg-[#D97706] h-full rounded-full transition-all" style={{ width: `${ruleRiskPct}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-[#64748B] mb-1 font-sans">
                  <span>Machine Learning Risk</span>
                  <span className="font-bold text-purple-700 font-sans tabular-nums">{mlRiskPct}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div className="bg-purple-600 h-full rounded-full transition-all" style={{ width: `${mlRiskPct}%` }} />
                </div>
              </div>

              <div>
                <div className="flex justify-between text-[11px] text-[#64748B] mb-1 font-sans">
                  <span>Combined Risk Index</span>
                  <span className="font-bold text-[#2563EB] font-sans tabular-nums">{combinedRiskPct}%</span>
                </div>
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div className="bg-[#2563EB] h-full rounded-full transition-all" style={{ width: `${combinedRiskPct}%` }} />
                </div>
              </div>
            </div>
          </div>

          {/* Triggered Rules Breakdown */}
          <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-4">
            <div className="flex items-center gap-2 mb-3">
              <Cpu className="h-4 w-4 text-purple-600" />
              <h3 className="text-xs font-bold uppercase text-[#0F172A] font-sans">🚨 Triggered Rules Evaluation</h3>
            </div>

            <div className="space-y-2">
              {rulesList.map((r) => {
                const isTriggered = triggeredFlags.includes(r.key);
                return (
                  <div
                    key={r.key}
                    className={`flex items-center justify-between p-2.5 rounded-lg border text-xs ${
                      isTriggered ? 'bg-amber-50 border-amber-200 text-amber-900' : 'bg-white border-[#E2E8F0] text-[#64748B]'
                    }`}
                  >
                    <div className="flex items-center gap-2.5">
                      {isTriggered ? (
                        <AlertTriangle className="h-4 w-4 text-[#D97706] shrink-0" />
                      ) : (
                        <CheckCircle2 className="h-4 w-4 text-[#16A34A] shrink-0" />
                      )}
                      <div>
                        <p className="font-bold text-[#0F172A] font-mono">{r.label}</p>
                        <p className="text-[10px] text-[#64748B] font-sans">{r.desc}</p>
                      </div>
                    </div>
                    <span
                      className={`text-[10px] px-2 py-0.5 rounded font-bold font-sans ${
                        isTriggered ? 'bg-amber-200 text-amber-900' : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {isTriggered ? 'TRIGGERED' : 'CLEAR'}
                    </span>
                  </div>
                );
              })}
              {triggeredFlags.length === 0 && (
                <p className="text-[#64748B] text-center py-2 text-[11px] font-sans">No fraud rules triggered for this transaction.</p>
              )}
            </div>
          </div>

          {/* Context Information Table */}
          <div className="bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl p-4 space-y-2.5 text-xs font-sans">
            <div className="flex justify-between border-b border-[#E2E8F0] pb-2">
              <span className="text-[#64748B]">User Identifier:</span>
              <span className="text-[#0F172A] font-semibold font-sans">{formatUserId(transaction.user_id)}</span>
            </div>
            <div className="flex justify-between border-b border-[#E2E8F0] pb-2">
              <span className="text-[#64748B]">Merchant:</span>
              <span className="text-[#0F172A] font-medium font-sans">{mName}</span>
            </div>
            <div className="flex justify-between border-b border-[#E2E8F0] pb-2">
              <span className="text-[#64748B]">Detection Latency:</span>
              <span className="text-[#0F172A] font-sans tabular-nums">
                {transaction.latency_ms ? `${transaction.latency_ms.toFixed(1)} ms` : 'N/A'}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-[#64748B]">Timestamp:</span>
              <span className="text-[#0F172A] font-sans tabular-nums">{transaction.processed_at || transaction.saved_at || 'N/A'}</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-[#E2E8F0] bg-[#F8FAFC] flex justify-end">
          <Button variant="secondary" onClick={onClose}>Close Intelligence Drawer</Button>
        </div>
      </div>
    </div>
  );
};