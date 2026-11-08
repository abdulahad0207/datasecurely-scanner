"use client";

import React, { useEffect, useState } from "react";
import Link from "next/link";
import Script from "next/script";
import {
  CheckCircle2,
  ArrowUpRight,
  Shield,
  ShieldCheck,
  Zap,
  HelpCircle,
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { fetchPlans, createBillingOrder, Plan } from "@/lib/api";
import { useTheme } from "@/components/ThemeProvider";

declare global {
  interface Window {
    Razorpay?: any;
  }
}

export default function PricingPage() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [plans, setPlans] = useState<Plan[]>([]);
  const [loading, setLoading] = useState(true);
  const [processingPlan, setProcessingPlan] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [expandedMobilePlans, setExpandedMobilePlans] = useState<Record<string, boolean>>({});

  useEffect(() => {
    const loadPlans = async () => {
      try {
        const data = await fetchPlans();
        setPlans(data || []);
      } catch (err: any) {
        console.error("Failed to load plans:", err);
      } finally {
        setLoading(false);
      }
    };
    loadPlans();
  }, []);

  const toggleMobileFeatures = (planId: string) => {
    setExpandedMobilePlans((prev) => ({
      ...prev,
      [planId]: !prev[planId],
    }));
  };

  const handleCheckout = async (planId: string) => {
    if (planId === "free") {
      window.location.href = "/dashboard";
      return;
    }

    try {
      setProcessingPlan(planId);
      setNotice(null);
      const order = await createBillingOrder(planId);

      if (typeof window !== "undefined" && window.Razorpay) {
        const options = {
          key: order.key_id,
          amount: order.amount,
          currency: order.currency,
          name: "datasecurely Scanner",
          description: `Upgrade to ${planId} plan`,
          order_id: order.razorpay_order_id.startsWith("order_mock_")
            ? undefined
            : order.razorpay_order_id,
          handler: function (response: any) {
            setNotice("Payment received. Upgrading account permissions...");
            setTimeout(() => {
              window.location.href = `/dashboard?payment=success&plan=${planId}`;
            }, 1200);
          },
          prefill: {
            name: "SMB Business Owner",
            email: "owner@business.in",
          },
          theme: {
            color: isDark ? "#2dd4bf" : "#0d9488",
          },
        };

        if (order.razorpay_order_id.startsWith("order_mock_")) {
          const confirmMock = window.confirm(
            `[DEV SIMULATION] Razorpay test order created (${order.razorpay_order_id}). Simulate successful payment?`
          );
          if (confirmMock) {
            setNotice("Simulating test payment completion...");
            setTimeout(() => {
              window.location.href = `/dashboard?payment=success&plan=${planId}`;
            }, 1000);
          }
        } else {
          const rzp = new window.Razorpay(options);
          rzp.open();
        }
      } else {
        alert("Payment gateway is initializing. Please try again in a moment.");
      }
    } catch (err: any) {
      alert(err.message || "Failed to initiate payment. Please try again.");
    } finally {
      setProcessingPlan(null);
    }
  };

  const formatPrice = (priceInr: number) => {
    return `₹${priceInr.toLocaleString("en-IN")}`;
  };

  const formatCycle = (cycle: string) => {
    switch (cycle.toLowerCase()) {
      case "one_time":
        return "one-time";
      case "monthly":
        return "/ month";
      case "forever":
        return "forever";
      default:
        return cycle.replace("_", "-");
    }
  };

  const isStandoutFeature = (feat: string) => {
    const keywords = [
      "Gemini AI",
      "Actionable fix",
      "weekly recurring",
      "change-detection",
      "agency branding",
      "A–F Security Score",
      "Priority Gemini",
    ];
    return keywords.some((kw) => feat.toLowerCase().includes(kw.toLowerCase()));
  };

  return (
    <>
      <Script src="https://checkout.razorpay.com/v1/checkout.js" strategy="lazyOnload" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 space-y-12 font-sans">
        {/* Header Section */}
        <div className="text-center space-y-3 max-w-2xl mx-auto">
          <div className="inline-flex items-center gap-2 font-mono text-xs text-teal-400 font-medium">
            <Shield className="w-3.5 h-3.5" />
            <span>Transparent pricing for Indian businesses</span>
          </div>
          <h1 className="text-3xl sm:text-4xl font-normal tracking-tight">
            Security plans that scale with your growth
          </h1>
          <p className={`text-xs sm:text-sm ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
            Automated vulnerability scans, TLS verification, and DPDP Act 2023 compliance auditing. Cancel or upgrade anytime.
          </p>
        </div>

        {/* Notice Banner */}
        {notice && (
          <div className="max-w-xl mx-auto p-3.5 rounded border border-teal-500/40 bg-teal-500/10 text-teal-400 text-xs font-mono text-center">
            {notice}
          </div>
        )}

        {/* Plans Grid: Proper 4-Column Grid on Wide Desktop, 2x2 on Medium, Stacked on Mobile */}
        {loading ? (
          <div className="py-16 text-center font-mono text-xs text-zinc-500">
            <RefreshCw className="w-5 h-5 mx-auto mb-2 animate-spin text-teal-400" />
            Loading subscription tiers...
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan) => {
              const isPopular = plan.id === "pro";
              const isExpanded = Boolean(expandedMobilePlans[plan.id]);
              const visibleFeatures = isExpanded ? plan.features : plan.features.slice(0, 3);
              const hasHiddenFeatures = plan.features.length > 3;

              return (
                <div
                  key={plan.id}
                  className={`p-6 rounded-lg border transition-all flex flex-col justify-between ${
                    isPopular
                      ? isDark
                        ? "border-teal-500/60 bg-[#14181a] shadow-sm ring-1 ring-teal-500/20"
                        : "border-teal-600/60 bg-teal-50/20 shadow-sm ring-1 ring-teal-600/20"
                      : isDark
                      ? "border-zinc-800 bg-[#121215]"
                      : "border-zinc-200 bg-white shadow-sm"
                  }`}
                >
                  <div className="space-y-4">
                    {/* Card Header & Title */}
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-1">
                        <h3 className="text-base font-medium tracking-tight capitalize">
                          {plan.name}
                        </h3>
                        {isPopular && (
                          <span className="text-[10px] font-mono text-teal-400 font-medium shrink-0 pt-0.5">
                            Most popular
                          </span>
                        )}
                      </div>
                      <p className={`text-xs leading-relaxed min-h-[36px] ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
                        {plan.tagline}
                      </p>
                    </div>

                    {/* Price Block: Proper Number Formatting with Commas and Suffix */}
                    <div className="pt-3 border-t border-zinc-800/60">
                      <div className="flex items-baseline gap-1.5 whitespace-nowrap">
                        <span className="text-2xl sm:text-3xl font-light tracking-tight font-mono">
                          {formatPrice(plan.price_inr)}
                        </span>
                        <span className="text-xs text-zinc-500 font-mono">
                          {formatCycle(plan.billing_cycle)}
                        </span>
                      </div>
                    </div>

                    {/* Feature Checklist: High-Value Features Highlighted vs Baseline */}
                    <div className="pt-3 border-t border-zinc-800/60 space-y-2.5 text-xs font-mono">
                      {/* Mobile Visible Features */}
                      <div className="block sm:hidden space-y-2.5">
                        {visibleFeatures.map((feat, idx) => {
                          const standout = isStandoutFeature(feat);
                          return (
                            <div key={idx} className="flex items-start gap-2">
                              <CheckCircle2
                                className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${
                                  standout ? "text-teal-400" : "text-zinc-500"
                                }`}
                              />
                              <span
                                className={
                                  standout
                                    ? isDark
                                      ? "text-zinc-100 font-medium"
                                      : "text-zinc-900 font-medium"
                                    : isDark
                                    ? "text-zinc-400"
                                    : "text-zinc-600"
                                }
                              >
                                {feat}
                              </span>
                            </div>
                          );
                        })}

                        {/* Mobile Expand / Collapse Feature List Toggle */}
                        {hasHiddenFeatures && (
                          <button
                            onClick={() => toggleMobileFeatures(plan.id)}
                            className="inline-flex items-center gap-1 text-[11px] text-teal-400 hover:underline pt-1"
                          >
                            <span>
                              {isExpanded
                                ? "Show fewer features"
                                : `Show all ${plan.features.length} features`}
                            </span>
                            {isExpanded ? (
                              <ChevronUp className="w-3 h-3" />
                            ) : (
                              <ChevronDown className="w-3 h-3" />
                            )}
                          </button>
                        )}
                      </div>

                      {/* Desktop All Features Display */}
                      <div className="hidden sm:block space-y-2.5">
                        {plan.features.map((feat, idx) => {
                          const standout = isStandoutFeature(feat);
                          return (
                            <div key={idx} className="flex items-start gap-2">
                              <CheckCircle2
                                className={`w-3.5 h-3.5 mt-0.5 shrink-0 ${
                                  standout ? "text-teal-400" : "text-zinc-500"
                                }`}
                              />
                              <span
                                className={
                                  standout
                                    ? isDark
                                      ? "text-zinc-100 font-medium"
                                      : "text-zinc-900 font-medium"
                                    : isDark
                                    ? "text-zinc-400"
                                    : "text-zinc-600"
                                }
                              >
                                {feat}
                              </span>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {/* Card Action Button */}
                  <div className="pt-6 mt-6 border-t border-zinc-800/60">
                    <button
                      onClick={() => handleCheckout(plan.id)}
                      disabled={processingPlan === plan.id}
                      className={`w-full py-2.5 px-4 rounded text-xs font-mono font-medium transition-opacity flex items-center justify-center gap-1.5 ${
                        processingPlan === plan.id
                          ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                          : isPopular
                          ? "bg-teal-500 hover:bg-teal-400 text-black"
                          : isDark
                          ? "bg-white text-black hover:opacity-90"
                          : "bg-zinc-900 text-white hover:opacity-90"
                      }`}
                    >
                      <span>
                        {processingPlan === plan.id
                          ? "Initiating checkout..."
                          : plan.id === "free"
                          ? "Get started free"
                          : `Upgrade to ${plan.name}`}
                      </span>
                      <ArrowUpRight className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}

        {/* ---------------- ENTERPRISE & COMPLIANCE GUARANTEE ---------------- */}
        <div
          className={`p-6 sm:p-8 rounded-lg border max-w-4xl mx-auto transition-colors ${
            isDark
              ? "border-zinc-800 bg-[#121215]"
              : "border-zinc-200 bg-white shadow-sm"
          }`}
        >
          <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 pb-6 border-b border-zinc-800/60">
            <div className="space-y-1">
              <div className="flex items-center gap-2 font-mono text-xs text-teal-400 font-medium">
                <ShieldCheck className="w-4 h-4 text-teal-400 shrink-0" />
                <span>Enterprise & compliance guarantee</span>
              </div>
              <h2 className="text-lg font-medium tracking-tight">
                DPDP Act 2023 statutory safeguard verification
              </h2>
            </div>

            <div className="flex flex-wrap gap-2 text-[11px] font-mono">
              <span
                className={`px-2.5 py-1 rounded border ${
                  isDark
                    ? "border-zinc-800 bg-zinc-900/60 text-zinc-300"
                    : "border-zinc-200 bg-zinc-100 text-zinc-700"
                }`}
              >
                Section 8(5) compliant
              </span>
              <span
                className={`px-2.5 py-1 rounded border ${
                  isDark
                    ? "border-zinc-800 bg-zinc-900/60 text-zinc-300"
                    : "border-zinc-200 bg-zinc-100 text-zinc-700"
                }`}
              >
                Non-destructive testing
              </span>
            </div>
          </div>

          <div className="pt-6 grid grid-cols-1 md:grid-cols-2 gap-6 text-xs leading-relaxed font-sans">
            <div className="space-y-2">
              <p className={isDark ? "text-zinc-300" : "text-zinc-700"}>
                All DataSecurely perimeter scans operate strictly under non-invasive transport verification mandates. We never execute destructive SQL injections, intrusive payloads, or denial-of-service simulations.
              </p>
            </div>
            <div className="space-y-2">
              <p className={isDark ? "text-zinc-400" : "text-zinc-600"}>
                Generated audit reports serve as evidentiary documentation to demonstrate reasonable cybersecurity safeguards under Section 8(5) of the Indian Digital Personal Data Protection Act, 2023.
              </p>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
