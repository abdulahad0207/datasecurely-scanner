"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowUpRight,
  Lock,
  Database,
  ShieldCheck,
  Trash2,
  UserCheck,
  ChevronDown,
  List,
  Building2,
  Mail,
  MapPin,
  Clock,
} from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";

const SECTIONS = [
  { id: "commitment", number: "1", title: "Commitment to privacy" },
  { id: "collection", number: "2", title: "Categories of data collected" },
  { id: "purpose", number: "3", title: "Purpose of data processing" },
  { id: "retention", number: "4", title: "Data retention & erasure" },
  { id: "grievance", number: "5", title: "Grievance officer & contact" },
];

const DATA_CATEGORIES = [
  {
    title: "Account identifiers",
    badge: "Identity",
    desc: "Email address, system-generated UUID token, and Razorpay billing transaction identifiers.",
    purpose: "Account authentication, tenant isolation, and invoice generation.",
  },
  {
    title: "Domain records",
    badge: "Authorization",
    desc: "Target hostnames, DNS verification TXT tokens, well-known file tokens, and ownership state.",
    purpose: "Scope enforcement and non-destructive audit authorization.",
  },
  {
    title: "Telemetry & findings",
    badge: "Technical",
    desc: "Observed HTTP response headers, TLS handshake details, cookie security flags, and vulnerability fingerprints.",
    purpose: "Vulnerability analysis, AI triage synthesis, and PDF report creation.",
  },
];

