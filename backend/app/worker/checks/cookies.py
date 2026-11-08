from typing import Any, Dict, List
import httpx
from app.core.logging import logger


async def check_cookie_security(hostname: str) -> List[Dict[str, Any]]:
    """
    Inspects Set-Cookie headers for missing security flags:
    Secure, HttpOnly, and SameSite.
    """
    findings = []
    url = f"https://{hostname}"

    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "datasecurely-scanner/1.0"})

            # Get raw Set-Cookie headers
            cookie_headers = resp.headers.get_list("set-cookie")
            for raw_cookie in cookie_headers:
                parts = [p.strip() for p in raw_cookie.split(";")]
                cookie_name = parts[0].split("=")[0] if parts else "unknown"
                parts_lower = [p.lower() for p in parts]

                # Check Secure flag
                if "secure" not in parts_lower:
                    findings.append({
                        "source_tool": "custom_cookies",
                        "template_id": "cookie-missing-secure",
                        "title": f"Cookie '{cookie_name}' Missing 'Secure' Flag",
                        "severity": "medium",
                        "host": hostname,
                        "evidence": f"Set-Cookie: {raw_cookie[:100]}",
                    })

                # Check HttpOnly flag
                if "httponly" not in parts_lower:
                    findings.append({
                        "source_tool": "custom_cookies",
                        "template_id": "cookie-missing-httponly",
                        "title": f"Cookie '{cookie_name}' Missing 'HttpOnly' Flag",
                        "severity": "low",
                        "host": hostname,
                        "evidence": f"Set-Cookie: {raw_cookie[:100]}",
                    })

                # Check SameSite attribute
                has_samesite = any(p.startswith("samesite") for p in parts_lower)
                if not has_samesite:
                    findings.append({
                        "source_tool": "custom_cookies",
                        "template_id": "cookie-missing-samesite",
                        "title": f"Cookie '{cookie_name}' Missing 'SameSite' Attribute",
                        "severity": "low",
                        "host": hostname,
                        "evidence": f"Set-Cookie: {raw_cookie[:100]}",
                    })

    except Exception as e:
        logger.info(f"Cookie check error for {hostname}: {e}")

    return findings
