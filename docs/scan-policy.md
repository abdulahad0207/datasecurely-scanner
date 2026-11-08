# Scan Policy & Safety Guardrails

## 1. Core Principles
- **Detection Only:** The scanner identifies, validates, and explains vulnerabilities and misconfigurations. It never attempts post-exploitation, payload pivoting, or privilege escalation.
- **Strict Authorization:** Scans will only be performed against hostnames with verified domain ownership via DNS TXT record (`datasecurely-verify=<token>`) or HTTP `.well-known` token file.
- **Non-Destructive Testing:** All scanner templates and checks are restricted to benign, non-destructive queries. Brute-force attacks, high-rate fuzzing, denial-of-service (DoS) vectors, and resource-exhaustion payloads are prohibited.

## 2. SSRF & Network Boundary Protection
All targets must resolve to public, routable IP addresses. Target IP addresses matching any entry in `config/blocked-networks.txt` (including RFC 1918, RFC 3927 link-local, RFC 5737 documentation, and cloud provider metadata IPs like 169.254.169.254) will be immediately terminated by the Scope Guard.

## 3. Rate Limiting and Subprocess Controls
- Max request concurrency: 10 requests/second.
- Timeout per HTTP request: 10 seconds.
- Hard scan timeout: 20 minutes maximum per target.
- Subprocesses execute through explicit argument lists (`subprocess.Popen` without `shell=True`).
