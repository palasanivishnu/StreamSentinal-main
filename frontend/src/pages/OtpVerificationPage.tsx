import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  KeyRound,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  RefreshCw,
  SlidersHorizontal,
  Check,
  XCircle,
  AlertTriangle,
  Lock,
  Sparkles,
  UserCheck
} from 'lucide-react';
import { verifyOTP, getApiBaseUrl, fetchHealth } from '../api/client';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { TransactionId } from '../components/ui/TransactionId';
import { formatUserId, formatMerchantName, normalizeRiskScore } from '../utils/formatters';

interface OtpItem {
  transaction_id: string;
  user_id: string;
  amount: number;
  merchant?: string;
  merchant_category?: string;
  risk_score: number;
  decision: string;
  otp_code: string;
  otp_status: string;
  expires_at?: string;
  time_remaining_sec: number;
  human_readable_reason?: string;
}

interface OtpVerificationPageProps {
  onRefresh: () => void;
  onShowToast: (title: string, message?: string, type?: 'success' | 'error' | 'warning' | 'info') => void;
}

export const OtpVerificationPage: React.FC<OtpVerificationPageProps> = ({ onRefresh, onShowToast }) => {
  const [pendingOtps, setPendingOtps] = useState<OtpItem[]>([]);
  const [selectedTxnId, setSelectedTxnId] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<'newest' | 'risk'>('newest');
  const [isLiveConnected, setIsLiveConnected] = useState<boolean>(false);
  const [otpDigits, setOtpDigits] = useState<string[]>(['', '', '', '', '', '']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{ success: boolean; message: string; expired?: boolean } | null>(null);
  const [manualUserId, setManualUserId] = useState('');
  const [manualTxnId, setManualTxnId] = useState('');
  const [showManual, setShowManual] = useState(false);

  const inputRefs = [
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
    useRef<HTMLInputElement>(null),
  ];

  // Fetch pending OTPs from actual backend
  const fetchPendingOtps = async () => {
    try {
      const res = await fetch(`${getApiBaseUrl()}/otp/pending?limit=50`);
      if (res.ok) {
        const data = await res.json();
        const otpsList: OtpItem[] = data.otps || [];
        setPendingOtps(otpsList);
        setIsLiveConnected(true);

        // Auto-select first item if nothing selected or current selection no longer exists
        if (otpsList.length > 0) {
          if (!selectedTxnId || !otpsList.some(item => item.transaction_id === selectedTxnId)) {
            setSelectedTxnId(otpsList[0].transaction_id);
          }
        } else {
          setSelectedTxnId(null);
        }
      } else {
        setIsLiveConnected(false);
      }
    } catch (e) {
      console.error('Error fetching pending OTPs:', e);
      setIsLiveConnected(false);
    }
  };

  // Check health for real status indicator
  const checkConnection = async () => {
    try {
      await fetchHealth();
      setIsLiveConnected(true);
    } catch {
      setIsLiveConnected(false);
    }
  };

  // Poll pending list every 2 seconds
  useEffect(() => {
    checkConnection();
    fetchPendingOtps();
    const interval = setInterval(fetchPendingOtps, 2000);
    return () => clearInterval(interval);
  }, []);

  // Tick down timer every second for accurate countdown display
  const [tick, setTick] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  // Deduplicate and sort pending OTPs
  const sortedOtps = useMemo(() => {
    // Deduplicate by transaction_id
    const map = new Map<string, OtpItem>();
    for (const item of pendingOtps) {
      if (item.transaction_id && !map.has(item.transaction_id)) {
        map.set(item.transaction_id, item);
      }
    }
    const unique = Array.from(map.values());

    if (sortBy === 'risk') {
      return unique.sort((a, b) => b.risk_score - a.risk_score);
    }
    return unique; // Default: newest first as returned by backend
  }, [pendingOtps, sortBy]);

  // Selected item object
  const selectedItem = useMemo(() => {
    if (!selectedTxnId) return sortedOtps[0] || null;
    return sortedOtps.find(item => item.transaction_id === selectedTxnId) || sortedOtps[0] || null;
  }, [sortedOtps, selectedTxnId]);

  // Format remaining time for an item
  const getRemainingTimeString = (item: OtpItem) => {
    if (item.expires_at) {
      const expTime = new Date(item.expires_at).getTime();
      const now = Date.now();
      const diffSec = Math.max(0, Math.floor((expTime - now) / 1000));
      if (diffSec <= 0) return 'EXPIRED';
      const m = Math.floor(diffSec / 60);
      const s = diffSec % 60;
      return `${m}m ${s < 10 ? '0' : ''}${s}s`;
    }
    const sec = item.time_remaining_sec ?? 300;
    if (sec <= 0) return 'EXPIRED';
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m}m ${s < 10 ? '0' : ''}${s}s`;
  };

  // Handle transaction row selection
  const handleSelectTransaction = (item: OtpItem) => {
    setSelectedTxnId(item.transaction_id);
    setResult(null);
    // Autofill demo OTP code into digits if available
    if (item.otp_code) {
      const digits = item.otp_code.slice(0, 6).split('');
      while (digits.length < 6) digits.push('');
      setOtpDigits(digits);
    } else {
      setOtpDigits(['', '', '', '', '', '']);
    }
    // Focus first input box
    setTimeout(() => {
      inputRefs[0].current?.focus();
    }, 50);
  };

  // Handle 6-digit input changes
  const handleDigitChange = (index: number, val: string) => {
    const cleanVal = val.replace(/\D/g, '');
    if (cleanVal.length === 0) {
      const nextDigits = [...otpDigits];
      nextDigits[index] = '';
      setOtpDigits(nextDigits);
      return;
    }

    const nextDigits = [...otpDigits];
    nextDigits[index] = cleanVal.slice(-1);
    setOtpDigits(nextDigits);

    // Auto-advance to next input box
    if (index < 5 && cleanVal.length > 0) {
      inputRefs[index + 1].current?.focus();
    }
  };

  // Handle backspace navigation
  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      inputRefs[index - 1].current?.focus();
    }
  };

  // Handle paste full 6-digit OTP
  const handlePaste = (e: React.ClipboardEvent<HTMLInputElement>) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    if (pasted.length > 0) {
      const digits = pasted.split('');
      while (digits.length < 6) digits.push('');
      setOtpDigits(digits);
      const targetIdx = Math.min(pasted.length, 5);
      inputRefs[targetIdx].current?.focus();
    }
  };

  // Autofill Demo OTP code button
  const handleAutofillDemoOtp = () => {
    const code = selectedItem?.otp_code;
    if (code) {
      const digits = code.slice(0, 6).split('');
      while (digits.length < 6) digits.push('');
      setOtpDigits(digits);
      inputRefs[5].current?.focus();
      onShowToast('Demo OTP Loaded', `Pre-populated demo OTP code: ${code}`, 'info');
    }
  };

  const fullOtpCode = otpDigits.join('');

  // Submit verification to real backend API
  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();

    const targetUser = selectedItem ? selectedItem.user_id : manualUserId.trim();
    const targetTxn = selectedItem ? selectedItem.transaction_id : manualTxnId.trim();

    if (!targetUser) {
      onShowToast('User Required', 'No target user specified for verification.', 'warning');
      return;
    }

    if (fullOtpCode.length < 6) {
      onShowToast('Invalid OTP', 'Please enter all 6 digits of the OTP code.', 'warning');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const res = await verifyOTP(targetUser, fullOtpCode, targetTxn || undefined);
      
      if (res.success) {
        setResult({
          success: true,
          message: res.message || 'OTP verified successfully. Transaction approved.'
        });
        onShowToast('✓ OTP Verified', 'Transaction status upgraded to ALLOW/APPROVED', 'success');
        
        // Refresh backend state immediately
        await fetchPendingOtps();
        onRefresh();
      } else {
        const isExpired = res.message.toLowerCase().includes('expired');
        setResult({
          success: false,
          message: res.message || 'Invalid OTP code. Verification failed.',
          expired: isExpired
        });
        onShowToast('Verification Failed', res.message, 'error');
      }
    } catch (err: any) {
      setResult({
        success: false,
        message: err.message || 'Error communicating with verification service.'
      });
      onShowToast('Error', err.message || 'Verification endpoint failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-12 font-sans">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-[#E6EAF0]">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-[#172033] tracking-tight">OTP Verification</h1>
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                isLiveConnected
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-rose-50 text-rose-700 border border-rose-200'
              }`}
            >
              <span className={`h-2 w-2 rounded-full ${isLiveConnected ? 'bg-emerald-500 animate-pulse' : 'bg-rose-500'}`} />
              {isLiveConnected ? 'LIVE CONNECTED' : 'DISCONNECTED'}
            </span>
          </div>
          <p className="text-xs text-[#64748B] mt-1 font-sans">
            Verify medium-risk transactions before approval. Real-time step-up security challenge workstation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              fetchPendingOtps();
              onShowToast('Refreshed', 'Synced pending OTP transactions from backend.', 'info');
            }}
            icon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Refresh List
          </Button>
        </div>
      </div>

      {/* 2. Pending OTP Transactions Section (Top / Left) */}
      <Card className="border-[#E6EAF0] bg-white shadow-xs overflow-hidden">
        <div className="p-4 sm:p-5 border-b border-[#E6EAF0] flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#F8FAFC]">
          <div>
            <div className="flex items-center gap-2">
              <KeyRound className="h-4 w-4 text-[#D97706]" />
              <h2 className="text-sm font-bold text-[#172033] uppercase tracking-wide">
                PENDING OTP TRANSACTIONS ({sortedOtps.length})
              </h2>
            </div>
            <p className="text-xs text-[#64748B] mt-0.5 font-sans">
              Transactions requiring additional verification.
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <span className="text-[#64748B] font-medium flex items-center gap-1">
              <SlidersHorizontal className="h-3.5 w-3.5 text-gray-400" /> Sort:
            </span>
            <div className="inline-flex rounded-lg border border-[#E6EAF0] bg-white p-0.5">
              <button
                type="button"
                onClick={() => setSortBy('newest')}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  sortBy === 'newest' ? 'bg-[#2563EB] text-white font-semibold' : 'text-[#64748B] hover:text-[#172033]'
                }`}
              >
                Newest First
              </button>
              <button
                type="button"
                onClick={() => setSortBy('risk')}
                className={`px-2.5 py-1 rounded-md text-xs font-medium transition-colors ${
                  sortBy === 'risk' ? 'bg-[#2563EB] text-white font-semibold' : 'text-[#64748B] hover:text-[#172033]'
                }`}
              >
                Highest Risk First
              </button>
            </div>
          </div>
        </div>

        {/* 3. Pending OTP Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-[#E6EAF0] bg-[#F1F5F9] text-[11px] font-sans uppercase text-[#64748B] font-semibold">
                <th className="py-3 px-4">Transaction ID</th>
                <th className="py-3 px-4">User</th>
                <th className="py-3 px-4">Merchant</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Risk Score</th>
                <th className="py-3 px-4">OTP Status</th>
                <th className="py-3 px-4">Expires In</th>
                <th className="py-3 px-4 text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E6EAF0] text-xs font-sans">
              {sortedOtps.map((item) => {
                const isSelected = selectedItem?.transaction_id === item.transaction_id;
                const timeRemainingStr = getRemainingTimeString(item);
                const isExpired = timeRemainingStr === 'EXPIRED';

                return (
                  <tr
                    key={item.transaction_id}
                    onClick={() => handleSelectTransaction(item)}
                    className={`cursor-pointer transition-all duration-150 ${
                      isSelected
                        ? 'bg-blue-50/70 border-l-4 border-[#2563EB] font-medium'
                        : 'hover:bg-gray-50/80'
                    }`}
                  >
                    <td className="py-3.5 px-4">
                      <TransactionId id={item.transaction_id} />
                    </td>
                    <td className="py-3.5 px-4 text-[#172033] font-sans font-medium">
                      {formatUserId(item.user_id)}
                    </td>
                    <td className="py-3.5 px-4 text-[#475569]">
                      {formatMerchantName(item.merchant, item.merchant_category)}
                    </td>
                    <td className="py-3.5 px-4 font-sans tabular-nums font-semibold text-[#172033]">
                      ${item.amount.toFixed(2)}
                    </td>
                    <td className="py-3.5 px-4 font-sans tabular-nums font-bold text-[#D97706]">
                      {normalizeRiskScore(item.risk_score).toFixed(1)}%
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded border text-[10px] font-sans font-bold uppercase ${
                          isExpired
                            ? 'bg-gray-100 text-gray-600 border-gray-300'
                            : 'bg-amber-50 text-[#D97706] border-amber-200'
                        }`}
                      >
                        {isExpired ? 'EXPIRED' : 'PENDING'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-[#64748B]">
                      <span className="inline-flex items-center gap-1 font-sans tabular-nums font-medium text-xs">
                        <Clock className={`h-3.5 w-3.5 ${isExpired ? 'text-rose-500' : 'text-amber-500'}`} />
                        <span className={isExpired ? 'text-rose-600 font-bold' : 'text-[#172033]'}>
                          {timeRemainingStr}
                        </span>
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <button
                        type="button"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleSelectTransaction(item);
                        }}
                        className={`px-3 py-1.5 rounded-lg text-xs font-semibold font-sans transition-all ${
                          isSelected
                            ? 'bg-[#2563EB] text-white shadow-xs'
                            : 'bg-white border border-[#E6EAF0] text-[#2563EB] hover:bg-blue-50'
                        }`}
                      >
                        {isSelected ? 'SELECTED' : 'VERIFY'}
                      </button>
                    </td>
                  </tr>
                );
              })}

              {/* 22. Empty State */}
              {sortedOtps.length === 0 && (
                <tr>
                  <td colSpan={8} className="py-12 text-center bg-gray-50/50">
                    <div className="max-w-md mx-auto flex flex-col items-center justify-center text-center">
                      <div className="h-12 w-12 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mb-3 shadow-xs">
                        <CheckCircle2 className="h-6 w-6" />
                      </div>
                      <h3 className="text-sm font-bold text-[#172033] font-sans">
                        ✓ No Pending OTP Transactions
                      </h3>
                      <p className="text-xs text-[#64748B] mt-1 font-sans">
                        All current OTP challenges have been completed. Medium-risk transactions (~25–50% risk score) generated by the simulator will automatically appear here.
                      </p>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      {/* 5-7. Verification Workstation Section (Right / Below) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        {/* Selected Transaction Card Summary */}
        <div className="lg:col-span-5 space-y-4">
          <Card className="border-[#E6EAF0] bg-white shadow-xs overflow-hidden">
            <div className="p-4 border-b border-[#E6EAF0] bg-[#F8FAFC] flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Lock className="h-4 w-4 text-[#2563EB]" />
                <h3 className="text-xs font-bold text-[#172033] uppercase tracking-wide">
                  SELECTED TRANSACTION
                </h3>
              </div>
              {selectedItem && (
                <span className="px-2 py-0.5 rounded text-[10px] font-sans font-bold bg-amber-50 text-[#D97706] border border-amber-200 uppercase">
                  OTP REQUIRED
                </span>
              )}
            </div>

            <div className="p-5 space-y-4">
              {selectedItem ? (
                <>
                  {/* Key Details Grid */}
                  <div className="bg-[#F8FAFC] p-4 rounded-xl border border-[#E6EAF0] space-y-3">
                    <div className="flex justify-between items-center pb-2 border-b border-[#E6EAF0]">
                      <span className="text-xs text-[#64748B]">Transaction ID</span>
                      <TransactionId id={selectedItem.transaction_id} />
                    </div>

                    <div className="flex justify-between items-center pb-2 border-b border-[#E6EAF0]">
                      <span className="text-xs text-[#64748B]">User</span>
                      <span className="text-xs font-sans font-medium text-[#172033]">{formatUserId(selectedItem.user_id)}</span>
                    </div>

                    <div className="flex justify-between items-center pb-2 border-b border-[#E6EAF0]">
                      <span className="text-xs text-[#64748B]">Merchant</span>
                      <span className="text-xs font-medium text-[#172033]">{formatMerchantName(selectedItem.merchant, selectedItem.merchant_category)}</span>
                    </div>

                    <div className="flex justify-between items-center pb-2 border-b border-[#E6EAF0]">
                      <span className="text-xs text-[#64748B]">Amount</span>
                      <span className="text-sm font-sans tabular-nums font-medium text-[#172033]">${selectedItem.amount.toFixed(2)}</span>
                    </div>

                    <div className="flex justify-between items-center pb-2 border-b border-[#E6EAF0]">
                      <span className="text-xs text-[#64748B]">Risk Score</span>
                      <span className="text-xs font-sans tabular-nums font-medium text-[#D97706] bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                        {normalizeRiskScore(selectedItem.risk_score).toFixed(1)}%
                      </span>
                    </div>

                    <div className="flex justify-between items-center pb-2 border-b border-[#E6EAF0]">
                      <span className="text-xs text-[#64748B]">Current Decision</span>
                      <span className="text-xs font-sans font-bold text-[#D97706] uppercase">OTP</span>
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="text-xs text-[#64748B]">Expiration</span>
                      <span className="text-xs font-sans tabular-nums font-bold text-[#172033] flex items-center gap-1">
                        <Clock className="h-3.5 w-3.5 text-amber-500" />
                        {getRemainingTimeString(selectedItem)}
                      </span>
                    </div>
                  </div>

                  {/* 18. Connection between OTP and Risk Explanation */}
                  <div className="p-3.5 bg-amber-50/60 rounded-xl border border-amber-200/80 text-xs text-[#92400E]">
                    <div className="flex items-start gap-2">
                      <AlertTriangle className="h-4 w-4 text-[#D97706] shrink-0 mt-0.5" />
                      <div>
                        <p className="font-bold text-[#78350F]">Medium-Risk Step-Up Verification</p>
                        <p className="mt-0.5 text-[11px] leading-relaxed text-[#92400E]">
                          {selectedItem.human_readable_reason || "Additional 2FA verification is required before this transaction is approved."}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* 7. Academic Demo OTP Display Box */}
                  {selectedItem.otp_code && (
                    <div className="p-4 bg-blue-50/70 rounded-xl border border-blue-200 space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-sans font-bold text-[#2563EB] uppercase tracking-wider flex items-center gap-1">
                          <Sparkles className="h-3 w-3" /> DEMO MODE — FOR ACADEMIC DEMONSTRATION ONLY
                        </span>
                      </div>
                      
                      <div className="flex items-center justify-between pt-1">
                        <div>
                          <span className="text-[11px] text-[#64748B] block font-medium">Real Backend Demo Passcode:</span>
                          <span className="text-xl font-mono font-bold text-[#2563EB] tracking-widest">
                            {selectedItem.otp_code}
                          </span>
                        </div>

                        <button
                          type="button"
                          onClick={handleAutofillDemoOtp}
                          className="px-3 py-1.5 rounded-lg bg-[#2563EB] hover:bg-blue-700 text-white font-sans font-semibold text-xs shadow-xs transition-colors"
                        >
                          Autofill Demo OTP
                        </button>
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="py-8 text-center text-[#64748B] text-xs">
                  Select a pending transaction from the table above to load verification workstation.
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Verification Workstation Panel (Main Form & Interactive 6-Digit Box) */}
        <div className="lg:col-span-7">
          <Card className="border-[#E6EAF0] bg-white shadow-xs p-6">
            <CardHeader
              title="VERIFY TRANSACTION"
              subtitle="Enter the 6-digit verification code for the selected transaction."
              icon={<ShieldCheck className="h-5 w-5 text-[#2563EB]" />}
            />

            {/* 19. Professor-Friendly Visual 4-Step Progress Indicator */}
            <div className="my-5 p-3 bg-[#F8FAFC] rounded-xl border border-[#E6EAF0]">
              <div className="grid grid-cols-4 gap-2 text-center text-[10px] font-sans">
                <div className="p-2 rounded bg-blue-100 text-[#2563EB] font-bold border border-blue-200">
                  1. PENDING TXN
                </div>
                <div className="p-2 rounded bg-amber-100 text-[#D97706] font-bold border border-amber-200">
                  2. OTP CHALLENGE
                </div>
                <div className="p-2 rounded bg-indigo-100 text-indigo-700 font-bold border border-indigo-200">
                  3. ENTER 6-DIGIT
                </div>
                <div className={`p-2 rounded font-bold border ${
                  result?.success
                    ? 'bg-emerald-100 text-emerald-700 border-emerald-300'
                    : 'bg-gray-100 text-gray-500 border-gray-200'
                }`}>
                  4. VERIFIED / ALLOW
                </div>
              </div>
            </div>

            <form onSubmit={handleVerify} className="space-y-6">
              {/* 8. Six-Digit OTP Input Grid */}
              <div className="space-y-3">
                <label className="block text-xs text-[#64748B] uppercase font-bold text-center tracking-wide">
                  ENTER 6-DIGIT VERIFICATION CODE *
                </label>

                <div className="flex justify-center items-center gap-2 sm:gap-3">
                  {otpDigits.map((digit, idx) => (
                    <input
                      key={idx}
                      ref={inputRefs[idx]}
                      id={`otp-digit-input-${idx}`}
                      type="text"
                      inputMode="numeric"
                      pattern="[0-9]*"
                      maxLength={1}
                      value={digit}
                      onChange={(e) => handleDigitChange(idx, e.target.value)}
                      onKeyDown={(e) => handleKeyDown(idx, e)}
                      onPaste={handlePaste}
                      className={`w-11 h-14 sm:w-13 sm:h-16 bg-[#F8FAFC] border-2 rounded-xl text-center text-2xl font-mono font-bold text-[#2563EB] transition-all shadow-xs focus:outline-none focus:bg-white ${
                        digit
                          ? 'border-[#2563EB] bg-blue-50/30'
                          : 'border-[#E6EAF0] focus:border-[#2563EB]'
                      }`}
                    />
                  ))}
                </div>

                <div className="flex justify-between items-center text-xs text-[#64748B] pt-1">
                  <span>Numeric input only (0-9)</span>
                  <button
                    type="button"
                    onClick={() => setOtpDigits(['', '', '', '', '', ''])}
                    className="text-[#2563EB] hover:underline font-medium"
                  >
                    Clear Input
                  </button>
                </div>
              </div>

              {/* 9. Verify Button */}
              <div className="pt-2 space-y-3">
                <Button
                  type="submit"
                  variant="primary"
                  className="w-full py-3.5 text-sm font-bold shadow-sm"
                  disabled={fullOtpCode.length < 6 || loading || (getRemainingTimeString(selectedItem || { time_remaining_sec: 1 } as any) === 'EXPIRED')}
                  isLoading={loading}
                  icon={<ShieldCheck className="h-5 w-5" />}
                >
                  {loading ? 'Verifying with Backend...' : 'VERIFY OTP'}
                </Button>

                {getRemainingTimeString(selectedItem || { time_remaining_sec: 1 } as any) === 'EXPIRED' && (
                  <p className="text-center text-xs font-bold text-rose-600 font-sans">
                    ✕ This OTP challenge has expired. Verification is disabled.
                  </p>
                )}
              </div>
            </form>

            {/* 10-12 & 17. Success / Failure / Expired Result Workflows */}
            {result && (
              <div className="mt-6">
                {result.success ? (
                  <div className="p-5 rounded-xl border-2 border-emerald-300 bg-emerald-50 text-emerald-900 space-y-3 animate-in fade-in duration-200">
                    <div className="flex items-start gap-3">
                      <div className="h-8 w-8 rounded-full bg-emerald-600 text-white flex items-center justify-center shrink-0">
                        <Check className="h-5 w-5 stroke-[3]" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-emerald-950 font-sans">
                          ✓ OTP VERIFIED — TRANSACTION APPROVED
                        </h4>
                        <p className="text-xs text-emerald-800 mt-0.5 font-sans">
                          {result.message}
                        </p>
                      </div>
                    </div>

                    <div className="pt-3 border-t border-emerald-200 grid grid-cols-2 gap-2 text-xs font-sans font-semibold">
                      <div className="bg-white/80 p-2.5 rounded-lg border border-emerald-200">
                        <span className="text-gray-500 text-[10px] block font-sans uppercase">Updated Decision</span>
                        <span className="text-emerald-700 font-bold text-sm">ALLOW</span>
                      </div>
                      <div className="bg-white/80 p-2.5 rounded-lg border border-emerald-200">
                        <span className="text-gray-500 text-[10px] block font-sans uppercase">Status</span>
                        <span className="text-emerald-700 font-bold text-sm">APPROVED</span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className={`p-4 rounded-xl border-2 space-y-2 ${
                    result.expired
                      ? 'bg-gray-100 border-gray-300 text-gray-900'
                      : 'bg-rose-50 border-rose-300 text-rose-950'
                  }`}>
                    <div className="flex items-start gap-3">
                      <XCircle className={`h-6 w-6 shrink-0 ${result.expired ? 'text-gray-600' : 'text-rose-600'}`} />
                      <div>
                        <h4 className="text-sm font-bold font-sans">
                          {result.expired ? '✕ OTP EXPIRED' : '✕ VERIFICATION FAILED'}
                        </h4>
                        <p className="text-xs mt-0.5 font-sans">
                          {result.message}
                        </p>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* 15. Optional Collapsible Manual Entry Fallback */}
            <div className="mt-8 pt-4 border-t border-[#E6EAF0]">
              <button
                type="button"
                onClick={() => setShowManual(!showManual)}
                className="text-xs text-[#64748B] hover:text-[#172033] font-medium flex items-center gap-1"
              >
                <span>{showManual ? '− Hide Manual Override Input' : '+ Manual User/Transaction Entry Fallback'}</span>
              </button>

              {showManual && (
                <div className="mt-3 p-4 bg-[#F8FAFC] rounded-xl border border-[#E6EAF0] space-y-3 text-xs font-sans">
                  <div>
                    <label className="block text-gray-600 mb-1 font-sans">User ID Override:</label>
                    <input
                      type="text"
                      value={manualUserId}
                      onChange={(e) => setManualUserId(e.target.value)}
                      placeholder="e.g. 4908846471916297"
                      className="w-full p-2 bg-white border border-[#E6EAF0] rounded font-mono text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-gray-600 mb-1 font-sans">Transaction ID Override (Optional):</label>
                    <input
                      type="text"
                      value={manualTxnId}
                      onChange={(e) => setManualTxnId(e.target.value)}
                      placeholder="Transaction UUID"
                      className="w-full p-2 bg-white border border-[#E6EAF0] rounded font-mono text-xs"
                    />
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};