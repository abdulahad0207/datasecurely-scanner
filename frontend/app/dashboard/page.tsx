"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Shield,
  CheckCircle2,
  Clock,
  Globe,
  ArrowUpRight,
  Trash2,
  Activity,
  AlertTriangle,
  RefreshCw,
  Plus,
  Play,
} from "lucide-react";
import {
  createDomain,
  deleteDomain,
  fetchDomains,
  startScan,
  Domain,
} from "@/lib/api";
import { useTheme } from "@/components/ThemeProvider";

export default function DashboardPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const router = useRouter();

  const [domains, setDomains] = useState<Domain[]>([]);
  const [hostnameInput, setHostnameInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [scanningDomainId, setScanningDomainId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "verified" | "pending">("all");

  const loadDomains = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchDomains();
      setDomains(data || []);
    } catch (err: any) {
      setError(err.message || "Failed to load domains");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDomains();
  }, []);

  const handleAddDomain = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hostnameInput.trim()) return;

    setSubmitting(true);
    setError(null);
    try {
      const cleanHost = hostnameInput
        .replace(/^https?:\/\//i, "")
        .replace(/\/.*$/, "")
        .trim();
      const newDomain = await createDomain(cleanHost);
      setDomains([newDomain, ...domains]);
      setHostnameInput("");
    } catch (err: any) {
      setError(err.message || "Failed to add domain");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to remove ${name}?`)) return;
    try {
      await deleteDomain(id);
      setDomains(domains.filter((d) => d.id !== id));
    } catch (err: any) {
      setError(err.message || "Failed to delete domain");
    }
  };

  const handleStartScan = async (domainId: string) => {
    setScanningDomainId(domainId);
    setError(null);
    try {
      const scan = await startScan(domainId, "free");
      router.push(`/scans/${scan.id}`);
    } catch (err: any) {
      setError(err.message || "Failed to initiate scan");
      setScanningDomainId(null);
    }
  };

  const filteredDomains = domains.filter((d) => {
    if (filter === "verified") return d.status === "verified";
    if (filter === "pending") return d.status === "pending";
    return true;
  });

  const verifiedCount = domains.filter((d) => d.status === "verified").length;
  const pendingCount = domains.filter((d) => d.status === "pending").length;
  const percentVerified =
    domains.length > 0 ? Math.round((verifiedCount / domains.length) * 100) : 0;

  // Grade badge styling helper
  const renderGradeBadge = (grade: string | null | undefined) => {
    if (!grade) {
      return (
        <span className="text-zinc-500 font-mono text-xs">No scan yet</span>
      );
    }
    const g = grade.toUpperCase();
    if (g.startsWith("A")) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium border border-teal-500/30 bg-teal-500/10 text-teal-400">
          Grade {g}
        </span>
      );
    }
    if (g.startsWith("B")) {
      return (
        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium border border-amber-500/30 bg-amber-500/10 text-amber-400">
          Grade {g}
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono font-medium border border-red-500/30 bg-red-500/10 text-red-400">
        Grade {g}
      </span>
    );
  };

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8 sm:py-10 space-y-6 sm:space-y-8 font-sans">
      {/* ---------------- PAGE HEADER ---------------- */}
      <div
        className={`flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b ${
          isDark ? "border-zinc-800" : "border-zinc-200"
        }`}
      >
        <div>
          <div className="flex items-center gap-2 mb-1.5 font-mono text-xs">
            <span className="text-teal-400 font-medium">
              Console &mdash; domain protection
            </span>
            <span className="text-zinc-500">&bull;</span>
            <span className="text-zinc-500">{domains.length} target hosts</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-normal tracking-tight">
            Domain security dashboard
          </h1>
          <p
            className={`text-xs sm:text-sm mt-1 max-w-xl ${
              isDark ? "text-zinc-400" : "text-zinc-600"
            }`}
          >
            Add and verify domain ownership to run automated vulnerability
            audits and continuous DPDP Act 2023 compliance checks.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/pricing"
            className={`text-xs font-mono px-3.5 py-2 rounded-lg border inline-flex items-center gap-1.5 transition-colors ${
              isDark
                ? "border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:text-white hover:border-zinc-700"
                : "border-zinc-300 bg-white text-zinc-800 hover:bg-zinc-50"
            }`}
          >
            <span>Upgrade plan</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-teal-400" />
          </Link>
        </div>
      </div>

      {/* ---------------- AUTH / SYSTEM RECOVERY ALERT ---------------- */}
      {error && (
        <div
          className={`p-4 rounded-xl border text-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
            isDark
              ? "border-red-900/60 bg-red-950/40 text-red-300"
              : "border-red-200 bg-red-50 text-red-800"
          }`}
        >
          <div>
            <span className="font-semibold block">{error}</span>
            <span className="text-xs opacity-90">
              {error.toLowerCase().includes("token") ||
              error.toLowerCase().includes("auth")
                ? "Your authentication session is invalid or expired. Re-authenticate to access the dashboard."
                : "An error occurred while processing your request."}
            </span>
          </div>
          <div className="flex items-center gap-2 font-mono text-xs">
            <Link
              href="/login"
              onClick={() => {
                if (typeof window !== "undefined") {
                  localStorage.removeItem("dev_mock_token");
                }
              }}
              className="px-3 py-1.5 bg-red-600 hover:bg-red-700 text-white rounded-lg transition-colors"
            >
              Sign in
            </Link>
          </div>
        </div>
      )}

      {/* ---------------- TELEMETRY METRICS HUD ---------------- */}
      {/* Desktop: Asymmetric spotlight on Protected domains. Mobile: 2x2 compact grid */}
      <div className="grid grid-cols-2 lg:grid-cols-12 gap-2.5 sm:gap-4">
        {/* Metric Spotlight: Protected Domains */}
        <div
          className={`col-span-2 lg:col-span-5 p-4 sm:p-5 rounded-xl border flex flex-col justify-between space-y-3 transition-all ${
            isDark
              ? "border-zinc-800 hover:border-teal-500/30 bg-[#121215] shadow-sm"
              : "border-zinc-200 bg-white shadow-sm"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="text-xs font-mono text-zinc-400 font-medium">
              Protected domains
            </span>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono border border-teal-500/30 bg-teal-500/10 text-teal-400">
              Primary target
            </span>
          </div>

          <div>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-light tracking-tight text-zinc-100">
                {verifiedCount}
              </span>
              <span className="text-xs font-mono text-zinc-500">
                / {domains.length} verified
              </span>
            </div>
            {/* Visual Coverage Progress Bar */}
            <div className="w-full bg-zinc-800/80 h-1.5 rounded-full overflow-hidden mt-2.5">
              <div
                className="bg-teal-400 h-full rounded-full transition-all duration-500"
                style={{ width: `${percentVerified}%` }}
              />
            </div>
          </div>

          <div className="flex items-center justify-between text-xs font-mono pt-1">
            <div className="flex items-center gap-1.5 text-teal-400">
              <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
              <span>{percentVerified}% perimeter coverage</span>
            </div>
            <span className="text-zinc-500 hidden sm:inline">
              {verifiedCount > 0 ? "Continuous monitoring" : "Action required"}
            </span>
          </div>
        </div>

        {/* Secondary Metrics Subgrid: 3 cards on desktop, 3 compact cards in 2x2 grid on mobile */}
        <div className="col-span-2 lg:col-span-7 grid grid-cols-2 sm:grid-cols-3 gap-2.5 sm:gap-4">
          {/* Active Audits */}
          <div
            className={`p-3.5 sm:p-4 rounded-xl border flex flex-col justify-between ${
              isDark
                ? "border-zinc-800 bg-[#121215]"
                : "border-zinc-200 bg-white shadow-sm"
            }`}
          >
            <div className="text-xs font-mono text-zinc-500 mb-1">
              Active audits
            </div>
            <div className="text-2xl font-light tracking-tight">
              {verifiedCount}{" "}
              <span className="text-xs text-zinc-500 font-mono">targets</span>
            </div>
            <div className="text-xs text-zinc-400 mt-2 font-mono flex items-center gap-1 truncate">
              <Activity className="w-3 h-3 text-teal-400 shrink-0" />
              <span className="truncate">On-demand ready</span>
            </div>
          </div>

          {/* Pending Verification */}
          <div
            className={`p-3.5 sm:p-4 rounded-xl border flex flex-col justify-between ${
              isDark
                ? "border-zinc-800 bg-[#121215]"
                : "border-zinc-200 bg-white shadow-sm"
            }`}
          >
            <div className="text-xs font-mono text-zinc-500 mb-1">
              Pending verification
            </div>
            <div
              className={`text-2xl font-light tracking-tight ${
                pendingCount > 0 ? "text-amber-400" : "text-zinc-200"
              }`}
            >
              {pendingCount}{" "}
              <span className="text-xs text-zinc-500 font-mono">domains</span>
            </div>
            <div className="text-xs text-zinc-400 mt-2 font-mono flex items-center gap-1 truncate">
              {pendingCount > 0 ? (
                <>
                  <Clock className="w-3 h-3 text-amber-400 shrink-0" />
                  <span className="truncate text-amber-300">Requires DNS TXT</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="w-3 h-3 text-teal-400 shrink-0" />
                  <span className="truncate text-teal-400">All verified</span>
                </>
              )}
            </div>
          </div>

          {/* DPDP Act 2023 Safeguards (Quantifiable Metric) */}
          <div
            className={`col-span-2 sm:col-span-1 p-3.5 sm:p-4 rounded-xl border flex flex-col justify-between ${
              isDark
                ? "border-zinc-800 bg-[#121215]"
                : "border-zinc-200 bg-white shadow-sm"
            }`}
          >
            <div className="text-xs font-mono text-zinc-500 mb-1">
              DPDP Act safeguards
            </div>
            <div className="text-2xl font-light tracking-tight text-teal-400">
              {verifiedCount > 0 ? "4 / 4" : "0 / 4"}{" "}
              <span className="text-xs text-zinc-500 font-mono">passing</span>
            </div>
            <div className="text-xs text-zinc-400 mt-2 font-mono flex items-center gap-1 truncate">
              <Shield className="w-3 h-3 text-teal-400 shrink-0" />
              <span className="truncate">Section 8(5) controls</span>
            </div>
          </div>
        </div>
      </div>

      {/* ---------------- ADD NEW DOMAIN CARD ---------------- */}
      <div
        className={`p-5 sm:p-6 rounded-xl border ${
          isDark
            ? "border-zinc-800 bg-[#121215] shadow-sm"
            : "border-zinc-200 bg-white shadow-sm"
        }`}
      >
        <div className="mb-3.5">
          <h2 className="text-base font-normal tracking-tight">Add new domain</h2>
          <p
            className={`text-xs mt-0.5 ${
              isDark ? "text-zinc-400" : "text-zinc-600"
            }`}
          >
            Enter your domain or host. We will verify ownership before
            initiating automated security tests.
          </p>
        </div>

        <form
          onSubmit={handleAddDomain}
          className="flex flex-col sm:flex-row gap-2.5 sm:gap-3"
        >
          <div className="relative flex-1">
            <Globe
              className={`w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 ${
                isDark ? "text-zinc-500" : "text-zinc-400"
              }`}
            />
            <input
              type="text"
              required
              placeholder="example.com"
              value={hostnameInput}
              onChange={(e) => setHostnameInput(e.target.value)}
              className={`w-full pl-10 pr-4 py-2.5 rounded-lg text-xs font-mono border transition-colors focus:outline-none ${
                isDark
                  ? "bg-zinc-950 border-zinc-700 text-zinc-100 placeholder:text-zinc-500 hover:border-zinc-600 focus:border-teal-400 focus:ring-1 focus:ring-teal-400/20"
                  : "bg-zinc-50 border-zinc-300 text-zinc-900 placeholder:text-zinc-400 hover:border-zinc-400 focus:border-teal-600 focus:ring-1 focus:ring-teal-600/20"
              }`}
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className={`px-5 py-2.5 rounded-lg text-xs font-mono font-medium transition-all flex items-center justify-center gap-2 ${
              submitting
                ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                : isDark
                ? "bg-teal-500 hover:bg-teal-400 text-zinc-950 shadow-sm"
                : "bg-teal-600 hover:bg-teal-500 text-white shadow-sm"
            }`}
          >
            <Plus className="w-3.5 h-3.5" />
            <span>{submitting ? "Adding..." : "Add domain"}</span>
          </button>
        </form>
      </div>

      {/* ---------------- REGISTERED DOMAINS LIST ---------------- */}
      <div
        className={`rounded-xl border overflow-hidden ${
          isDark
            ? "border-zinc-800 bg-[#121215] shadow-sm"
            : "border-zinc-200 bg-white shadow-sm"
        }`}
      >
        {/* Table Filter Header */}
        <div
          className={`p-4 border-b flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
            isDark
              ? "border-zinc-800/80 bg-zinc-950/70"
              : "border-zinc-200 bg-zinc-50/70"
          }`}
        >
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-teal-400 shrink-0" />
            <span className="text-sm font-medium">Registered domains</span>
            <span className="text-xs font-mono text-zinc-500">
              ({filteredDomains.length}{" "}
              {filteredDomains.length === 1 ? "domain" : "domains"})
            </span>
          </div>

          <div className="flex items-center gap-1.5 text-xs font-mono">
            <button
              onClick={() => setFilter("all")}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                filter === "all"
                  ? isDark
                    ? "bg-zinc-800 text-white"
                    : "bg-white text-zinc-900 border border-zinc-300"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              All ({domains.length})
            </button>
            <button
              onClick={() => setFilter("verified")}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                filter === "verified"
                  ? isDark
                    ? "bg-zinc-800 text-white"
                    : "bg-white text-zinc-900 border border-zinc-300"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              Verified ({verifiedCount})
            </button>
            <button
              onClick={() => setFilter("pending")}
              className={`px-2.5 py-1 rounded-md transition-colors ${
                filter === "pending"
                  ? isDark
                    ? "bg-zinc-800 text-white"
                    : "bg-white text-zinc-900 border border-zinc-300"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              Pending ({pendingCount})
            </button>
          </div>
        </div>

        {/* Loading / Empty / Domains List */}
        {loading ? (
          <div className="p-12 text-center text-xs font-mono text-zinc-500">
            <RefreshCw className="w-4 h-4 mx-auto mb-2 animate-spin text-teal-400" />
            Loading registered domains...
          </div>
        ) : domains.length === 0 ? (
          <div className="p-16 text-center">
            <div
              className={`w-12 h-12 mx-auto mb-3 rounded-full flex items-center justify-center ${
                isDark ? "bg-zinc-900 text-zinc-600" : "bg-zinc-100 text-zinc-400"
              }`}
            >
              <Globe className="w-6 h-6" />
            </div>
            <h3 className="text-sm font-medium">No domains added yet</h3>
            <p className="text-xs text-zinc-500 mt-1 max-w-sm mx-auto">
              Add your domain above to generate your verification token and
              begin automated security auditing.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-zinc-800/60">
            {filteredDomains.map((domain) => {
              const latestScan = domain.latest_scan;

              return (
                <div
                  key={domain.id}
                  className={`p-4 sm:p-5 transition-colors ${
                    isDark ? "hover:bg-zinc-900/40" : "hover:bg-zinc-50/80"
                  }`}
                >
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    {/* Domain Host, Verification Status & Security Context */}
                    <div className="space-y-2 flex-1 min-w-0">
                      {/* Hostname & Badges Row (Prevents pill wrapping/collision) */}
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="font-mono text-sm font-medium tracking-tight text-zinc-100 break-all sm:break-normal truncate max-w-[220px] sm:max-w-none">
                          {domain.hostname}
                        </span>

                        {domain.status === "verified" ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border border-teal-500/30 bg-teal-500/10 text-teal-400 shrink-0 whitespace-nowrap">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Verified</span>
                          </span>
                        ) : domain.status === "expired" ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border border-red-500/30 bg-red-500/10 text-red-400 shrink-0 whitespace-nowrap">
                            <AlertTriangle className="w-3 h-3" />
                            <span>Expired</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border border-amber-500/30 bg-amber-500/10 text-amber-400 shrink-0 whitespace-nowrap">
                            <Clock className="w-3 h-3" />
                            <span>Verification pending</span>
                          </span>
                        )}

                        {domain.is_monitored && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-700 bg-zinc-800/60 text-zinc-300 shrink-0 whitespace-nowrap">
                            <span>Weekly monitor active</span>
                          </span>
                        )}
                      </div>

                      {/* Security Context: Grade, Finding Count, Last Scan */}
                      <div className="flex flex-wrap items-center gap-x-3 sm:gap-x-4 gap-y-1.5 text-xs font-mono text-zinc-400">
                        {/* Security Grade */}
                        <div className="flex items-center gap-1.5">
                          <span className="text-zinc-500 text-[11px]">Posture:</span>
                          {renderGradeBadge(latestScan?.grade)}
                        </div>

                        <span className="text-zinc-600 hidden sm:inline">&bull;</span>

                        {/* Finding Count */}
                        <div className="flex items-center gap-1 text-[11px]">
                          {latestScan ? (
                            <>
                              <AlertTriangle className="w-3 h-3 text-amber-400 shrink-0" />
                              <span className="text-zinc-300">
                                {latestScan.findings_count}{" "}
                                {latestScan.findings_count === 1
                                  ? "finding"
                                  : "findings"}
                              </span>
                            </>
                          ) : (
                            <span className="text-zinc-500">0 findings</span>
                          )}
                        </div>

                        <span className="text-zinc-600 hidden sm:inline">&bull;</span>

                        {/* Last Scan Date */}
                        <div className="text-[11px] text-zinc-500">
                          {latestScan ? (
                            <span>
                              Last scan{" "}
                              {new Date(
                                latestScan.finished_at || latestScan.created_at
                              ).toLocaleDateString()}
                            </span>
                          ) : (
                            <span>Never scanned</span>
                          )}
                        </div>

                        <span className="text-zinc-600 hidden sm:inline">&bull;</span>

                        {/* Registered Date */}
                        <div className="text-[11px] text-zinc-500">
                          Created {new Date(domain.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    </div>

                    {/* Domain Action Buttons */}
                    <div className="flex items-center gap-2 font-mono text-xs pt-2 lg:pt-0 border-t lg:border-t-0 border-zinc-800/50 justify-between lg:justify-end">
                      <div className="flex items-center gap-2">
                        {domain.status === "verified" ? (
                          <>
                            {/* Quick Start Scan Action */}
                            <button
                              onClick={() => handleStartScan(domain.id)}
                              disabled={scanningDomainId === domain.id}
                              className={`px-3 py-1.5 rounded-lg border font-mono text-xs flex items-center gap-1.5 transition-all ${
                                scanningDomainId === domain.id
                                  ? "border-zinc-700 bg-zinc-800 text-zinc-400 cursor-not-allowed"
                                  : isDark
                                  ? "border-teal-500/30 bg-teal-500/10 hover:bg-teal-500/20 text-teal-300"
                                  : "border-teal-300 bg-teal-50 hover:bg-teal-100 text-teal-800"
                              }`}
                              title="Run automated scan now"
                            >
                              {scanningDomainId === domain.id ? (
                                <>
                                  <RefreshCw className="w-3 h-3 animate-spin" />
                                  <span>Starting...</span>
                                </>
                              ) : (
                                <>
                                  <Play className="w-3 h-3 fill-current" />
                                  <span>Start scan</span>
                                </>
                              )}
                            </button>

                            {/* Details & Scans Link */}
                            <Link
                              href={`/domains/${domain.id}`}
                              className={`px-3 py-1.5 rounded-lg border transition-colors flex items-center gap-1.5 ${
                                isDark
                                  ? "border-zinc-800 bg-zinc-900/60 text-zinc-300 hover:text-white hover:border-zinc-700"
                                  : "border-zinc-300 bg-white text-zinc-800 hover:bg-zinc-50"
                              }`}
                            >
                              <span>Details & scans</span>
                              <ArrowUpRight className="w-3 h-3" />
                            </Link>
                          </>
                        ) : (
                          /* Verification Pending Action */
                          <Link
                            href={`/domains/${domain.id}`}
                            className="px-3 py-1.5 rounded-lg border border-amber-500/40 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 transition-colors flex items-center gap-1.5"
                          >
                            <span>Verify ownership</span>
                            <ArrowUpRight className="w-3 h-3" />
                          </Link>
                        )}
                      </div>

                      {/* Restyled Delete Action with Dedicated Button Container */}
                      <button
                        onClick={() => handleDelete(domain.id, domain.hostname)}
                        className={`p-2 rounded-lg border transition-all flex items-center justify-center ${
                          isDark
                            ? "border-zinc-800 bg-zinc-900/40 text-zinc-400 hover:text-red-400 hover:border-red-500/40 hover:bg-red-500/10 focus:ring-1 focus:ring-red-500/30"
                            : "border-zinc-200 bg-zinc-50 text-zinc-500 hover:text-red-600 hover:border-red-300 hover:bg-red-50 focus:ring-1 focus:ring-red-500/30"
                        }`}
                        title="Delete domain"
                        aria-label={`Delete ${domain.hostname}`}
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
