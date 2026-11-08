# datasecurely Scanner: Architecture Blueprint

Prepared for Abdul Ahad · v1.0 · Updated for Google Gemini API · Audience: the AI coding assistant that will write the code, plus the founder.

## 0. Product definition

**One-liner:** a one-click, AI-assisted website security scanner for Indian SMBs. The user enters a domain, proves they own it, and gets a plain-English (English or Hinglish) report with prioritized fixes.

**In scope:** recon, safe vulnerability detection, misconfiguration checks, AI triage, report generation, scheduled re-scans, payments.

**Out of scope (hard rules):** no exploitation, no brute forcing, no DoS-style tests, no scanning of unverified domains, no scanning of private or internal IP ranges. The product *detects and explains*; it never attacks.

## 1. Tech stack

| Layer | Choice | Why |
| --- | --- | --- |
| Frontend | Next.js (App Router) + Tailwind + shadcn/ui | Fast to build, free hosting on Vercel |
| Auth + DB | Supabase (Postgres + Auth + Row Level Security) | Free tier, one service for login and data |
| API | FastAPI (Python 3.12) | Async, typed, auto OpenAPI docs, same language as the worker |
| Queue | Redis + ARQ | Simple, high-throughput, async job queue for long scans |
| Worker | Python worker in Docker, bundling httpx, Subfinder, Nuclei, Nmap | Scanners are CLI binaries; they need a real container |
| Scanners | ProjectDiscovery tools (httpx, Subfinder, Nuclei), Nmap, plus custom Python checks (headers, TLS, cookies) | Mature, template-driven, open source |
| AI | Google Gemini API (`gemini-3.8-flash`) | Triage, dedupe, report writing, fast bilingual (English & Hinglish) output, native structured JSON schema support |
| Reports | Jinja2 HTML template → PDF via Playwright | Branded output, pixel-perfect formatting |
| Payments | Razorpay | UPI and cards for Indian SMBs |
| Email | Resend (or Brevo) | Free tier, simple API |
| Hosting | Frontend on Vercel. API + worker + Redis on VPS with Docker Compose | Persistent worker needed for scanning tasks |
| Observability | Sentry (errors) + structured JSON logs | Catches silent scan failures |

## 2. Architecture and logic flow

### 2.1 High-level diagram

```
Browser (Next.js)
   │  Supabase Auth (JWT)
   ▼
FastAPI ──► Postgres (Supabase)
   │            ▲
   │ enqueue    │ read/write
   ▼            │
Redis queue ──► Worker (Docker)
                 ├─ Scope Guard (SSRF / Ownership check)
                 ├─ Recon → Scan → Normalize
                 ├─ AI Triage + Report Writer (Gemini API: gemini-3.8-flash)
                 └─ PDF render → Storage → Email
```

### 2.2 Safety Guardrails (Non-negotiable)
- **Authorization Gate:** No scan without a verified domain and recorded user consent.
- **Scope Lock:** Strict domain bounding, ignoring third-party subdomains or external redirects.
- **SSRF Protection:** Pre-scan DNS resolution blocklist checking against private/loopback/cloud metadata ranges (`config/blocked-networks.txt`).
- **Safe Nuclei Profile:** Rate-limited, safe tags only, strictly excluding intrusive/DoS/fuzzing templates.
