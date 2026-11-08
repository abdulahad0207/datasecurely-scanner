import { supabase } from "./supabase";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface LatestScanSummary {
  id: string;
  status: string;
  grade?: string | null;
  findings_count: number;
  created_at: string;
  finished_at?: string | null;
}

export interface Domain {
  id: string;
  user_id: string;
  hostname: string;
  verify_token: string;
  status: "pending" | "verified" | "expired";
  is_monitored?: boolean;
  last_monitored_at?: string | null;
  verified_at: string | null;
  created_at: string;
  dns_record_name: string;
  dns_record_value: string;
  well_known_url: string;
  latest_scan?: LatestScanSummary | null;
}

export async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data } = await supabase.auth.getSession();
  let token = data?.session?.access_token;

  // Development bypass is strictly gated behind an explicit environment variable
  // that is never set in staging or production.
  const isDevBypassAllowed =
    process.env.NEXT_PUBLIC_ENABLE_DEV_AUTH_BYPASS === "true";

  if (!token && isDevBypassAllowed && typeof window !== "undefined") {
    let mock = localStorage.getItem("dev_mock_token");
    if (!mock || !mock.startsWith("test-token-")) {
      mock = "test-token-00000000-0000-0000-0000-000000000001-demo@example.com";
      localStorage.setItem("dev_mock_token", mock);
    }
    token = mock;
  }

  // The API client must NEVER substitute a fake token when unauthenticated
  if (!token) {
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      window.location.href = "/login";
    }
    throw new Error("Authentication required. Please sign in to continue.");
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

// Helper to handle 401 authentication errors gracefully
async function handleApiError(res: Response, fallbackMessage: string): Promise<never> {
  if (res.status === 401 && typeof window !== "undefined") {
    localStorage.removeItem("dev_mock_token");
    try {
      await supabase.auth.signOut();
    } catch {}
  }
  const err = await res.json().catch(() => ({ detail: fallbackMessage }));
  throw new Error(err.detail || fallbackMessage);
}

export async function fetchDomains(): Promise<Domain[]> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/domains`, { headers });
  if (!res.ok) {
    await handleApiError(res, "Failed to fetch domains");
  }
  const data = await res.json();
  return data.domains;
}

export async function createDomain(hostname: string): Promise<Domain> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/domains`, {
    method: "POST",
    headers,
    body: JSON.stringify({ hostname }),
  });
  if (!res.ok) {
    await handleApiError(res, "Failed to add domain");
  }
  return res.json();
}

export interface InfrastructureTelemetry {
  hostname: string;
  ip_address?: string | null;
  tls_version?: string | null;
  tls_cipher?: string | null;
  cert_issuer?: string | null;
  cert_expires?: string | null;
  cert_days_remaining?: number | null;
  server_banner?: string | null;
  hsts_header?: string | null;
  csp_header?: string | null;
}

export async function fetchDomainTelemetry(domainId: string): Promise<InfrastructureTelemetry | null> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/domains/${domainId}/telemetry`, { headers });
  if (!res.ok) {
    return null;
  }
  return res.json();
}

export async function getDomain(id: string): Promise<Domain> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/domains/${id}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to fetch domain" }));
    throw new Error(err.detail || "Failed to fetch domain");
  }
  return res.json();
}

export interface VerificationResult {
  verified: boolean;
  status: "pending" | "verified" | "expired";
  method: "dns_txt" | "well_known" | null;
  message: string;
  verified_at: string | null;
  details: {
    dns?: string;
    well_known?: string;
  };
}

export async function verifyDomain(id: string): Promise<VerificationResult> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/domains/${id}/verify`, {
    method: "POST",
    headers,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Verification request failed" }));
    throw new Error(err.detail || "Verification request failed");
  }
  return res.json();
}

export interface Scan {
  id: string;
  domain_id: string;
  user_id: string;
  hostname: string;
  profile: "free" | "full" | "monitor";
  status: "queued" | "recon" | "scanning" | "scoring" | "completed" | "failed" | "cancelled";
  progress: number;
  stage_message: string | null;
  grade: string | null;
  findings_count: number;
  started_at: string | null;
  finished_at: string | null;
  error: string | null;
  created_at: string;
}

export async function startScan(domainId: string, profile: string = "free"): Promise<Scan> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/scans`, {
    method: "POST",
    headers,
    body: JSON.stringify({ domain_id: domainId, profile }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to start scan" }));
    throw new Error(err.detail || "Failed to start scan");
  }
  return res.json();
}

export async function getScan(scanId: string): Promise<Scan> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/scans/${scanId}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to fetch scan" }));
    throw new Error(err.detail || "Failed to fetch scan");
  }
  return res.json();
}

export async function fetchDomainScans(domainId: string): Promise<Scan[]> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/scans/domain/${domainId}`, { headers });
  if (!res.ok) {
    return [];
  }
  const data = await res.json();
  return data.scans || [];
}