export default function PrivacyPolicyPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [mobileTocOpen, setMobileTocOpen] = useState(false);

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-10 font-sans">
      {/* ---------------- NAVIGATION HEADER ---------------- */}
      <div className="mb-8">
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-500 hover:text-zinc-200 transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to dashboard</span>
        </Link>
        <div className="flex items-center gap-2 mb-1.5">
          <Lock className="w-4 h-4 text-teal-400" />
          <span className="font-mono text-xs text-teal-400 font-medium">
            Data privacy & governance
          </span>
          <span className="text-zinc-600 text-xs">&bull;</span>
          <span className="font-mono text-[11px] text-zinc-500">
            DPDP Act, 2023
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-normal tracking-tight text-zinc-100 font-mono">
          Privacy Policy
        </h1>
        <p className="text-xs text-zinc-400 font-mono mt-1.5">
          Effective: November 2026 &bull; Compliant with Digital Personal Data Protection Act, 2023 (DPDP)
        </p>
      </div>

      {/* ---------------- MAIN TWO-COLUMN LAYOUT ---------------- */}
      <div className="flex flex-col lg:flex-row gap-8">
        {/* Mobile Collapsible Table of Contents (< lg) */}
        <div className="lg:hidden">
          <button
            onClick={() => setMobileTocOpen(!mobileTocOpen)}
            className={`w-full px-4 py-3 rounded-lg border text-xs font-mono flex items-center justify-between transition-colors ${
              isDark
                ? "border-zinc-800 bg-[#121215] text-zinc-200"
                : "border-zinc-200 bg-white text-zinc-800"
            }`}
          >
            <span className="flex items-center gap-2 font-medium">
              <List className="w-4 h-4 text-teal-400" />
              <span>Table of contents (5 sections)</span>
            </span>
            <ChevronDown
              className={`w-4 h-4 text-zinc-400 transition-transform ${
                mobileTocOpen ? "rotate-180" : ""
              }`}
            />
          </button>
          {mobileTocOpen && (
            <div
              className={`mt-2 p-3 rounded-lg border space-y-1 font-mono text-xs ${
                isDark ? "border-zinc-800 bg-[#121215]" : "border-zinc-200 bg-white shadow-sm"
              }`}
            >
              {SECTIONS.map((sec) => (
                <a
                  key={sec.id}
                  href={`#${sec.id}`}
                  onClick={() => setMobileTocOpen(false)}
                  className="flex items-center gap-2 p-2 rounded hover:bg-zinc-800/60 text-zinc-400 hover:text-zinc-200 transition-colors"
                >
                  <span className="text-teal-400 text-[11px] font-bold w-4">{sec.number}.</span>
                  <span className="truncate">{sec.title}</span>
                </a>
              ))}
            </div>
          )}
        </div>

        {/* Desktop Sticky Sidebar Table of Contents (lg and up) */}
        <aside className="hidden lg:block w-64 shrink-0">
          <div className="sticky top-24 space-y-4">
            <div
              className={`p-4 rounded-lg border space-y-3 font-mono text-xs ${
                isDark ? "border-white/10 bg-[#121215]" : "border-zinc-200 bg-white"
              }`}
            >
              <div className="flex items-center gap-2 text-zinc-300 font-medium pb-2 border-b border-zinc-800/80">
                <List className="w-3.5 h-3.5 text-teal-400" />
                <span>Table of contents</span>
              </div>
              <nav className="space-y-1">
                {SECTIONS.map((sec) => (
                  <a
                    key={sec.id}
                    href={`#${sec.id}`}
                    className="flex items-center gap-2.5 py-1.5 px-2 rounded text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800/50 transition-colors group"
                  >
                    <span className="text-zinc-500 group-hover:text-teal-400 text-[11px] font-mono">
                      0{sec.number}
                    </span>
                    <span className="truncate">{sec.title}</span>
                  </a>
                ))}
              </nav>
            </div>

            {/* DPDP Safeguard Badge Card */}
            <div
              className={`p-4 rounded-lg border text-xs font-mono space-y-2 ${
                isDark ? "border-zinc-800/70 bg-[#0d0d10] text-zinc-400" : "border-zinc-200 bg-zinc-50"
              }`}
            >
              <div className="text-zinc-200 font-medium flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
                <span>Data fiduciary notice</span>
              </div>
              <p className="text-[11px] leading-relaxed text-zinc-500">
                datasecurely processes telemetry exclusively as a Data Fiduciary under DPDP Act 2023 without reselling business data.
              </p>
            </div>
          </div>
        </aside>

        {/* Main Document Content */}
        <main className="flex-1 min-w-0">
          <div
            className={`p-6 sm:p-10 rounded-lg border space-y-10 ${
              isDark ? "border-white/10 bg-[#121215] text-zinc-100" : "border-zinc-200 bg-white text-zinc-900"
            }`}
          >
            {/* Section 1 */}
            <section id="commitment" className="scroll-mt-24 space-y-4">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 1
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  Commitment to privacy & confidentiality
                </h2>
              </div>

              {/* Data Fiduciary Callout with Left Accent */}
              <div
                className={`p-4 rounded-r-lg border-l-2 border-l-teal-400 border border-zinc-800/80 space-y-1.5 ${
                  isDark ? "bg-teal-500/[0.03]" : "bg-teal-50/50"
                }`}
              >
                <div className="text-xs font-semibold text-teal-300 flex items-center gap-1.5">
                  <ShieldCheck className="w-4 h-4 text-teal-400" />
                  <span>Statutory data fiduciary commitment</span>
                </div>
                <p className="text-xs leading-relaxed text-zinc-300">
                  datasecurely acts as a Data Fiduciary under the Digital Personal Data Protection Act, 2023. We collect and process only the minimal security telemetry required to conduct non-destructive scans, verify domain ownership, and generate confidential remediation reports.
                </p>
              </div>

              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                We do not sell, rent, monetize, or disclose your scan telemetry or vulnerability records to third-party advertising brokers or unauthorized entities. Your security findings remain strictly segregated under your tenant account.
              </p>
            </section>

            {/* Section 2 */}
            <section id="collection" className="scroll-mt-24 space-y-4">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 2
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  Categories of data collected
                </h2>
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                To provide vulnerability monitoring and automated security audits, we collect the following three specific classes of data:
              </p>

              {/* Structured 3-Card Grid for Data Classes */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-1">
                {DATA_CATEGORIES.map((cat, idx) => (
                  <div
                    key={idx}
                    className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-900/40 flex flex-col justify-between space-y-3 font-mono text-xs"
                  >
                    <div>
                      <div className="flex items-center justify-between pb-2 border-b border-zinc-800/60">
                        <span className="font-semibold text-zinc-200">{cat.title}</span>
                        <span className="text-[10px] text-teal-400 bg-teal-500/10 border border-teal-500/20 px-1.5 py-0.5 rounded">
                          {cat.badge}
                        </span>
                      </div>
                      <p className="text-[11px] text-zinc-400 leading-relaxed mt-2.5">
                        {cat.desc}
                      </p>
                    </div>
                    <div className="pt-2 border-t border-zinc-800/40 text-[10px] text-zinc-500">
                      <span className="text-zinc-400">Purpose: </span>{cat.purpose}
                    </div>
                  </div>
                ))}
              </div>
            </section>

            {/* Section 3 */}
            <section id="purpose" className="scroll-mt-24 space-y-4">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 3
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  Purpose of data processing
                </h2>
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                Data is processed solely for purpose-bound, legitimate security operational uses:
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 font-mono text-xs">
                <div className="p-3 rounded border border-zinc-800/60 bg-zinc-900/30 flex items-start gap-2.5 text-zinc-300">
                  <Database className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
                  <span>Execute non-destructive vulnerability assessments on authorized domains</span>
                </div>
                <div className="p-3 rounded border border-zinc-800/60 bg-zinc-900/30 flex items-start gap-2.5 text-zinc-300">
                  <ShieldCheck className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
                  <span>Synthesize bilingual executive advisories via Google Gemini models</span>
                </div>
                <div className="p-3 rounded border border-zinc-800/60 bg-zinc-900/30 flex items-start gap-2.5 text-zinc-300">
                  <Lock className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
                  <span>Generate confidential PDF reports and vulnerability diff alerts</span>
                </div>
                <div className="p-3 rounded border border-zinc-800/60 bg-zinc-900/30 flex items-start gap-2.5 text-zinc-300">
                  <UserCheck className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
                  <span>Validate domain ownership and manage subscription tier quotas</span>
                </div>
              </div>
            </section>

            {/* Section 4 */}
            <section id="retention" className="scroll-mt-24 space-y-4">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 4
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  Data retention & automated erasure
                </h2>
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                In strict compliance with the DPDP Act 2023 data minimization mandates, we enforce strict retention windows and automated deletion lifecycles:
              </p>

              {/* Retention Highlights */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 font-mono text-xs">
                <div className="p-3.5 rounded border border-zinc-800 bg-zinc-900/30 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-200 font-medium">Telemetry retention</span>
                    <span className="text-teal-400 font-bold">90 days</span>
                  </div>
                  <p className="text-[11px] text-zinc-400 leading-relaxed">
                    Historical scan findings and PDF reports are preserved for 90 days to enable regression diffing.
                  </p>
                </div>
                <div className="p-3.5 rounded border border-zinc-800 bg-zinc-900/30 space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-zinc-200 font-medium">Deletion turnaround</span>
                    <span className="text-teal-400 font-bold">48 hours</span>
                  </div>
                  <p className="text-[11px] text-zinc-400 leading-relaxed">
                    When you delete a domain or account, all associated scans, findings, and PDFs are permanently purged within 48 hours.
                  </p>
                </div>
              </div>
            </section>

            {/* Section 5 */}
            <section id="grievance" className="scroll-mt-24 space-y-4">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 5
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  Grievance officer & statutory contact
                </h2>
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                Pursuant to Rule 5(9) of the Information Technology (Reasonable Security Practices) Rules, 2011 and Section 8 of the DPDP Act 2023, you may address privacy concerns, data erasure requests, or grievances to:
              </p>

              {/* Restyled Grievance Officer Business Card Layout */}
              <div
                className={`p-5 rounded-lg border font-mono text-xs space-y-4 ${
                  isDark
                    ? "border-white/10 bg-[#0d0d10] text-zinc-200"
                    : "border-zinc-200 bg-zinc-50 text-zinc-800"
                }`}
              >
                <div className="flex items-center justify-between pb-3 border-b border-zinc-800/80">
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4 text-teal-400" />
                    <span className="font-semibold text-zinc-100 text-sm">
                      Statutory Grievance Officer
                    </span>
                  </div>
                  <span className="text-[10px] text-zinc-500 uppercase tracking-wider">
                    DPDP Act Compliance
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <div className="text-[11px] text-zinc-500 flex items-center gap-1.5">
                      <UserCheck className="w-3.5 h-3.5 text-teal-400" />
                      <span>Designated entity</span>
                    </div>
                    <div className="text-zinc-200 font-medium">
                      datasecurely Privacy & Compliance Team
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="text-[11px] text-zinc-500 flex items-center gap-1.5">
                      <Mail className="w-3.5 h-3.5 text-teal-400" />
                      <span>Direct grievance email</span>
                    </div>
                    <a
                      href="mailto:privacy@datasecurely.com"
                      className="text-teal-400 hover:underline font-medium"
                    >
                      privacy@datasecurely.com
                    </a>
                  </div>

                  <div className="space-y-1">
                    <div className="text-[11px] text-zinc-500 flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-teal-400" />
                      <span>Registered jurisdiction</span>
                    </div>
                    <div className="text-zinc-300">
                      Bangalore, Karnataka 560001, India
                    </div>
                  </div>

                  <div className="space-y-1">
                    <div className="text-[11px] text-zinc-500 flex items-center gap-1.5">
                      <Clock className="w-3.5 h-3.5 text-teal-400" />
                      <span>Response SLA</span>
                    </div>
                    <div className="text-zinc-300">
                      24h acknowledgment &bull; 30 days resolution
                    </div>
                  </div>
                </div>
              </div>
            </section>

            {/* ---------------- FIXED BOTTOM CROSS-LINK BAR ---------------- */}
            <div className="pt-8 border-t border-zinc-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs font-mono text-zinc-500">
              <div>
                <span className="text-zinc-300 font-medium">datasecurely</span>
                <span> &bull; Automated website security platform for Indian SMBs</span>
              </div>
              <Link
                href="/terms"
                className="inline-flex items-center gap-1.5 text-teal-400 hover:text-teal-300 transition-colors font-medium shrink-0 self-start sm:self-auto"
              >
                <span>View terms of service</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
