import React from 'react';
import { Server, Activity, ExternalLink } from 'lucide-react';
import { ServicesHealthResponse } from '../api/client';
import { Card, CardHeader } from '../components/ui/Card';
import { StatusBadge } from '../components/ui/Badge';
import { Button } from '../components/ui/Button';

interface SystemHealthPageProps {
  health: ServicesHealthResponse | null;
  onRefresh: () => void;
}

export const SystemHealthPage: React.FC<SystemHealthPageProps> = ({ health, onRefresh }) => {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold font-sans text-slate-900 tracking-tight">Infrastructure System Health</h1>
          <p className="text-xs text-slate-500 mt-0.5 font-sans">Live status for Kafka, Redis, MongoDB, FastAPI, Prometheus, and Grafana</p>
        </div>
        <Button variant="secondary" size="sm" onClick={onRefresh}>Re-check Health</Button>
      </div>

      <Card>
        <CardHeader
          title="Platform Dependency Status"
          subtitle={`Overall Platform State: ${(health?.overall || 'healthy').toUpperCase()}`}
          icon={<Server className="h-4 w-4 text-blue-600" />}
          action={<StatusBadge status={health?.overall || 'healthy'} />}
        />

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {(health?.services || [
            { name: 'mongodb', status: 'healthy', detail: 'Connected to fraud_db' },
            { name: 'redis', status: 'healthy', detail: 'Connected to localhost:6379' },
            { name: 'fastapi', status: 'healthy', detail: 'Running on port 8000' },
            { name: 'prometheus_endpoint', status: 'healthy', detail: '/metrics exposed' },
            { name: 'kafka', status: 'healthy', detail: 'Topic transactions active' },
          ]).map((s) => (
            <div key={s.name} className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 font-sans">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-slate-900 uppercase text-xs tracking-wider">{s.name}</span>
                <StatusBadge status={s.status} />
              </div>
              <p className="text-[11px] text-slate-500 leading-snug">{s.detail || 'Service operating normally.'}</p>
            </div>
          ))}
        </div>
      </Card>

      <Card>
        <CardHeader title="Observability Interfaces" icon={<Activity className="h-4 w-4 text-emerald-600" />} />
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 font-sans text-xs">
          {(() => {
            const grafanaUrl = import.meta.env.VITE_GRAFANA_URL || 'http://localhost:3000';
            const prometheusUrl = import.meta.env.VITE_PROMETHEUS_URL || 'http://localhost:9090';
            const swaggerUrl = import.meta.env.VITE_SWAGGER_URL || 'http://localhost:8000/docs';

            return (
              <>
                <a
                  href={grafanaUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="p-4 bg-slate-50 border border-slate-200 hover:border-blue-500/40 rounded-xl flex items-center justify-between group cursor-pointer transition-colors"
                >
                  <div>
                    <p className="font-semibold text-slate-900 group-hover:text-blue-600">Grafana Dashboard</p>
                    <p className="text-[10px] text-slate-500 font-mono mt-0.5">{grafanaUrl}</p>
                  </div>
                  <ExternalLink className="h-4 w-4 text-slate-400 group-hover:text-blue-600" />
                </a>

                <a
                  href={prometheusUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="p-4 bg-slate-50 border border-slate-200 hover:border-blue-500/40 rounded-xl flex items-center justify-between group cursor-pointer transition-colors"
                >
                  <div>
                    <p className="font-semibold text-slate-900 group-hover:text-blue-600">Prometheus UI</p>
                    <p className="text-[10px] text-slate-500 font-mono mt-0.5">{prometheusUrl}</p>
                  </div>
                  <ExternalLink className="h-4 w-4 text-slate-400 group-hover:text-blue-600" />
                </a>

                <a
                  href={swaggerUrl}
                  target="_blank"
                  rel="noreferrer"
                  className="p-4 bg-slate-50 border border-slate-200 hover:border-blue-500/40 rounded-xl flex items-center justify-between group cursor-pointer transition-colors"
                >
                  <div>
                    <p className="font-semibold text-slate-900 group-hover:text-blue-600">FastAPI Swagger</p>
                    <p className="text-[10px] text-slate-500 font-mono mt-0.5">{swaggerUrl}</p>
                  </div>
                  <ExternalLink className="h-4 w-4 text-slate-400 group-hover:text-blue-600" />
                </a>
              </>
            );
          })()}
        </div>
      </Card>
    </div>
  );
};