"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  User,
  Shield,
  CreditCard,
  KeyRound,
  LogOut,
  ArrowUpRight,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  Calendar,
  Clock,
  ArrowLeft,
} from "lucide-react";
import { supabase } from "@/lib/supabase";
import { fetchAccountBilling, AccountBillingData, BillingOrderItem } from "@/lib/api";
import { useTheme } from "@/components/ThemeProvider";

export default function AccountPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const router = useRouter();

  const [loading, setLoading] = useState(true);
  const [email, setEmail] = useState<string>("");
  const [userId, setUserId] = useState<string>("");
  const [createdAt, setCreatedAt] = useState<string>("");
  const [billingData, setBillingData] = useState<AccountBillingData | null>(null);

  // Password change state
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [passwordSuccess, setPasswordSuccess] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  useEffect(() => {
    const initializeAccount = async () => {
      try {
        setLoading(true);
        const { data: sessionData } = await supabase.auth.getSession();
        const hasDevToken =
          typeof window !== "undefined" && Boolean(localStorage.getItem("dev_mock_token"));

        if (!sessionData?.session && !hasDevToken) {
          router.push("/login");
          return;
        }

        if (sessionData?.session?.user) {
          const user = sessionData.session.user;
          setEmail(user.email || "No email registered");
          setUserId(user.id);
          setCreatedAt(user.created_at || new Date().toISOString());
        } else if (hasDevToken) {
          const mock = localStorage.getItem("dev_mock_token") || "";
          const parts = mock.split("-");
          const mockEmail = parts.length > 3 ? parts[parts.length - 1] : "demo@example.com";
          setEmail(mockEmail);
          setUserId("00000000-0000-0000-0000-000000000001");
          setCreatedAt(new Date().toISOString());
        }

        // Fetch billing subscription and orders history
        try {
          const billing = await fetchAccountBilling();
          setBillingData(billing);
        } catch (err: any) {
          // Fallback if billing endpoint is temporarily unavailable
          setBillingData({
            plan: "free",
            renewal_date: null,
            orders: [],
          });
        }
      } catch (err) {
        router.push("/login");
      } finally {
        setLoading(false);
      }
    };

    initializeAccount();
  }, [router]);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(null);

    if (!newPassword) {
      setPasswordError("Please enter a new password.");
      return;
    }

    if (newPassword.length < 8) {
      setPasswordError("Password must be at least 8 characters.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError("Passwords do not match.");
      return;
    }

    setPasswordLoading(true);
    try {
      const { data: sessionData } = await supabase.auth.getSession();
      if (sessionData?.session) {
        const { error } = await supabase.auth.updateUser({ password: newPassword });
        if (error) {
          throw error;
        }
      }
      setPasswordSuccess("Password updated successfully.");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: any) {
      setPasswordError(err.message || "Failed to update password.");
    } finally {
      setPasswordLoading(false);
    }
  };

  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch {}
    if (typeof window !== "undefined") {
      localStorage.removeItem("dev_mock_token");
    }
    router.push("/login");
  };

  const formatDate = (isoString?: string | null) => {
    if (!isoString) return "—";
    try {
      const d = new Date(isoString);
      return d.toLocaleDateString("en-IN", {
        year: "numeric",
        month: "short",
        day: "2-digit",
      });
    } catch {
      return isoString;
    }
  };

  const formatAmount = (paise: number, currency: string = "INR") => {
    const rupees = (paise / 100).toFixed(0);
    return `₹${Number(rupees).toLocaleString("en-IN")}`;
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-20 text-center font-mono text-xs text-zinc-500">
        <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-teal-400" />
        Loading account details...
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8 sm:py-12 space-y-8 font-sans">
      {/* ---------------- BREADCRUMB & HEADER ---------------- */}
      <div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-xs font-mono text-zinc-500 hover:text-zinc-300 transition-colors mb-3"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to dashboard</span>
        </Link>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-zinc-800">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-teal-400 font-medium">Account</span>
              <span className="text-zinc-600">&bull;</span>
              <span className="font-mono text-xs text-zinc-500">Settings & billing</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-normal tracking-tight">Account overview</h1>
          </div>

          <button
            onClick={handleSignOut}
            className={`px-3 py-1.5 rounded text-xs font-mono border transition-colors inline-flex items-center gap-1.5 self-start sm:self-auto ${
              isDark
                ? "border-zinc-800 text-zinc-400 hover:text-zinc-200 hover:border-zinc-700 bg-zinc-900/60"
                : "border-zinc-300 text-zinc-700 hover:bg-zinc-100 bg-white"
            }`}
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign out</span>
          </button>
        </div>
      </div>

      {/* ---------------- 1. PROFILE SECTION ---------------- */}
      <section
        className={`p-6 rounded-lg border ${
          isDark ? "border-zinc-800 bg-[#121215]" : "border-zinc-200 bg-white shadow-sm"
        }`}
      >
        <div className="flex items-center gap-2 mb-4">
          <User className="w-4 h-4 text-teal-400" />
          <h2 className="text-base font-medium">Profile</h2>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          <div className="space-y-1.5">
            <label className="block text-xs text-zinc-500">Email address</label>
            <div
              className={`p-2.5 rounded border text-xs font-mono select-all ${
                isDark ? "border-zinc-800 bg-zinc-950 text-zinc-200" : "border-zinc-200 bg-zinc-50 text-zinc-800"
              }`}
            >
              {email}
            </div>
            <p className="text-[11px] text-zinc-500">Managed through Supabase authentication.</p>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs text-zinc-500">Account created</label>
            <div
              className={`p-2.5 rounded border text-xs font-mono ${
                isDark ? "border-zinc-800 bg-zinc-950 text-zinc-200" : "border-zinc-200 bg-zinc-50 text-zinc-800"
              }`}
            >
              {formatDate(createdAt)}
            </div>
            <p className="text-[11px] text-zinc-500">Registration timestamp recorded at sign-up.</p>
          </div>
        </div>
      </section>

      {/* ---------------- 2. PLAN & SUBSCRIPTION SECTION ---------------- */}
      <section
        className={`p-6 rounded-lg border ${
          isDark ? "border-zinc-800 bg-[#121215]" : "border-zinc-200 bg-white shadow-sm"
        }`}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Shield className="w-4 h-4 text-teal-400" />
            <h2 className="text-base font-medium">Current plan</h2>
          </div>
          <Link
            href="/pricing"
            className="inline-flex items-center gap-1 text-xs font-mono text-teal-400 hover:underline"
          >
            <span>Compare all plans</span>
            <ArrowUpRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-4 rounded border border-zinc-800/80 bg-zinc-900/30">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="capitalize font-medium text-base text-zinc-100">
                {billingData?.plan || "Free"} plan
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono border border-teal-500/30 text-teal-400 bg-teal-500/10">
                Active
              </span>
            </div>
            <p className="text-xs text-zinc-400">
              {billingData?.plan === "pro"
                ? "Continuous 24-hour perimeter scans, DPDP Act compliance diffing, and bilingual reporting."
                : billingData?.plan === "full"
                ? "Deep perimeter auditing with full remediation blueprints for verified hosts."
                : "Standard baseline transport security scanning with 24-hour queue cooldown."}
            </p>
          </div>

          <div className="flex items-center gap-3 shrink-0">
            {billingData?.renewal_date ? (
              <div className="text-left sm:text-right">
                <span className="block text-[11px] text-zinc-500">Next renewal</span>
                <span className="font-mono text-xs text-zinc-200">
                  {formatDate(billingData.renewal_date)}
                </span>
              </div>
            ) : null}

            <Link
              href="/pricing"
              className={`px-3.5 py-1.5 rounded text-xs font-mono font-medium transition-opacity inline-flex items-center gap-1 ${
                isDark
                  ? "bg-white text-black hover:opacity-90"
                  : "bg-zinc-900 text-white hover:opacity-90"
              }`}
            >
              <span>{billingData?.plan === "free" ? "Upgrade plan" : "Change plan"}</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </section>

      {/* ---------------- 3. BILLING HISTORY SECTION ---------------- */}
      <section
        className={`p-6 rounded-lg border ${
          isDark ? "border-zinc-800 bg-[#121215]" : "border-zinc-200 bg-white shadow-sm"
        }`}
      >
        <div className="flex items-center gap-2 mb-4">
          <CreditCard className="w-4 h-4 text-teal-400" />
          <h2 className="text-base font-medium">Billing history</h2>
        </div>

        {billingData?.orders && billingData.orders.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-zinc-800 text-zinc-500 font-mono text-[11px]">
                  <th className="py-2.5 px-3 font-normal">Date</th>
                  <th className="py-2.5 px-3 font-normal">Plan</th>
                  <th className="py-2.5 px-3 font-normal">Amount</th>
                  <th className="py-2.5 px-3 font-normal">Status</th>
                  <th className="py-2.5 px-3 font-normal text-right">Order reference</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800/60 font-mono">
                {billingData.orders.map((order) => (
                  <tr key={order.id} className="hover:bg-zinc-900/30 transition-colors">
                    <td className="py-3 px-3 text-zinc-300">{formatDate(order.created_at)}</td>
                    <td className="py-3 px-3 capitalize text-zinc-200">{order.plan}</td>
                    <td className="py-3 px-3 text-zinc-200">{formatAmount(order.amount, order.currency)}</td>
                    <td className="py-3 px-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-[10px] capitalize ${
                          order.status === "paid"
                            ? "text-teal-400 bg-teal-500/10 border border-teal-500/20"
                            : "text-zinc-400 bg-zinc-800/50 border border-zinc-700/40"
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${
                            order.status === "paid" ? "bg-teal-400" : "bg-zinc-400"
                          }`}
                        />
                        <span>{order.status}</span>
                      </span>
                    </td>
                    <td className="py-3 px-3 text-right text-zinc-500 truncate max-w-[120px]">
                      {order.razorpay_order_id}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="py-8 px-4 text-center border border-dashed border-zinc-800 rounded">
            <p className="text-xs text-zinc-400 mb-1">No past payments recorded.</p>
            <p className="text-[11px] text-zinc-600">
              Completed invoices and upgrade transactions will appear in this log.
            </p>
          </div>
        )}
      </section>

      {/* ---------------- 4. CHANGE PASSWORD SECTION ---------------- */}
      <section
        className={`p-6 rounded-lg border ${
          isDark ? "border-zinc-800 bg-[#121215]" : "border-zinc-200 bg-white shadow-sm"
        }`}
      >
        <div className="flex items-center gap-2 mb-2">
          <KeyRound className="w-4 h-4 text-teal-400" />
          <h2 className="text-base font-medium">Change password</h2>
        </div>
        <p className="text-xs text-zinc-500 mb-6">
          Set a new password for your account. You will need to enter it on your next sign-in.
        </p>

        <form onSubmit={handlePasswordChange} className="space-y-4 max-w-md">
          {passwordSuccess && (
            <div className="p-3 rounded border border-teal-500/30 bg-teal-500/10 text-xs text-teal-300 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-teal-400 shrink-0" />
              <span>{passwordSuccess}</span>
            </div>
          )}

          {passwordError && (
            <div className="p-3 rounded border border-rose-500/30 bg-rose-500/10 text-xs text-rose-300 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 text-rose-400 shrink-0" />
              <span>{passwordError}</span>
            </div>
          )}

          <div className="space-y-1.5">
            <label className="block text-xs text-zinc-400">New password</label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              placeholder="Minimum 8 characters"
              className={`w-full px-3 py-2 rounded text-xs border font-mono transition-colors focus:outline-none ${
                isDark
                  ? "border-zinc-800 bg-zinc-950 text-zinc-200 focus:border-zinc-600"
                  : "border-zinc-300 bg-white text-zinc-800 focus:border-zinc-500"
              }`}
            />
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs text-zinc-400">Confirm password</label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Re-enter new password"
              className={`w-full px-3 py-2 rounded text-xs border font-mono transition-colors focus:outline-none ${
                isDark
                  ? "border-zinc-800 bg-zinc-950 text-zinc-200 focus:border-zinc-600"
                  : "border-zinc-300 bg-white text-zinc-800 focus:border-zinc-500"
              }`}
            />
          </div>

          <button
            type="submit"
            disabled={passwordLoading}
            className={`px-4 py-2 rounded text-xs font-mono transition-colors border flex items-center gap-2 ${
              isDark
                ? "border-zinc-700 text-zinc-200 hover:border-zinc-500 hover:bg-zinc-900 bg-zinc-900/60"
                : "border-zinc-300 text-zinc-800 hover:bg-zinc-100 bg-white"
            } disabled:opacity-50`}
          >
            {passwordLoading && <RefreshCw className="w-3.5 h-3.5 animate-spin text-teal-400" />}
            <span>{passwordLoading ? "Updating..." : "Save password"}</span>
          </button>
        </form>
      </section>

      {/* ---------------- 5. SESSION & LOGOUT SECTION ---------------- */}
      <section
        className={`p-6 rounded-lg border flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
          isDark ? "border-zinc-800 bg-[#121215]" : "border-zinc-200 bg-white shadow-sm"
        }`}
      >
        <div className="space-y-1">
          <h2 className="text-base font-medium">Session management</h2>
          <p className="text-xs text-zinc-500">
            Terminate the active browser authentication session.
          </p>
        </div>

        <button
          onClick={handleSignOut}
          className={`px-4 py-2 rounded text-xs font-mono border transition-colors inline-flex items-center gap-2 shrink-0 ${
            isDark
              ? "border-zinc-800 text-zinc-300 hover:text-white hover:border-zinc-700 hover:bg-zinc-900"
              : "border-zinc-300 text-zinc-700 hover:bg-zinc-100"
          }`}
        >
          <LogOut className="w-3.5 h-3.5" />
          <span>Sign out of session</span>
        </button>
      </section>
    </div>
  );
}
