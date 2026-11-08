"use client";

import React, { useState } from "react";
import {
  AlertTriangle,
  ChevronDown,
  ChevronUp,
  Copy,
  Check,
  Terminal,
  ShieldAlert,
} from "lucide-react";
import { Finding } from "@/lib/api";
import { useTheme } from "./ThemeProvider";

const SEVERITY_BADGES: Record<string, { border: string; bg: string; text: string }> = {
  critical: {
    border: "border-red-500/40",
    bg: "bg-red-500/10",
    text: "text-red-400",
  },
  high: {
    border: "border-amber-500/40",
    bg: "bg-amber-500/10",
    text: "text-amber-400",
  },
  medium: {
    border: "border-yellow-500/40",
    bg: "bg-yellow-500/10",
    text: "text-yellow-400",
  },
  low: {
    border: "border-teal-500/40",
    bg: "bg-teal-500/10",
    text: "text-teal-400",
  },
  info: {
    border: "border-zinc-700",
    bg: "bg-zinc-800/60",
    text: "text-zinc-400",
  },
};

export default function FindingCard({ finding }: { finding: Finding }) {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  const [expanded, setExpanded] = useState(false);
  const [copiedEvidence, setCopiedEvidence] = useState(false);

  const badge =
    SEVERITY_BADGES[finding.severity?.toLowerCase()] || SEVERITY_BADGES.info;

  const handleCopyEvidence = () => {
    if (!finding.evidence) return;
    navigator.clipboard?.writeText(finding.evidence);
    setCopiedEvidence(true);
    setTimeout(() => setCopiedEvidence(false), 2000);
  };

  return (
    <div
      className={`p-5 rounded-lg border transition-colors space-y-3 font-sans ${
        isDark ? "border-zinc-800 bg-zinc-900/30" : "border-zinc-200 bg-white shadow-sm"
      }`}
    >
      {/* Header: Severity Badge, Title, Tool */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5">
        <div className="flex items-center gap-3">
          <span
            className={`px-2 py-0.5 rounded text-[11px] font-mono capitalize border ${badge.border} ${badge.bg} ${badge.text}`}
          >
            {finding.severity}
          </span>
          <h4 className="font-medium text-sm tracking-tight">{finding.title}</h4>
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-zinc-500">
          <span>Source:</span>
          <span className={isDark ? "text-zinc-300" : "text-zinc-700"}>
            {finding.source_tool}
          </span>
        </div>
      </div>

      {/* Target & Template Metadata */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs font-mono text-zinc-500">
        <span>
          Host:{" "}
          <strong className={isDark ? "text-zinc-300 font-normal" : "text-zinc-800 font-normal"}>
            {finding.host}
          </strong>
        </span>
        <span>&bull;</span>
        <span>
          Rule: <code className="text-zinc-400">{finding.template_id}</code>
        </span>
      </div>

      {/* Observed Raw Evidence */}
      {finding.evidence && (
        <div
          className={`p-3 rounded border space-y-1.5 ${
            isDark ? "border-zinc-800 bg-zinc-950" : "border-zinc-200 bg-zinc-50"
          }`}
        >
          <div className="flex items-center justify-between text-[11px] font-mono text-zinc-500">
            <span>Observed telemetry evidence</span>
            <button
              onClick={handleCopyEvidence}
              className="hover:text-teal-400 transition-colors flex items-center gap-1"
            >
              {copiedEvidence ? (
                <>
                  <Check className="w-3 h-3 text-teal-400" />
                  <span className="text-teal-400">Copied</span>
                </>
              ) : (
                <>
                  <Copy className="w-3 h-3" />
                  <span>Copy</span>
                </>
              )}
            </button>
          </div>
          <pre className="text-xs font-mono text-zinc-400 break-all whitespace-pre-wrap max-h-28 overflow-y-auto">
            {finding.evidence}
          </pre>
        </div>
      )}

      {/* AI Triage Guidance Accordion */}
      {finding.ai_json && (
        <div className="pt-2 border-t border-zinc-800/60">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs font-mono text-teal-400 hover:underline flex items-center gap-1.5"
          >
            <Terminal className="w-3.5 h-3.5" />
            <span>{expanded ? "Hide remediation advisory" : "View remediation advisory"}</span>
            {expanded ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
          </button>

          {expanded && (
            <div
              className={`mt-3 p-4 rounded border space-y-2 text-xs font-mono ${
                isDark ? "border-teal-500/20 bg-teal-500/5 text-zinc-300" : "border-teal-600/20 bg-teal-50/50 text-zinc-800"
              }`}
            >
              <div>
                <span className="text-teal-400 font-semibold block mb-0.5">Plain summary</span>
                <p className="leading-relaxed opacity-90">{finding.ai_json.plain_summary}</p>
              </div>

              {finding.ai_json.business_impact && (
                <div className="pt-2 border-t border-teal-500/10">
                  <span className="text-teal-400 font-semibold block mb-0.5">Business & DPDP impact</span>
                  <p className="leading-relaxed opacity-90">{finding.ai_json.business_impact}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
