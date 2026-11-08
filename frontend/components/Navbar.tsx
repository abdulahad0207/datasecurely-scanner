"use client";

import React, { useEffect, useState, useRef } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Sun,
  Moon,
  ArrowUpRight,
  ShieldCheck,
  Menu,
  X,
  User,
  ChevronDown,
  LogOut,
} from "lucide-react";
import { useTheme } from "./ThemeProvider";
import { supabase } from "@/lib/supabase";

export default function Navbar() {
  const { theme, toggleTheme } = useTheme();
  const pathname = usePathname();
  const router = useRouter();
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const checkAuth = async () => {
      const { data } = await supabase.auth.getSession();
      const hasDevToken =
        typeof window !== "undefined" &&
        Boolean(localStorage.getItem("dev_mock_token"));

      if (data?.session?.user?.email) {
        setUserEmail(data.session.user.email);
      } else if (hasDevToken) {
        const mock = localStorage.getItem("dev_mock_token") || "";
        const parts = mock.split("-");
        const mockEmail = parts.length > 3 ? parts[parts.length - 1] : "demo@example.com";
        setUserEmail(mockEmail);
      } else {
        setUserEmail(null);
      }

      setIsAuthenticated(Boolean(data?.session || hasDevToken));
    };
    checkAuth();
  }, [pathname]);

  // Close menus whenever pathname changes
  useEffect(() => {
    setMobileMenuOpen(false);
    setUserMenuOpen(false);
  }, [pathname]);

  // Handle outside click for user dropdown
  useEffect(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    if (userMenuOpen) {
      document.addEventListener("mousedown", handleOutsideClick);
    }
    return () => {
      document.removeEventListener("mousedown", handleOutsideClick);
    };
  }, [userMenuOpen]);

  const handleSignOut = async () => {
    try {
      await supabase.auth.signOut();
    } catch {}
    if (typeof window !== "undefined") {
      localStorage.removeItem("dev_mock_token");
    }
    setIsAuthenticated(false);
    setUserEmail(null);
    setUserMenuOpen(false);
    setMobileMenuOpen(false);
    router.push("/login");
  };

  const isDark = theme === "dark";

  return (
    <header
      className={`sticky top-0 z-50 border-b backdrop-blur-md transition-colors duration-200 ${
        isDark
          ? "border-zinc-800/80 bg-[#09090b]/90 text-zinc-100"
          : "border-zinc-200/80 bg-[#fbfbfa]/90 text-zinc-900"
      }`}
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        {/* Brand Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <div
            className={`w-7 h-7 rounded flex items-center justify-center font-mono font-bold text-xs transition-transform group-hover:scale-105 ${
              isDark ? "bg-white text-black" : "bg-zinc-900 text-white"
            }`}
          >
            DS
          </div>
          <span className="font-medium text-sm tracking-tight">datasecurely</span>
          <span className="text-xs text-zinc-500 pl-3 border-l border-zinc-700/40 hidden sm:inline font-mono">
            Security Scanner
          </span>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-6 text-xs font-mono">
          <Link
            href="/"
            className={`transition-colors ${
              pathname === "/"
                ? isDark
                  ? "text-teal-400 font-medium"
                  : "text-teal-600 font-medium"
                : isDark
                ? "text-zinc-400 hover:text-zinc-200"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            Scanner
          </Link>
          <Link
            href="/dashboard"
            className={`transition-colors flex items-center gap-1.5 ${
              pathname.startsWith("/dashboard") || pathname.startsWith("/domains")
                ? isDark
                  ? "text-teal-400 font-medium"
                  : "text-teal-600 font-medium"
                : isDark
                ? "text-zinc-400 hover:text-zinc-200"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            <span>Dashboard</span>
            <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
          </Link>
          <Link
            href="/pricing"
            className={`transition-colors ${
              pathname === "/pricing"
                ? isDark
                  ? "text-teal-400 font-medium"
                  : "text-teal-600 font-medium"
                : isDark
                ? "text-zinc-400 hover:text-zinc-200"
                : "text-zinc-600 hover:text-zinc-900"
            }`}
          >
            Pricing
          </Link>
        </nav>

        {/* Right Side Controls */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Theme Toggle Button */}
          <button
            onClick={toggleTheme}
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-mono border transition-colors ${
              isDark
                ? "border-zinc-800 text-zinc-400 hover:text-zinc-100 hover:border-zinc-700 bg-zinc-900/60"
                : "border-zinc-200 text-zinc-600 hover:text-zinc-900 hover:border-zinc-300 bg-white"
            }`}
            title="Toggle color theme"
          >
            {isDark ? <Sun className="w-3.5 h-3.5" /> : <Moon className="w-3.5 h-3.5" />}
            <span className="capitalize hidden sm:inline">{theme}</span>
          </button>

          {/* Account / Dashboard Action (Desktop) */}
          <div className="hidden sm:flex items-center gap-2">
            {isAuthenticated ? (
              <>
                <Link
                  href="/dashboard"
                  className={`text-xs px-3.5 py-1.5 rounded font-mono font-medium inline-flex items-center gap-1.5 transition-opacity ${
                    isDark
                      ? "bg-white text-black hover:opacity-90"
                      : "bg-zinc-900 text-white hover:opacity-90"
                  }`}
                >
                  <span>Console</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>

                {/* Desktop User Menu Dropdown */}
                <div className="relative" ref={userMenuRef}>
                  <button
                    onClick={() => setUserMenuOpen(!userMenuOpen)}
                    className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded text-xs font-mono border transition-colors ${
                      isDark
                        ? "border-zinc-800 text-zinc-300 hover:text-white hover:border-zinc-700 bg-zinc-900/60"
                        : "border-zinc-200 text-zinc-700 hover:text-zinc-900 bg-white"
                    } ${pathname === "/account" ? (isDark ? "border-teal-500/50 text-teal-400" : "border-teal-600 text-teal-600") : ""}`}
                    aria-label="User account menu"
                    aria-expanded={userMenuOpen}
                  >
                    <User className="w-3.5 h-3.5 text-teal-400" />
                    <span className="max-w-[100px] truncate">
                      {userEmail ? userEmail.split("@")[0] : "Account"}
                    </span>
                    <ChevronDown
                      className={`w-3 h-3 text-zinc-500 transition-transform ${
                        userMenuOpen ? "rotate-180" : ""
                      }`}
                    />
                  </button>

                  {userMenuOpen && (
                    <div
                      className={`absolute right-0 top-full mt-2 w-52 rounded-lg border py-1.5 shadow-xl font-mono text-xs z-50 animate-in fade-in zoom-in-95 duration-100 ${
                        isDark
                          ? "border-zinc-800 bg-[#121215] text-zinc-200"
                          : "border-zinc-200 bg-white text-zinc-800 shadow-lg"
                      }`}
                    >
                      <div className="px-3 py-2 border-b border-zinc-800/80 mb-1">
                        <p className="text-[10px] text-zinc-500 font-sans">Signed in as</p>
                        <p className="text-xs truncate text-zinc-300">{userEmail || "Active user"}</p>
                      </div>

                      <Link
                        href="/dashboard"
                        onClick={() => setUserMenuOpen(false)}
                        className={`flex items-center gap-2 px-3 py-2 transition-colors ${
                          isDark
                            ? "hover:bg-zinc-900 text-zinc-300 hover:text-white"
                            : "hover:bg-zinc-100 text-zinc-700 hover:text-zinc-900"
                        }`}
                      >
                        <span>Dashboard</span>
                      </Link>

                      <Link
                        href="/account"
                        onClick={() => setUserMenuOpen(false)}
                        className={`flex items-center gap-2 px-3 py-2 transition-colors ${
                          pathname === "/account"
                            ? isDark
                              ? "text-teal-400 font-medium bg-zinc-900/60"
                              : "text-teal-600 font-medium bg-zinc-100"
                            : isDark
                            ? "hover:bg-zinc-900 text-zinc-300 hover:text-white"
                            : "hover:bg-zinc-100 text-zinc-700 hover:text-zinc-900"
                        }`}
                      >
                        <span>Account</span>
                      </Link>

                      <div className={`my-1 border-t ${isDark ? "border-zinc-800" : "border-zinc-200"}`} />

                      <button
                        onClick={handleSignOut}
                        className={`w-full flex items-center gap-2 px-3 py-2 text-left transition-colors ${
                          isDark
                            ? "hover:bg-zinc-900 text-zinc-400 hover:text-rose-400"
                            : "hover:bg-zinc-100 text-zinc-600 hover:text-rose-600"
                        }`}
                      >
                        <LogOut className="w-3.5 h-3.5" />
                        <span>Sign out</span>
                      </button>
                    </div>
                  )}
                </div>
              </>
            ) : (
              <Link
                href="/login"
                className={`text-xs px-3.5 py-1.5 rounded font-mono transition-colors border ${
                  isDark
                    ? "border-zinc-800 text-zinc-300 hover:bg-zinc-900 hover:border-zinc-700"
                    : "border-zinc-300 text-zinc-700 hover:bg-zinc-100"
                }`}
              >
                Sign in
              </Link>
            )}
          </div>

          {/* Mobile Navigation Trigger (Hamburger / Close) */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className={`md:hidden p-2 rounded border transition-colors flex items-center justify-center ${
              isDark
                ? "border-zinc-800 text-zinc-400 hover:text-zinc-100 bg-zinc-900/60"
                : "border-zinc-200 text-zinc-600 hover:text-zinc-900 bg-white"
            }`}
            aria-label="Toggle navigation menu"
            aria-expanded={mobileMenuOpen}
          >
            {mobileMenuOpen ? <X className="w-4 h-4" /> : <Menu className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* Mobile Navigation Drawer / Dropdown */}
      {mobileMenuOpen && (
        <div
          className={`md:hidden border-b px-4 py-4 space-y-3 font-mono text-xs transition-all ${
            isDark
              ? "border-zinc-800 bg-[#09090b]/98 text-zinc-200"
              : "border-zinc-200 bg-[#fbfbfa]/98 text-zinc-800 shadow-md"
          }`}
        >
          <div className="flex flex-col space-y-1">
            <Link
              href="/"
              onClick={() => setMobileMenuOpen(false)}
              className={`px-3 py-2.5 rounded transition-colors ${
                pathname === "/"
                  ? isDark
                    ? "bg-zinc-900 text-teal-400 font-medium border border-zinc-800"
                    : "bg-zinc-100 text-teal-600 font-medium"
                  : isDark
                  ? "hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200"
                  : "hover:bg-zinc-100 text-zinc-600 hover:text-zinc-900"
              }`}
            >
              Scanner
            </Link>
            <Link
              href="/dashboard"
              onClick={() => setMobileMenuOpen(false)}
              className={`px-3 py-2.5 rounded transition-colors flex items-center justify-between ${
                pathname.startsWith("/dashboard") || pathname.startsWith("/domains")
                  ? isDark
                    ? "bg-zinc-900 text-teal-400 font-medium border border-zinc-800"
                    : "bg-zinc-100 text-teal-600 font-medium"
                  : isDark
                  ? "hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200"
                  : "hover:bg-zinc-100 text-zinc-600 hover:text-zinc-900"
              }`}
            >
              <span>Dashboard</span>
              <span className="w-1.5 h-1.5 rounded-full bg-teal-400" />
            </Link>
            <Link
              href="/pricing"
              onClick={() => setMobileMenuOpen(false)}
              className={`px-3 py-2.5 rounded transition-colors ${
                pathname === "/pricing"
                  ? isDark
                    ? "bg-zinc-900 text-teal-400 font-medium border border-zinc-800"
                    : "bg-zinc-100 text-teal-600 font-medium"
                  : isDark
                  ? "hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200"
                  : "hover:bg-zinc-100 text-zinc-600 hover:text-zinc-900"
              }`}
            >
              Pricing
            </Link>
            {isAuthenticated && (
              <Link
                href="/account"
                onClick={() => setMobileMenuOpen(false)}
                className={`px-3 py-2.5 rounded transition-colors flex items-center gap-2 ${
                  pathname === "/account"
                    ? isDark
                      ? "bg-zinc-900 text-teal-400 font-medium border border-zinc-800"
                      : "bg-zinc-100 text-teal-600 font-medium"
                    : isDark
                    ? "hover:bg-zinc-900 text-zinc-400 hover:text-zinc-200"
                    : "hover:bg-zinc-100 text-zinc-600 hover:text-zinc-900"
                }`}
              >
                <User className="w-3.5 h-3.5" />
                <span>Account</span>
              </Link>
            )}
          </div>

          <div
            className={`pt-3 border-t flex items-center justify-between gap-3 ${
              isDark ? "border-zinc-800" : "border-zinc-200"
            }`}
          >
            {isAuthenticated ? (
              <div className="flex items-center gap-2 w-full">
                <Link
                  href="/dashboard"
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex-1 text-center py-2 px-3 rounded font-medium inline-flex items-center justify-center gap-1.5 ${
                    isDark
                      ? "bg-white text-black hover:opacity-90"
                      : "bg-zinc-900 text-white hover:opacity-90"
                  }`}
                >
                  <span>Console</span>
                  <ArrowUpRight className="w-3.5 h-3.5" />
                </Link>
                <button
                  onClick={handleSignOut}
                  className={`py-2 px-3 rounded border font-medium flex items-center justify-center gap-1.5 transition-colors ${
                    isDark
                      ? "border-zinc-800 text-zinc-400 hover:text-rose-400 hover:border-zinc-700 bg-zinc-900/60"
                      : "border-zinc-300 text-zinc-700 hover:text-rose-600 bg-white"
                  }`}
                >
                  <LogOut className="w-3.5 h-3.5" />
                  <span>Sign out</span>
                </button>
              </div>
            ) : (
              <Link
                href="/login"
                onClick={() => setMobileMenuOpen(false)}
                className={`flex-1 text-center py-2 px-3 rounded border font-medium ${
                  isDark
                    ? "border-zinc-800 text-zinc-300 hover:bg-zinc-900"
                    : "border-zinc-300 text-zinc-700 hover:bg-zinc-100"
                }`}
              >
                Sign in
              </Link>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
