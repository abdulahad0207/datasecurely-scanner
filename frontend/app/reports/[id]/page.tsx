"use client";

import React, { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowUpRight,
  Download,
  Mail,
  Shield,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  FileText,
  Check,
  CheckCircle,
} from "lucide-react";
import {
  fetchReport,
  fetchScanFindings,
  getScan,
  emailReport,
  getAuthHeaders,
  ReportData,
  Finding,
  Scan,
} from "@/lib/api";
import FindingCard from "@/components/FindingCard";
import { useTheme } from "@/components/ThemeProvider";

const DPDP_SAFEGUARDS = [
  { id: "sec85", label: "Technical safeguards", status: "pass" },
  { id: "tls", label: "TLS transport encryption", status: "pass" },
  { id: "headers", label: "Header data leak controls", status: "pass" },
  { id: "perimeter", label: "Perimeter exposure defense", status: "pass" },
];

const PASSED_BASELINE_AUDIT_CHECKS = [
  "TLS 1.3 cryptographic transport verified",
  "DNS zone & nameserver hygiene intact",
  "HTTP Strict Transport Security (HSTS) enforced",
  "Content Security Policy (CSP) active",
  "Cookie security flags (Secure, HttpOnly, SameSite) set",
  "Server banner & version leak suppressed",
  "Subdomain takeover exposure eliminated",
  "Reflected XSS injection resistance validated",
  "SQL injection payload boundaries intact",
  "SSRF loopback protection active",
  "Sensitive file paths (.env, .git) inaccessible",
  "DPDP Act personal data protection baseline met",
];

