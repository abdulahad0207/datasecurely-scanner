"use client";

import React from "react";
import Link from "next/link";
import { useTheme } from "./ThemeProvider";

export default function Footer() {
  const { theme } = useTheme();
  const isDark = theme === "dark";

  return (
    <footer
      className={`border-t py-12 px-4 sm:px-6 text-xs transition-colors duration-200 ${
        isDark
          ? "border-zinc-800/80 text-zinc-500 bg-[#09090b]"
          : "border-zinc-200 text-zinc-600 bg-[#fbfbfa]"
      }`}
    >
      <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-6 sm:gap-4 font-mono text-center sm:text-left">
        <div className="flex flex-col sm:flex-row items-center gap-1 sm:gap-2">
          <span className={`font-medium ${isDark ? "text-zinc-300" : "text-zinc-800"}`}>
            datasecurely
          </span>
          <span className="hidden sm:inline text-zinc-600">&bull;</span>
          <span className={isDark ? "text-zinc-500" : "text-zinc-500"}>
            Automated website security platform for Indian SMBs
          </span>
        </div>
        <div className="flex flex-wrap items-center justify-center gap-5 sm:gap-6 pt-1 sm:pt-0">
          <Link
            href="/pricing"
            className={`transition-colors ${
              isDark ? "hover:text-zinc-300" : "hover:text-zinc-900"
            }`}
          >
            Pricing
          </Link>
          <Link
            href="/terms"
            className={`transition-colors ${
              isDark ? "hover:text-zinc-300" : "hover:text-zinc-900"
            }`}
          >
            Terms of service
          </Link>
          <Link
            href="/privacy"
            className={`transition-colors ${
              isDark ? "hover:text-zinc-300" : "hover:text-zinc-900"
            }`}
          >
            Privacy policy
          </Link>
        </div>
      </div>
    </footer>
  );
}
