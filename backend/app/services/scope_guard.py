import ipaddress
from pathlib import Path
from typing import List, Optional
import dns.asyncresolver
import dns.resolver
from app.core.config import settings
from app.core.errors import ScopeViolationError, VerificationRequiredError
from app.core.logging import logger
from app.db.models import DomainModel
from app.services.verification import is_verification_expired


class ScopeGuard:
    """
    Enforces non-negotiable security boundaries before and during scans:
    1. Re-checks domain ownership verification and 90-day validity.
    2. Resolves DNS A and AAAA records.
    3. Blocks SSRF by rejecting any resolution to private, loopback, or metadata IP ranges.
    4. Pins resolved IPs for downstream scanner use.
    """

    def __init__(self, blocked_networks_path: Optional[Path] = None):
        self.blocked_path = (
            blocked_networks_path
            or settings.BASE_DIR / settings.BLOCKED_NETWORKS_FILE
        )
        self.blocked_networks = self._load_blocked_networks()

    def _load_blocked_networks(self) -> List[ipaddress.IPv4Network | ipaddress.IPv6Network]:
        networks = []
        if not self.blocked_path.exists():
            logger.warning(f"Blocked networks file not found at {self.blocked_path}, using hardcoded defaults.")
            default_cidrs = [
                "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16",
                "127.0.0.0/8", "169.254.0.0/16", "100.64.0.0/10",
                "::1/128", "fe80::/10", "0.0.0.0/8"
            ]
            return [ipaddress.ip_network(cidr) for cidr in default_cidrs]

        with open(self.blocked_path, "r", encoding="utf-8") as f:
            for line in f:
                clean = line.strip()
                if clean and not clean.startswith("#"):
                    try:
                        networks.append(ipaddress.ip_network(clean))
                    except ValueError as e:
                        logger.error(f"Invalid CIDR '{clean}' in blocked networks file: {e}")
        return networks

    def check_authorization(self, domain: DomainModel) -> None:
        """Validates that the domain is actively verified and not expired."""
        if domain.status != "verified":
            raise VerificationRequiredError(
                f"Domain '{domain.hostname}' is not verified. Current status: '{domain.status}'."
            )
        if is_verification_expired(domain.verified_at):
            raise VerificationRequiredError(
                f"Ownership verification for '{domain.hostname}' has expired. Re-verification required."
            )

    def is_ip_blocked(self, ip_str: str) -> bool:
        """Checks if a single IP address falls within any blocked network range."""
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return True  # Malformed IP is treated as blocked

        for network in self.blocked_networks:
            if ip in network:
                return True
        return False

    async def resolve_and_guard(self, hostname: str) -> List[str]:
        """
        Resolves DNS records and validates that none point to blocked network ranges.
        Returns pinned public IP addresses.
        """
        resolver = dns.asyncresolver.Resolver()
        resolver.timeout = 5.0
        resolver.lifetime = 5.0

        resolved_ips: List[str] = []

        # Query A records (IPv4)
        try:
            answers_a = await resolver.resolve(hostname, "A")
            for rdata in answers_a:
                resolved_ips.append(str(rdata))
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass
        except Exception as e:
            logger.warning(f"A record query failed for {hostname}: {e}")

        # Query AAAA records (IPv6)
        try:
            answers_aaaa = await resolver.resolve(hostname, "AAAA")
            for rdata in answers_aaaa:
                resolved_ips.append(str(rdata))
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
            pass
        except Exception as e:
            logger.warning(f"AAAA record query failed for {hostname}: {e}")

        if not resolved_ips:
            raise ScopeViolationError(
                f"Domain '{hostname}' could not be resolved to any valid IP address."
            )

        # Deduplicate resolved IPs
        resolved_ips = list(dict.fromkeys(resolved_ips))

        # Check every resolved IP
        for ip in resolved_ips:
            if self.is_ip_blocked(ip):
                logger.critical(
                    f"SSRF BLOCK: Hostname '{hostname}' resolved to prohibited address {ip}."
                )
                raise ScopeViolationError(
                    f"Target '{hostname}' resolved to prohibited/internal IP range ({ip}). Scan aborted."
                )

        logger.info(f"Scope Guard approved '{hostname}' -> {resolved_ips}")
        return resolved_ips


scope_guard = ScopeGuard()
