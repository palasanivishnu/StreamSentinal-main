import React, { useState, useEffect } from 'react';
import {
  fetchAnalyticsSummary,
  fetchTransactions,
  fetchAlerts,
  fetchReviews,
  fetchServicesHealth,
  triggerSimulator,
  AnalyticsSummary,
  Transaction,
  Alert,
  ServicesHealthResponse,
} from './api/client';
import { Layout } from './components/layout/Layout';
import { ToastMessage } from './components/ui/Toast';

import { OverviewPage } from './pages/OverviewPage';
import { LiveTransactionsPage } from './pages/LiveTransactionsPage';
import { AlertCenterPage } from './pages/AlertCenterPage';
import { ReviewQueuePage } from './pages/ReviewQueuePage';
import { OtpVerificationPage } from './pages/OtpVerificationPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { DetectionEnginePage } from './pages/DetectionEnginePage';

export const App: React.FC = () => {
  const [currentPage, setCurrentPage] = useState('overview');
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [reviews, setReviews] = useState<Transaction[]>([]);
  const [health, setHealth] = useState<ServicesHealthResponse | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<'initializing' | 'connected' | 'disconnected'>('initializing');
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [selectedTransaction, setSelectedTransaction] = useState<Transaction | null>(null);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const addToast = (title: string, message?: string, type: 'success' | 'error' | 'warning' | 'info' = 'info') => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  };

  const loadData = async () => {
    setIsRefreshing(true);
    try {
      const [sumData, txnsData, alertsData, reviewsData, healthData] = await Promise.all([
        fetchAnalyticsSummary().catch(() => null),
        fetchTransactions({ limit: 50 }).catch(() => null),
        fetchAlerts({ limit: 50 }).catch(() => null),
        fetchReviews(50).catch(() => null),
        fetchServicesHealth().catch(() => null),
      ]);

      if (sumData) setSummary(sumData);
      if (txnsData) setTransactions(txnsData.transactions || []);
      if (alertsData) setAlerts(alertsData.alerts || []);
      if (reviewsData) setReviews(reviewsData.reviews || []);
      if (healthData) setHealth(healthData);

      if (sumData !== null || txnsData !== null || alertsData !== null || reviewsData !== null || healthData !== null) {
        setConnectionStatus('connected');
      } else {
        setConnectionStatus('disconnected');
      }
    } catch (err: any) {
      console.error('Data load error:', err);
      setConnectionStatus('disconnected');
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleRunDemo = async () => {
    try {
      await triggerSimulator(10, false);
      addToast('Simulator Batch Ingested', 'Replayed 10 real-time transactions through detection pipeline.', 'success');
      loadData();
    } catch (err: any) {
      addToast('Demo Execution Error', err.message, 'error');
    }
  };

  return (
    <Layout
      currentPage={currentPage}
      onNavigate={setCurrentPage}
      onRefresh={loadData}
      isRefreshing={isRefreshing}
      selectedTransaction={selectedTransaction}
      onSelectTransaction={setSelectedTransaction}
      toasts={toasts}
      onDismissToast={(id) => setToasts((prev) => prev.filter((t) => t.id !== id))}
    >
      {currentPage === 'overview' && (
        <OverviewPage
          summary={summary}
          transactions={transactions}
          alerts={alerts}
          health={health}
          onSelectTransaction={setSelectedTransaction}
          onNavigate={setCurrentPage}
          onRunDemo={handleRunDemo}
        />
      )}
      {currentPage === 'transactions' && (
        <LiveTransactionsPage
          transactions={transactions}
          connectionStatus={connectionStatus}
          onSelectTransaction={setSelectedTransaction}
          onRefresh={loadData}
        />
      )}
      {currentPage === 'alerts' && <AlertCenterPage alerts={alerts} onRefresh={loadData} onShowToast={addToast} onSelectTransaction={setSelectedTransaction} />}
      {currentPage === 'reviews' && <ReviewQueuePage reviews={reviews} onRefresh={loadData} onShowToast={addToast} />}
      {currentPage === 'otp' && <OtpVerificationPage onRefresh={loadData} onShowToast={addToast} />}
      {currentPage === 'analytics' && <AnalyticsPage summary={summary} />}
      {currentPage === 'engine' && <DetectionEnginePage />}
    </Layout>
  );
};

export default App;