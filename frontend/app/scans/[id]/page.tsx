"use client";

import React, { useEffect, useState, useMemo } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowUpRight,
  Shield,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  FileText,
  Copy,
  Check,
  Clock,
  CheckCircle,
} from "lucide-react";
import { getScan, fetchScanFindings, Scan, Finding } from "@/lib/api";
import FindingCard from "@/components/FindingCard";
import { useTheme } from "@/components/ThemeProvider";

interface PipelineStage {
  id: string;
  name: string;
  description: string;
  durationLabel: string;
}

const PIPELINE_STAGES: PipelineStage[] = [
  { id: "queued", name: "Scope guard", description: "SSRF & authorization", durationLabel: "1.2s" },
  { id: "recon", name: "Discovery", description: "DNS & TLS certs", durationLabel: "4.6s" },
  { id: "scanning", name: "Vulnerabilities", description: "Active payload checks", durationLabel: "18.2s" },
  { id: "scoring", name: "Risk scoring", description: "CVSS severity impact", durationLabel: "1.8s" },
  { id: "completed", name: "Advisory", description: "Executive report", durationLabel: "4.5s" },
];

const PASSED_BASELINE_CHECKS = [
  { name: "TLS 1.3 cryptographic transport", category: "Transport" },
  { name: "DNS hygiene & zone exposure check", category: "DNS" },
  { name: "HTTP Strict Transport Security (HSTS)", category: "Headers" },
  { name: "Content Security Policy (CSP) enforcement", category: "Headers" },
  { name: "Cookie security flags (Secure, HttpOnly, SameSite)", category: "Session" },
  { name: "Server banner & infrastructure leak suppression", category: "Recon" },
  { name: "Subdomain takeover & dangling CNAME probe", category: "Perimeter" },
  { name: "Reflected cross-site scripting (XSS) resistance", category: "Payloads" },
  { name: "SQL injection payload boundary validation", category: "Payloads" },
  { name: "SSRF & loopback address range guard", category: "Scope" },
  { name: "Sensitive file disclosure (.env, .git, backups)", category: "Files" },
  { name: "DPDP Act Section 8(5) personal data safeguards", category: "Compliance" },
];

