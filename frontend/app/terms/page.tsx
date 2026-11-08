"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  ArrowUpRight,
  FileText,
  AlertTriangle,
  Scale,
  ShieldCheck,
  Ban,
  ChevronDown,
  List,
  CheckCircle2,
} from "lucide-react";
import { useTheme } from "@/components/ThemeProvider";

const SECTIONS = [
  { id: "acceptance", number: "1", title: "Acceptance of terms" },
  { id: "authorization", number: "2", title: "Mandatory domain authorization" },
  { id: "scope", number: "3", title: "Non-destructive testing scope" },
  { id: "advisory", number: "4", title: "AI-assisted advisory disclaimer" },
  { id: "billing", number: "5", title: "Billing, quotas & subscriptions" },
  { id: "governing-law", number: "6", title: "Governing law & jurisdiction" },
];

const PROHIBITED_ACTIVITIES = [
  {
    title: "No DoS or stress flooding",
    desc: "Denial of Service (DoS/DDoS) stress testing, resource exhaustion, or volume attacks.",
  },
  {
    title: "No brute-force attacks",
    desc: "Automated credential stuffing, dictionary attacks, or authentication bypass attempts.",
  },
  {
    title: "No data exfiltration",
    desc: "Active database extraction, exploitation payloads, or unauthorized lateral data retrieval.",
  },
  {
    title: "No internal subnet scans",
    desc: "Probing private RFC 1918 subnets (10.0.0.0/8, 192.168.0.0/16) or cloud metadata IPs.",
  },
];

