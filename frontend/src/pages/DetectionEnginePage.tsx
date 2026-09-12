import React from 'react';
import {
  Cpu,
  ShieldCheck,
  Zap,
  Layers,
  GitMerge,
  AlertTriangle,
  Info,
  ArrowRight,
  Calculator,
  Sliders,
  FileText,
  Activity,
  ArrowDown
} from 'lucide-react';
import { Card, CardHeader } from '../components/ui/Card';

export const DetectionEnginePage: React.FC = () => {
  const inputFeatures = [
    {
      name: 'amount',
      desc: 'Raw transaction value ($)',
    },
    {
      name: 'amount_vs_avg_ratio',
      desc: 'Transaction amount relative to the user\'s rolling average',
    },
    {
      name: 'txn_count_last_5min',
      desc: 'Number of recent transactions within the 5-minute window',
    },
    {
      name: 'time_since_last_txn_sec',
      desc: 'Time elapsed since the user\'s previous transaction',
    },
    {
      name: 'distance_from_last_location_km',
      desc: 'Geographic distance from the previous transaction',
    },
    {
      name: 'merchant_category_is_new_for_user',
      desc: 'Whether this merchant category is new for the user',
    },
  ];

  const activeRules = [
    {
      name: 'HIGH_AMOUNT',
      desc: 'Detects unusually large transactions exceeding $1,000 or 5x user rolling average',
      status: 'ACTIVE',
    },
    {
      name: 'HIGH_VELOCITY',
      desc: 'Detects high transaction frequency exceeding 5 transactions in 5 minutes',
      status: 'ACTIVE',
    },
    {
      name: 'IMPOSSIBLE_TRAVEL',
      desc: 'Detects physical geographical displacement exceeding 500 km in short window',
      status: 'ACTIVE',
    },
    {
      name: 'NEW_MERCHANT_CATEGORY',
      desc: 'Detects first-time transactions in merchant categories new to the user',
      status: 'ACTIVE',
    },
  ];

  return (
    <div className="space-y-8 font-sans pb-8">
      {/* Page Title & Subtitle */}
      <div>
        <h1 className="text-xl font-bold font-sans text-[#0F172A] tracking-tight">Detection Engine</h1>
        <p className="text-xs text-[#64748B] mt-0.5 font-sans">
          Hybrid fraud detection using behavioral features, deterministic rules, and XGBoost machine learning.
        </p>
      </div>

      {/* SECTION 1 — HERO DETECTION FLOW */}
      <Card className="border-[#E2E8F0] bg-white shadow-xs">
        <CardHeader
          title="How StreamSentinel Detects Fraud"
          subtitle="End-to-end telemetry transformation, hybrid scoring, and decision execution"
          icon={<Zap className="h-4 w-4 text-[#2563EB]" />}
        />
        <div className="p-6 bg-[#F8FAFC] border-t border-[#E2E8F0]">
          <div className="flex flex-col lg:flex-row items-center justify-between gap-3 text-xs">
            {/* Stage 1: Transaction */}
            <div className="p-3.5 bg-white border border-[#E2E8F0] rounded-xl text-center w-full lg:w-40 shadow-xs">
              <div className="w-8 h-8 mx-auto bg-blue-50 text-[#2563EB] rounded-lg flex items-center justify-center mb-2">
                <Activity className="h-4 w-4" />
              </div>
              <p className="font-semibold text-[#0F172A] font-sans text-xs">TRANSACTION</p>
              <p className="text-[10px] text-[#64748B] font-sans mt-0.5">Live Event Stream</p>
            </div>

            <ArrowRight className="h-4 w-4 text-slate-400 hidden lg:block shrink-0" />
            <ArrowDown className="h-4 w-4 text-slate-400 lg:hidden shrink-0" />

            {/* Stage 2: Feature Vector */}
            <div className="p-3.5 bg-white border border-[#E2E8F0] rounded-xl text-center w-full lg:w-44 shadow-xs">
              <div className="w-8 h-8 mx-auto bg-blue-50 text-[#2563EB] rounded-lg flex items-center justify-center mb-2">
                <Sliders className="h-4 w-4" />
              </div>
              <p className="font-semibold text-[#0F172A] font-sans text-xs">FEATURE VECTOR</p>
              <p className="text-[10px] text-[#64748B] font-sans mt-0.5">6 Behavioral Signals</p>
            </div>

            <ArrowRight className="h-4 w-4 text-slate-400 hidden lg:block shrink-0" />
            <ArrowDown className="h-4 w-4 text-slate-400 lg:hidden shrink-0" />

            {/* Stage 3: Hybrid Detection */}
            <div className="p-3.5 bg-blue-50/60 border border-blue-200 rounded-xl text-center w-full lg:w-56 shadow-xs">
              <div className="w-8 h-8 mx-auto bg-[#2563EB] text-white rounded-lg flex items-center justify-center mb-2">
                <GitMerge className="h-4 w-4" />
              </div>
              <p className="font-bold text-[#2563EB] font-sans text-xs uppercase tracking-wider">HYBRID DETECTION</p>
              <p className="text-[10px] text-[#0F172A] font-sans mt-0.5 font-medium">Rule Engine + XGBoost ML</p>
            </div>

            <ArrowRight className="h-4 w-4 text-slate-400 hidden lg:block shrink-0" />
            <ArrowDown className="h-4 w-4 text-slate-400 lg:hidden shrink-0" />

            {/* Stage 4: Combined Risk Score */}
            <div className="p-3.5 bg-white border border-[#E2E8F0] rounded-xl text-center w-full lg:w-44 shadow-xs">
              <div className="w-8 h-8 mx-auto bg-purple-50 text-purple-600 rounded-lg flex items-center justify-center mb-2">
                <Calculator className="h-4 w-4" />
              </div>
              <p className="font-semibold text-[#0F172A] font-sans text-xs">RISK SCORE</p>
              <p className="text-[10px] text-[#64748B] font-sans mt-0.5">Combined 0.00 – 1.00</p>
            </div>

            <ArrowRight className="h-4 w-4 text-slate-400 hidden lg:block shrink-0" />
            <ArrowDown className="h-4 w-4 text-slate-400 lg:hidden shrink-0" />

            {/* Stage 5: Decision Engine */}
            <div className="p-3.5 bg-white border border-[#E2E8F0] rounded-xl text-center w-full lg:w-48 shadow-xs">
              <div className="w-8 h-8 mx-auto bg-emerald-50 text-emerald-600 rounded-lg flex items-center justify-center mb-2">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <p className="font-semibold text-[#0F172A] font-sans text-xs">DECISION ENGINE</p>
              <p className="text-[10px] text-emerald-700 font-sans mt-0.5 font-bold uppercase">ALLOW / OTP / REVIEW / BLOCK</p>
            </div>
          </div>
        </div>
      </Card>

      {/* SECTION 2 — INPUT FEATURES */}
      <Card className="border-[#E2E8F0] bg-white shadow-xs">
        <CardHeader
          title="Transaction Features"
          subtitle="Behavioral features generated from the current transaction and recent user activity."
          icon={<Sliders className="h-4 w-4 text-[#2563EB]" />}
        />
        <div className="p-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {inputFeatures.map((feat, idx) => (
            <div key={idx} className="p-3.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl space-y-1">
              <span className="font-mono text-xs font-semibold text-[#2563EB]">{feat.name}</span>
              <p className="text-xs text-[#64748B] font-sans leading-relaxed">{feat.desc}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* SECTION 3 — HYBRID DETECTION (2 COLUMNS: RULE ENGINE + XGBOOST) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* LEFT: Rule Engine */}
        <Card className="border-[#E2E8F0] bg-white shadow-xs">
          <CardHeader
            title="Rule Engine"
            subtitle="Deterministic behavioral checks"
            icon={<AlertTriangle className="h-4 w-4 text-[#D97706]" />}
          />
          <div className="p-5 space-y-3">
            {activeRules.map((rule) => (
              <div key={rule.name} className="p-3.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl space-y-1">
                <div className="flex items-center justify-between">
                  <span className="font-mono font-semibold text-xs text-[#D97706]">{rule.name}</span>
                  <span className="px-2 py-0.5 text-[10px] font-mono font-semibold rounded bg-amber-50 text-[#D97706] border border-amber-200">
                    {rule.status}
                  </span>
                </div>
                <p className="text-xs text-[#64748B] font-sans leading-relaxed">{rule.desc}</p>
              </div>
            ))}
          </div>
        </Card>

        {/* RIGHT: XGBoost ML Model */}
        <Card className="border-[#E2E8F0] bg-white shadow-xs">
          <CardHeader
            title="XGBoost ML Model"
            subtitle="Supervised machine-learning fraud probability"
            icon={<Cpu className="h-4 w-4 text-purple-600" />}
          />
          <div className="p-5 space-y-4 text-xs font-sans">
            <div className="grid grid-cols-2 gap-3">
              <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl">
                <span className="text-[10px] text-[#64748B] uppercase font-semibold block font-sans">Model Architecture</span>
                <span className="font-sans text-xs font-bold text-purple-700 mt-0.5 block">XGBoost</span>
              </div>
              <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl">
                <span className="text-[10px] text-[#64748B] uppercase font-semibold block font-sans">Output Metric</span>
                <span className="font-sans text-xs font-bold text-[#0F172A] mt-0.5 block">ML Fraud Score</span>
              </div>
            </div>

            <div className="p-3.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl space-y-1">
              <div className="flex justify-between font-sans text-xs">
                <span className="text-[#64748B]">Score Range:</span>
                <span className="font-bold text-[#0F172A] tabular-nums">0.0 – 1.0 (0% – 100%)</span>
              </div>
              <div className="flex justify-between font-sans text-xs">
                <span className="text-[#64748B]">Artifact Path:</span>
                <span className="font-mono text-[11px] text-[#2563EB]">models/xgboost_fraud_detector.json</span>
              </div>
            </div>

            <div className="p-3.5 bg-purple-50/60 border border-purple-200 rounded-xl space-y-1 text-purple-900">
              <div className="flex items-center gap-1.5 font-bold text-purple-700 text-xs">
                <Info className="h-4 w-4 shrink-0" />
                <span>Supervised Estimation</span>
              </div>
              <p className="text-xs text-[#0F172A] leading-relaxed pl-5 font-sans">
                The model estimates the probability that the transaction is fraudulent based on the engineered behavioral features.
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* SECTION 4 — RISK CALCULATION */}
      <Card className="border-[#E2E8F0] bg-white shadow-xs max-w-3xl mx-auto">
        <CardHeader
          title="COMBINED RISK SCORE"
          subtitle="Hybrid weighting formula fusing ML probabilities with deterministic rule heuristics"
          icon={<Calculator className="h-4 w-4 text-[#2563EB]" />}
        />
        <div className="p-6 text-center space-y-4">
          <div className="inline-block p-4 bg-[#F8FAFC] border border-[#E2E8F0] rounded-2xl shadow-xs">
            <span className="font-mono text-sm sm:text-base font-bold text-[#0F172A]">
              Risk Score = 0.5 × ML Fraud Score + 0.5 × Rule Score
            </span>
          </div>
          <p className="text-xs text-[#64748B] max-w-lg mx-auto leading-relaxed font-sans">
            The final risk score combines the machine-learning fraud score with the deterministic rule score.
          </p>
        </div>
      </Card>

      {/* SECTION 5 & 6 — DECISION ENGINE & THRESHOLDS */}
      <Card className="border-[#E2E8F0] bg-white shadow-xs">
        <CardHeader
          title="Decision Engine"
          subtitle="Final action based on the combined risk score."
          icon={<ShieldCheck className="h-4 w-4 text-emerald-600" />}
        />
        <div className="p-5 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* ALLOW */}
          <div className="p-4 bg-emerald-50/60 border border-emerald-200 rounded-xl space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-sans font-bold text-xs text-emerald-800 uppercase">ALLOW</span>
              <span className="px-2 py-0.5 text-[10px] font-sans tabular-nums font-bold rounded bg-emerald-100 text-emerald-800">
                ≤ 0.25
              </span>
            </div>
            <p className="text-xs text-[#0F172A] font-sans leading-relaxed">
              Low-risk transaction is permitted.
            </p>
          </div>

          {/* OTP */}
          <div className="p-4 bg-amber-50/60 border border-amber-200 rounded-xl space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-sans font-bold text-xs text-amber-800 uppercase">OTP</span>
              <span className="px-2 py-0.5 text-[10px] font-sans tabular-nums font-bold rounded bg-amber-100 text-amber-800">
                0.25 – 0.50
              </span>
            </div>
            <p className="text-xs text-[#0F172A] font-sans leading-relaxed">
              Moderate-risk transaction requires additional user verification.
            </p>
          </div>

          {/* REVIEW */}
          <div className="p-4 bg-orange-50/60 border border-orange-200 rounded-xl space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-sans font-bold text-xs text-orange-800 uppercase">REVIEW</span>
              <span className="px-2 py-0.5 text-[10px] font-sans tabular-nums font-bold rounded bg-orange-100 text-orange-800">
                0.50 – 0.75
              </span>
            </div>
            <p className="text-xs text-[#0F172A] font-sans leading-relaxed">
              High-risk transaction is escalated for human investigation.
            </p>
          </div>

          {/* BLOCK */}
          <div className="p-4 bg-rose-50/60 border border-rose-200 rounded-xl space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-sans font-bold text-xs text-rose-800 uppercase">BLOCK</span>
              <span className="px-2 py-0.5 text-[10px] font-sans tabular-nums font-bold rounded bg-rose-100 text-rose-800">
                &gt; 0.75
              </span>
            </div>
            <p className="text-xs text-[#0F172A] font-sans leading-relaxed">
              Critical-risk transaction is prevented.
            </p>
          </div>
        </div>
      </Card>

      {/* SECTION 7 & 8 — EXPLAINABILITY & SAMPLE FLOW */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Explainability Card */}
        <Card className="border-[#E2E8F0] bg-white shadow-xs">
          <CardHeader
            title="Explainable Detection"
            subtitle="Full auditability for financial compliance and fraud analysts"
            icon={<FileText className="h-4 w-4 text-[#2563EB]" />}
          />
          <div className="p-5 space-y-3 text-xs">
            <p className="text-[#64748B] leading-relaxed font-sans">
              StreamSentinel transparently attributes every decision for human compliance and auditing. The system does not only say <strong className="text-[#0F172A]">WHAT</strong> the decision is; it also helps explain <strong className="text-[#0F172A]">WHY</strong>.
            </p>
            <div className="grid grid-cols-2 gap-2 pt-2">
              <div className="p-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg">
                <span className="font-sans text-[11px] font-semibold text-[#2563EB]">Rule Flags</span>
                <p className="text-[10px] text-[#64748B] font-sans">Triggered heuristics list</p>
              </div>
              <div className="p-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg">
                <span className="font-sans text-[11px] font-semibold text-purple-700">ML Fraud Score</span>
                <p className="text-[10px] text-[#64748B] font-sans">XGBoost output metric</p>
              </div>
              <div className="p-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg">
                <span className="font-sans text-[11px] font-semibold text-[#0F172A]">Human Reason</span>
                <p className="text-[10px] text-[#64748B] font-sans">Plain-language explanation</p>
              </div>
              <div className="p-2.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-lg">
                <span className="font-sans text-[11px] font-semibold text-emerald-700">SHAP Importance</span>
                <p className="text-[10px] text-[#64748B] font-sans">Model feature explanations</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Illustrative Example Card */}
        <Card className="border-[#E2E8F0] bg-white shadow-xs">
          <CardHeader
            title="Sample Decision Flow"
            subtitle="Illustrative execution walkthrough of a suspicious transaction"
            icon={<Layers className="h-4 w-4 text-[#D97706]" />}
          />
          <div className="p-5 space-y-3 text-xs">
            <div className="flex items-center justify-between">
              <span className="px-2 py-0.5 rounded bg-amber-50 text-[#D97706] border border-amber-200 font-sans text-[10px] font-bold uppercase">
                ILLUSTRATIVE EXAMPLE
              </span>
              <span className="font-mono text-[11px] text-[#64748B]">txn_sample_8819</span>
            </div>

            <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl space-y-2">
              <div className="flex items-center justify-between text-[11px] font-sans">
                <span className="text-[#64748B]">Input Signals:</span>
                <span className="font-mono font-semibold text-[#D97706]">HIGH_AMOUNT + HIGH_VELOCITY</span>
              </div>
              <div className="flex items-center justify-between text-[11px] font-sans">
                <span className="text-[#64748B]">XGBoost Fraud Score:</span>
                <span className="font-sans tabular-nums font-bold text-purple-700">62.0%</span>
              </div>
              <div className="flex items-center justify-between text-[11px] font-sans">
                <span className="text-[#64748B]">Combined Risk Score:</span>
                <span className="font-sans tabular-nums font-bold text-[#0F172A]">68.0%</span>
              </div>
            </div>

            <div className="p-3 bg-orange-50/70 border border-orange-200 rounded-xl flex items-center justify-between">
              <span className="font-sans font-semibold text-orange-900">Executed Action:</span>
              <span className="px-3 py-1 bg-orange-100 text-orange-900 font-sans font-bold uppercase rounded-lg border border-orange-200">
                REVIEW
              </span>
            </div>
          </div>
        </Card>
      </div>

      {/* BOTTOM TECHNICAL SUMMARY BAR */}
      <div className="p-4 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#64748B] font-sans">
        <div className="flex items-center gap-4 flex-wrap">
          <span>Model: <strong className="text-[#0F172A]">XGBoost</strong></span>
          <span>Rules: <strong className="text-[#0F172A]">4</strong></span>
          <span>Decision Classes: <strong className="text-[#0F172A]">4</strong></span>
          <span>Features: <strong className="text-[#0F172A]">6</strong></span>
        </div>
        <div>
          <span>Explainability: <strong className="text-[#2563EB]">SHAP / Rule Reasoning</strong></span>
        </div>
      </div>
    </div>
  );
};