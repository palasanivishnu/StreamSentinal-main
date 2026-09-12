export interface Transaction {
  transaction_id: string;
  user_id: string;
  amount: number;
  currency?: string;
  merchant?: string;
  merchant_id?: string;
  merchant_category?: string;
  location?: { lat: number; lon: number };
  timestamp?: string;
  risk_score: number;
  ml_fraud_score?: number;
  rule_flags?: string[];
  decision: 'allow' | 'otp' | 'review' | 'block' | string;
  human_readable_reason?: string;
  processed_at?: string;
  latency_ms?: number;
  saved_at?: string;
  review_action?: string;
  review_action_at?: string;
  review_note?: string;
}

export interface Alert {
  alert_id: string;
  transaction_id: string;
  user_id: string;
  severity: 'CRITICAL' | 'HIGH' | 'WARNING' | string;
  decision: string;
  risk_score: number;
  reason: string;
  triggered_at: string;
  acknowledged?: boolean;
  acknowledged_at?: string;
  otp_code?: string;
}

export interface AnalyticsSummary {
  total_transactions: number;
  allow_count: number;
  otp_count: number;
  review_count: number;
  block_count: number;
  avg_risk_score: number;
  alerts_count: number;
}

export interface ServiceHealth {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded' | string;
  detail?: string;
}

export interface ServicesHealthResponse {
  overall: string;
  services: ServiceHealth[];
  timestamp: string;
}

export interface LatencyStats {
  avg_latency_ms: number;
  min_latency_ms: number;
  max_latency_ms: number;
  p50_latency_ms?: number;
  p95_latency_ms?: number;
  p99_latency_ms?: number;
  count: number;
}

export interface SearchResult {
  query: string;
  transactions: Transaction[];
  alerts: Alert[];
  users: string[];
}

export const getApiBaseUrl = (): string => {
  const envUrl = import.meta.env.VITE_API_URL;
  const localUrl = localStorage.getItem('streamsentinel_api_url');
  const baseUrl = envUrl || localUrl || 'http://localhost:8000';
  return baseUrl.replace(/\/+$/, '');
};

export async function fetchHealth(): Promise<{ status: string; environment: string; timestamp: string }> {
  const url = `${getApiBaseUrl()}/health`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchServicesHealth(): Promise<ServicesHealthResponse> {
  const url = `${getApiBaseUrl()}/health/services`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Services health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchAnalyticsSummary(): Promise<AnalyticsSummary> {
  const url = `${getApiBaseUrl()}/analytics/summary`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Analytics summary failed: ${res.statusText}`);
  return res.json();
}

export async function fetchAnalyticsLatency(): Promise<LatencyStats> {
  const url = `${getApiBaseUrl()}/analytics/latency`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Latency stats failed: ${res.statusText}`);
  return res.json();
}

export async function fetchRiskDistribution(hours = 24): Promise<any> {
  const url = `${getApiBaseUrl()}/analytics/risk-distribution?hours=${hours}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Risk distribution failed: ${res.statusText}`);
  return res.json();
}

export async function fetchTransactions(params?: {
  limit?: number;
  decision?: string;
  min_risk?: number;
  user_id?: string;
}): Promise<{ count: number; transactions: Transaction[] }> {
  const query = new URLSearchParams();
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.decision && params.decision !== 'all') query.append('decision', params.decision);
  if (params?.min_risk !== undefined && params.min_risk > 0) query.append('min_risk', params.min_risk.toString());
  if (params?.user_id) query.append('user_id', params.user_id);

  const url = `${getApiBaseUrl()}/transactions?${query.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Fetch transactions failed: ${res.statusText}`);
  return res.json();
}

export async function fetchTransaction(transaction_id: string): Promise<Transaction> {
  const url = `${getApiBaseUrl()}/transactions/${transaction_id}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Fetch transaction failed: ${res.statusText}`);
  return res.json();
}

export async function fetchUserTransactions(user_id: string, limit = 50): Promise<{ user_id: string; count: number; transactions: Transaction[] }> {
  const url = `${getApiBaseUrl()}/users/${user_id}/transactions?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Fetch user transactions failed: ${res.statusText}`);
  return res.json();
}

export async function fetchAlerts(params?: { limit?: number; severity?: string }): Promise<{ count: number; alerts: Alert[] }> {
  const query = new URLSearchParams();
  if (params?.limit) query.append('limit', params.limit.toString());
  if (params?.severity && params.severity !== 'all') query.append('severity', params.severity);

  const url = `${getApiBaseUrl()}/alerts?${query.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Fetch alerts failed: ${res.statusText}`);
  return res.json();
}

export async function acknowledgeAlert(alert_id: string): Promise<{ success: boolean; message: string }> {
  const url = `${getApiBaseUrl()}/alerts/${alert_id}/acknowledge`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error(`Acknowledge alert failed: ${res.statusText}`);
  return res.json();
}

export async function fetchReviews(limit = 50): Promise<{ count: number; reviews: Transaction[] }> {
  const url = `${getApiBaseUrl()}/reviews?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Fetch reviews failed: ${res.statusText}`);
  return res.json();
}

export async function approveReview(transaction_id: string): Promise<{ success: boolean; message: string }> {
  const url = `${getApiBaseUrl()}/reviews/${transaction_id}/approve`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error(`Approve review failed: ${res.statusText}`);
  return res.json();
}

export async function blockReview(transaction_id: string): Promise<{ success: boolean; message: string }> {
  const url = `${getApiBaseUrl()}/reviews/${transaction_id}/block`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error(`Block review failed: ${res.statusText}`);
  return res.json();
}

export interface PendingOTP {
  transaction_id: string;
  user_id: string;
  amount: number;
  merchant?: string;
  merchant_category?: string;
  risk_score: number;
  decision: string;
  timestamp?: string;
  otp_code?: string;
  otp_status?: string;
  expires_at?: string;
  time_remaining_sec?: number;
  human_readable_reason?: string;
}

export async function fetchPendingOtps(limit = 50): Promise<{ count: number; otps: PendingOTP[] }> {
  const url = `${getApiBaseUrl()}/otp/pending?limit=${limit}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Fetch pending OTPs failed: ${res.statusText}`);
  return res.json();
}

export async function verifyOTP(user_id: string, otp_code: string, transaction_id?: string): Promise<{ success: boolean; message: string }> {
  const url = `${getApiBaseUrl()}/otp/verify`;
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id, otp_code, transaction_id }),
  });
  if (!res.ok) throw new Error(`Verify OTP failed: ${res.statusText}`);
  return res.json();
}

export async function triggerSimulator(limit = 10, trigger_fraud = false): Promise<{ success: boolean; message: string; count?: number; transaction_id?: string }> {
  const url = `${getApiBaseUrl()}/simulator/replay?limit=${limit}&trigger_fraud=${trigger_fraud}`;
  const res = await fetch(url, { method: 'POST' });
  if (!res.ok) throw new Error(`Simulator trigger failed: ${res.statusText}`);
  return res.json();
}

export async function globalSearch(query: string): Promise<SearchResult> {
  const url = `${getApiBaseUrl()}/search?q=${encodeURIComponent(query)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Search failed: ${res.statusText}`);
  return res.json();
}