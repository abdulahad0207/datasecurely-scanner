import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import dns.asyncresolver
import dns.resolver
import httpx
from app.core.logging import logger

VERIFICATION_PREFIX = "datasecurely-verify="
EXPIRY_DAYS = 90


class VerificationResult:
    def __init__(
        self,
        verified: bool,
        method: Optional[str] = None,
        message: str = "",
        dns_details: Optional[str] = None,
        http_details: Optional[str] = None,
    ):
        self.verified = verified
        self.method = method  # "dns_txt" or "well_known"
        self.message = message
        self.dns_details = dns_details
        self.http_details = http_details

    def to_dict(self):
        return {
            "verified": self.verified,
            "method": self.method,
            "message": self.message,
            "details": {
                "dns": self.dns_details,
                "well_known": self.http_details,
            },
        }


async def check_dns_txt(hostname: str, token: str) -> Tuple[bool, str]:
    """
    Checks for the verification token in DNS TXT records.
    Queries both '_datasecurely.<hostname>' and apex '<hostname>'.
    """
    expected_value = f"{VERIFICATION_PREFIX}{token}".strip()
    candidate_names = [f"_datasecurely.{hostname}", hostname]
    errors = []

    resolver = dns.asyncresolver.Resolver()
    resolver.timeout = 5.0
    resolver.lifetime = 5.0

    for name in candidate_names:
        try:
            answers = await resolver.resolve(name, "TXT")
            for rdata in answers:
                # DNS TXT strings can be broken into multiple pieces
                txt_record = "".join(
                    chunk.decode("utf-8", errors="ignore") if isinstance(chunk, bytes) else str(chunk)
                    for chunk in rdata.strings
                ).strip()

                if txt_record == expected_value or txt_record == token:
                    return True, f"Valid TXT record detected at '{name}'."
            errors.append(f"TXT records found at '{name}', but none matched '{expected_value}'.")
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            errors.append(f"No TXT records found at '{name}'.")
        except dns.exception.Timeout:
            errors.append(f"DNS lookup timed out for '{name}'.")
        except Exception as e:
            errors.append(f"DNS query error for '{name}': {str(e)}")

    return False, " | ".join(errors)


async def check_well_known_file(hostname: str, token: str) -> Tuple[bool, str]:
    """
    Checks for the verification token at:
    - https://<hostname>/.well-known/datasecurely.txt
    - http://<hostname>/.well-known/datasecurely.txt
    """
    urls = [
        f"https://{hostname}/.well-known/datasecurely.txt",
        f"http://{hostname}/.well-known/datasecurely.txt",
    ]
    errors = []

    async with httpx.AsyncClient(timeout=6.0, follow_redirects=True) as client:
        for url in urls:
            try:
                # Custom User-Agent to avoid generic crawler blocks
                headers = {"User-Agent": "datasecurely-verifier/1.0"}
                resp = await client.get(url, headers=headers)

                # Ensure redirect stayed on same host
                if resp.url.host != hostname:
                    errors.append(f"Redirected off-scope to {resp.url.host}")
                    continue

                if resp.status_code == 200:
                    body = resp.text.strip()
                    if token in body:
                        return True, f"Verification token found at {url}"
                    else:
                        errors.append(f"{url} returned HTTP 200 but token did not match.")
                else:
                    errors.append(f"{url} returned HTTP {resp.status_code}.")
            except httpx.RequestError as e:
                errors.append(f"Request failed for {url}: {str(e)}")

    return False, " | ".join(errors)


async def verify_domain_ownership(hostname: str, token: str) -> VerificationResult:
    """
    Executes DNS TXT and HTTP well-known checks to verify domain control.
    """
    # 1. Try DNS TXT first (fastest and most standard)
    dns_ok, dns_msg = await check_dns_txt(hostname, token)
    if dns_ok:
        logger.info(f"Ownership verified for {hostname} via DNS TXT.")
        return VerificationResult(
            verified=True,
            method="dns_txt",
            message=f"Domain verified successfully via DNS TXT record.",
            dns_details=dns_msg,
        )

    # 2. Try HTTP well-known file
    http_ok, http_msg = await check_well_known_file(hostname, token)
    if http_ok:
        logger.info(f"Ownership verified for {hostname} via HTTP well-known file.")
        return VerificationResult(
            verified=True,
            method="well_known",
            message=f"Domain verified successfully via .well-known HTTP file.",
            dns_details=dns_msg,
            http_details=http_msg,
        )

    # 3. Both failed
    logger.warning(f"Verification failed for {hostname}: DNS ({dns_msg}), HTTP ({http_msg})")
    return VerificationResult(
        verified=False,
        message="Could not verify domain ownership. Please ensure your DNS TXT record or .well-known file is deployed.",
        dns_details=dns_msg,
        http_details=http_msg,
    )


def is_verification_expired(verified_at: Optional[datetime]) -> bool:
    """Checks if a domain's verification is older than 90 days."""
    if not verified_at:
        return True
    now = datetime.now(timezone.utc)
    # Ensure verified_at is tz-aware
    if verified_at.tzinfo is None:
        verified_at = verified_at.replace(tzinfo=timezone.utc)
    return (now - verified_at) > timedelta(days=EXPIRY_DAYS)
