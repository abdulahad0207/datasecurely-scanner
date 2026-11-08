"use client";

import React, { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Globe,
  ArrowUpRight,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Info,
  X,
  FileText,
  Activity,
  Layers,
  Code2,
  Copy,
  Check,
  RefreshCw,
  Lock,
} from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";
import { supabase } from "@/lib/supabase";
import { fetchDomains, createDomain, startScan } from "@/lib/api";

export default function HomePage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const router = useRouter();

  const [domainInput, setDomainInput] = useState("");
  const [isAuditing, setIsAuditing] = useState(false);
  const [auditMessage, setAuditMessage] = useState<string | null>(null);
  const [copiedSnippet, setCopiedSnippet] = useState(false);

  // -------------------------------------------------------------
  // Audit Action: Authenticate & Verify Domain Ownership
  // -------------------------------------------------------------
  const handleAudit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const raw = domainInput.trim();
    if (!raw) return;

    const cleanHost = raw
      .replace(/^https?:\/\//i, "")
      .replace(/\/.*$/, "")
      .toLowerCase();

    setIsAuditing(true);
    setAuditMessage("Checking session and domain authorization...");

    try {
      // 1. Check Authentication Status
      const { data } = await supabase.auth.getSession();
      const hasDevToken =
        typeof window !== "undefined" &&
        Boolean(localStorage.getItem("dev_mock_token"));
      const isAuthed = Boolean(data?.session || hasDevToken);

      if (!isAuthed) {
        if (typeof window !== "undefined") {
          localStorage.setItem("pending_audit_domain", cleanHost);
        }
        router.push(`/login?domain=${encodeURIComponent(cleanHost)}`);
        return;
      }

      // 2. Authenticated: Fetch user's registered domains
      setAuditMessage("Checking domain verification status...");
      const domainsList = await fetchDomains();
      const existing = domainsList.find(
        (d) => d.hostname.toLowerCase() === cleanHost
      );

      if (!existing) {
        // Register target domain -> status: pending -> redirect to verification console
        setAuditMessage("Registering domain for ownership verification...");
        const newDomain = await createDomain(cleanHost);
        router.push(`/domains/${newDomain.id}`);
        return;
      }

      // Domain already registered: check status
      if (existing.status !== "verified") {
        setAuditMessage("Domain ownership pending. Redirecting to verification console...");
        router.push(`/domains/${existing.id}`);
        return;
      }

      // 3. Domain is verified: execute scan and navigate to live scan page
      setAuditMessage("Ownership confirmed. Initiating automated vulnerability audit...");
      const scan = await startScan(existing.id, "free");
      router.push(`/scans/${scan.id}`);
    } catch (err: any) {
      if (
        err.message?.includes("Authentication") ||
        err.message?.includes("sign in") ||
        err.message?.includes("401")
      ) {
        if (typeof window !== "undefined") {
          localStorage.setItem("pending_audit_domain", cleanHost);
        }
        router.push(`/login?domain=${encodeURIComponent(cleanHost)}`);
      } else {
        setAuditMessage(err.message || "Failed to process domain audit.");
        setIsAuditing(false);
      }
    }
  };

  const copyRemediationSnippet = (snippet: string) => {
    navigator.clipboard?.writeText(snippet);
    setCopiedSnippet(true);
    setTimeout(() => setCopiedSnippet(false), 2000);
  };

  return (
    <div className="space-y-16 py-8">
      {/* ---------------- HERO SECTION ---------------- */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 pt-8 pb-4 grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
        <div className="lg:col-span-7 space-y-6">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-zinc-500 font-medium">
              01 &mdash; Automated security scanner
            </span>
            <div className={`h-[1px] w-12 ${isDark ? "bg-zinc-800" : "bg-zinc-300"}`} />
          </div>

          <h1 className="text-4xl sm:text-5xl font-normal tracking-tight leading-[1.15]">
            Find security risks before they find you.
          </h1>

          <p
            className={`text-base sm:text-lg leading-relaxed max-w-lg font-light ${
              isDark ? "text-zinc-400" : "text-zinc-600"
            }`}
          >
            DataSecurely automates reconnaissance, TLS 1.3 verification, Content Security Policy audits, and DPDP Act 2023 compliance checks for verified web applications.
          </p>

          {/* Authenticated & Verified Scanner Form */}
          <form onSubmit={handleAudit} className="space-y-3 max-w-md pt-2">
            <div
              className={`p-1.5 rounded-lg border flex flex-col sm:flex-row gap-2 transition-all ${
                isDark
                  ? "border-zinc-800 bg-[#121215] focus-within:border-zinc-600"
                  : "border-zinc-300 bg-white focus-within:border-zinc-400 shadow-[0_1px_2px_rgba(0,0,0,0.04)]"
              }`}
            >
              <div className="flex items-center gap-2 px-2.5 py-1.5 sm:py-0 flex-1">
                <Globe
                  className={`w-4 h-4 shrink-0 ${isDark ? "text-zinc-500" : "text-zinc-400"}`}
                />
                <input
                  type="text"
                  required
                  value={domainInput}
                  onChange={(e) => setDomainInput(e.target.value)}
                  placeholder="example.com"
                  className="w-full bg-transparent text-sm font-mono focus:outline-none placeholder:text-zinc-500"
                />
              </div>
              <button
                type="submit"
                disabled={isAuditing}
                className={`px-4 py-2.5 sm:py-2 rounded text-xs font-mono font-medium flex items-center justify-center gap-1.5 transition-all ${
                  isAuditing
                    ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                    : isDark
                    ? "bg-teal-500 hover:bg-teal-400 text-black"
                    : "bg-teal-600 hover:bg-teal-500 text-white"
                }`}
              >
                <span>{isAuditing ? "Verifying..." : "Audit"}</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </div>

            {auditMessage && (
              <div className="text-xs font-mono text-teal-400 flex items-center gap-2">
                <RefreshCw className="w-3 h-3 animate-spin shrink-0" />
                <span>{auditMessage}</span>
              </div>
            )}

            {/* Softened Supporting Copy (Inline, not generic pill badges) */}
            <div className="text-xs text-zinc-500 font-mono space-y-1 pt-0.5">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-teal-400 shrink-0" />
                <span>Non-destructive perimeter inspection &bull; Mandatory ownership verification</span>
              </div>
              <div className="text-zinc-600 pl-3.5">
                Evaluates transport layers against Section 8(5) of the Digital Personal Data Protection Act, 2023.
              </div>
            </div>
          </form>
        </div>

        {/* Real Product Inspection Console (Replaces Idle 3D Canvas) */}
        <div className="lg:col-span-5 flex flex-col justify-center">
          <div
            className={`rounded-xl border transition-all overflow-hidden ${
              isDark
                ? "border-zinc-800 bg-[#121215] shadow-sm text-zinc-200"
                : "border-zinc-200 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.05)] text-zinc-800"
            }`}
          >
            {/* Console Header Bar */}
            <div
              className={`px-4 py-3 border-b flex items-center justify-between text-xs font-mono ${
                isDark ? "border-zinc-800/80 bg-zinc-950/70" : "border-zinc-100 bg-zinc-50"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-teal-400" />
                <span className="text-zinc-400">audit_telemetry</span>
                <span className="text-zinc-600">/</span>
                <span className="text-zinc-200 font-medium">eastcoastindus.com</span>
              </div>
              <span className="px-1.5 py-0.5 rounded text-[10px] font-mono border border-teal-500/30 bg-teal-500/10 text-teal-400">
                Verified
              </span>
            </div>

            {/* Telemetry Output Body */}
            <div className="p-4 space-y-3 font-mono text-xs">
              <div className="flex items-center justify-between pb-3 border-b border-zinc-800/60">
                <div>
                  <span className="text-zinc-500 block text-[11px]">Security posture</span>
                  <span className="text-xl font-normal tracking-tight text-zinc-100">Grade B</span>
                  <span className="text-zinc-500 text-[11px] ml-2">(6 findings detected)</span>
                </div>
                <div className="text-right">
                  <span className="text-zinc-500 block text-[11px]">DPDP Act 2023</span>
                  <span className="text-teal-400 font-medium">Section 8(5)</span>
                </div>
              </div>

              {/* Sample Real Scan Observations */}
              <div className="space-y-2 text-[11px]">
                <div className="flex items-center justify-between p-2 rounded bg-zinc-900/60 border border-zinc-800/60">
                  <div className="flex items-center gap-2 truncate pr-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                    <span className="text-zinc-300 truncate">Missing Content-Security-Policy</span>
                  </div>
                  <span className="text-zinc-500 shrink-0">CWE-693</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-zinc-900/60 border border-zinc-800/60">
                  <div className="flex items-center gap-2 truncate pr-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-yellow-400 shrink-0" />
                    <span className="text-zinc-300 truncate">HSTS max-age duration below 1 year</span>
                  </div>
                  <span className="text-zinc-500 shrink-0">CWE-523</span>
                </div>

                <div className="flex items-center justify-between p-2 rounded bg-zinc-900/60 border border-zinc-800/60">
                  <div className="flex items-center gap-2 truncate pr-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-teal-400 shrink-0" />
                    <span className="text-zinc-300 truncate">TLS 1.3 protocol handshake</span>
                  </div>
                  <span className="text-teal-400 shrink-0">Passed</span>
                </div>
              </div>
            </div>

            {/* Console Footer */}
            <div
              className={`px-4 py-2.5 border-t flex items-center justify-between text-[11px] font-mono text-zinc-500 ${
                isDark ? "border-zinc-800/80 bg-zinc-950/40" : "border-zinc-100 bg-zinc-50/50"
              }`}
            >
              <span className="flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-teal-400" />
                Scope guard enforced
              </span>
              <span>Worker: Redis + ARQ</span>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- ASYMMETRIC ARCHITECTURE PIPELINE ---------------- */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        <div className="flex items-center gap-3 mb-4">
          <span className="font-mono text-xs text-zinc-500 font-medium">
            02 &mdash; Architecture
          </span>
          <div className={`h-[1px] w-12 ${isDark ? "bg-zinc-800" : "bg-zinc-300"}`} />
        </div>

        <h2 className="text-2xl sm:text-3xl font-normal tracking-tight mb-2">
          Defensive cybersecurity pipeline
        </h2>
        <p className={`text-xs max-w-xl mb-8 ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
          Three discrete phases execute in sequence to provide comprehensive transport-layer verification without invasive payload delivery.
        </p>

        {/* Asymmetric 2-Column Grid (Varying Widths & Content Depth) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* Card 1: Detect (Reconnaissance) - 5 Columns */}
          <div
            className={`lg:col-span-5 p-6 rounded-lg border transition-colors flex flex-col justify-between ${
              isDark ? "border-zinc-800 bg-[#121215]" : "border-zinc-200 bg-white shadow-sm"
            }`}
          >
            <div>
              <div className="w-8 h-8 rounded border border-zinc-700/60 flex items-center justify-center font-mono text-xs mb-4 text-teal-400">
                01
              </div>
              <h3 className="text-base font-medium mb-1.5">Detect &mdash; Surface reconnaissance</h3>
              <p className={`text-xs leading-relaxed mb-4 ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
                Automated perimeter discovery mapped against your verified domain without invasive penetration techniques.
              </p>
            </div>

            <div className="space-y-1.5 font-mono text-[11px] pt-3 border-t border-zinc-800/60 text-zinc-400">
              <div className="flex items-center gap-2">
                <span className="text-teal-400">&bull;</span>
                <span>DNS TXT cryptographic verification</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-teal-400">&bull;</span>
                <span>TLS 1.3 handshakes & certificate validation</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-teal-400">&bull;</span>
                <span>HTTP security headers (HSTS, CSP, CORS)</span>
              </div>
            </div>
          </div>

          {/* Card 2: Analyze (Scoring & DPDP Act) - 7 Columns */}
          <div
            className={`lg:col-span-7 p-6 rounded-lg border transition-colors flex flex-col justify-between ${
              isDark ? "border-zinc-800 bg-[#121215]" : "border-zinc-200 bg-white shadow-sm"
            }`}
          >
            <div>
              <div className="w-8 h-8 rounded border border-zinc-700/60 flex items-center justify-center font-mono text-xs mb-4 text-teal-400">
                02
              </div>
              <h3 className="text-base font-medium mb-1.5">Analyze &mdash; Deterministic scoring & DPDP Act compliance</h3>
              <p className={`text-xs leading-relaxed mb-4 ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
                Findings are weighted deterministically against CVSS v3.1 impact matrices and mapped to the Indian Digital Personal Data Protection Act, 2023 mandate for reasonable data safeguards.
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-3 border-t border-zinc-800/60 font-mono text-[11px] text-zinc-400">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-teal-400">&bull;</span>
                  <span>Section 8(5) personal data safeguards</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-teal-400">&bull;</span>
                  <span>Deterministic A&ndash;F security score</span>
                </div>
              </div>
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-teal-400">&bull;</span>
                  <span>Bilingual advisory (English & Hinglish)</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-teal-400">&bull;</span>
                  <span>Regression diffing against prior scans</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ---------------- 03 SECURE & REMEDIATION BLUEPRINT SECTION ---------------- */}
      <section className="max-w-6xl mx-auto px-4 sm:px-6 py-6">
        <div
          className={`p-6 rounded-lg border ${
            isDark ? "border-zinc-800 bg-[#121215]" : "border-zinc-200 bg-white shadow-sm"
          }`}
        >
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
            <div>
              <div className="flex items-start gap-3 mb-1.5">
                <div className="w-5 h-5 rounded border border-zinc-700/60 flex items-center justify-center font-mono text-[10px] text-teal-400 shrink-0 mt-0.5">
                  03
                </div>
                <h3 className="text-base font-medium leading-snug">Secure &mdash; Automated remediation blueprint</h3>
              </div>
              <p className={`text-xs ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
                Drop-in security headers configuration for Caddy and Nginx reverse proxies to resolve identified misconfigurations immediately.
              </p>
            </div>

            <button
              onClick={() =>
                copyRemediationSnippet(
                  `header {\n  Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"\n  X-Content-Type-Options "nosniff"\n  X-Frame-Options "DENY"\n  Referrer-Policy "strict-origin-when-cross-origin"\n  Content-Security-Policy "default-src 'self'; script-src 'self'; frame-ancestors 'none';"\n}`
                )
              }
              className={`px-3 py-1.5 rounded text-xs font-mono border transition-colors flex items-center gap-1.5 shrink-0 ${
                isDark
                  ? "border-zinc-800 text-zinc-300 hover:text-white hover:border-zinc-700 bg-zinc-900"
                  : "border-zinc-300 text-zinc-800 hover:bg-zinc-50 bg-white"
              }`}
            >
              {copiedSnippet ? (
                <>
                  <Check className="w-3.5 h-3.5 text-teal-400" />
                  <span>Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3.5 h-3.5" />
                  <span>Copy Caddyfile directive</span>
                </>
              )}
            </button>
          </div>

          <pre
            className={`p-4 rounded border text-xs font-mono overflow-x-auto ${
              isDark ? "border-zinc-800 bg-zinc-950 text-zinc-300" : "border-zinc-200 bg-zinc-50 text-zinc-800"
            }`}
          >
{`header {
  Strict-Transport-Security "max-age=63072000; includeSubDomains; preload"
  X-Content-Type-Options "nosniff"
  X-Frame-Options "DENY"
  Referrer-Policy "strict-origin-when-cross-origin"
  Content-Security-Policy "default-src 'self'; script-src 'self'; frame-ancestors 'none';"
}`}
          </pre>
        </div>
      </section>
    </div>
  );
}
