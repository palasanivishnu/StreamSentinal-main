import React, { useState } from 'react';
import { Settings, Save, CheckCircle2 } from 'lucide-react';
import { Card, CardHeader } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

interface SettingsPageProps {
  onShowToast: (title: string, message?: string, type?: 'success' | 'error' | 'warning' | 'info') => void;
}

export const SettingsPage: React.FC<SettingsPageProps> = ({ onShowToast }) => {
  const [apiUrl, setApiUrl] = useState(localStorage.getItem('streamsentinel_api_url') || 'http://localhost:8000');

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem('streamsentinel_api_url', apiUrl.trim());
    onShowToast('Settings Saved', 'Backend API URL updated successfully.', 'success');
  };

  return (
    <div className="space-y-6 max-w-3xl mx-auto">
      <div>
        <h1 className="text-xl font-bold font-sans text-slate-900 tracking-tight">Application Settings</h1>
        <p className="text-xs text-slate-500 mt-0.5 font-sans">Frontend configuration and backend connection settings</p>
      </div>

      <Card>
        <CardHeader title="Backend Connection Settings" icon={<Settings className="h-4 w-4 text-blue-600" />} />
        <form onSubmit={handleSave} className="space-y-4">
          <div>
            <label className="block text-xs font-sans font-medium text-slate-500 mb-1.5 uppercase tracking-wider">FastAPI Backend Base URL</label>
            <input
              type="text"
              value={apiUrl}
              onChange={(e) => setApiUrl(e.target.value)}
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-900 font-mono focus:outline-none focus:border-blue-500 focus:bg-white transition-all"
              required
            />
          </div>

          <Button type="submit" variant="primary" icon={<Save className="h-4 w-4" />}>
            Save Configuration
          </Button>
        </form>
      </Card>
    </div>
  );
};