export interface Finding {
  id?: string;
  scan_id?: string;
  source_tool: string;
  template_id: string;
  title: string;
  severity: "info" | "low" | "medium" | "high" | "critical";
  host: string;
  evidence?: string | null;
  raw_ref?: string | null;
  fingerprint: string;
  ai_json?: {
    plain_summary: string;
    business_impact: string;
    fix_steps: string[];
    priority: number;
    confidence: number;
    effort: "low" | "medium" | "high";
  } | null;
}

export async function fetchScanFindings(scanId: string): Promise<Finding[]> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/scans/${scanId}/findings`, { headers });
  if (!res.ok) {
    return [];
  }
  const data = await res.json();
  return data.findings || [];
}

export async function deleteDomain(id: string): Promise<void> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/domains/${id}`, {
    method: "DELETE",
    headers,
  });
  if (!res.ok) {
    throw new Error("Failed to delete domain");
  }
}

export interface ReportData {
  id: string;
  scan_id: string;
  hostname: string;
  grade: string | null;
  language: string;
  pdf_download_url: string;
  summary: {
    executive_summary: string;
    top_actions: string[];
    grade_rationale: string;
    language: string;
  } | null;
  findings_count: number;
  created_at: string;
}

export async function fetchReport(scanId: string, lang: string = "en"): Promise<ReportData> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/reports/${scanId}?lang=${lang}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to load report" }));
    throw new Error(err.detail || "Failed to load report");
  }
  return res.json();
}

export function getReportDownloadUrl(scanId: string, lang: string = "en"): string {
  return `${API_BASE_URL}/api/v1/reports/${scanId}/download?lang=${lang}`;
}

export async function emailReport(
  scanId: string,
  email?: string,
  lang: string = "en"
): Promise<{ success: boolean; message: string; recipient: string; provider: string }> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/reports/${scanId}/email`, {
    method: "POST",
    headers,
    body: JSON.stringify({ email: email || null, language: lang }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to send email" }));
    throw new Error(err.detail || "Failed to send email");
  }
  return res.json();
}

export interface Plan {
  id: string;
  name: string;
  tagline: string;
  price_inr: number;
  billing_cycle: string;
  features: string[];
  popular: boolean;
}

export interface OrderResponse {
  order_id: string;
  razorpay_order_id: string;
  amount: number;
  currency: string;
  key_id: string;
  plan: string;
  domain_id?: string | null;
}

export interface QuotaStatus {
  allowed: boolean;
  reason: string;
  plan: string;
  wait_seconds: number | null;
  domain_id: string | null;
}

export async function fetchPlans(): Promise<Plan[]> {
  const res = await fetch(`${API_BASE_URL}/api/v1/billing/plans`);
  if (!res.ok) {
    return [];
  }
  return res.json();
}

export async function createBillingOrder(plan: string, domainId?: string): Promise<OrderResponse> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/billing/create-order`, {
    method: "POST",
    headers,
    body: JSON.stringify({ plan, domain_id: domainId || null }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to create order" }));
    throw new Error(err.detail || "Failed to create order");
  }
  return res.json();
}

export async function checkDomainQuota(domainId: string): Promise<QuotaStatus> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/billing/quota?domain_id=${domainId}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to check quota" }));
    throw new Error(err.detail || "Failed to check quota");
  }
  return res.json();
}

export interface ScanDiff {
  id: string;
  scan_id: string;
  domain_id: string;
  previous_scan_id: string | null;
  grade_change: "improved" | "degraded" | "unchanged" | "first_scan";
  new_findings_count: number;
  resolved_findings_count: number;
  persistent_findings_count: number;
  diff_json?: {
    new_findings: Finding[];
    resolved_findings: Finding[];
    persistent_findings: Finding[];
    previous_grade?: string;
    current_grade?: string;
  } | null;
  created_at: string;
}

export async function toggleMonitoring(
  domainId: string,
  enabled: boolean
): Promise<{ domain_id: string; is_monitored: boolean; message: string }> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/monitoring/toggle`, {
    method: "POST",
    headers,
    body: JSON.stringify({ domain_id: domainId, enabled }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to update monitoring setting" }));
    throw new Error(err.detail || "Failed to update monitoring setting");
  }
  return res.json();
}

export async function fetchScanDiff(scanId: string): Promise<ScanDiff> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/monitoring/diff/${scanId}`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to fetch scan diff" }));
    throw new Error(err.detail || "Failed to fetch scan diff");
  }
  return res.json();
}

export interface BillingOrderItem {
  id: string;
  razorpay_order_id: string;
  razorpay_payment_id?: string | null;
  plan: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string | null;
}

export interface AccountBillingData {
  plan: string;
  renewal_date: string | null;
  orders: BillingOrderItem[];
}

export async function fetchAccountBilling(): Promise<AccountBillingData> {
  const headers = await getAuthHeaders();
  const res = await fetch(`${API_BASE_URL}/api/v1/billing/account`, { headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Failed to load account billing details" }));
    throw new Error(err.detail || "Failed to load account billing details");
  }
  return res.json();
}




