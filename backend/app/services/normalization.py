import ipaddress
import re
import secrets
import urllib.parse
from app.core.errors import AppError


BLOCKED_TLDS = {
    "local", "localhost", "internal", "lan", "test",
    "example", "invalid", "home", "corp", "intra",
}

HOSTNAME_REGEX = re.compile(
    r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-_]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63}$"
)


class InvalidDomainError(AppError):
    """Raised when an invalid, non-routable, or disallowed domain is provided."""
    def __init__(self, message: str):
        super().__init__(message, code="INVALID_DOMAIN")


def normalize_domain(raw_input: str) -> str:
    """
    Normalizes and validates a target domain string.
    - Strips scheme (http://, https://)
    - Strips port numbers (:8000)
    - Strips path, query params, trailing slashes
    - Converts to lowercase
    - Rejects IP addresses, localhost, and internal/private TLDs
    """
    if not raw_input or not isinstance(raw_input, str):
        raise InvalidDomainError("Domain cannot be empty.")

    target = raw_input.strip()

    # Prepend scheme if missing so urllib.parse can reliably extract hostname
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", target):
        target = "https://" + target

    parsed = urllib.parse.urlparse(target)
    hostname = parsed.hostname

    if not hostname:
        raise InvalidDomainError(f"Could not extract a valid hostname from '{raw_input}'.")

    hostname = hostname.lower().strip(".")

    # Reject localhost explicitly
    if hostname == "localhost" or hostname.endswith(".localhost"):
        raise InvalidDomainError("Localhost targets are not allowed.")

    # Check if target is an IP address
    try:
        ip = ipaddress.ip_address(hostname)
        raise InvalidDomainError(
            f"Direct IP addresses ('{ip}') cannot be scanned. Please provide a domain name."
        )
    except ValueError:
        # Not a raw IP address, continue
        pass

    # Check TLD
    parts = hostname.split(".")
    if len(parts) < 2:
        raise InvalidDomainError("Target must be a fully-qualified domain name (FQDN).")

    tld = parts[-1]
    if tld in BLOCKED_TLDS:
        raise InvalidDomainError(f"Domains ending with '.{tld}' are internal or reserved and cannot be scanned.")

    # Check length
    if len(hostname) > 253:
        raise InvalidDomainError("Domain name exceeds maximum permitted length of 253 characters.")

    # Validate against FQDN regex
    if not HOSTNAME_REGEX.match(hostname):
        raise InvalidDomainError(f"'{hostname}' is not a syntactically valid domain name.")

    return hostname


def generate_verification_token() -> str:
    """Generates a cryptographically secure random verification token."""
    return secrets.token_urlsafe(24)
