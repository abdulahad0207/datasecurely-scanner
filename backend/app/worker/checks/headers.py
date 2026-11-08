from typing import Any, Dict, List
import httpx
from app.core.logging import logger

RECOMMENDED_HEADERS = {
    "strict-transport-security": {
        "title": "Missing HTTP Strict Transport Security (HSTS) Header",
        "severity": "medium",
        "description": "HSTS ensures browsers only connect to your website using encrypted HTTPS connections.",
    },
    "content-security-policy": {
        "title": "Missing Content-Security-Policy (CSP) Header",
        "severity": "medium",
        "description": "CSP provides strong defense-in-depth against Cross-Site Scripting (XSS) and data injection.",
    },
    "x-frame-options": {
        "title": "Missing X-Frame-Options Clickjacking Defense",
        "severity": "low",
        "description": "X-Frame-Options prevents your website from being embedded inside malicious iframes.",
    },
    "x-content-type-options": {
        "title": "Missing X-Content-Type-Options Header",
        "severity": "low",
        "description": "Prevents MIME-type confusion attacks by enforcing declared Content-Type headers.",
    },
    "referrer-policy": {
        "title": "Missing Referrer-Policy Header",
        "severity": "info",
        "description": "Protects user privacy by controlling how much referrer information is transmitted.",
    },
    "permissions-policy": {
        "title": "Missing Permissions-Policy Header",
        "severity": "info",
        "description": "Restricts browser features like camera, microphone, and geolocation on your site.",
    },
}


async def check_security_headers(hostname: str) -> List[Dict[str, Any]]:
    """
    Inspects response headers of the target website for missing security configurations
    and sensitive header disclosures.
    """
    findings = []
    url = f"https://{hostname}"

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "datasecurely-scanner/1.0"})
            headers_lower = {k.lower(): v for k, v in resp.headers.items()}

            # 1. Check for missing security headers
            for header_name, meta in RECOMMENDED_HEADERS.items():
                if header_name not in headers_lower:
                    findings.append({
                        "source_tool": "custom_headers",
                        "template_id": f"missing-{header_name}",
                        "title": meta["title"],
                        "severity": meta["severity"],
                        "host": hostname,
                        "evidence": f"Header '{header_name}' was not returned by {url}",
                    })

            # 2. Check for technology disclosure headers
            if "server" in headers_lower:
                server_val = headers_lower["server"]
                # If version numbers are exposed
                if any(char.isdigit() for char in server_val):
                    findings.append({
                        "source_tool": "custom_headers",
                        "template_id": "exposed-server-version",
                        "title": "Web Server Version Disclosed",
                        "severity": "low",
                        "host": hostname,
                        "evidence": f"Server: {server_val}",
                    })

            if "x-powered-by" in headers_lower:
                findings.append({
                    "source_tool": "custom_headers",
                    "template_id": "exposed-x-powered-by",
                    "title": "Technology Fingerprint Disclosed via X-Powered-By",
                    "severity": "low",
                    "host": hostname,
                    "evidence": f"X-Powered-By: {headers_lower['x-powered-by']}",
                })

    except Exception as e:
        logger.warning(f"Header check error for {hostname}: {e}")

    return findings
