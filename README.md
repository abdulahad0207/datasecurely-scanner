# datasecurely Scanner

One-click, AI-assisted website security scanner for Indian SMBs. Enter a domain, verify ownership, and receive an actionable security report in plain English or Hinglish with prioritized remediation steps.

## Architecture & Stack
- **Frontend:** Next.js (App Router), Tailwind CSS, shadcn/ui.
- **Backend API:** FastAPI (Python 3.12).
- **Task Queue & Broker:** Redis + ARQ.
- **Worker:** Containerized Python runner orchestrating Subfinder, httpx, Nuclei (safe profile), Nmap, and custom Python security checks.
- **AI Engine:** Google Gemini API (`gemini-3.8-flash`) with strict Pydantic JSON schema output.
- **Database & Auth:** Supabase (PostgreSQL + Row-Level Security).
- **Reports:** Jinja2 HTML templates rendered to PDF via Playwright.

## Getting Started

### 1. Prerequisites
- Docker & Docker Compose
- Python 3.12+
- Node.js 20+

### 2. Quickstart with Docker Compose
```bash
# Clone and enter directory
cp .env.example .env

# Start API, Worker, and Redis services
docker compose up -d

# Verify API health
curl http://localhost:8000/health
```

### 3. Running Tests
```bash
pytest backend/tests -v
```
