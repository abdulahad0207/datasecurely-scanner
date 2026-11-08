import asyncio
from datetime import datetime, timezone
import socket
import ssl
from typing import Any, Dict, List
from app.core.logging import logger


async def check_tls_configuration(hostname: str, port: int = 443) -> List[Dict[str, Any]]:
    """
    Inspects SSL/TLS certificate validity, expiration, and negotiated cipher suite.
    """
    findings = []

    def _sync_tls_inspect():
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED

        with socket.create_connection((hostname, port), timeout=6.0) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                version = ssock.version()
                cipher = ssock.cipher()
                return cert, version, cipher

    try:
        cert, version, cipher = await asyncio.to_thread(_sync_tls_inspect)

        # 1. Check expiration date
        if cert and "notAfter" in cert:
            # Format: 'May  4 12:00:00 2027 GMT'
            date_str = cert["notAfter"]
            try:
                expiry_dt = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                now = datetime.now(timezone.utc)
                days_left = (expiry_dt - now).days

                if days_left < 0:
                    findings.append({
                        "source_tool": "custom_tls",
                        "template_id": "tls-cert-expired",
                        "title": "SSL/TLS Certificate Has Expired",
                        "severity": "high",
                        "host": hostname,
                        "evidence": f"Certificate expired on {expiry_dt.strftime('%Y-%m-%d')} ({abs(days_left)} days ago).",
                    })
                elif days_left < 15:
                    findings.append({
                        "source_tool": "custom_tls",
                        "template_id": "tls-cert-expiring-critical",
                        "title": "SSL/TLS Certificate Expiring Within 15 Days",
                        "severity": "high",
                        "host": hostname,
                        "evidence": f"Certificate expires in {days_left} days on {expiry_dt.strftime('%Y-%m-%d')}.",
                    })
                elif days_left < 30:
                    findings.append({
                        "source_tool": "custom_tls",
                        "template_id": "tls-cert-expiring-warning",
                        "title": "SSL/TLS Certificate Expiring Soon (<30 Days)",
                        "severity": "medium",
                        "host": hostname,
                        "evidence": f"Certificate expires in {days_left} days on {expiry_dt.strftime('%Y-%m-%d')}.",
                    })
            except Exception as parse_err:
                logger.warning(f"Failed to parse cert expiry date '{date_str}': {parse_err}")

        # 2. Check deprecated protocol version
        if version in ["TLSv1", "TLSv1.1", "SSLv3", "SSLv2"]:
            findings.append({
                "source_tool": "custom_tls",
                "template_id": "deprecated-tls-protocol",
                "title": f"Deprecated TLS Protocol Version Supported ({version})",
                "severity": "high",
                "host": hostname,
                "evidence": f"Negotiated connection with deprecated protocol: {version}",
            })

    except ssl.SSLCertVerificationError as ssl_err:
        findings.append({
            "source_tool": "custom_tls",
            "template_id": "tls-verification-failed",
            "title": "SSL/TLS Certificate Validation Failed",
            "severity": "high",
            "host": hostname,
            "evidence": str(ssl_err),
        })
    except Exception as e:
        logger.info(f"TLS inspection skipped or failed for {hostname}: {e}")

    return findings
