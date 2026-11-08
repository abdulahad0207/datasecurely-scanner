"use client";

import React, { useEffect, useRef, useState } from "react";
import {
  Globe,
  ArrowUpRight,
  Shield,
  CheckCircle2,
  AlertTriangle,
  Info,
  Sun,
  Moon,
  X,
  Copy,
  Check,
  RefreshCw,
  Trash2,
  Clock,
  Lock,
  Server,
  Layers,
  Code2,
  FileText,
  Sliders,
  ExternalLink,
  ChevronRight,
  Activity,
  Zap,
} from "lucide-react";

export default function PreviewPage() {
  const [viewMode, setViewMode] = useState<"landing" | "dashboard">("dashboard");
  const [theme, setTheme] = useState<"dark" | "light">("dark");
  const [domainInput, setDomainInput] = useState("example.com");
  const [isScanning, setIsScanning] = useState(false);
  const [scanProgress, setScanProgress] = useState(0);
  const [scanStageText, setScanStageText] = useState("Ready to initiate audit");
  const [activeStage, setActiveStage] = useState<number>(0);
  const [findings, setFindings] = useState<any[]>([]);
  const [gradeResult, setGradeResult] = useState<any | null>(null);
  const [isReportOpen, setIsReportOpen] = useState(false);
  const [reportLang, setReportLang] = useState<"en" | "hi">("en");
  const [activePillar, setActivePillar] = useState<"detect" | "analyze" | "secure">("detect");

  // Dashboard interactive state
  const [newHostname, setNewHostname] = useState("");
  const [dashFilter, setDashFilter] = useState<"all" | "verified" | "pending">("all");
  const [activeVerifyDomain, setActiveVerifyDomain] = useState<any | null>(null);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [activeAuditingDomainId, setActiveAuditingDomainId] = useState<string | null>(null);
  const [auditProgress, setAuditProgress] = useState<number>(0);

  const [domainsList, setDomainsList] = useState<any[]>([
    {
      id: "dom-1",
      hostname: "app.example.in",
      status: "verified",
      isMonitored: true,
      lastScanned: "18 minutes ago",
      grade: "A",
      score: 92,
      findingsCount: 1,
      criticalCount: 0,
      highCount: 0,
      mediumCount: 1,
      diff: { new: 0, resolved: 3, persistent: 1 },
      txtRecord: "datasecurely-verification=txt-8f3a92c4b1",
      wellKnownUrl: "/.well-known/datasecurely-verify.txt",
      tlsVersion: "TLS 1.3",
      cspStatus: "Enforced (Strict nonce)",
      hsts: "max-age=63072000; preload",
      dpdpReady: true,
    },
    {
      id: "dom-2",
      hostname: "api.example.in",
      status: "verified",
      isMonitored: false,
      lastScanned: "Yesterday at 16:40",
      grade: "B+",
      score: 84,
      findingsCount: 3,
      criticalCount: 0,
      highCount: 1,
      mediumCount: 2,
      diff: { new: 1, resolved: 1, persistent: 2 },
      txtRecord: "datasecurely-verification=txt-21b790d98f",
      wellKnownUrl: "/.well-known/datasecurely-verify.txt",
      tlsVersion: "TLS 1.3",
      cspStatus: "Report-only mode",
      hsts: "max-age=31536000",
      dpdpReady: false,
    },
    {
      id: "dom-3",
      hostname: "staging.portal.in",
      status: "pending",
      isMonitored: false,
      lastScanned: "Never audited",
      grade: "—",
      score: null,
      findingsCount: 0,
      criticalCount: 0,
      highCount: 0,
      mediumCount: 0,
      diff: null,
      txtRecord: "datasecurely-verification=txt-9e61c77042",
      wellKnownUrl: "/.well-known/datasecurely-verify.txt",
      tlsVersion: "Pending verification",
      cspStatus: "Pending verification",
      hsts: "Pending verification",
      dpdpReady: false,
    },
  ]);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  // -------------------------------------------------------------
  // Dynamic 3D Particle Mesh Canvas
  // -------------------------------------------------------------
  useEffect(() => {
    if (viewMode !== "landing") return;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = canvas.parentElement?.clientWidth || 500);
    let height = (canvas.height = canvas.parentElement?.clientHeight || 450);

    const handleResize = () => {
      if (!canvas || !canvas.parentElement) return;
      width = canvas.width = canvas.parentElement.clientWidth;
      height = canvas.height = canvas.parentElement.clientHeight;
    };
    window.addEventListener("resize", handleResize);

    const NUM_PARTICLES = 550;
    const RADIUS = 130;
    const particles: { x: number; y: number; z: number }[] = [];

    for (let i = 0; i < NUM_PARTICLES; i++) {
      const phi = Math.acos(1 - (2 * (i + 0.5)) / NUM_PARTICLES);
      const theta = Math.PI * (1 + Math.sqrt(5)) * (i + 0.5);
      particles.push({
        x: RADIUS * Math.sin(phi) * Math.cos(theta),
        y: RADIUS * Math.sin(phi) * Math.sin(theta),
        z: RADIUS * Math.cos(phi),
      });
    }

    let rotX = 0.2;
    let rotY = 0;
    let targetX = 0.2;
    let targetY = 0;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left - width / 2;
      const mouseY = e.clientY - rect.top - height / 2;
      targetY = mouseX * 0.0012;
      targetX = -mouseY * 0.0012;
    };
    window.addEventListener("mousemove", handleMouseMove);

    const render = () => {
      ctx.clearRect(0, 0, width, height);

      rotX += (targetX - rotX) * 0.05;
      rotY += (targetY - rotY) * 0.05 + 0.002;

      const cosX = Math.cos(rotX);
      const sinX = Math.sin(rotX);
      const cosY = Math.cos(rotY);
      const sinY = Math.sin(rotY);

      const cx = width * 0.52;
      const cy = height * 0.5;

      const isDarkMode = theme === "dark";

      for (let i = 0; i < NUM_PARTICLES; i++) {
        const p = particles[i];
        const x1 = p.x * cosY - p.z * sinY;
        const z1 = p.z * cosY + p.x * sinY;
        const y2 = p.y * cosX - z1 * sinX;
        const z2 = z1 * cosX + p.y * sinX;

        const fov = 340;
        const scale = fov / (fov + z2);
        const projX = cx + x1 * scale;
        const projY = cy + y2 * scale;

        const alpha = Math.max(0.12, (z2 + RADIUS) / (2 * RADIUS));
        const dotSize = Math.max(1, 1.8 * scale);

        ctx.beginPath();
        ctx.arc(projX, projY, dotSize, 0, Math.PI * 2);
        ctx.fillStyle = isDarkMode
          ? `rgba(244, 244, 245, ${alpha * 0.75})`
          : `rgba(24, 24, 27, ${alpha * 0.65})`;
        ctx.fill();

        if (i % 12 === 0 && isScanning) {
          ctx.beginPath();
          ctx.arc(projX, projY, dotSize * 1.5, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(20, 184, 166, ${alpha * 0.9})`;
          ctx.fill();
        }
      }

      ctx.beginPath();
      ctx.arc(cx, cy, 14, 0, Math.PI * 2);
      ctx.fillStyle = isDarkMode ? "#ffffff" : "#18181b";
      ctx.fill();

      ctx.beginPath();
      ctx.arc(cx, cy, 5, 0, Math.PI * 2);
      ctx.fillStyle = isDarkMode ? "#09090b" : "#fbfbfa";
      ctx.fill();

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("mousemove", handleMouseMove);
    };
  }, [theme, isScanning, viewMode]);

  // -------------------------------------------------------------
  // Scan Simulator Engine
  // -------------------------------------------------------------
  const stages = [
    { name: "Scope Guard", desc: "Validating SSRF boundaries and public IP range" },
    { name: "Recon & Discovery", desc: "Enumerating TLS ciphers, CORS policies, CSP nonces" },
    { name: "Vulnerability Scan", desc: "Executing active payload checks and cookie flags" },
    { name: "Score Calculation", desc: "Applying CVSS-aligned security matrix" },
    { name: "AI Triage & Synthesis", desc: "Generating bilingual remediation advisory" },
  ];

  const handleStartScan = (targetHost?: string) => {
    const host = targetHost || domainInput.trim() || "example.com";
    setIsScanning(true);
    setScanProgress(0);
    setActiveStage(0);
    setFindings([]);
    setGradeResult(null);

    const stageIntervals = [
      { progress: 18, stage: 0, text: `Validating scope guard for ${host}` },
      { progress: 42, stage: 1, text: "Enumerating TLS 1.3 ciphers and CORS headers" },
      { progress: 71, stage: 2, text: "Scanning CSP directives and session cookie flags" },
      { progress: 88, stage: 3, text: "Calculating domain risk score and security grade" },
      { progress: 100, stage: 4, text: "Audit complete. Bilingual report ready." },
    ];

    stageIntervals.forEach((item, index) => {
      setTimeout(() => {
        setScanProgress(item.progress);
        setActiveStage(item.stage);
        setScanStageText(item.text);

        if (index === 2) {
          setFindings([
            {
              id: "f1",
              severity: "high",
              title: "Content Security Policy missing script nonce",
              rule: "CWE-79",
              target: "script-src 'unsafe-inline'",
            },
            {
              id: "f2",
              severity: "medium",
              title: "Session cookie without SameSite=Lax attribute",
              rule: "CWE-1275",
              target: "Set-Cookie: session_id",
            },
            {
              id: "f3",
              severity: "low",
              title: "HSTS preload flag not declared in response header",
              rule: "CWE-319",
              target: "Strict-Transport-Security",
            },
          ]);
        }

        if (index === stageIntervals.length - 1) {
          setIsScanning(false);
          setGradeResult({
            grade: "B+",
            score: 84,
            status: "Audit Complete",
            host,
            timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
            dpdpCompliance: "Compliant with 1 warning",
          });
        }
      }, (index + 1) * 750);
    });
  };

  // -------------------------------------------------------------
  // Dashboard Interactive Actions
  // -------------------------------------------------------------
  const handleAddDomain = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newHostname.trim()) return;

    const cleanHost = newHostname
      .replace(/^https?:\/\//i, "")
      .replace(/\/.*$/, "")
      .toLowerCase();

    const newEntry = {
      id: `dom-${Date.now()}`,
      hostname: cleanHost,
      status: "pending",
      isMonitored: false,
      lastScanned: "Never audited",
      grade: "—",
      score: null,
      findingsCount: 0,
      criticalCount: 0,
      highCount: 0,
      mediumCount: 0,
      diff: null,
      txtRecord: `datasecurely-verification=txt-${Math.random().toString(36).substring(2, 10)}`,
      wellKnownUrl: "/.well-known/datasecurely-verify.txt",
      tlsVersion: "Pending verification",
      cspStatus: "Pending verification",
      hsts: "Pending verification",
      dpdpReady: false,
    };

    setDomainsList([newEntry, ...domainsList]);
    setNewHostname("");
    setActiveVerifyDomain(newEntry);
  };

  const handleSimulateVerify = (domainId: string) => {
    setDomainsList((prev) =>
      prev.map((d) =>
        d.id === domainId
          ? {
              ...d,
              status: "verified",
              tlsVersion: "TLS 1.3",
              cspStatus: "Enforced",
              hsts: "max-age=31536000",
              dpdpReady: true,
            }
          : d
      )
    );
    if (activeVerifyDomain?.id === domainId) {
      setActiveVerifyDomain(null);
    }
  };

  const handleToggleMonitoring = (domainId: string) => {
    setDomainsList((prev) =>
      prev.map((d) => (d.id === domainId ? { ...d, isMonitored: !d.isMonitored } : d))
    );
  };

  const handleDeleteDomain = (domainId: string, hostname: string) => {
    if (confirm(`Remove ${hostname} from domain security monitoring?`)) {
      setDomainsList((prev) => prev.filter((d) => d.id !== domainId));
    }
  };

  const handleTriggerAuditInDashboard = (domain: any) => {
    setActiveAuditingDomainId(domain.id);
    setAuditProgress(15);

    const steps = [35, 68, 90, 100];
    steps.forEach((p, idx) => {
      setTimeout(() => {
        setAuditProgress(p);
        if (p === 100) {
          setActiveAuditingDomainId(null);
          setDomainsList((prev) =>
            prev.map((d) =>
              d.id === domain.id
                ? {
                    ...d,
                    lastScanned: "Just now",
                    grade: "A",
                    score: 94,
                    findingsCount: 0,
                    diff: { new: 0, resolved: d.findingsCount, persistent: 0 },
                  }
                : d
            )
          );
        }
      }, (idx + 1) * 650);
    });
  };

  const copyToClipboard = (text: string, fieldKey: string) => {
    navigator.clipboard?.writeText(text);
    setCopiedField(fieldKey);
    setTimeout(() => setCopiedField(null), 1800);
  };

  const filteredDomains = domainsList.filter((d) => {
    if (dashFilter === "verified") return d.status === "verified";
    if (dashFilter === "pending") return d.status === "pending";
    return true;
  });

  const isDark = theme === "dark";

  return (
    <div
      className={`min-h-screen transition-colors duration-200 font-sans ${
        isDark ? "bg-[#09090b] text-zinc-100" : "bg-[#fbfbfa] text-zinc-900"
      }`}
    >
      {/* ---------------- NAVIGATION ---------------- */}
      <nav
        className={`sticky top-0 z-40 border-b backdrop-blur-md ${
          isDark
            ? "border-zinc-800/80 bg-[#09090b]/85"
            : "border-zinc-200/80 bg-[#fbfbfa]/90"
        }`}
      >
        <div className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          {/* Logo & Platform Name */}
          <div className="flex items-center gap-3">
            <div
              className={`w-7 h-7 rounded flex items-center justify-center font-mono font-bold text-xs ${
                isDark ? "bg-white text-black" : "bg-zinc-900 text-white"
              }`}
            >
              DS
            </div>
            <span className="font-medium text-sm tracking-tight">datasecurely</span>
            <span className="text-xs text-zinc-500 pl-3 border-l border-zinc-700/40 hidden sm:inline">
              Website security platform
            </span>
          </div>

          {/* View Mode Switcher: Landing vs Dashboard */}
          <div
            className={`inline-flex p-0.5 rounded border text-xs font-mono ${
              isDark ? "border-zinc-800 bg-zinc-950" : "border-zinc-300 bg-zinc-100"
            }`}
          >
            <button
              onClick={() => setViewMode("landing")}
              className={`px-3 py-1 rounded transition-colors ${
                viewMode === "landing"
                  ? isDark
                    ? "bg-zinc-800 text-white"
                    : "bg-white text-zinc-900 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              Scanner landing
            </button>
            <button
              onClick={() => setViewMode("dashboard")}
              className={`px-3 py-1 rounded transition-colors flex items-center gap-1.5 ${
                viewMode === "dashboard"
                  ? isDark
                    ? "bg-zinc-800 text-white"
                    : "bg-white text-zinc-900 shadow-sm"
                  : "text-zinc-500 hover:text-zinc-300"
              }`}
            >
              <span>Security dashboard</span>
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
            </button>
          </div>

          {/* Controls: Theme & Actions */}
          <div className="flex items-center gap-3">
            <button
              onClick={() => setTheme(isDark ? "light" : "dark")}
              className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-mono border transition-colors ${
                isDark
                  ? "border-zinc-800 text-zinc-400 hover:text-zinc-100 hover:border-zinc-700 bg-zinc-900/60"
                  : "border-zinc-200 text-zinc-600 hover:text-zinc-900 hover:border-zinc-300 bg-white"
              }`}
              title="Toggle theme preview"
            >
              {isDark ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
              <span className="capitalize">{theme}</span>
            </button>

            <a
              href="/pricing"
              className={`text-xs px-3 py-1.5 rounded border transition-colors hidden sm:inline ${
                isDark
                  ? "border-zinc-800 text-zinc-300 hover:bg-zinc-800"
                  : "border-zinc-300 text-zinc-700 hover:bg-zinc-100"
              }`}
            >
              Pricing
            </a>

            <button
              onClick={() => {
                if (viewMode === "dashboard") {
                  document.getElementById("add-domain-input")?.focus();
                } else {
                  handleStartScan();
                }
              }}
              className={`text-xs px-3.5 py-1.5 rounded font-medium inline-flex items-center gap-1.5 transition-opacity ${
                isDark ? "bg-white text-black hover:opacity-90" : "bg-zinc-900 text-white hover:opacity-90"
              }`}
            >
              <span>{viewMode === "dashboard" ? "Add domain" : "Scan website"}</span>
              <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </nav>

      {/* ============================================================= */}
      {/* VIEW 1: DOMAIN SECURITY DASHBOARD (Direct answer to screenshot) */}
      {/* ============================================================= */}
      {viewMode === "dashboard" && (
        <main className="max-w-6xl mx-auto px-6 py-10 space-y-8 animate-fadeIn">
          {/* Header Banner */}
          <div
            className={`flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b ${
              isDark ? "border-zinc-800" : "border-zinc-200"
            }`}
          >
            <div>
              <div className="flex items-center gap-2 mb-1.5">
                <span className="font-mono text-xs text-teal-400 font-medium">
                  Console &mdash; domain protection
                </span>
                <span className="text-zinc-500 text-xs">&bull;</span>
                <span className="text-xs text-zinc-500 font-mono">3 target hosts</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-normal tracking-tight">
                Domain security dashboard
              </h1>
              <p className={`text-sm mt-1 max-w-xl ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
                Add and verify domain ownership to run automated vulnerability audits and continuous DPDP Act 2023 compliance checks.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <a
                href="/pricing"
                className={`text-xs font-mono px-3.5 py-2 rounded border inline-flex items-center gap-1.5 transition-colors ${
                  isDark
                    ? "border-zinc-800 bg-zinc-900 text-zinc-300 hover:text-white hover:border-zinc-700"
                    : "border-zinc-300 bg-white text-zinc-800 hover:bg-zinc-50"
                }`}
              >
                <span>Upgrade plan</span>
                <ArrowUpRight className="w-3 h-3 text-teal-400" />
              </a>
            </div>
          </div>

          {/* Quick Metrics HUD */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div
              className={`p-4 rounded-lg border ${
                isDark ? "border-zinc-800 bg-zinc-900/30" : "border-zinc-200 bg-white"
              }`}
            >
              <div className="text-xs font-mono text-zinc-500 mb-1">Protected domains</div>
              <div className="text-2xl font-light tracking-tight">
                2 <span className="text-xs text-zinc-500 font-mono">/ 3 active</span>
              </div>
              <div className="text-xs text-teal-400 mt-2 font-mono flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" />
                <span>66% verified</span>
              </div>
            </div>

            <div
              className={`p-4 rounded-lg border ${
                isDark ? "border-zinc-800 bg-zinc-900/30" : "border-zinc-200 bg-white"
              }`}
            >
              <div className="text-xs font-mono text-zinc-500 mb-1">Average security score</div>
              <div className="text-2xl font-light tracking-tight">
                88 <span className="text-xs text-zinc-500 font-mono">/ 100</span>
              </div>
              <div className="text-xs text-zinc-400 mt-2 font-mono flex items-center gap-1">
                <Activity className="w-3 h-3 text-teal-400" />
                <span>Grade A baseline</span>
              </div>
            </div>

            <div
              className={`p-4 rounded-lg border ${
                isDark ? "border-zinc-800 bg-zinc-900/30" : "border-zinc-200 bg-white"
              }`}
            >
              <div className="text-xs font-mono text-zinc-500 mb-1">Open vulnerabilities</div>
              <div className="text-2xl font-light tracking-tight text-amber-400">
                4 <span className="text-xs text-zinc-500 font-mono">total</span>
              </div>
              <div className="text-xs text-zinc-400 mt-2 font-mono">
                0 critical &bull; 1 high &bull; 3 medium
              </div>
            </div>

            <div
              className={`p-4 rounded-lg border ${
                isDark ? "border-zinc-800 bg-zinc-900/30" : "border-zinc-200 bg-white"
              }`}
            >
              <div className="text-xs font-mono text-zinc-500 mb-1">DPDP Act 2023 status</div>
              <div className="text-2xl font-light tracking-tight text-teal-400">
                Compliant
              </div>
              <div className="text-xs text-zinc-500 mt-2 font-mono">
                Next weekly audit in 4 days
              </div>
            </div>
          </div>

          {/* Add New Domain Card */}
          <div
            className={`p-6 rounded-lg border ${
              isDark ? "border-zinc-800 bg-zinc-900/40" : "border-zinc-200 bg-white"
            }`}
          >
            <div className="mb-4">
              <h2 className="text-base font-medium tracking-tight">Add new domain</h2>
              <p className={`text-xs mt-0.5 ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
                Enter your company domain or website address. Ownership will be verified via DNS TXT or HTTP token before active security scans commence.
              </p>
            </div>

            <form onSubmit={handleAddDomain} className="flex flex-col sm:flex-row gap-3">
              <div className="relative flex-1">
                <Globe
                  className={`w-4 h-4 absolute left-3.5 top-1/2 -translate-y-1/2 ${
                    isDark ? "text-zinc-500" : "text-zinc-400"
                  }`}
                />
                <input
                  id="add-domain-input"
                  type="text"
                  required
                  placeholder="example.com or https://app.example.in"
                  value={newHostname}
                  onChange={(e) => setNewHostname(e.target.value)}
                  className={`w-full pl-10 pr-4 py-2.5 rounded text-sm border font-mono transition-colors focus:outline-none ${
                    isDark
                      ? "bg-zinc-950 border-zinc-800 text-zinc-100 focus:border-teal-400"
                      : "bg-zinc-50 border-zinc-300 text-zinc-900 focus:border-teal-600"
                  }`}
                />
              </div>

              <button
                type="submit"
                className={`px-5 py-2.5 rounded text-xs font-mono font-medium transition-opacity flex items-center justify-center gap-2 ${
                  isDark ? "bg-white text-black hover:opacity-90" : "bg-zinc-900 text-white hover:opacity-90"
                }`}
              >
                <span>Add domain</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>

          {/* Registered Domains Section */}
          <div
            className={`rounded-lg border overflow-hidden ${
              isDark ? "border-zinc-800 bg-zinc-900/20" : "border-zinc-200 bg-white"
            }`}
          >
            {/* Table Filter Header */}
            <div
              className={`p-4 border-b flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 ${
                isDark ? "border-zinc-800 bg-zinc-900/50" : "border-zinc-200 bg-zinc-50/70"
              }`}
            >
              <div className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-teal-400" />
                <span className="text-sm font-medium">Registered domains</span>
                <span className="text-xs font-mono text-zinc-500">
                  ({filteredDomains.length} {filteredDomains.length === 1 ? "domain" : "domains"})
                </span>
              </div>

              <div className="flex items-center gap-1.5 text-xs font-mono">
                <button
                  onClick={() => setDashFilter("all")}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    dashFilter === "all"
                      ? isDark
                        ? "bg-zinc-800 text-white"
                        : "bg-white text-zinc-900 border border-zinc-300"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  All ({domainsList.length})
                </button>
                <button
                  onClick={() => setDashFilter("verified")}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    dashFilter === "verified"
                      ? isDark
                        ? "bg-zinc-800 text-white"
                        : "bg-white text-zinc-900 border border-zinc-300"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  Verified ({domainsList.filter((d) => d.status === "verified").length})
                </button>
                <button
                  onClick={() => setDashFilter("pending")}
                  className={`px-2.5 py-1 rounded transition-colors ${
                    dashFilter === "pending"
                      ? isDark
                        ? "bg-zinc-800 text-white"
                        : "bg-white text-zinc-900 border border-zinc-300"
                      : "text-zinc-500 hover:text-zinc-300"
                  }`}
                >
                  Pending ({domainsList.filter((d) => d.status === "pending").length})
                </button>
              </div>
            </div>

            {/* Domains Table / Cards */}
            <div className="divide-y divide-zinc-800/60">
              {filteredDomains.map((domain) => (
                <div
                  key={domain.id}
                  className={`p-5 transition-colors ${
                    isDark ? "hover:bg-zinc-900/40" : "hover:bg-zinc-50/80"
                  }`}
                >
                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
                    {/* Domain Identifier & Status */}
                    <div className="space-y-1.5 flex-1">
                      <div className="flex items-center gap-2.5">
                        <span className="font-mono text-sm font-medium tracking-tight text-zinc-100">
                          {domain.hostname}
                        </span>

                        {domain.status === "verified" ? (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border border-teal-500/30 bg-teal-500/10 text-teal-400">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Verified</span>
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border border-amber-500/30 bg-amber-500/10 text-amber-400">
                            <Clock className="w-3 h-3" />
                            <span>Verification pending</span>
                          </span>
                        )}

                        {domain.isMonitored && (
                          <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border border-zinc-700 bg-zinc-800/60 text-zinc-300">
                            <span>Weekly monitor active</span>
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-xs text-zinc-500 font-mono">
                        <span>Last scan: {domain.lastScanned}</span>
                        <span>&bull;</span>
                        <span>TLS: {domain.tlsVersion}</span>
                        <span>&bull;</span>
                        <span>CSP: {domain.cspStatus}</span>
                      </div>
                    </div>

                    {/* Security Grade & Audit Metric */}
                    <div className="flex items-center gap-4">
                      {domain.status === "verified" ? (
                        <div className="flex items-center gap-3">
                          <div
                            className={`w-10 h-10 rounded border flex items-center justify-center font-mono font-bold text-sm ${
                              domain.grade === "A"
                                ? "border-teal-500/40 text-teal-400 bg-teal-500/5"
                                : "border-amber-500/40 text-amber-400 bg-amber-500/5"
                            }`}
                          >
                            {domain.grade}
                          </div>

                          <div className="text-left font-mono">
                            <div className="text-xs font-semibold text-zinc-200">
                              {domain.score}/100 score
                            </div>
                            <div className="text-[11px] text-zinc-500">
                              {domain.findingsCount === 0
                                ? "0 vulnerabilities"
                                : `${domain.findingsCount} findings`}
                            </div>
                          </div>
                        </div>
                      ) : (
                        <button
                          onClick={() => setActiveVerifyDomain(domain)}
                          className="px-3 py-1.5 rounded border border-amber-500/40 text-amber-400 hover:bg-amber-500/10 text-xs font-mono transition-colors"
                        >
                          Complete verification
                        </button>
                      )}

                      {/* Actions */}
                      <div className="flex items-center gap-2 border-l border-zinc-800 pl-4">
                        {domain.status === "verified" && (
                          <button
                            disabled={activeAuditingDomainId === domain.id}
                            onClick={() => handleTriggerAuditInDashboard(domain)}
                            className={`p-2 rounded border text-xs font-mono transition-colors flex items-center gap-1.5 ${
                              activeAuditingDomainId === domain.id
                                ? "border-teal-500 text-teal-400 bg-teal-500/10 cursor-not-allowed"
                                : isDark
                                ? "border-zinc-800 text-zinc-300 hover:text-white hover:border-zinc-700 bg-zinc-900/60"
                                : "border-zinc-200 text-zinc-700 hover:text-zinc-900 bg-white"
                            }`}
                            title="Trigger immediate scan"
                          >
                            <RefreshCw
                              className={`w-3.5 h-3.5 ${
                                activeAuditingDomainId === domain.id ? "animate-spin" : ""
                              }`}
                            />
                            <span className="hidden sm:inline">
                              {activeAuditingDomainId === domain.id
                                ? `Auditing (${auditProgress}%)`
                                : "Run audit"}
                            </span>
                          </button>
                        )}

                        <button
                          onClick={() => handleToggleMonitoring(domain.id)}
                          className={`p-2 rounded border text-xs font-mono transition-colors ${
                            domain.isMonitored
                              ? "border-teal-500/40 text-teal-400 bg-teal-500/5"
                              : isDark
                              ? "border-zinc-800 text-zinc-500 hover:text-zinc-300"
                              : "border-zinc-200 text-zinc-400 hover:text-zinc-700"
                          }`}
                          title="Toggle weekly automated monitoring"
                        >
                          <Activity className="w-3.5 h-3.5" />
                        </button>

                        <button
                          onClick={() => handleDeleteDomain(domain.id, domain.hostname)}
                          className="p-2 rounded border border-zinc-800/80 text-zinc-500 hover:text-red-400 hover:border-red-500/40 transition-colors"
                          title="Remove domain"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Inline Audit Progress Bar */}
                  {activeAuditingDomainId === domain.id && (
                    <div className="mt-3 pt-3 border-t border-zinc-800/60">
                      <div className="flex items-center justify-between text-xs font-mono mb-1.5 text-teal-400">
                        <span>Running active audit & DPDP check on {domain.hostname}</span>
                        <span>{auditProgress}%</span>
                      </div>
                      <div className="h-1 w-full bg-zinc-800 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-teal-400 transition-all duration-300"
                          style={{ width: `${auditProgress}%` }}
                        />
                      </div>
                    </div>
                  )}

                  {/* Vulnerability Diff History */}
                  {domain.diff && (
                    <div className="mt-3 pt-3 border-t border-zinc-800/40 flex items-center gap-4 text-xs font-mono text-zinc-500">
                      <span>Vulnerability delta:</span>
                      <span className="text-teal-400">
                        +{domain.diff.new} new
                      </span>
                      <span className="text-teal-400">
                        -{domain.diff.resolved} resolved
                      </span>
                      <span>{domain.diff.persistent} persistent</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Verification Modal / Drawer */}
          {activeVerifyDomain && (
            <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
              <div
                className={`max-w-lg w-full rounded-lg border p-6 shadow-2xl space-y-5 animate-scaleIn ${
                  isDark ? "bg-[#0c0c0e] border-zinc-800" : "bg-white border-zinc-200"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-medium tracking-tight">
                      Verify domain ownership
                    </h3>
                    <p className="text-xs text-zinc-500 font-mono mt-0.5">
                      {activeVerifyDomain.hostname}
                    </p>
                  </div>
                  <button
                    onClick={() => setActiveVerifyDomain(null)}
                    className="p-1.5 text-zinc-400 hover:text-zinc-200"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>

                <div className="space-y-4 text-xs">
                  <p className="text-zinc-400 leading-relaxed">
                    To prevent unauthorized security testing, add one of the following verification tokens to your domain. We will check both records automatically.
                  </p>

                  {/* Method A: DNS TXT */}
                  <div
                    className={`p-3.5 rounded border space-y-2 ${
                      isDark ? "border-zinc-800 bg-zinc-900/60" : "border-zinc-200 bg-zinc-50"
                    }`}
                  >
                    <div className="flex items-center justify-between font-mono">
                      <span className="text-zinc-300 font-medium">Method 1: DNS TXT record</span>
                      <span className="text-teal-400 text-[11px]">Recommended</span>
                    </div>
                    <div className="text-zinc-400 text-[11px]">
                      Add a TXT record to your DNS root or subdomain:
                    </div>
                    <div className="flex items-center justify-between gap-2 p-2 rounded bg-zinc-950 border border-zinc-800 font-mono text-zinc-200">
                      <span className="truncate">{activeVerifyDomain.txtRecord}</span>
                      <button
                        onClick={() => copyToClipboard(activeVerifyDomain.txtRecord, "txt")}
                        className="p-1 hover:text-teal-400 transition-colors"
                        title="Copy record"
                      >
                        {copiedField === "txt" ? (
                          <Check className="w-3.5 h-3.5 text-teal-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Method B: Well-Known HTTP */}
                  <div
                    className={`p-3.5 rounded border space-y-2 ${
                      isDark ? "border-zinc-800 bg-zinc-900/60" : "border-zinc-200 bg-zinc-50"
                    }`}
                  >
                    <div className="flex items-center justify-between font-mono">
                      <span className="text-zinc-300 font-medium">Method 2: HTTP well-known token</span>
                    </div>
                    <div className="text-zinc-400 text-[11px]">
                      Host a plain text file accessible at:
                    </div>
                    <div className="p-2 rounded bg-zinc-950 border border-zinc-800 font-mono text-zinc-200 truncate">
                      https://{activeVerifyDomain.hostname}{activeVerifyDomain.wellKnownUrl}
                    </div>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-zinc-800">
                  <span className="text-xs text-zinc-500 font-mono">DNS propagation: ~2-5 mins</span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => setActiveVerifyDomain(null)}
                      className="px-3 py-1.5 rounded border border-zinc-800 text-xs font-mono text-zinc-400 hover:text-zinc-200"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={() => handleSimulateVerify(activeVerifyDomain.id)}
                      className="px-3.5 py-1.5 rounded bg-teal-500 hover:bg-teal-400 text-black font-mono text-xs font-medium transition-colors"
                    >
                      Verify now
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      )}

      {/* ============================================================= */}
      {/* VIEW 2: SCANNER LANDING PAGE (3D particle sphere + HUD) */}
      {/* ============================================================= */}
      {viewMode === "landing" && (
        <>
          {/* Hero Section */}
          <section className="max-w-6xl mx-auto px-6 pt-16 pb-12 grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            <div className="lg:col-span-7">
              <div className="flex items-center gap-3 mb-5">
                <span className="font-mono text-xs text-zinc-500 font-medium">
                  01 &mdash; Website security scanner
                </span>
                <div className={`h-[1px] w-12 ${isDark ? "bg-zinc-800" : "bg-zinc-300"}`} />
              </div>

              <h1 className="text-4xl sm:text-5xl font-normal tracking-tight leading-[1.1] mb-5">
                Find security risks before they find{" "}
                <span className="font-serif italic font-normal">you.</span>
                <span className="text-teal-400 ml-1 font-sans not-italic">/</span>
              </h1>

              <p
                className={`text-base sm:text-lg leading-relaxed max-w-lg mb-8 font-light ${
                  isDark ? "text-zinc-400" : "text-zinc-600"
                }`}
              >
                DataSecurely performs automated reconnaissance, TLS verification, CSP policy testing, and DPDP Act 2023 compliance auditing on web applications.
              </p>

              {/* Dynamic Scanner Input */}
              <div className="space-y-4 max-w-md">
                <div
                  className={`p-1.5 rounded-lg border flex items-center gap-2 transition-all ${
                    isDark
                      ? "border-zinc-800 bg-zinc-900/60 focus-within:border-zinc-600"
                      : "border-zinc-300 bg-white focus-within:border-zinc-400"
                  }`}
                >
                  <Globe
                    className={`w-4 h-4 ml-2.5 ${isDark ? "text-zinc-500" : "text-zinc-400"}`}
                  />
                  <input
                    type="text"
                    value={domainInput}
                    onChange={(e) => setDomainInput(e.target.value)}
                    placeholder="Enter website (e.g. example.com)"
                    className="w-full bg-transparent px-2 py-2 text-sm font-mono focus:outline-none placeholder:text-zinc-500"
                  />
                  <button
                    disabled={isScanning}
                    onClick={() => handleStartScan()}
                    className={`px-4 py-2 rounded text-xs font-mono font-medium flex items-center gap-1.5 transition-all ${
                      isScanning
                        ? "bg-zinc-700 text-zinc-400 cursor-not-allowed"
                        : isDark
                        ? "bg-teal-500 hover:bg-teal-400 text-black"
                        : "bg-teal-600 hover:bg-teal-500 text-white"
                    }`}
                  >
                    <span>{isScanning ? "Scanning..." : "Audit"}</span>
                    <ArrowUpRight className="w-3.5 h-3.5" />
                  </button>
                </div>

                <div className="flex items-center gap-6 text-xs text-zinc-500 font-mono">
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
                    No software install
                  </span>
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
                    Non-invasive tests
                  </span>
                  <span className="flex items-center gap-1.5">
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" />
                    DPDP Act compliant
                  </span>
                </div>
              </div>
            </div>

            {/* 3D Particle Mesh Canvas */}
            <div className="lg:col-span-5 flex justify-center items-center relative min-h-[360px]">
              <div
                className={`absolute inset-0 rounded-2xl border transition-colors ${
                  isDark ? "border-zinc-800/40 bg-zinc-950/40" : "border-zinc-200/60 bg-white/40"
                }`}
              />
              <canvas
                ref={canvasRef}
                className="relative z-10 w-full h-[360px] cursor-grab active:cursor-grabbing"
              />

              {/* Dynamic Scan HUD Card */}
              <div
                className={`absolute bottom-3 left-3 right-3 p-3.5 rounded-lg border backdrop-blur-md z-20 transition-all ${
                  isDark
                    ? "border-zinc-800/90 bg-[#09090b]/90 text-zinc-200"
                    : "border-zinc-200/90 bg-white/95 text-zinc-800 shadow-sm"
                }`}
              >
                <div className="flex items-center justify-between text-xs font-mono mb-2">
                  <span className="flex items-center gap-2">
                    <span
                      className={`w-2 h-2 rounded-full ${
                        isScanning ? "bg-teal-400 animate-pulse" : "bg-zinc-500"
                      }`}
                    />
                    <span className="font-medium truncate max-w-[190px]">
                      {isScanning ? scanStageText : "Live Pipeline Status"}
                    </span>
                  </span>
                  <span className="text-zinc-500">{scanProgress}%</span>
                </div>

                <div className="h-1 w-full bg-zinc-800/40 rounded-full overflow-hidden mb-2">
                  <div
                    className="h-full bg-teal-400 transition-all duration-300"
                    style={{ width: `${scanProgress}%` }}
                  />
                </div>

                <div className="flex items-center justify-between text-[11px] font-mono text-zinc-500">
                  <span>Scope Guard: Enforced</span>
                  <span>Engine: OWASP ZAP / Nuclei</span>
                </div>
              </div>
            </div>
          </section>

          {/* Audit Results HUD */}
          {gradeResult && (
            <section className="max-w-6xl mx-auto px-6 py-6 animate-fadeIn">
              <div
                className={`p-6 rounded-lg border ${
                  isDark ? "border-zinc-800 bg-zinc-900/30" : "border-zinc-200 bg-white"
                }`}
              >
                <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/60">
                  <div className="flex items-center gap-3">
                    <div
                      className={`w-12 h-12 rounded border flex items-center justify-center font-mono font-bold text-lg ${
                        gradeResult.grade === "A"
                          ? "border-teal-500/40 text-teal-400 bg-teal-500/10"
                          : "border-amber-500/40 text-amber-400 bg-amber-500/10"
                      }`}
                    >
                      {gradeResult.grade}
                    </div>
                    <div>
                      <div className="font-mono text-sm font-medium">
                        Audit report for {gradeResult.host}
                      </div>
                      <div className="text-xs text-zinc-500 font-mono">
                        Score: {gradeResult.score}/100 &bull; {gradeResult.dpdpCompliance}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => setIsReportOpen(true)}
                    className="px-4 py-2 rounded border border-teal-500/40 text-teal-400 hover:bg-teal-500/10 text-xs font-mono transition-colors flex items-center gap-1.5"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>View bilingual report (English / Hinglish)</span>
                  </button>
                </div>

                {findings.length > 0 && (
                  <div className="mt-4 space-y-2">
                    <div className="text-xs font-mono text-zinc-500 mb-2">
                      Detected findings ({findings.length})
                    </div>
                    {findings.map((f) => (
                      <div
                        key={f.id}
                        className={`p-3 rounded border flex items-center justify-between text-xs font-mono ${
                          isDark ? "border-zinc-800/80 bg-zinc-950" : "border-zinc-200 bg-zinc-50"
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <AlertTriangle
                            className={`w-3.5 h-3.5 ${
                              f.severity === "high"
                                ? "text-amber-400"
                                : f.severity === "medium"
                                ? "text-yellow-400"
                                : "text-zinc-400"
                            }`}
                          />
                          <span className="text-zinc-200">{f.title}</span>
                          <span className="text-zinc-500">[{f.rule}]</span>
                        </div>
                        <span className="text-zinc-400 text-[11px] truncate max-w-[200px]">
                          {f.target}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Three Pillars: Detect, Analyze, Secure */}
          <section className="max-w-6xl mx-auto px-6 py-16">
            <div className="flex items-center gap-3 mb-4">
              <span className="font-mono text-xs text-zinc-500 font-medium">
                02 &mdash; Methodology
              </span>
              <div className={`h-[1px] w-12 ${isDark ? "bg-zinc-800" : "bg-zinc-300"}`} />
            </div>

            <h2 className="text-2xl sm:text-3xl font-normal tracking-tight mb-8">
              Continuous defensive verification
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div
                className={`p-6 rounded-lg border transition-colors ${
                  isDark ? "border-zinc-800 bg-zinc-900/20" : "border-zinc-200 bg-white"
                }`}
              >
                <div className="w-8 h-8 rounded border border-zinc-700 flex items-center justify-center font-mono text-xs mb-4 text-teal-400">
                  01
                </div>
                <h3 className="text-base font-medium mb-2">Detect</h3>
                <p className={`text-xs leading-relaxed ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
                  Reconnaissance mapping for exposed subdomains, legacy TLS configurations, and missing HTTP security response headers.
                </p>
              </div>

              <div
                className={`p-6 rounded-lg border transition-colors ${
                  isDark ? "border-zinc-800 bg-zinc-900/20" : "border-zinc-200 bg-white"
                }`}
              >
                <div className="w-8 h-8 rounded border border-zinc-700 flex items-center justify-center font-mono text-xs mb-4 text-teal-400">
                  02
                </div>
                <h3 className="text-base font-medium mb-2">Analyze</h3>
                <p className={`text-xs leading-relaxed ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
                  Deterministic scoring cross-referenced with the DPDP Act 2023 schedule for personal identifiable data leak vectors.
                </p>
              </div>

              <div
                className={`p-6 rounded-lg border transition-colors ${
                  isDark ? "border-zinc-800 bg-zinc-900/20" : "border-zinc-200 bg-white"
                }`}
              >
                <div className="w-8 h-8 rounded border border-zinc-700 flex items-center justify-center font-mono text-xs mb-4 text-teal-400">
                  03
                </div>
                <h3 className="text-base font-medium mb-2">Secure</h3>
                <p className={`text-xs leading-relaxed ${isDark ? "text-zinc-400" : "text-zinc-600"}`}>
                  Actionable copy-paste remediation directives for Caddy, Nginx, FastAPI, and Next.js middlewares.
                </p>
              </div>
            </div>
          </section>
        </>
      )}

      {/* ---------------- BILINGUAL REPORT MODAL ---------------- */}
      {isReportOpen && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div
            className={`max-w-2xl w-full rounded-lg border p-6 shadow-2xl space-y-5 animate-scaleIn max-h-[85vh] overflow-y-auto ${
              isDark ? "bg-[#0c0c0e] border-zinc-800" : "bg-white border-zinc-200"
            }`}
          >
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-teal-400" />
                <h3 className="text-sm font-medium">Bilingual Audit Report</h3>
              </div>

              <div className="flex items-center gap-3">
                {/* Language Switcher */}
                <div className="inline-flex p-0.5 rounded border border-zinc-800 text-xs font-mono bg-zinc-950">
                  <button
                    onClick={() => setReportLang("en")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      reportLang === "en" ? "bg-zinc-800 text-white" : "text-zinc-500"
                    }`}
                  >
                    English
                  </button>
                  <button
                    onClick={() => setReportLang("hi")}
                    className={`px-2 py-0.5 rounded transition-colors ${
                      reportLang === "hi" ? "bg-zinc-800 text-white" : "text-zinc-500"
                    }`}
                  >
                    Hinglish (हिंदी)
                  </button>
                </div>

                <button
                  onClick={() => setIsReportOpen(false)}
                  className="p-1 text-zinc-400 hover:text-zinc-200"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {reportLang === "en" ? (
              <div className="space-y-4 text-xs font-mono text-zinc-300">
                <div className="p-3 rounded bg-zinc-950 border border-zinc-800">
                  <div className="text-teal-400 font-semibold mb-1">Executive Summary</div>
                  <p className="text-zinc-400 leading-relaxed">
                    The audit completed with security grade B+ (84/100). The domain enforces TLS 1.3 but exhibits a missing Content Security Policy nonce directive, which poses a risk for Cross-Site Scripting (XSS).
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="text-zinc-500 text-xs">DPDP Act 2023 compliance advisory</div>
                  <p className="text-zinc-400 leading-relaxed">
                    Under Section 8(5) of the Digital Personal Data Protection Act, reasonable security safeguards must be maintained to prevent personal data breach. Ensure session cookies declare Secure and SameSite attributes.
                  </p>
                </div>
              </div>
            ) : (
              <div className="space-y-4 text-xs font-mono text-zinc-300">
                <div className="p-3 rounded bg-zinc-950 border border-zinc-800">
                  <div className="text-teal-400 font-semibold mb-1">Mukhya Saransh (Executive Summary)</div>
                  <p className="text-zinc-400 leading-relaxed">
                    Aapki website ka security grade B+ (84/100) mila hai. TLS 1.3 encryption active hai, lekin Content Security Policy me nonce missing hai, jisse Cross-Site Scripting (XSS) ka risk badhta hai.
                  </p>
                </div>

                <div className="space-y-2">
                  <div className="text-zinc-500 text-xs">DPDP Act 2023 salah (advisory)</div>
                  <p className="text-zinc-400 leading-relaxed">
                    DPDP Act ke Section 8(5) ke mutabiq, customer ka data secure rakhna zaroori hai. Session cookies me hamesha Secure aur SameSite=Lax flags lagayein taaki data leak na ho.
                  </p>
                </div>
              </div>
            )}

            <div className="pt-3 border-t border-zinc-800 flex justify-end">
              <button
                onClick={() => setIsReportOpen(false)}
                className="px-3.5 py-1.5 rounded bg-zinc-800 hover:bg-zinc-700 text-xs font-mono transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ---------------- FOOTER ---------------- */}
      <footer
        className={`border-t py-12 px-6 text-xs transition-colors ${
          isDark ? "border-zinc-800/80 text-zinc-500 bg-zinc-950" : "border-zinc-200 text-zinc-600 bg-zinc-50"
        }`}
      >
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="font-medium text-zinc-300">datasecurely</span>
            <span>&bull; Automated website security platform for Indian SMBs</span>
          </div>
          <div className="flex items-center gap-5">
            <a href="/pricing" className="hover:text-zinc-300">
              Pricing
            </a>
            <a href="/terms" className="hover:text-zinc-300">
              Terms of service
            </a>
            <a href="/privacy" className="hover:text-zinc-300">
              Privacy policy
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