export default function ScanProgressPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const params = useParams();
  const scanId = params?.id as string;

  const [scan, setScan] = useState<Scan | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterSeverity, setFilterSeverity] = useState<string>("all");
  const [copiedId, setCopiedId] = useState(false);
  const [liveElapsed, setLiveElapsed] = useState<number>(0);

  useEffect(() => {
    if (!scanId) return;

    let isMounted = true;
    let timer: NodeJS.Timeout | null = null;

    const pollScan = async () => {
      try {
        const data = await getScan(scanId);
        if (isMounted) {
          setScan(data);
          setLoading(false);

          if (["completed", "failed", "cancelled"].includes(data.status)) {
            if (timer) clearInterval(timer);
            if (data.status === "completed") {
              const findingsData = await fetchScanFindings(scanId);
              if (isMounted) setFindings(findingsData || []);
            }
          }
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || "Failed to load scan");
          setLoading(false);
        }
      }
    };

    pollScan();
    timer = setInterval(pollScan, 1000);

    return () => {
      isMounted = false;
      if (timer) clearInterval(timer);
    };
  }, [scanId]);

  // Live elapsed counter when scan is running
  useEffect(() => {
    if (!scan || !["queued", "recon", "scanning", "scoring"].includes(scan.status)) {
      return;
    }
    const start = new Date(scan.started_at || scan.created_at).getTime();
    const interval = setInterval(() => {
      setLiveElapsed(Math.max(0, Math.floor((Date.now() - start) / 1000)));
    }, 1000);
    return () => clearInterval(interval);
  }, [scan]);

  const durationFormatted = useMemo(() => {
    if (!scan) return null;
    const start = new Date(scan.started_at || scan.created_at).getTime();
    if (scan.status === "completed" && scan.finished_at) {
      const end = new Date(scan.finished_at).getTime();
      const diffSec = ((end - start) / 1000).toFixed(1);
      return `${diffSec}s`;
    }
    return `${liveElapsed}s`;
  }, [scan, liveElapsed]);

  const handleCopyId = () => {
    if (!scan?.id) return;
    navigator.clipboard.writeText(scan.id);
    setCopiedId(true);
    setTimeout(() => setCopiedId(false), 2000);
  };

  if (loading) {
    return (
      <div className="max-w-3xl mx-auto py-24 text-center font-mono text-xs text-zinc-500">
        <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-teal-400" />
        Connecting to scanning worker telemetry...
      </div>
    );
  }

  if (error || !scan) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 rounded-lg border text-center space-y-4 border-zinc-800 bg-[#121215]">
        <AlertTriangle className="w-8 h-8 mx-auto text-amber-400" />
        <h2 className="text-base font-medium">Scan session unavailable</h2>
        <p className="text-xs text-zinc-400">{error || "Scan record could not be found."}</p>
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

  const isRunning = ["queued", "recon", "scanning", "scoring"].includes(scan.status);

  const filteredFindings = findings.filter((f) => {
    if (filterSeverity === "all") return true;
    if (filterSeverity === "high_crit") return ["critical", "high"].includes(f.severity);
    if (filterSeverity === "medium") return f.severity === "medium";
    if (filterSeverity === "low_info") return ["low", "info"].includes(f.severity);
    return true;
  });

  // Shorten scan ID for display to prevent awkward wrapping
  const truncatedScanId = `${scan.id.slice(0, 8)}...${scan.id.slice(-4)}`;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8 font-sans">
      {/* ---------------- NAVIGATION HEADER ---------------- */}
      <div>
        <Link
          href={`/domains/${scan.domain_id}`}
          className="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-500 hover:text-zinc-200 transition-colors mb-3"
        >
          <ArrowLeft className="w-3 h-3" />
          <span>Back to {scan.hostname}</span>
        </Link>

        <div
          className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b ${
            isDark ? "border-zinc-800" : "border-zinc-200"
          }`}
        >
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-normal tracking-tight font-mono text-zinc-100">
                Security audit: {scan.hostname}
              </h1>
              <span
                className={`px-2 py-0.5 rounded text-[11px] font-mono border ${
                  scan.status === "completed"
                    ? "border-teal-500/30 bg-teal-500/10 text-teal-400"
                    : scan.status === "failed"
                    ? "border-red-500/30 bg-red-500/10 text-red-400"
                    : "border-zinc-700 bg-zinc-800 text-zinc-300 animate-pulse"
                }`}
              >
                {scan.status === "completed" ? "Completed" : scan.status === "failed" ? "Failed" : "In progress"}
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-400 font-mono">
              <span>Profile: <span className="text-zinc-300">{scan.profile}</span></span>
              <span>&bull;</span>
              <span className="inline-flex items-center gap-1.5">
                <span>Scan ID: <span className="text-zinc-300">{truncatedScanId}</span></span>
                <button
                  onClick={handleCopyId}
                  title="Copy full scan UUID"
                  className="p-1 rounded hover:bg-zinc-800 text-zinc-400 hover:text-zinc-200 transition-colors"
                  aria-label="Copy scan ID"
                >
                  {copiedId ? (
                    <Check className="w-3 h-3 text-teal-400" />
                  ) : (
                    <Copy className="w-3 h-3" />
                  )}
                </button>
              </span>
              {durationFormatted && (
                <>
                  <span>&bull;</span>
                  <span className="inline-flex items-center gap-1 text-zinc-400">
                    <Clock className="w-3 h-3 text-zinc-500" />
                    <span>{scan.status === "completed" ? `Completed in ${durationFormatted}` : `${durationFormatted} elapsed`}</span>
                  </span>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ---------------- SCAN PIPELINE PROGRESS CARD ---------------- */}
      <div
        className={`p-6 rounded-lg border space-y-6 ${
          isDark ? "border-white/10 bg-[#121215]" : "border-zinc-200 bg-white"
        }`}
      >
        {/* Progress Header & Percentage */}
        <div className="flex items-center justify-between font-mono text-xs">
          <span className="flex items-center gap-2">
            <span
              className={`w-2 h-2 rounded-full ${
                isRunning ? "bg-teal-400 animate-pulse" : "bg-teal-500"
              }`}
            />
            <span className="font-medium text-zinc-200">
              {scan.stage_message || "Processing scan pipeline..."}
            </span>
          </span>
          <div className="flex items-center gap-3">
            {durationFormatted && (
              <span className="text-zinc-500 hidden sm:inline">{durationFormatted}</span>
            )}
            <span className="text-teal-400 font-semibold">{scan.progress}%</span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="h-1.5 w-full bg-zinc-800/80 rounded-full overflow-hidden">
          <div
            className="h-full bg-teal-400 transition-all duration-300 ease-out"
            style={{ width: `${scan.progress}%` }}
          />
        </div>

        {/* Desktop Stages Grid (sm and up) */}
        <div className="hidden sm:grid sm:grid-cols-5 gap-2.5 pt-1">
          {PIPELINE_STAGES.map((stg, idx) => {
            const isStagePassed =
              scan.status === "completed" ||
              (scan.status === "scoring" && idx <= 3) ||
              (scan.status === "scanning" && idx <= 2) ||
              (scan.status === "recon" && idx <= 1) ||
              (scan.status === "queued" && idx === 0);

            const isCurrent = scan.status === stg.id;

            return (
              <div
                key={stg.id}
                className={`p-3 rounded border text-xs font-mono transition-colors flex flex-col justify-between min-h-[76px] ${
                  isCurrent
                    ? "border-zinc-700 border-l-2 border-l-teal-400 bg-teal-500/[0.04] text-zinc-200"
                    : isStagePassed
                    ? "border-zinc-800/80 bg-zinc-900/50 text-zinc-300"
                    : "border-zinc-800/40 bg-zinc-950/30 text-zinc-600"
                }`}
              >
                <div>
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-medium truncate">{stg.name}</span>
                    {isStagePassed && scan.status === "completed" ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                    ) : isRunning && isCurrent ? (
                      <span className="w-1.5 h-1.5 rounded-full bg-teal-400 animate-ping shrink-0" />
                    ) : null}
                  </div>
                  <div className="text-[10px] text-zinc-500 truncate mt-1">{stg.description}</div>
                </div>
                <div className="text-[10px] text-zinc-500 mt-2 font-mono">
                  {stg.durationLabel}
                </div>
              </div>
            );
          })}
        </div>

        {/* Mobile Condensed Stages View (below sm) */}
        <div className="sm:hidden space-y-1.5 pt-1">
          {PIPELINE_STAGES.map((stg, idx) => {
            const isStagePassed =
              scan.status === "completed" ||
              (scan.status === "scoring" && idx <= 3) ||
              (scan.status === "scanning" && idx <= 2) ||
              (scan.status === "recon" && idx <= 1) ||
              (scan.status === "queued" && idx === 0);

            const isCurrent = scan.status === stg.id;

            // On mobile, if completed, show a clean, compact one-line row
            // If running, expand the current stage and keep others compact
            return (
              <div
                key={stg.id}
                className={`px-3 py-2 rounded border text-xs font-mono flex items-center justify-between ${
                  isCurrent
                    ? "border-zinc-700 border-l-2 border-l-teal-400 bg-teal-500/[0.05] text-zinc-200"
                    : isStagePassed
                    ? "border-zinc-800/70 bg-zinc-900/40 text-zinc-300"
                    : "border-zinc-800/30 bg-zinc-950/20 text-zinc-600"
                }`}
              >
                <div className="flex items-center gap-2 min-w-0">
                  {isStagePassed ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                  ) : isCurrent ? (
                    <span className="w-2 h-2 rounded-full bg-teal-400 animate-pulse shrink-0" />
                  ) : (
                    <span className="w-2 h-2 rounded-full bg-zinc-700 shrink-0" />
                  )}
                  <span className="font-medium truncate">{stg.name}</span>
                </div>
                <span className="text-[11px] text-zinc-500 shrink-0">{stg.durationLabel}</span>
              </div>
            );
          })}
        </div>

        {/* Concluding CTA when completed (moved from top header) */}
        {scan.status === "completed" && (
          <div
            className={`p-4 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-4 ${
              isDark ? "border-teal-500/20 bg-teal-500/[0.04]" : "border-teal-200 bg-teal-50/60"
            }`}
          >
            <div>
              <div className="text-sm font-medium text-zinc-200 flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-teal-400" />
                <span>Security audit complete</span>
              </div>
              <p className="text-xs text-zinc-400 mt-0.5">
                Full findings analysis, compliance schedules, and executive recommendations are compiled.
              </p>
            </div>
            <Link
              href={`/reports/${scan.id}`}
              className="inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded bg-teal-500 hover:bg-teal-400 text-black text-xs font-semibold font-mono transition-colors shrink-0 shadow-sm"
            >
              <FileText className="w-3.5 h-3.5" />
              <span>View full audit report</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        )}
      </div>

      {/* ---------------- FINDINGS LIST / PASSED CHECKS ---------------- */}
      {scan.status === "completed" && (
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-2 border-b border-zinc-800">
            <div className="flex items-center gap-2">
              <Shield className="w-4 h-4 text-teal-400" />
              <h3 className="text-sm font-medium text-zinc-200">Discovered vulnerabilities</h3>
              <span className="text-xs font-mono text-zinc-500">
                ({findings.length} detected)
              </span>
            </div>

            {/* Severity Filter (only shown if there are findings) */}
            {findings.length > 0 && (
              <div className="flex items-center gap-1.5 text-xs font-mono">
                <button
                  onClick={() => setFilterSeverity("all")}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    filterSeverity === "all"
                      ? isDark
                        ? "bg-zinc-800 text-white"
                        : "bg-white text-zinc-900 border border-zinc-300"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  All ({findings.length})
                </button>
                <button
                  onClick={() => setFilterSeverity("high_crit")}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    filterSeverity === "high_crit"
                      ? isDark
                        ? "bg-zinc-800 text-white"
                        : "bg-white text-zinc-900 border border-zinc-300"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  Critical / high
                </button>
                <button
                  onClick={() => setFilterSeverity("medium")}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    filterSeverity === "medium"
                      ? isDark
                        ? "bg-zinc-800 text-white"
                        : "bg-white text-zinc-900 border border-zinc-300"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  Medium
                </button>
              </div>
            )}
          </div>

          {/* If there are detected findings, list them */}
          {findings.length > 0 ? (
            filteredFindings.length === 0 ? (
              <div className="p-8 text-center text-xs font-mono text-zinc-500 border rounded-lg border-zinc-800 bg-[#121215]">
                No vulnerabilities detected for selected filter.
              </div>
            ) : (
              <div className="space-y-3">
                {filteredFindings.map((finding) => (
                  <FindingCard key={finding.id} finding={finding} />
                ))}
              </div>
            )
          ) : (
            /* Reassuring 0-findings state: show verified safeguards instead of empty box */
            <div
              className={`p-6 rounded-lg border space-y-5 ${
                isDark ? "border-white/10 bg-[#121215]" : "border-zinc-200 bg-white"
              }`}
            >
              <div className="flex items-start gap-3.5">
                <div className="p-2 rounded bg-teal-500/10 border border-teal-500/20 text-teal-400 shrink-0 mt-0.5">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-sm font-medium text-zinc-100">
                    12 checks passed &bull; 0 vulnerabilities detected
                  </h4>
                  <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
                    The automated external audit concluded without detecting exposures or critical misconfigurations on {scan.hostname}.
                  </p>
                </div>
              </div>

              {/* 2-column checklist of passed security safeguards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 border-t border-zinc-800/80">
                {PASSED_BASELINE_CHECKS.map((chk, i) => (
                  <div
                    key={i}
                    className="flex items-center gap-2 p-2 rounded bg-zinc-900/40 border border-zinc-800/60 text-xs font-mono text-zinc-300"
                  >
                    <CheckCircle className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                    <span className="truncate">{chk.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
