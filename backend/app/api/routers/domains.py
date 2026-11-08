import asyncio
from datetime import datetime, timezone
import socket
import ssl
import time
from typing import Dict, List, Optional, Tuple
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from app.api.deps import get_current_user
from app.core.errors import ScopeViolationError, VerificationRequiredError
from app.core.logging import logger
from app.db.repository import repo
from app.schemas.domain import (
    DomainCreate,
    DomainListResponse,
    DomainResponse,
    InfrastructureTelemetry,
    LatestScanSummary,
    VerificationCheckDetails,
    VerificationCheckResponse,
)
from app.schemas.user import AuthUser
from app.services.normalization import (
    InvalidDomainError,
    generate_verification_token,
    normalize_domain,
)
from app.services.scope_guard import scope_guard
from app.services.verification import (
    is_verification_expired,
    verify_domain_ownership,
)

router = APIRouter(prefix="/api/v1/domains", tags=["domains"])


def format_domain_response(domain, latest_scan=None) -> DomainResponse:
    """Helper to populate DNS and well-known verification helpers in responses."""
    current_status = domain.status
    if current_status == "verified" and is_verification_expired(domain.verified_at):
        current_status = "expired"

    return DomainResponse(
        id=domain.id,
        user_id=domain.user_id,
        hostname=domain.hostname,
        verify_token=domain.verify_token,
        status=current_status,
        verified_at=domain.verified_at,
        created_at=domain.created_at,
        dns_record_name=f"_datasecurely.{domain.hostname}",
        dns_record_value=f"datasecurely-verify={domain.verify_token}",
        well_known_url=f"https://{domain.hostname}/.well-known/datasecurely.txt",
        latest_scan=latest_scan,
    )


@router.post("", response_model=DomainResponse, status_code=status.HTTP_201_CREATED)
async def add_domain(
    payload: DomainCreate,
    current_user: AuthUser = Depends(get_current_user),
) -> DomainResponse:
    """
    Normalizes, validates, and adds a target domain for ownership verification.
    Sets status to 'pending'.
    """
    try:
        clean_hostname = normalize_domain(payload.hostname)
    except InvalidDomainError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=e.message,
        )

    # Check for duplicate hostname under the same user
    existing = await repo.get_domain_by_hostname(user_id=current_user.id, hostname=clean_hostname)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Domain '{clean_hostname}' has already been added to your account.",
        )

    verify_token = generate_verification_token()
    domain = await repo.create_domain(
        user_id=current_user.id,
        hostname=clean_hostname,
        verify_token=verify_token,
    )

    logger.info(f"User {current_user.id} added domain {clean_hostname} (status: pending)")
    return format_domain_response(domain)


@router.get("", response_model=DomainListResponse)
async def list_domains(
    current_user: AuthUser = Depends(get_current_user),
) -> DomainListResponse:
    """Lists all domains registered under the authenticated user account."""
    domains = await repo.list_domains_by_user(user_id=current_user.id)
    domain_responses = []
    for d in domains:
        latest_scan_model = None
        if d.status == "verified":
            try:
                scans = await repo.list_scans_by_domain(domain_id=d.id, user_id=current_user.id)
                if scans:
                    latest = scans[0]
                    latest_scan_model = LatestScanSummary(
                        id=latest.id,
                        status=latest.status,
                        grade=latest.grade,
                        findings_count=latest.findings_count,
                        created_at=latest.created_at,
                        finished_at=latest.finished_at,
                    )
            except Exception:
                pass
        domain_responses.append(format_domain_response(d, latest_scan=latest_scan_model))

    return DomainListResponse(
        domains=domain_responses,
        total=len(domain_responses),
    )