export default function TermsOfServicePage() {
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
          <Scale className="w-4 h-4 text-teal-400" />
          <span className="font-mono text-xs text-teal-400 font-medium">
            Legal & compliance
          </span>
          <span className="text-zinc-600 text-xs">&bull;</span>
          <span className="font-mono text-[11px] text-zinc-500">
            Terms of service
          </span>
        </div>
        <h1 className="text-3xl sm:text-4xl font-normal tracking-tight text-zinc-100 font-mono">
          Terms of Service
        </h1>
        <p className="text-xs text-zinc-400 font-mono mt-1.5">
          Effective: November 2026 &bull; Enforced pursuant to the Indian Information Technology Act, 2000
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
              <span>Table of contents (6 sections)</span>
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

            {/* Quick Context Card */}
            <div
              className={`p-4 rounded-lg border text-xs font-mono space-y-2 ${
                isDark ? "border-zinc-800/70 bg-[#0d0d10] text-zinc-400" : "border-zinc-200 bg-zinc-50"
              }`}
            >
              <div className="text-zinc-200 font-medium flex items-center gap-1.5">
                <ShieldCheck className="w-3.5 h-3.5 text-teal-400" />
                <span>Scope guarantee</span>
              </div>
              <p className="text-[11px] leading-relaxed text-zinc-500">
                datasecurely strictly restricts probes to verified target perimeters without executing active payload exploitation.
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
            <section id="acceptance" className="scroll-mt-24 space-y-3">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 1
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  Acceptance of terms
                </h2>
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                By accessing or using the datasecurely security auditing platform (&quot;Service&quot;), you agree to be bound by these Terms of Service. If you represent an organization or business entity, you represent and warrant that you hold legitimate authority to bind such entity to these provisions.
              </p>
            </section>

            {/* Section 2 */}
            <section id="authorization" className="scroll-mt-24 space-y-4">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 2
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  Mandatory domain authorization & ownership warranty
                </h2>
              </div>

              {/* Restrained Scope Warranty Callout with Left Accent */}
              <div
                className={`p-4 rounded-r-lg border-l-2 border-l-amber-400 border border-zinc-800/80 space-y-2 ${
                  isDark ? "bg-amber-500/[0.03]" : "bg-amber-50/50"
                }`}
              >
                <div className="flex items-center gap-2 text-xs font-semibold text-amber-300">
                  <AlertTriangle className="w-4 h-4 shrink-0 text-amber-400" />
                  <span>Strict scope warranty</span>
                </div>
                <p className="text-xs leading-relaxed text-zinc-300">
                  You warrant that you own or have obtained express written authorization from the legitimate owner of every domain submitted. Unauthorized automated penetration testing violates Sections 43 and 66 of the Indian Information Technology Act, 2000.
                </p>
              </div>

              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                Before any automated scan is queued, ownership must be validated via cryptographic DNS TXT token resolution or HTTP <code>/.well-known/datasecurely-verification.txt</code> file matching. Unverified targets are strictly blocked by our automated scope guard.
              </p>
            </section>

            {/* Section 3 */}
            <section id="scope" className="scroll-mt-24 space-y-4">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 3
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  Non-destructive testing scope
                </h2>
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                The Service executes exclusively passive reconnaissance, transport verification, and safe exterior perimeter configuration checks. To prevent downtime or service interruption, datasecurely strictly prohibits and will never perform:
              </p>

              {/* 2x2 Grid for Prohibited Boundaries */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                {PROHIBITED_ACTIVITIES.map((act, i) => (
                  <div
                    key={i}
                    className="p-3.5 rounded border border-zinc-800/80 bg-zinc-900/40 space-y-1.5"
                  >
                    <div className="flex items-center gap-2 text-xs font-medium text-zinc-200">
                      <Ban className="w-3.5 h-3.5 text-red-400 shrink-0" />
                      <span>{act.title}</span>
                    </div>
                    <p className="text-[11px] text-zinc-400 leading-relaxed font-mono">
                      {act.desc}
                    </p>
                  </div>
                ))}
              </div>
            </section>

            {/* Section 4 */}
            <section id="advisory" className="scroll-mt-24 space-y-3">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 4
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  AI-assisted advisory disclaimer
                </h2>
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                Executive summaries and remediation checklists are generated with assistance from Google Gemini AI models. AI triage outputs are provided for educational and remediation prioritization guidance only. They do not constitute formal legal counsel, statutory audit certification, or an absolute guarantee against zero-day compromises.
              </p>
            </section>

            {/* Section 5 */}
            <section id="billing" className="scroll-mt-24 space-y-4">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 5
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  Billing, quotas & subscriptions
                </h2>
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                Free accounts receive non-destructive baseline audits per verified domain. Paid plans (Pro SMB and Business) are billed in Indian Rupees (INR) via Razorpay. Subscriptions renew automatically unless cancelled prior to the billing cycle cutoff.
              </p>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 font-mono text-xs">
                <div className="p-3 rounded border border-zinc-800 bg-zinc-900/30 space-y-1">
                  <div className="text-zinc-200 font-medium">Free plan tier</div>
                  <div className="text-[11px] text-zinc-400">1 domain audit &bull; Baseline checks &bull; Self-service</div>
                </div>
                <div className="p-3 rounded border border-teal-500/20 bg-teal-500/[0.03] space-y-1">
                  <div className="text-zinc-200 font-medium text-teal-400">Paid plans (Pro / Business)</div>
                  <div className="text-[11px] text-zinc-400">Multi-domain &bull; Continuous monitoring &bull; PDF export</div>
                </div>
              </div>
            </section>

            {/* Section 6 */}
            <section id="governing-law" className="scroll-mt-24 space-y-3">
              <div className="flex items-center gap-2.5">
                <span className="px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-800 bg-zinc-900 text-teal-400">
                  Section 6
                </span>
                <h2 className="text-base sm:text-lg font-medium text-zinc-100">
                  Governing law & jurisdiction
                </h2>
              </div>
              <p className="text-xs sm:text-sm leading-relaxed text-zinc-300">
                These Terms shall be governed by and construed in accordance with the substantive laws of the Republic of India. Any legal dispute, controversy, or claim arising out of or relating to these terms shall be subject to the exclusive jurisdiction of the competent courts in Bangalore, Karnataka, India.
              </p>
            </section>

            {/* ---------------- FIXED BOTTOM CROSS-LINK BAR ---------------- */}
            <div className="pt-8 border-t border-zinc-800/80 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs font-mono text-zinc-500">
              <div>
                <span className="text-zinc-300 font-medium">datasecurely</span>
                <span> &bull; Non-destructive security platform for Indian SMBs</span>
              </div>
              <Link
                href="/privacy"
                className="inline-flex items-center gap-1.5 text-teal-400 hover:text-teal-300 transition-colors font-medium shrink-0 self-start sm:self-auto"
              >
                <span>View privacy policy</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
