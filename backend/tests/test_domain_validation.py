import pytest
from app.services.normalization import (
    InvalidDomainError,
    generate_verification_token,
    normalize_domain,
)


def test_normalize_valid_domains():
    assert normalize_domain("example.com") == "example.com"
    assert normalize_domain("https://example.com") == "example.com"
    assert normalize_domain("http://EXAMPLE.COM/") == "example.com"
    assert normalize_domain("https://sub.store.co.in/path/to/page?id=123") == "sub.store.co.in"
    assert normalize_domain("my-shop.in:8080") == "my-shop.in"


def test_reject_raw_ip_addresses():
    with pytest.raises(InvalidDomainError, match="Direct IP addresses"):
        normalize_domain("127.0.0.1")

    with pytest.raises(InvalidDomainError, match="Direct IP addresses"):
        normalize_domain("192.168.1.100")

    with pytest.raises(InvalidDomainError, match="Direct IP addresses"):
        normalize_domain("https://10.0.0.1:443")


def test_reject_localhost():
    with pytest.raises(InvalidDomainError, match="Localhost targets are not allowed"):
        normalize_domain("localhost")

    with pytest.raises(InvalidDomainError, match="Localhost targets are not allowed"):
        normalize_domain("http://localhost:3000")


def test_reject_internal_and_reserved_tlds():
    with pytest.raises(InvalidDomainError, match="internal or reserved"):
        normalize_domain("company.local")

    with pytest.raises(InvalidDomainError, match="internal or reserved"):
        normalize_domain("server.internal")

    with pytest.raises(InvalidDomainError, match="internal or reserved"):
        normalize_domain("test.lan")


def test_reject_invalid_syntax():
    with pytest.raises(InvalidDomainError):
        normalize_domain("")

    with pytest.raises(InvalidDomainError):
        normalize_domain("invalid_domain_without_tld")


def test_generate_verification_token():
    t1 = generate_verification_token()
    t2 = generate_verification_token()
    assert len(t1) >= 24
    assert t1 != t2