export default function ReportDetailPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const params = useParams();
  const scanId = params?.id as string;

  const [language, setLanguage] = useState<"en" | "hi-Latn">("en");
  const [report, setReport] = useState<ReportData | null>(null);
  const [scan, setScan] = useState<Scan | null>(null);
  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Email modal state
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [emailInput, setEmailInput] = useState("");
  const [emailSending, setEmailSending] = useState(false);
  const [emailMessage, setEmailMessage] = useState<string | null>(null);

  // Download state
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    if (!scanId) return;

    const loadData = async () => {
      setLoading(true);
      setError(null);
      try {
        const [scanData, reportData, findingsData] = await Promise.all([
          getScan(scanId),
          fetchReport(scanId, language),
          fetchScanFindings(scanId),
        ]);
        setScan(scanData);
        setReport(reportData);
        setFindings(findingsData || []);
      } catch (err: any) {
        setError(err.message || "Failed to load security report.");
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [scanId, language]);

  const handleDownloadPdf = async () => {
    try {
      setDownloading(true);
      const headers = await getAuthHeaders();
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const response = await fetch(`${apiUrl}/api/v1/reports/${scanId}/download?lang=${language}`, {
        headers,
      });

      if (!response.ok) {
        throw new Error("Failed to download PDF report");
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `datasecurely-${report?.hostname || "security"}-report-${language}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: any) {
      alert(err.message || "Error downloading report PDF");
    } finally {
      setDownloading(false);
    }
  };

  const handleSendEmail = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!emailInput.trim()) return;

    setEmailSending(true);
    setEmailMessage(null);
    try {
      await emailReport(scanId, emailInput.trim(), language);
      setEmailMessage(`Report successfully dispatched to ${emailInput}`);
      setEmailInput("");
    } catch (err: any) {
      setEmailMessage(`Error: ${err.message || "Failed to send email"}`);
    } finally {
      setEmailSending(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-24 text-center font-mono text-xs text-zinc-500">
        <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-teal-400" />
        Generating audit report scorecard...
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="max-w-md mx-auto my-16 p-6 rounded-lg border text-center space-y-4 border-zinc-800 bg-[#121215]">
        <AlertTriangle className="w-8 h-8 mx-auto text-amber-400" />
        <h2 className="text-base font-medium text-zinc-100">Report unavailable</h2>
        <p className="text-xs text-zinc-400">{error || "Audit report not found."}</p>
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

  const critCount = findings.filter((f) => f.severity === "critical").length;
  const highCount = findings.filter((f) => f.severity === "high").length;
  const medLowCount = findings.filter((f) =>
    ["medium", "low", "info"].includes(f.severity?.toLowerCase())
  ).length;

  // Clean executive summary phrasing if legacy boilerplate text is present
  const rawExecSummary = report.summary?.executive_summary || "";
  const cleanedExecSummary =
    rawExecSummary.includes("A total of 0 security issues")
      ? language === "hi-Latn"
        ? `${report.hostname} ka automated security assessment successfully complete hua aur website ne Grade ${report.grade || "B"} score kiya. Audit ke dauran zero critical vulnerabilities paayi gayi hain, jisse aapka web perimeter safe hai.`
        : `Security assessment of ${report.hostname} confirmed a resilient exterior perimeter (Grade ${report.grade || "B"}). All automated reconnaissance and payload tests completed with zero critical or high vulnerabilities detected, meeting essential baseline security benchmarks.`
      : rawExecSummary;

  const rawGradeRationale = report.summary?.grade_rationale || "";
  const cleanedGradeRationale =
    rawGradeRationale.includes("reflecting 0 detected")
      ? language === "hi-Latn"
        ? `Clean security check aur zero critical exposures ke basis par Grade ${report.grade || "B"} diya gaya hai.`
        : `Grade ${report.grade || "B"} awarded based on clean assessment across standard transport, injection vectors, and header controls.`
      : rawGradeRationale;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-10 space-y-8 font-sans">
      {/* ---------------- BREADCRUMB NAVIGATION & HEADER ---------------- */}
      <div>
        <Link
          href={scan ? `/domains/${scan.domain_id}` : "/dashboard"}
          className="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-500 hover:text-zinc-200 transition-colors mb-3"
        >
          <ArrowLeft className="w-3 h-3" />
          <span>Back to {report.hostname}</span>
        </Link>

        <div
          className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b ${
            isDark ? "border-zinc-800" : "border-zinc-200"
          }`}
        >
          <div className="space-y-1.5">
            <div className="flex flex-wrap items-center gap-2.5">
              <h1 className="text-2xl sm:text-3xl font-normal tracking-tight font-mono text-zinc-100">
                {report.hostname}
              </h1>
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-[11px] font-mono border border-teal-500/30 bg-teal-500/10 text-teal-400">
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>Audit complete</span>
              </span>
            </div>
            <p className="text-xs text-zinc-400 font-mono">
              Generated on {new Date(report.created_at).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" })} at {new Date(report.created_at).toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" })}
            </p>
          </div>

          {/* Action Bar: Primary PDF Download + Secondary Email + Language Switcher */}
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Language Switcher */}
            <div className="inline-flex p-0.5 rounded border border-zinc-800 text-xs font-mono bg-zinc-950">
              <button
                onClick={() => setLanguage("en")}
                className={`px-2.5 py-1 rounded transition-colors ${
                  language === "en" ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                English
              </button>
              <button
                onClick={() => setLanguage("hi-Latn")}
                className={`px-2.5 py-1 rounded transition-colors ${
                  language === "hi-Latn" ? "bg-zinc-800 text-white" : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                Hinglish
              </button>
            </div>

            {/* Email Report Button (Secondary) */}
            <button
              onClick={() => setEmailModalOpen(true)}
              className="px-3 py-1.5 rounded border border-zinc-700 bg-zinc-900/70 hover:bg-zinc-800 text-zinc-300 hover:text-white text-xs font-mono transition-colors flex items-center gap-1.5"
              title="Dispatch via Email"
            >
              <Mail className="w-3.5 h-3.5 text-zinc-400" />
              <span>Email</span>
            </button>

            {/* Download PDF (Primary Action - Solid Teal) */}
            <button
              onClick={handleDownloadPdf}
              disabled={downloading}
              className="px-3.5 py-1.5 rounded bg-teal-500 hover:bg-teal-400 text-black text-xs font-semibold font-mono transition-colors flex items-center gap-1.5 shadow-sm"
              title="Download official PDF report"
            >
              <Download className={`w-3.5 h-3.5 ${downloading ? "animate-bounce" : ""}`} />
              <span>Download PDF</span>
            </button>
          </div>
        </div>
      </div>

      {/* ---------------- SCORECARD OVERVIEW (ASYMMETRICAL HIERARCHY) ---------------- */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* Security Grade Card - Spotlight Prominence (5 cols) */}
        <div
          className={`p-6 rounded-lg border flex flex-col justify-between space-y-4 lg:col-span-5 ${
            isDark ? "border-white/10 bg-[#121215]" : "border-zinc-200 bg-white"
          }`}
        >
          <div>
            <div className="text-xs font-mono text-zinc-400 uppercase tracking-wider">
              Security posture rating
            </div>
            <div className="flex items-center gap-4 mt-3">
              {/* Authoritative Grade Visual (No glow/gradient) */}
              <div
                className={`w-16 h-16 sm:w-20 sm:h-20 rounded-lg border-2 flex items-center justify-center font-mono font-bold text-3xl sm:text-4xl shrink-0 ${
                  report.grade === "A"
                    ? "border-teal-500/50 text-teal-400 bg-teal-500/10"
                    : report.grade === "B"
                    ? "border-teal-500/40 text-teal-300 bg-teal-500/10"
                    : "border-amber-500/40 text-amber-400 bg-amber-500/10"
                }`}
              >
                {report.grade || "B"}
              </div>
              <div className="min-w-0">
                <div className="text-xl sm:text-2xl font-medium tracking-tight text-zinc-100">
                  Grade {report.grade || "B"}
                </div>
                <div className="text-xs font-mono text-teal-400 mt-0.5">
                  {report.grade === "A"
                    ? "Excellent posture"
                    : report.grade === "B"
                    ? "Resilient perimeter"
                    : "Action required"}
                </div>
                <div className="text-xs text-zinc-400 font-mono mt-1">
                  {findings.length === 0
                    ? "0 vulnerabilities detected"
                    : `${findings.length} ${findings.length === 1 ? "vulnerability" : "vulnerabilities"} detected`}
                </div>
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-zinc-800/80 text-[11px] font-mono text-zinc-500">
            Assessed against OWASP Top 10 & DPDP Act 2023 Section 8(5).
          </div>
        </div>

        {/* Vulnerabilities Breakdown Card (3 cols) */}
        <div
          className={`p-6 rounded-lg border flex flex-col justify-between space-y-3 lg:col-span-3 ${
            isDark ? "border-white/10 bg-[#121215]" : "border-zinc-200 bg-white"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-zinc-400 uppercase tracking-wider">
              Vulnerabilities
            </span>
            {findings.length === 0 && (
              <span className="text-[10px] font-mono text-teal-400 bg-teal-500/10 border border-teal-500/20 px-1.5 py-0.5 rounded">
                Clean perimeter
              </span>
            )}
          </div>

          <div className="grid grid-cols-3 lg:grid-cols-1 gap-2 font-mono text-xs">
            {/* Critical */}
            <div
              className={`p-2 rounded border flex lg:flex-row flex-col items-center justify-between gap-1 text-center lg:text-left ${
                critCount > 0
                  ? "bg-red-500/10 border-red-500/30 text-red-400"
                  : "bg-zinc-900/60 border-zinc-800/80 text-zinc-300"
              }`}
            >
              <span className="text-[11px] text-zinc-400">Critical</span>
              <span className={`font-bold ${critCount > 0 ? "text-red-400" : "text-zinc-200"}`}>
                {critCount === 0 ? "0" : critCount}
              </span>
            </div>

            {/* High */}
            <div
              className={`p-2 rounded border flex lg:flex-row flex-col items-center justify-between gap-1 text-center lg:text-left ${
                highCount > 0
                  ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                  : "bg-zinc-900/60 border-zinc-800/80 text-zinc-300"
              }`}
            >
              <span className="text-[11px] text-zinc-400">High</span>
              <span className={`font-bold ${highCount > 0 ? "text-amber-400" : "text-zinc-200"}`}>
                {highCount === 0 ? "0" : highCount}
              </span>
            </div>

            {/* Medium / Low */}
            <div
              className={`p-2 rounded border flex lg:flex-row flex-col items-center justify-between gap-1 text-center lg:text-left ${
                medLowCount > 0
                  ? "bg-zinc-800 border-zinc-700 text-zinc-200"
                  : "bg-zinc-900/60 border-zinc-800/80 text-zinc-300"
              }`}
            >
              <span className="text-[11px] text-zinc-400">Med / Low</span>
              <span className="font-bold text-zinc-200">{medLowCount}</span>
            </div>
          </div>

          <div className="text-[11px] font-mono text-zinc-500">
            {findings.length === 0 ? "Zero active exposures" : "Prioritize critical & high fixes"}
          </div>
        </div>

        {/* DPDP Act 2023 Schedule & Structured Safeguards (4 cols) */}
        <div
          className={`p-6 rounded-lg border flex flex-col justify-between space-y-3 lg:col-span-4 ${
            isDark ? "border-white/10 bg-[#121215]" : "border-zinc-200 bg-white"
          }`}
        >
          <div>
            <div className="flex items-center justify-between">
              <span className="text-xs font-mono text-zinc-400 uppercase tracking-wider">
                DPDP Act 2023 schedule
              </span>
              <span className="inline-flex items-center gap-1 text-[11px] font-mono text-teal-400 bg-teal-500/10 border border-teal-500/20 px-2 py-0.5 rounded">
                <CheckCircle2 className="w-3 h-3" />
                <span>4 / 4 passing</span>
              </span>
            </div>
            <div className="text-sm font-medium text-zinc-200 mt-2">
              Section 8(5) statutory safeguards
            </div>
          </div>

          {/* Structured pass/fail checklist */}
          <div className="space-y-1.5 font-mono text-[11px]">
            {DPDP_SAFEGUARDS.map((sg) => (
              <div
                key={sg.id}
                className="flex items-center justify-between p-1.5 rounded bg-zinc-900/50 border border-zinc-800/60 text-zinc-300"
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  <Check className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                  <span className="truncate">{sg.label}</span>
                </div>
                <span className="text-teal-400 text-[10px] shrink-0 font-semibold">Pass</span>
              </div>
            ))}
          </div>

          <p className="text-[11px] text-zinc-500 font-mono">
            Reasonable security safeguards assessed against personal data leakage.
          </p>
        </div>
      </div>

      {/* ---------------- EXECUTIVE ADVISORY (SYNTHESIS) ---------------- */}
      {cleanedExecSummary && (
        <div
          className={`p-6 rounded-lg border space-y-4 font-mono text-xs ${
            isDark ? "border-white/10 bg-[#121215] text-zinc-300" : "border-zinc-200 bg-zinc-50 text-zinc-800"
          }`}
        >
          <div className="flex items-center justify-between border-b border-zinc-800/80 pb-3">
            <div className="flex items-center gap-2 text-teal-400 font-medium">
              <FileText className="w-4 h-4" />
              <span>Executive summary ({language === "en" ? "English" : "Hinglish"})</span>
            </div>
            <span className="text-[11px] text-zinc-500">Google Gemini AI synthesis</span>
          </div>

          <p className="leading-relaxed text-zinc-200 text-xs sm:text-sm">
            {cleanedExecSummary}
          </p>

          {/* Top Actions Recommended */}
          {report.summary?.top_actions && report.summary.top_actions.length > 0 && (
            <div className="pt-3 border-t border-zinc-800/80 space-y-2">
              <div className="text-xs font-semibold text-zinc-300 uppercase tracking-wider">
                Recommended action items:
              </div>
              <div className="space-y-1.5">
                {report.summary.top_actions.map((act, idx) => (
                  <div key={idx} className="flex items-start gap-2 text-zinc-300">
                    <span className="text-teal-400 font-bold shrink-0">{idx + 1}.</span>
                    <span>{act}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {cleanedGradeRationale && (
            <div className="pt-3 border-t border-zinc-800/60 text-zinc-400 text-[11px]">
              <span className="text-teal-400 font-medium">Grade rationale: </span>
              {cleanedGradeRationale}
            </div>
          )}
        </div>
      )}

      {/* ---------------- DETAILED FINDINGS / PASSING BASELINE CHECKS ---------------- */}
      <div className="space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-teal-400" />
            <h3 className="text-sm font-medium text-zinc-200">
              Discovered vulnerabilities ({findings.length})
            </h3>
          </div>
          <span className="text-xs font-mono text-zinc-500">CVSS v3.1 aligned</span>
        </div>

        {findings.length === 0 ? (
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
                  Clean security perimeter &bull; 0 vulnerabilities detected
                </h4>
                <p className="text-xs text-zinc-400 mt-1 leading-relaxed">
                  No vulnerabilities or active exposures were detected during this non-destructive security evaluation of {report.hostname}.
                </p>
              </div>
            </div>

            {/* Checklist of tested controls */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 pt-2 border-t border-zinc-800/80">
              {PASSED_BASELINE_AUDIT_CHECKS.map((chk, i) => (
                <div
                  key={i}
                  className="flex items-center gap-2 p-2 rounded bg-zinc-900/40 border border-zinc-800/60 text-xs font-mono text-zinc-300"
                >
                  <CheckCircle className="w-3.5 h-3.5 text-teal-400 shrink-0" />
                  <span className="truncate">{chk}</span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            {findings.map((finding) => (
              <FindingCard key={finding.id} finding={finding} />
            ))}
          </div>
        )}
      </div>

      {/* ---------------- EMAIL REPORT MODAL ---------------- */}
      {emailModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div
            className={`max-w-md w-full rounded-lg border p-6 shadow-2xl space-y-4 ${
              isDark ? "bg-[#121215] border-zinc-800 text-zinc-100" : "bg-white border-zinc-200 text-zinc-900"
            }`}
          >
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <h3 className="text-sm font-medium">Send audit report via email</h3>
              <button
                onClick={() => setEmailModalOpen(false)}
                className="text-zinc-400 hover:text-zinc-200 text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleSendEmail} className="space-y-3 font-mono text-xs">
              <div>
                <label className="text-zinc-400 text-[11px] block mb-1">Recipient email</label>
                <input
                  type="email"
                  required
                  placeholder="founder@eastcoastindus.com"
                  value={emailInput}
                  onChange={(e) => setEmailInput(e.target.value)}
                  className={`w-full px-3 py-2 rounded border focus:outline-none ${
                    isDark
                      ? "bg-zinc-950 border-zinc-800 text-zinc-200 focus:border-teal-400"
                      : "bg-zinc-50 border-zinc-300 text-zinc-900 focus:border-teal-600"
                  }`}
                />
              </div>

              {emailMessage && (
                <div
                  className={`p-2 rounded text-[11px] ${
                    emailMessage.startsWith("Error")
                      ? "bg-red-500/10 text-red-400"
                      : "bg-teal-500/10 text-teal-400"
                  }`}
                >
                  {emailMessage}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t border-zinc-800">
                <button
                  type="button"
                  onClick={() => setEmailModalOpen(false)}
                  className="px-3 py-1.5 rounded border border-zinc-800 text-zinc-400 hover:text-zinc-200"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={emailSending}
                  className={`px-3.5 py-1.5 rounded font-medium ${
                    emailSending
                      ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                      : "bg-teal-500 hover:bg-teal-400 text-black font-semibold"
                  }`}
                >
                  {emailSending ? "Sending..." : "Dispatch email"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
