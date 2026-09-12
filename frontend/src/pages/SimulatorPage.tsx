import React, { useState } from 'react';
import { PlayCircle, ShieldAlert, Zap, RefreshCw } from 'lucide-react';
import { triggerSimulator } from '../api/client';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

interface SimulatorPageProps {
  onRefresh: () => void;
  onShowToast: (title: string, message?: string, type?: 'success' | 'error' | 'warning' | 'info') => void;
}

export const SimulatorPage: React.FC<SimulatorPageProps> = ({ onRefresh, onShowToast }) => {
  const [loading, setLoading] = useState(false);
  const [lastLog, setLastLog] = useState<string | null>(null);

  const handleReplay = async (limit: number, triggerFraud = false) => {
    setLoading(true);
    setLastLog(null);
    try {
      const res = await triggerSimulator(limit, triggerFraud);
      setLastLog(res.message);
      onShowToast('Simulator Triggered', res.message, 'success');
      onRefresh();
    } catch (err: any) {
      onShowToast('Simulator Error', err.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-xl font-bold font-sans text-slate-900 tracking-tight">Live Transaction Simulator Control</h1>
        <p className="text-xs text-slate-500 mt-0.5 font-sans">
          Demonstration interface to trigger dataset transaction replay through Person A &rarr; Person B &rarr; Person C
        </p>
      </div>

      <Card>
        <CardHeader
          title="Interactive Simulator Controls"
          subtitle="Replay dataset transactions from data/fraud_sample.csv into the live detection pipeline"
          icon={<PlayCircle className="h-4 w-4 text-blue-600" />}
        />

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Button
            variant="primary"
            className="py-4 font-sans font-medium text-xs"
            isLoading={loading}
            onClick={() => handleReplay(10, false)}
            icon={<Zap className="h-4 w-4" />}
          >
            Replay 10 Transactions
          </Button>

          <Button
            variant="secondary"
            className="py-4 font-sans font-medium text-xs"
            isLoading={loading}
            onClick={() => handleReplay(50, false)}
            icon={<RefreshCw className="h-4 w-4" />}
          >
            Replay 50 Transactions
          </Button>

          <Button
            variant="danger"
            className="py-4 font-sans font-medium text-xs"
            isLoading={loading}
            onClick={() => handleReplay(1, true)}
            icon={<ShieldAlert className="h-4 w-4" />}
          >
            Inject On-Demand Fraud
          </Button>
        </div>

        {lastLog && (
          <div className="mt-6 p-4 bg-slate-900 border border-slate-800 rounded-xl font-mono text-xs text-emerald-400">
            <p className="text-[10px] font-sans text-slate-400 uppercase tracking-wider font-medium">Simulator Execution Output Log:</p>
            <p className="mt-1.5 leading-relaxed font-mono">{lastLog}</p>
          </div>
        )}
      </Card>
    </div>
  );
};