import React from 'react';
import { AlertTriangle } from 'lucide-react';
import { Card, CardHeader } from '../components/ui/Card';

export const RulesPage: React.FC = () => {
  const rules = [
    {
      name: 'HIGH_AMOUNT',
      title: 'High Transaction Amount Rule',
      desc: 'Triggers when single transaction amount is excessively high (> $1,000 or 5x user average).',
      impact: 'Elevates rule score and triggers review/otp recommendation.',
      weight: 'High (0.35)',
    },
    {
      name: 'HIGH_VELOCITY',
      title: 'Transaction Velocity Spikes',
      desc: 'Triggers when transaction frequency exceeds 5 transactions in a 5-minute rolling window.',
      impact: 'Indicates rapid carding or automated script behavior.',
      weight: 'High (0.30)',
    },
    {
      name: 'IMPOSSIBLE_TRAVEL',
      title: 'Geographic Impossible Travel',
      desc: 'Triggers when physical distance between consecutive transactions exceeds 500 km in a short time frame.',
      impact: 'Indicates account takeover or cloned card credentials across regions.',
      weight: 'Critical (0.40)',
    },
    {
      name: 'NEW_MERCHANT_CATEGORY',
      title: 'Merchant Category Novelty',
      desc: 'Triggers when transaction takes place in a merchant category never previously seen in user history.',
      impact: 'Adds baseline novelty risk factor.',
      weight: 'Medium (0.15)',
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-bold font-sans text-[#0F172A] tracking-tight">Active Person B Rule Engine Specifications</h1>
        <p className="text-xs text-[#64748B] mt-0.5 font-sans">Explanatory overview of the 4 authoritative heuristic fraud rules</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {rules.map((r) => (
          <Card key={r.name} className="border-[#E2E8F0] bg-white shadow-xs">
            <CardHeader title={r.name} subtitle={r.title} icon={<AlertTriangle className="h-4 w-4 text-[#D97706]" />} />
            <div className="space-y-2 text-xs font-sans text-[#0F172A]">
              <p><strong className="text-[#0F172A]">Behavior Description:</strong> <span className="text-[#64748B]">{r.desc}</span></p>
              <p><strong className="text-[#0F172A]">Operational Impact:</strong> <span className="text-[#64748B]">{r.impact}</span></p>
              <p><strong className="text-[#0F172A]">Rule Weight:</strong> <span className="text-[#D97706] font-mono font-bold">{r.weight}</span></p>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
};