@router.get("/{domain_id}", response_model=DomainResponse)
async def get_domain(
    domain_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> DomainResponse:
    """Retrieves verification details and status for a specific domain."""
    domain = await repo.get_domain(domain_id=domain_id, user_id=current_user.id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found",
        )
    latest_scan_model = None
    if domain.status == "verified":
        try:
            scans = await repo.list_scans_by_domain(domain_id=domain.id, user_id=current_user.id)
            if scans:
                latest = scans[0]
                latest_scan_model = LatestScanSummary(
                    id=latest.id,
                    status=latest.status,
                    grade=latest.grade,
                    findings_count=latest.findings_count,
                    created_at=latest.created_at,
                    finished_at=latest.finished_at,
                )
        except Exception:
            pass
    return format_domain_response(domain, latest_scan=latest_scan_model)


# In-memory TTL cache for infrastructure reconnaissance
# Key: domain_id -> (timestamp, InfrastructureTelemetry)
TELEMETRY_CACHE_TTL_SECONDS = 300  # 5 minutes
_telemetry_cache: Dict[str, Tuple[float, InfrastructureTelemetry]] = {}


async def inspect_infrastructure(hostname: str) -> InfrastructureTelemetry:
    telemetry = InfrastructureTelemetry(hostname=hostname)

    # 1. Resolve IP with SSRF Protection via ScopeGuard
    try:
        resolved_ips = await scope_guard.resolve_and_guard(hostname)
        if resolved_ips:
            telemetry.ip_address = resolved_ips[0]
    except ScopeViolationError as e:
        logger.warning(f"Scope guard rejected telemetry IP for {hostname}: {e}")
        return telemetry
    except Exception:
        pass

    if not telemetry.ip_address:
        try:
            ip = await asyncio.to_thread(socket.gethostbyname, hostname)
            if not scope_guard.is_ip_blocked(ip):
                telemetry.ip_address = ip
        except Exception:
            pass

    # 2. Inspect TLS
    def _sync_tls():
        ctx = ssl.create_default_context()
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        with socket.create_connection((hostname, 443), timeout=3.5) as sock:
            with ctx.wrap_socket(sock, server_hostname=hostname) as ssock:
                return ssock.getpeercert(), ssock.version(), ssock.cipher()

    try:
        cert, version, cipher = await asyncio.to_thread(_sync_tls)
        telemetry.tls_version = version
        telemetry.tls_cipher = cipher[0] if cipher else None
        if cert:
            issuer_entries = cert.get("issuer", ())
            issuer_org = None
            for rdn in issuer_entries:
                for key, val in rdn:
                    if key in ("organizationName", "commonName"):
                        issuer_org = val
                        break
                if issuer_org:
                    break
            telemetry.cert_issuer = issuer_org or "Public CA"

            if "notAfter" in cert:
                date_str = cert["notAfter"]
                try:
                    exp_dt = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                    telemetry.cert_expires = exp_dt.strftime("%Y-%m-%d")
                    days_remaining = (exp_dt - datetime.now(timezone.utc)).days
                    telemetry.cert_days_remaining = max(0, days_remaining)
                except Exception:
                    telemetry.cert_expires = str(date_str)
    except Exception:
        pass

    # 3. HTTP Server Banner & Security Headers
    try:
        async with httpx.AsyncClient(timeout=3.5, verify=False, follow_redirects=True) as client:
            res = await client.get(f"https://{hostname}", headers={"User-Agent": "DataSecurely/1.0"})
            telemetry.server_banner = res.headers.get("server")
            telemetry.hsts_header = res.headers.get("strict-transport-security")
            telemetry.csp_header = res.headers.get("content-security-policy")
    except Exception:
        pass

    return telemetry


@router.get("/{domain_id}/telemetry", response_model=InfrastructureTelemetry)
async def get_domain_telemetry(
    domain_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> InfrastructureTelemetry:
    """
    Retrieves infrastructure reconnaissance: DNS IP, TLS certificate, and HTTP headers.
    Guarded by:
    1. Tenant isolation (domain must belong to authenticated user).
    2. ScopeGuard authorization check (domain must be cryptographically verified and not expired).
    3. SSRF prevention (ScopeGuard resolves and blocks internal/private IPs).
    4. 5-minute cache (prevents hammering target domain on repeated views).
    5. Middleware rate limiting (15 requests/min per IP).
    """
    domain = await repo.get_domain(domain_id=domain_id, user_id=current_user.id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found under your account",
        )

    # 1. Authorization Gate: Strict ownership verification check (reuses same gate as scan initiation)
    try:
        scope_guard.check_authorization(domain)
    except VerificationRequiredError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=e.message,
        )

    # 2. Cache Gate: Check if we have fresh cached telemetry (< 5 minutes old)
    now = time.time()
    cached = _telemetry_cache.get(domain_id)
    if cached:
        cached_time, cached_data = cached
        if now - cached_time < TELEMETRY_CACHE_TTL_SECONDS:
            logger.info(f"Serving cached telemetry for {domain.hostname} (age: {int(now - cached_time)}s)")
            return cached_data

    # 3. Perform Live Reconnaissance (SSRF guarded)
    telemetry = await inspect_infrastructure(domain.hostname)

    # 4. Store in Cache
    _telemetry_cache[domain_id] = (now, telemetry)

    return telemetry


@router.post("/{domain_id}/verify", response_model=VerificationCheckResponse)
async def verify_domain(
    domain_id: str,
    current_user: AuthUser = Depends(get_current_user),
) -> VerificationCheckResponse:
    """
    Triggers an immediate ownership verification check via DNS TXT or HTTP well-known file.
    Flips status to 'verified' upon success.
    """
    domain = await repo.get_domain(domain_id=domain_id, user_id=current_user.id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found",
        )

    # Perform the check
    result = await verify_domain_ownership(domain.hostname, domain.verify_token)

    new_status = domain.status
    verified_at = domain.verified_at

    if result.verified:
        new_status = "verified"
        verified_at = datetime.now(timezone.utc)
        await repo.update_domain_status(
            domain_id=domain.id,
            status=new_status,
            verified_at=verified_at,
        )
        logger.info(f"Domain {domain.hostname} marked as VERIFIED for user {current_user.id}")
    else:
        # If it was expired and failed re-verification, keep expired; otherwise pending
        if domain.status != "expired":
            new_status = "pending"

    return VerificationCheckResponse(
        verified=result.verified,
        status=new_status,
        method=result.method,
        message=result.message,
        verified_at=verified_at,
        details=VerificationCheckDetails(
            dns=result.dns_details,
            well_known=result.http_details,
        ),
    )


@router.delete("/{domain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_domain(
    domain_id: str,
    current_user: AuthUser = Depends(get_current_user),
):
    """Deletes a domain from the user's account."""
    domain = await repo.get_domain(domain_id=domain_id, user_id=current_user.id)
    if not domain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Domain not found",
        )
    await repo.delete_domain(domain_id=domain_id, user_id=current_user.id)
    logger.info(f"User {current_user.id} deleted domain {domain.hostname}")
    return None
