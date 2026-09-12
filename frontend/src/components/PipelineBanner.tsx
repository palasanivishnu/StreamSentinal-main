import React from 'react';
import { Cpu, Database, Server, Zap, ShieldCheck, AlertOctagon } from 'lucide-react';

export const PipelineBanner: React.FC = () => {
  const steps = [
    { label: 'Person A: Data & State', sub: 'Simulator -> Kafka -> Redis', icon: <Server className="h-4 w-4 text-blue-600" />, tag: 'INGEST' },
    { label: 'Feature Engineering', sub: '6 Rolling State Features', icon: <Database className="h-4 w-4 text-blue-600" />, tag: 'VECTOR' },
    { label: 'Person B: Detection Engine', sub: 'Rule Engine + XGBoost ML', icon: <Cpu className="h-4 w-4 text-purple-600" />, tag: 'SCORING' },
    { label: 'Decision Engine', sub: 'ALLOW | OTP | REVIEW | BLOCK', icon: <ShieldCheck className="h-4 w-4 text-amber-600" />, tag: 'DECISION' },
    { label: 'Person C: Operations', sub: 'MongoDB -> FastAPI -> Alert/OTP', icon: <AlertOctagon className="h-4 w-4 text-emerald-600" />, tag: 'ACTION' },
  ];

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-4 mb-6 shadow-xs relative overflow-hidden">
      <div className="flex items-center justify-between mb-3 border-b border-gray-100 pb-2">
        <div className="flex items-center gap-2">
          <Zap className="h-4 w-4 text-blue-600 animate-pulse" />
          <h2 className="text-xs font-sans font-bold tracking-wider text-gray-900 uppercase">
            End-to-End Execution Architecture Pipeline (A &rarr; B &rarr; C)
          </h2>
        </div>
        <span className="text-[10px] font-sans bg-blue-50 text-blue-700 border border-blue-200 px-2 py-0.5 rounded-full font-semibold">
          LIVE DATAFLOW
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
        {steps.map((step, idx) => (
          <div key={idx} className="relative bg-gray-50 border border-gray-200 rounded-lg p-3 flex flex-col justify-between">
            <div className="flex items-center justify-between mb-2">
              <div className="p-1.5 bg-white rounded-md border border-gray-200">{step.icon}</div>
              <span className="text-[9px] font-sans px-1.5 py-0.5 rounded bg-white text-gray-600 border border-gray-200 font-semibold">
                {step.tag}
              </span>
            </div>
            <div>
              <p className="text-xs font-semibold text-gray-900 font-sans">{step.label}</p>
              <p className="text-[10px] text-gray-500 mt-0.5 font-sans">{step.sub}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};