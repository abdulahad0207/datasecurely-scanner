"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  Shield,
  ArrowUpRight,
  AlertTriangle,
  CheckCircle2,
  Globe,
  Lock,
} from "lucide-react";
import { supabase } from "@/lib/supabase";
import { fetchDomains, createDomain } from "@/lib/api";
import { useTheme } from "@/components/ThemeProvider";

export default function LoginPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const router = useRouter();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pendingDomain, setPendingDomain] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      const dom =
        urlParams.get("domain") || localStorage.getItem("pending_audit_domain");
      if (dom) {
        setPendingDomain(dom);
      }
    }
  }, []);

  const handlePostLoginRedirect = async () => {
    let domainToAudit = pendingDomain;
    if (!domainToAudit && typeof window !== "undefined") {
      const urlParams = new URLSearchParams(window.location.search);
      domainToAudit =
        urlParams.get("domain") || localStorage.getItem("pending_audit_domain");
    }

    if (!domainToAudit) {
      router.push("/dashboard");
      return;
    }

    try {
      const cleanHost = domainToAudit
        .replace(/^https?:\/\//i, "")
        .replace(/\/.*$/, "")
        .trim()
        .toLowerCase();

      const domains = await fetchDomains();
      let found = domains.find((d) => d.hostname.toLowerCase() === cleanHost);

      if (!found) {
        found = await createDomain(cleanHost);
      }

      if (typeof window !== "undefined") {
        localStorage.removeItem("pending_audit_domain");
      }

      router.push(`/domains/${found.id}`);
    } catch {
      router.push("/dashboard");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      if (isSignUp) {
        const { error: signUpError } = await supabase.auth.signUp({
          email,
          password,
        });
        if (signUpError) throw signUpError;
        setMessage("Confirmation email sent. Please check your inbox.");
      } else {
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (signInError) throw signInError;
        await handlePostLoginRedirect();
      }
    } catch (err: any) {
      setError(err.message || "Authentication request failed.");
    } finally {
      setLoading(false);
    }
  };

  const isDevBypassAllowed =
    process.env.NODE_ENV === "development" ||
    process.env.NEXT_PUBLIC_ENABLE_DEV_AUTH_BYPASS === "true";

  const handleDevLogin = async () => {
    if (!isDevBypassAllowed) return;
    const mockToken = `test-token-00000000-0000-0000-0000-000000000001-demo@example.com`;
    localStorage.setItem("dev_mock_token", mockToken);
    await handlePostLoginRedirect();
  };

  return (
    <div className="max-w-5xl mx-auto my-8 sm:my-14 px-3 sm:px-6 font-sans">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
        {/* Contextual Security & Telemetry Panel (Desktop Left, Mobile Bottom) */}
        <div className="order-2 lg:order-1 lg:col-span-7 space-y-6">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs text-zinc-500 font-medium">
              Console &mdash; Continuous security assessment
            </span>
            <div
              className={`h-[1px] w-12 ${
                isDark ? "bg-zinc-800" : "bg-zinc-300"
              }`}
            />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl sm:text-3xl font-normal tracking-tight">
              Automated perimeter verification for Indian web applications
            </h2>
            <p
              className={`text-xs sm:text-sm leading-relaxed font-light max-w-lg ${
                isDark ? "text-zinc-400" : "text-zinc-600"
              }`}
            >
              Sign in to manage verified hostnames, trigger non-destructive TLS
              1.3 handshakes, and download executive compliance reports aligned
              with Section 8(5) of the Digital Personal Data Protection Act, 2023.
            </p>
          </div>

          {/* Product Telemetry Snippet */}
          <div
            className={`rounded-xl border transition-all overflow-hidden ${
              isDark
                ? "border-zinc-800 bg-[#121215] shadow-sm text-zinc-200"
                : "border-zinc-200 bg-white shadow-[0_1px_3px_rgba(0,0,0,0.05)] text-zinc-800"
            }`}
          >
            {/* Telemetry Header */}
            <div
              className={`px-4 py-2.5 border-b flex items-center justify-between text-xs font-mono ${
                isDark
                  ? "border-zinc-800/80 bg-zinc-950/70"
                  : "border-zinc-100 bg-zinc-50"
              }`}
            >
              <div className="flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-teal-400" />
                <span className="text-zinc-400">auth_telemetry</span>
                <span className="text-zinc-600">/</span>
                <span className="text-zinc-200 font-medium">transport_guard</span>
              </div>
              <span className="text-[11px] text-zinc-500 font-mono">
                Live monitor
              </span>
            </div>

            {/* Telemetry Rows */}
            <div className="p-4 space-y-2 font-mono text-[11px]">
              <div className="flex items-center justify-between p-2 rounded bg-zinc-900/60 border border-zinc-800/60">
                <div className="flex items-center gap-2 truncate pr-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-400 shrink-0" />
                  <span className="text-zinc-300 truncate">
                    Domain ownership verification
                  </span>
                </div>
                <span className="text-teal-400 shrink-0">Enforced</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-zinc-900/60 border border-zinc-800/60">
                <div className="flex items-center gap-2 truncate pr-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-400 shrink-0" />
                  <span className="text-zinc-300 truncate">
                    TLS 1.3 cryptographic handshake
                  </span>
                </div>
                <span className="text-teal-400 shrink-0">Active</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-zinc-900/60 border border-zinc-800/60">
                <div className="flex items-center gap-2 truncate pr-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-amber-400 shrink-0" />
                  <span className="text-zinc-300 truncate">
                    Security headers (CSP, HSTS) audit
                  </span>
                </div>
                <span className="text-amber-400 shrink-0">Automated</span>
              </div>

              <div className="flex items-center justify-between p-2 rounded bg-zinc-900/60 border border-zinc-800/60">
                <div className="flex items-center gap-2 truncate pr-2">
                  <span className="w-1.5 h-1.5 rounded-full bg-teal-400 shrink-0" />
                  <span className="text-zinc-300 truncate">
                    DPDP Act 2023 Section 8(5) triage
                  </span>
                </div>
                <span className="text-zinc-400 shrink-0">Mapped</span>
              </div>
            </div>

            {/* Telemetry Footer */}
            <div
              className={`px-4 py-2 border-t flex items-center justify-between text-[11px] font-mono text-zinc-500 ${
                isDark
                  ? "border-zinc-800/80 bg-zinc-950/40"
                  : "border-zinc-100 bg-zinc-50/50"
              }`}
            >
              <span className="flex items-center gap-1.5">
                <Shield className="w-3.5 h-3.5 text-teal-400" />
                Non-destructive perimeter probe
              </span>
              <span>Scope guard active</span>
            </div>
          </div>

          {/* Compliance & Trust Guarantees */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 text-xs font-mono text-zinc-400">
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
              <span className="text-[11px] leading-relaxed">
                Cryptographic proof of domain ownership required before scanning
              </span>
            </div>
            <div className="flex items-start gap-2">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-400 shrink-0 mt-0.5" />
              <span className="text-[11px] leading-relaxed">
                Actionable remediation snippets with copy-paste web server configs
              </span>
            </div>
          </div>
        </div>

        {/* Authentication Card (Desktop Right, Mobile First) */}
        <div className="order-1 lg:order-2 lg:col-span-5">
          <div
            className={`p-5 sm:p-7 rounded-xl border space-y-6 ${
              isDark
                ? "border-zinc-800 bg-[#121215] shadow-sm"
                : "border-zinc-200 bg-white shadow-sm"
            }`}
          >
            <div className="space-y-1.5">
              <h1 className="text-xl font-normal tracking-tight">
                {isSignUp ? "Create an account" : "Sign in to console"}
              </h1>
              <p
                className={`text-xs ${
                  isDark ? "text-zinc-400" : "text-zinc-600"
                }`}
              >
                {isSignUp
                  ? "Start automated vulnerability audits for your domain"
                  : "Access your continuous security assessment reports"}
              </p>
            </div>

            {/* Pending Domain Context Banner */}
            {pendingDomain && (
              <div
                className={`p-3 rounded-lg border text-xs font-mono flex items-center gap-2.5 ${
                  isDark
                    ? "border-teal-500/30 bg-teal-500/10 text-teal-300"
                    : "border-teal-300 bg-teal-50 text-teal-800"
                }`}
              >
                <Globe className="w-4 h-4 shrink-0 text-teal-400" />
                <div>
                  <span className="font-semibold block">{pendingDomain}</span>
                  <span className="text-[11px] opacity-80">
                    Sign in to proceed to domain ownership verification.
                  </span>
                </div>
              </div>
            )}

            {error && (
              <div
                className={`p-3 rounded-lg border text-xs font-mono flex items-center gap-2 ${
                  isDark
                    ? "border-red-900/60 bg-red-950/40 text-red-300"
                    : "border-red-200 bg-red-50 text-red-700"
                }`}
              >
                <AlertTriangle className="w-3.5 h-3.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}

            {message && (
              <div
                className={`p-3 rounded-lg border text-xs font-mono flex items-center gap-2 ${
                  isDark
                    ? "border-teal-900/60 bg-teal-950/40 text-teal-300"
                    : "border-teal-200 bg-teal-50 text-teal-700"
                }`}
              >
                <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                <span>{message}</span>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4 text-xs font-mono">
              <div>
                <label className="block text-zinc-400 text-[11px] mb-1.5">
                  Email address
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono transition-colors focus:outline-none ${
                    isDark
                      ? "bg-zinc-950 border-zinc-700 text-zinc-100 placeholder:text-zinc-500 hover:border-zinc-600 focus:border-teal-400 focus:ring-1 focus:ring-teal-400/20"
                      : "bg-zinc-50 border-zinc-300 text-zinc-900 placeholder:text-zinc-400 hover:border-zinc-400 focus:border-teal-600 focus:ring-1 focus:ring-teal-600/20"
                  }`}
                  placeholder="founder@company.in"
                />
              </div>

              <div>
                <label className="block text-zinc-400 text-[11px] mb-1.5">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className={`w-full px-3 py-2 rounded-lg border text-xs font-mono transition-colors focus:outline-none ${
                    isDark
                      ? "bg-zinc-950 border-zinc-700 text-zinc-100 placeholder:text-zinc-500 hover:border-zinc-600 focus:border-teal-400 focus:ring-1 focus:ring-teal-400/20"
                      : "bg-zinc-50 border-zinc-300 text-zinc-900 placeholder:text-zinc-400 hover:border-zinc-400 focus:border-teal-600 focus:ring-1 focus:ring-teal-600/20"
                  }`}
                  placeholder="••••••••"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className={`w-full py-2.5 px-4 rounded-lg font-mono text-xs font-medium transition-all flex items-center justify-center gap-2 ${
                  loading
                    ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                    : isDark
                    ? "bg-teal-500 hover:bg-teal-400 text-zinc-950 shadow-sm"
                    : "bg-teal-600 hover:bg-teal-500 text-white shadow-sm"
                }`}
              >
                <span>
                  {loading
                    ? "Authenticating..."
                    : isSignUp
                    ? "Create account"
                    : "Sign in"}
                </span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </form>

            <div className="text-center text-xs text-zinc-500 pt-1 font-mono">
              {isSignUp ? "Already have an account?" : "Don't have an account?"}{" "}
              <button
                type="button"
                onClick={() => {
                  setIsSignUp(!isSignUp);
                  setError(null);
                  setMessage(null);
                }}
                className="text-teal-400 hover:underline ml-1 font-medium"
              >
                {isSignUp ? "Sign in" : "Sign up"}
              </button>
            </div>

            {isDevBypassAllowed && (
              <div className="pt-4 border-t border-zinc-800/80">
                <button
                  type="button"
                  onClick={handleDevLogin}
                  className={`w-full py-2 px-3 rounded-lg border text-xs font-mono transition-colors flex items-center justify-center gap-2 ${
                    isDark
                      ? "border-zinc-800 bg-zinc-900/60 hover:bg-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-zinc-200"
                      : "border-zinc-200 bg-zinc-100 hover:bg-zinc-200 text-zinc-600 hover:text-zinc-900"
                  }`}
                >
                  <span>Dev mode test bypass</span>
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
