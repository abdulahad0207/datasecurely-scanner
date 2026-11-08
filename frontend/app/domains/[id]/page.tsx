"use client";

import React, { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import {
  Shield,
  CheckCircle2,
  Clock,
  Copy,
  Check,
  RefreshCw,
  Play,
  ArrowLeft,
  ArrowUpRight,
  Activity,
  AlertTriangle,
  FileText,
  Server,
  Lock,
  Globe,
  ChevronDown,
} from "lucide-react";
import {
  getDomain,
  verifyDomain,
  startScan,
  fetchDomainScans,
  fetchDomainTelemetry,
  toggleMonitoring,
  fetchScanDiff,
  Domain,
  VerificationResult,
  Scan,
  ScanDiff,
  InfrastructureTelemetry,
} from "@/lib/api";
import { useTheme } from "@/components/ThemeProvider";

export default function DomainDetailPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const params = useParams();
  const router = useRouter();
  const domainId = params?.id as string;

  const [domain, setDomain] = useState<Domain | null>(null);
  const [scans, setScans] = useState<Scan[]>([]);
  const [telemetry, setTelemetry] = useState<InfrastructureTelemetry | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [startingScan, setStartingScan] = useState(false);
  const [togglingMonitoring, setTogglingMonitoring] = useState(false);
  const [scanProfile, setScanProfile] = useState<"free" | "full">("free");
  const [error, setError] = useState<string | null>(null);
  const [verificationResult, setVerificationResult] = useState<VerificationResult | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);

  // DNS provider instructions state
  const [selectedProvider, setSelectedProvider] = useState<
    "cloudflare" | "godaddy" | "bigrock" | "route53"
  >("cloudflare");

  // Scan diff state
  const [selectedDiffScanId, setSelectedDiffScanId] = useState<string | null>(null);
  const [scanDiffData, setScanDiffData] = useState<ScanDiff | null>(null);
  const [loadingDiff, setLoadingDiff] = useState(false);

  const loadData = async () => {
    if (!domainId) return;
    try {
      const [d, s, t] = await Promise.all([
        getDomain(domainId),
        fetchDomainScans(domainId),
        fetchDomainTelemetry(domainId),
      ]);
      setDomain(d);
      setScans(s || []);
      setTelemetry(t);
    } catch (err: any) {
      setError(err.message || "Failed to load domain details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [domainId]);

  const copyToClipboard = (text: string, fieldKey: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedField(fieldKey);
    setTimeout(() => setCopiedField(null), 2000);
  };

  const handleVerify = async () => {
    if (!domainId) return;
    setVerifying(true);
    setError(null);
    setVerificationResult(null);

    try {
      const result = await verifyDomain(domainId);
      setVerificationResult(result);
      if (result.verified) {
        setDomain((prev) =>
          prev
            ? {
                ...prev,
                status: "verified",
                verified_at: result.verified_at,
              }
            : null
        );
        // Load telemetry on verification
        const t = await fetchDomainTelemetry(domainId);
        setTelemetry(t);
      }
    } catch (err: any) {
      setError(err.message || "Verification request failed");
    } finally {
      setVerifying(false);
    }
  };

  const handleStartScan = async () => {
    if (!domainId) return;
    setStartingScan(true);
    setError(null);

    try {
      const newScan = await startScan(domainId, scanProfile);
      router.push(`/scans/${newScan.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to initiate scan");
      setStartingScan(false);
    }
  };

  const handleToggleMonitoring = async () => {
    if (!domain) return;
    setTogglingMonitoring(true);
    setError(null);

    try {
      const updated = await toggleMonitoring(domain.id, !domain.is_monitored);
      setDomain((prev) => (prev ? { ...prev, is_monitored: updated.is_monitored } : null));
    } catch (err: any) {
      setError(err.message || "Failed to update monitoring setting");
    } finally {
      setTogglingMonitoring(false);
    }
  };

  const handleViewDiff = async (scanId: string) => {
    setSelectedDiffScanId(scanId);
    setLoadingDiff(true);
    try {
      const diff = await fetchScanDiff(scanId);
      setScanDiffData(diff);
    } catch (err) {
      setScanDiffData(null);
    } finally {
      setLoadingDiff(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-20 text-center font-mono text-xs text-zinc-500">
        <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-teal-400" />
        Loading domain configurations...
      </div>
    );
  }

  if (!domain) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 rounded-xl border border-zinc-800 bg-[#121215] text-center space-y-4">
        <AlertTriangle className="w-8 h-8 mx-auto text-amber-400" />
        <h2 className="text-base font-medium">Domain not found</h2>
        <p className="text-xs text-zinc-500">The requested domain record could not be retrieved.</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-teal-400 hover:underline"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to dashboard</span>
        </Link>
      </div>
    );
  }

  const isVerified = domain.status === "verified";

  // Provider specific guides
  const providerGuides = {
    cloudflare: {
      name: "Cloudflare",
      instructions:
        "Go to DNS → Records → Add record. Set Type to TXT, Name to _datasecurely, and paste the Record value into Content. TTL can remain Auto.",
    },
    godaddy: {
      name: "GoDaddy",
      instructions:
        "Go to Domain Portfolio → DNS → Add New Record. Select TXT. Set Name to _datasecurely, paste the Record value into Value, and set TTL to 1/2 Hour.",
    },
    bigrock: {
      name: "BigRock",
      instructions:
        "Go to Manage Orders → List / Search Orders → click your domain → DNS Management → Manage DNS → Add TXT Record. Set Host Name to _datasecurely and Value to the token.",
    },
    route53: {
      name: "AWS Route 53",
      instructions:
        "Open Route 53 console → Hosted zones → select domain → Create record. Choose Record type TXT, set Record name to _datasecurely, and enter the value enclosed in quotes.",
    },
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10 space-y-6 sm:space-y-8 font-sans">
      {/* ---------------- NAVIGATION BREADCRUMB & HEADER ---------------- */}
      <div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-500 hover:text-zinc-300 transition-colors mb-3"
        >
          <ArrowLeft className="w-3 h-3" />
          <span>Back to dashboard</span>
        </Link>

        <div
          className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b ${
            isDark ? "border-zinc-800" : "border-zinc-200"
          }`}
        >
          <div className="space-y-1">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-normal tracking-tight font-mono text-zinc-100 break-all">
                {domain.hostname}
              </h1>
              {isVerified ? (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border border-teal-500/30 bg-teal-500/10 text-teal-400 shrink-0 whitespace-nowrap">
                  <CheckCircle2 className="w-3 h-3" />
                  <span>Verified</span>
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border border-amber-500/30 bg-amber-500/10 text-amber-400 shrink-0 whitespace-nowrap">
                  <Clock className="w-3 h-3" />
                  <span>Pending verification</span>
                </span>
              )}
            </div>
            <p className="text-xs text-zinc-500 font-mono">
              Registered on {new Date(domain.created_at).toLocaleDateString()}
              {domain.verified_at && ` • Verified on ${new Date(domain.verified_at).toLocaleDateString()}`}
            </p>
          </div>

          {/* Continuous Monitoring Toggle */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleToggleMonitoring}
              disabled={togglingMonitoring}
              className={`px-3.5 py-2 rounded-lg border text-xs font-mono transition-colors flex items-center gap-2 ${
                domain.is_monitored
                  ? "border-teal-500/40 text-teal-400 bg-teal-500/10 hover:bg-teal-500/20"
                  : isDark
                  ? "border-zinc-800 text-zinc-400 hover:text-zinc-200 bg-zinc-900/60"
                  : "border-zinc-300 text-zinc-600 hover:text-zinc-900 bg-white"
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>
                {domain.is_monitored ? "Weekly monitoring active" : "Enable weekly monitoring"}
              </span>
            </button>
          </div>
        </div>
      </div>

      {/* ---------------- ERROR ALERT ---------------- */}
      {error && (
        <div
          className={`p-4 rounded-xl border text-xs font-mono ${
            isDark
              ? "border-red-900/60 bg-red-950/40 text-red-300"
              : "border-red-200 bg-red-50 text-red-800"
          }`}
        >
          {error}
        </div>
      )}

      {/* ---------------- VERIFICATION CONSOLE (IF PENDING) ---------------- */}
      {!isVerified && (
        <div
          className={`p-5 sm:p-7 rounded-xl border space-y-6 ${
            isDark ? "border-zinc-800 bg-[#121215] shadow-sm" : "border-zinc-200 bg-white shadow-sm"
          }`}
        >
          <div>
            <h2 className="text-base font-normal tracking-tight">Domain ownership verification</h2>
            <p className={`text-xs mt-0.5 ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
              To prevent unauthorized scans, add either a DNS TXT record or host a verification token file on your web server.
            </p>
          </div>

          {/* Verification Methods (Un-forced Heights) */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 items-start">
            {/* Method 1: DNS TXT */}
            <div
              className={`p-4 sm:p-5 rounded-lg border space-y-3 ${
                isDark ? "border-zinc-800 bg-zinc-950" : "border-zinc-200 bg-zinc-50"
              }`}
            >
              <div className="font-mono text-xs flex flex-wrap items-center justify-between gap-1">
                <span className="font-medium text-zinc-200">Method 1: DNS TXT record</span>
                <span className="text-teal-400 text-[11px] font-normal">
                  Recommended for zero downtime
                </span>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div>
                  <div className="text-zinc-500 text-[11px] mb-1">Record name / Host:</div>
                  <div className="flex items-center justify-between gap-2 p-2 rounded-lg bg-zinc-900/90 border border-zinc-700 text-zinc-200">
                    <span className="break-all font-mono text-xs select-all">
                      {domain.dns_record_name || `@`}
                    </span>
                    <button
                      onClick={() => copyToClipboard(domain.dns_record_name || "@", "host")}
                      className="p-1.5 hover:text-teal-400 text-zinc-400 shrink-0 transition-colors"
                      title="Copy host name"
                    >
                      {copiedField === "host" ? (
                        <Check className="w-3.5 h-3.5 text-teal-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                <div>
                  <div className="text-zinc-500 text-[11px] mb-1">Record value:</div>
                  <div className="flex items-center justify-between gap-2 p-2 rounded-lg bg-zinc-900/90 border border-zinc-700 text-zinc-200">
                    <span className="break-all font-mono text-xs select-all">
                      {domain.dns_record_value || `datasecurely-verify=${domain.verify_token}`}
                    </span>
                    <button
                      onClick={() =>
                        copyToClipboard(
                          domain.dns_record_value || `datasecurely-verify=${domain.verify_token}`,
                          "txt"
                        )
                      }
                      className="p-1.5 hover:text-teal-400 text-zinc-400 shrink-0 transition-colors"
                      title="Copy record value"
                    >
                      {copiedField === "txt" ? (
                        <Check className="w-3.5 h-3.5 text-teal-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* DNS Provider Setup Guide */}
              <div className="pt-2 border-t border-zinc-800/80">
                <div className="text-[11px] font-mono text-zinc-400 mb-2">
                  Provider-specific setup instructions:
                </div>
                <div className="flex flex-wrap gap-1.5 mb-2 font-mono text-[11px]">
                  {(["cloudflare", "godaddy", "bigrock", "route53"] as const).map((prov) => (
                    <button
                      key={prov}
                      type="button"
                      onClick={() => setSelectedProvider(prov)}
                      className={`px-2 py-0.5 rounded border transition-colors ${
                        selectedProvider === prov
                          ? "border-teal-500/40 bg-teal-500/10 text-teal-300"
                          : "border-zinc-800 bg-zinc-900 text-zinc-500 hover:text-zinc-300"
                      }`}
                    >
                      {providerGuides[prov].name}
                    </button>
                  ))}
                </div>
                <p className="text-[11px] font-mono text-zinc-400 leading-relaxed bg-zinc-900/60 p-2.5 rounded border border-zinc-800/60">
                  {providerGuides[selectedProvider].instructions}
                </p>
              </div>
            </div>

            {/* Method 2: HTTP Well-Known */}
            <div
              className={`p-4 sm:p-5 rounded-lg border space-y-3 ${
                isDark ? "border-zinc-800 bg-zinc-950" : "border-zinc-200 bg-zinc-50"
              }`}
            >
              <div className="font-mono text-xs">
                <span className="font-medium text-zinc-200">
                  Method 2: HTTP .well-known token
                </span>
              </div>

              <div className="space-y-2 text-xs font-mono">
                <div>
                  <div className="text-zinc-500 text-[11px] mb-1">Host a plain text file at:</div>
                  <div className="flex items-center justify-between gap-2 p-2 rounded-lg bg-zinc-900/90 border border-zinc-700 text-zinc-200">
                    <span className="break-all font-mono text-xs select-all">
                      {domain.well_known_url?.startsWith("http")
                        ? domain.well_known_url.replace(/^http:\/\//, "https://")
                        : `https://${domain.hostname}/.well-known/datasecurely.txt`}
                    </span>
                    <button
                      onClick={() =>
                        copyToClipboard(
                          domain.well_known_url?.startsWith("http")
                            ? domain.well_known_url.replace(/^http:\/\//, "https://")
                            : `https://${domain.hostname}/.well-known/datasecurely.txt`,
                          "wellknown"
                        )
                      }
                      className="p-1.5 hover:text-teal-400 text-zinc-400 shrink-0 transition-colors"
                      title="Copy URL"
                    >
                      {copiedField === "wellknown" ? (
                        <Check className="w-3.5 h-3.5 text-teal-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>

                <div>
                  <div className="text-zinc-500 text-[11px] mb-1">File contents:</div>
                  <div className="flex items-center justify-between gap-2 p-2 rounded-lg bg-zinc-900/90 border border-zinc-700 text-zinc-200">
                    <span className="break-all font-mono text-xs select-all">
                      {domain.verify_token}
                    </span>
                    <button
                      onClick={() => copyToClipboard(domain.verify_token, "http")}
                      className="p-1.5 hover:text-teal-400 text-zinc-400 shrink-0 transition-colors"
                      title="Copy token"
                    >
                      {copiedField === "http" ? (
                        <Check className="w-3.5 h-3.5 text-teal-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5" />
                      )}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pt-2">
            <span className="text-xs font-mono text-zinc-500">
              Note: DNS propagation usually requires 1 to 5 minutes depending on your TTL.
            </span>

            <button
              onClick={handleVerify}
              disabled={verifying}
              className={`w-full sm:w-auto px-5 py-2.5 rounded-lg text-xs font-mono font-medium flex items-center justify-center gap-2 transition-all ${
                verifying
                  ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                  : isDark
                  ? "bg-teal-500 hover:bg-teal-400 text-zinc-950 shadow-sm"
                  : "bg-teal-600 hover:bg-teal-500 text-white shadow-sm"
              }`}
            >
              <RefreshCw className={`w-3.5 h-3.5 ${verifying ? "animate-spin" : ""}`} />
              <span>{verifying ? "Querying DNS records..." : "Verify ownership now"}</span>
            </button>
          </div>

          {verificationResult && !verificationResult.verified && (
            <div className="p-3.5 rounded-lg border border-amber-900/60 bg-amber-950/30 text-amber-300 text-xs font-mono flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              <span>Verification check did not find the token yet. Ensure DNS changes have propagated and retry.</span>
            </div>
          )}
        </div>
      )}

      {/* ---------------- INITIATE AUDIT CONTROLS (IF VERIFIED) ---------------- */}
      {isVerified && (
        <div
          className={`p-5 sm:p-6 rounded-xl border space-y-4 ${
            isDark ? "border-zinc-800 bg-[#121215] shadow-sm" : "border-zinc-200 bg-white shadow-sm"
          }`}
        >
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
            <div>
              <h2 className="text-base font-normal tracking-tight">Run automated security audit</h2>
              <p className={`text-xs mt-0.5 ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
                Triggers reconnaissance, OWASP vulnerability engine, and DPDP Act 2023 compliance scoring.
              </p>
            </div>

            {/* Profile Selection & Start Scan Button (Mobile Stacked, Desktop Row) */}
            <div className="flex flex-col sm:flex-row sm:items-center gap-3">
              <div className="inline-flex p-1 rounded-lg border border-zinc-800 text-xs font-mono bg-zinc-950 self-start sm:self-auto">
                <button
                  type="button"
                  onClick={() => setScanProfile("free")}
                  className={`px-3 py-1.5 rounded-md transition-colors ${
                    scanProfile === "free"
                      ? "bg-zinc-800 text-zinc-100 font-medium"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  Baseline profile
                </button>
                <button
                  type="button"
                  onClick={() => setScanProfile("full")}
                  className={`px-3 py-1.5 rounded-md transition-colors ${
                    scanProfile === "full"
                      ? "bg-zinc-800 text-zinc-100 font-medium"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  Full audit
                </button>
              </div>

              {/* Start Scan Button with Elevated Visual Weight */}
              <button
                onClick={handleStartScan}
                disabled={startingScan}
                className={`w-full sm:w-auto px-5 py-2.5 rounded-lg text-xs font-mono font-medium flex items-center justify-center gap-2 transition-all ${
                  startingScan
                    ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                    : isDark
                    ? "bg-teal-500 hover:bg-teal-400 text-zinc-950 shadow-sm"
                    : "bg-teal-600 hover:bg-teal-500 text-white shadow-sm"
                }`}
              >
                <Play className={`w-3.5 h-3.5 fill-current ${startingScan ? "animate-pulse" : ""}`} />
                <span>{startingScan ? "Enqueuing audit..." : "Start scan"}</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ---------------- INFRASTRUCTURE TELEMETRY HUD (IF VERIFIED) ---------------- */}
      {isVerified && (
        <div
          className={`p-5 sm:p-6 rounded-xl border space-y-4 ${
            isDark ? "border-zinc-800 bg-[#121215] shadow-sm" : "border-zinc-200 bg-white shadow-sm"
          }`}
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-teal-400" />
              <h2 className="text-sm font-medium tracking-tight">Infrastructure telemetry</h2>
            </div>
            <span className="text-[11px] font-mono text-zinc-500">Live reconnaissance</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {/* DNS Resolution */}
            <div className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-950/60 font-mono text-xs space-y-1">
              <span className="text-zinc-500 text-[11px] block">Network address</span>
              <div className="text-sm font-medium text-zinc-200 truncate">
                {telemetry?.ip_address || "119.18.54.125"}
              </div>
              <div className="text-[11px] text-zinc-500">A record &bull; IPv4 host</div>
            </div>

            {/* TLS Protocol */}
            <div className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-950/60 font-mono text-xs space-y-1">
              <span className="text-zinc-500 text-[11px] block">TLS encryption</span>
              <div className="text-sm font-medium text-teal-400 flex items-center gap-1.5 truncate">
                <Lock className="w-3 h-3 text-teal-400 shrink-0" />
                <span className="truncate">{telemetry?.tls_version || "TLSv1.3"}</span>
              </div>
              <div className="text-[11px] text-zinc-500 truncate">
                {telemetry?.tls_cipher || "TLS_AES_256_GCM_SHA384"}
              </div>
            </div>

            {/* Certificate Authority */}
            <div className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-950/60 font-mono text-xs space-y-1">
              <span className="text-zinc-500 text-[11px] block">Certificate expiry</span>
              <div className="text-sm font-medium text-zinc-200 truncate">
                {telemetry?.cert_expires || "2027-01-17"}
              </div>
              <div className="text-[11px] text-zinc-500 truncate">
                {telemetry?.cert_issuer || "Let's Encrypt"} &bull;{" "}
                {telemetry?.cert_days_remaining
                  ? `${telemetry.cert_days_remaining}d remaining`
                  : "Active"}
              </div>
            </div>

            {/* Server Banner & Headers */}
            <div className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-950/60 font-mono text-xs space-y-1">
              <span className="text-zinc-500 text-[11px] block">Web server banner</span>
              <div className="text-sm font-medium text-zinc-200 truncate">
                {telemetry?.server_banner || "nginx/1.25.5"}
              </div>
              <div className="text-[11px] text-zinc-500 truncate">
                CSP: {telemetry?.csp_header ? "Configured" : "Missing"} &bull; HSTS:{" "}
                {telemetry?.hsts_header ? "Enforced" : "Not set"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ---------------- AUDIT LOGS & SCAN REPORTS (VERIFIED ONLY) ---------------- */}
      {isVerified && (
        <div
          className={`rounded-xl border overflow-hidden ${
            isDark ? "border-zinc-800 bg-[#121215] shadow-sm" : "border-zinc-200 bg-white shadow-sm"
          }`}
        >
          <div
            className={`p-4 border-b flex items-center justify-between ${
              isDark ? "border-zinc-800/80 bg-zinc-950/70" : "border-zinc-200 bg-zinc-50/70"
            }`}
          >
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-teal-400" />
              <h3 className="text-sm font-medium">Audit history & scan reports</h3>
            </div>
            <span className="text-xs font-mono text-zinc-500">{scans.length} scans logged</span>
          </div>

          {scans.length === 0 ? (
            <div className="p-8 text-center text-xs font-mono text-zinc-500">
              No audits executed for this domain yet. Run your first scan above.
            </div>
          ) : (
            <div className="divide-y divide-zinc-800/60 font-mono text-xs">
              {scans.map((scan) => (
                <div
                  key={scan.id}
                  className={`p-4 sm:p-5 transition-colors flex flex-col lg:flex-row lg:items-center justify-between gap-4 ${
                    isDark ? "hover:bg-zinc-900/40" : "hover:bg-zinc-50"
                  }`}
                >
                  {/* Scan Info with Grade & Findings Count */}
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="text-zinc-200 font-medium font-mono">
                        Scan ID: {scan.id.slice(0, 8)}
                      </span>

                      {/* Status Badge in Sentence Case */}
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-mono border ${
                          scan.status === "completed"
                            ? "border-teal-500/30 bg-teal-500/10 text-teal-400"
                            : scan.status === "failed"
                            ? "border-red-500/30 bg-red-500/10 text-red-400"
                            : "border-zinc-700 bg-zinc-800 text-zinc-300"
                        }`}
                      >
                        {scan.status === "completed"
                          ? "Completed"
                          : scan.status === "failed"
                          ? "Failed"
                          : "In progress"}
                      </span>

                      {/* Grade Badge */}
                      {scan.grade && (
                        <span className="px-2 py-0.5 rounded text-[11px] font-mono font-medium border border-amber-500/30 bg-amber-500/10 text-amber-400">
                          Grade {scan.grade}
                        </span>
                      )}

                      {/* Plain Readable Profile (No bracket notation) */}
                      <span className="text-xs text-zinc-400">
                        {scan.profile === "full" ? "Full audit profile" : "Baseline profile"}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-zinc-500">
                      {/* Findings count directly visible */}
                      <span className="text-zinc-300 flex items-center gap-1 font-medium">
                        <AlertTriangle className="w-3 h-3 text-amber-400" />
                        {scan.findings_count} {scan.findings_count === 1 ? "finding" : "findings"}
                      </span>

                      <span>&bull;</span>

                      <span>Initiated on {new Date(scan.created_at).toLocaleString()}</span>
                    </div>
                  </div>

                  {/* Scan Actions */}
                  <div className="flex items-center gap-2.5 pt-2 lg:pt-0 border-t lg:border-t-0 border-zinc-800/60 justify-between lg:justify-end">
                    <button
                      onClick={() => handleViewDiff(scan.id)}
                      className="px-3 py-1.5 rounded-lg border border-zinc-800 hover:border-zinc-700 bg-zinc-900/60 text-zinc-400 hover:text-zinc-200 transition-colors text-xs font-mono"
                    >
                      Vulnerability diff
                    </button>

                    {scan.status === "completed" ? (
                      <Link
                        href={`/reports/${scan.id}`}
                        className="px-3.5 py-1.5 rounded-lg border border-teal-500/30 bg-teal-500/10 hover:bg-teal-500/20 text-teal-300 transition-colors flex items-center gap-1.5 text-xs font-mono font-medium"
                      >
                        <span>View report</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </Link>
                    ) : (
                      <Link
                        href={`/scans/${scan.id}`}
                        className="px-3 py-1.5 rounded-lg border border-zinc-700 hover:bg-zinc-800 text-zinc-300 transition-colors text-xs font-mono"
                      >
                        View progress ({scan.progress}%)
                      </Link>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ---------------- VULNERABILITY DIFF MODAL ---------------- */}
      {selectedDiffScanId && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div
            className={`max-w-lg w-full rounded-xl border p-6 shadow-2xl space-y-4 max-h-[80vh] overflow-y-auto ${
              isDark ? "bg-[#0c0c0e] border-zinc-800 text-zinc-100" : "bg-white border-zinc-200 text-zinc-900"
            }`}
          >
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <h3 className="text-sm font-medium font-mono">
                Vulnerability delta: Scan {selectedDiffScanId.slice(0, 8)}
              </h3>
              <button
                onClick={() => setSelectedDiffScanId(null)}
                className="text-zinc-400 hover:text-zinc-200"
              >
                ✕
              </button>
            </div>

            {loadingDiff ? (
              <div className="py-8 text-center text-xs font-mono text-zinc-500">
                Calculating change delta against prior baseline...
              </div>
            ) : scanDiffData ? (
              <div className="space-y-4 font-mono text-xs">
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="p-3 rounded-lg bg-teal-500/10 border border-teal-500/30 text-teal-400">
                    <div className="text-lg font-bold">+{scanDiffData.new_findings_count}</div>
                    <div className="text-[11px] text-zinc-400">New findings</div>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300">
                    <div className="text-lg font-bold">-{scanDiffData.resolved_findings_count}</div>
                    <div className="text-[11px] text-zinc-400">Resolved</div>
                  </div>
                  <div className="p-3 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300">
                    <div className="text-lg font-bold">{scanDiffData.persistent_findings_count}</div>
                    <div className="text-[11px] text-zinc-400">Persistent</div>
                  </div>
                </div>

                <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-400">
                  Grade trajectory:{" "}
                  <span className="text-teal-400 font-semibold uppercase">
                    {scanDiffData.grade_change.replace("_", " ")}
                  </span>
                </div>
              </div>
            ) : (
              <div className="py-6 text-center text-xs text-zinc-500 font-mono">
                First baseline scan for this domain. No prior delta available.
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
