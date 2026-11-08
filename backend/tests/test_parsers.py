from pathlib import Path
from app.worker.runners.httpx_runner import parse_httpx_output
from app.worker.runners.nmap_runner import parse_nmap_xml
from app.worker.runners.nuclei_runner import parse_nuclei_output
from app.worker.runners.subfinder_runner import parse_subfinder_output

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_httpx_fixture():
    content = (FIXTURES_DIR / "httpx_sample.json").read_text(encoding="utf-8")
    results = parse_httpx_output(content)
    assert len(results) == 1
    item = results[0]
    assert item["status_code"] == 200
    assert item["title"] == "Example Domain"
    assert "HSTS" in item["tech"]
    assert item["tls_version"] == "tls13"


def test_parse_subfinder_fixture():
    content = (FIXTURES_DIR / "subfinder_sample.json").read_text(encoding="utf-8")
    subdomains = parse_subfinder_output(content)
    assert len(subdomains) == 3
    assert "api.example.com" in subdomains
    assert "dev.example.com" in subdomains
    assert "mail.example.com" in subdomains


def test_parse_nuclei_fixture():
    content = (FIXTURES_DIR / "nuclei_sample.jsonl").read_text(encoding="utf-8")
    findings = parse_nuclei_output(content)
    assert len(findings) == 2
    f1, f2 = findings[0], findings[1]
    assert f1["template_id"] == "ssl-issuer"
    assert f1["severity"] == "info"
    assert f2["template_id"] == "missing-csp-header"
    assert f2["severity"] == "low"


def test_parse_nmap_fixture():
    content = (FIXTURES_DIR / "nmap_sample.xml").read_text(encoding="utf-8")
    open_ports = parse_nmap_xml(content)
    # Only open ports 80 and 443 should be extracted, closed port 22 ignored
    assert len(open_ports) == 2
    port_ids = [p["port"] for p in open_ports]
    assert 80 in port_ids
    assert 443 in port_ids
    assert 22 not in port_ids
