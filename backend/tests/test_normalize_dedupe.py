from app.worker.pipeline.stages.normalize import (
    compute_normalized_fingerprint,
    normalize_and_dedupe_findings,
)


def test_fingerprint_deterministic():
    fp1 = compute_normalized_fingerprint("missing-csp-header", "example.com")
    fp2 = compute_normalized_fingerprint("missing-content-security-policy", "EXAMPLE.COM")
    # Both map to canonical:missing-csp on example.com
    assert fp1 == fp2


def test_deduplicate_identical_issue_from_two_tools():
    scan_id = "test-scan-dedupe-1"
    raw_findings = [
        {
            "source_tool": "custom_headers",
            "template_id": "missing-content-security-policy",
            "title": "Missing Content-Security-Policy (CSP) Header",
            "severity": "medium",
            "host": "example.com",
            "evidence": "Header 'content-security-policy' not returned",
        },
        {
            "source_tool": "nuclei",
            "template_id": "missing-csp-header",
            "title": "Missing Content-Security-Policy Header",
            "severity": "low",
            "host": "example.com",
            "evidence": "curl -i https://example.com",
        },
    ]

    deduped = normalize_and_dedupe_findings(raw_findings, scan_id=scan_id)

    # Must be merged into exactly one finding
    assert len(deduped) == 1
    f = deduped[0]
    assert f.template_id == "canonical:missing-csp"
    # Escalated to highest severity between 'low' and 'medium'
    assert f.severity == "medium"
    # Source tools merged
    assert "custom_headers" in f.source_tool
    assert "nuclei" in f.source_tool
    # Consolidated evidence
    assert "content-security-policy" in f.evidence
    assert "curl -i" in f.evidence


def test_severity_escalation():
    scan_id = "test-scan-dedupe-2"
    raw_findings = [
        {
            "source_tool": "tool_a",
            "template_id": "exposed-git-head",
            "title": "Git Exposed",
            "severity": "medium",
            "host": "my-site.in",
            "evidence": "sample1",
        },
        {
            "source_tool": "tool_b",
            "template_id": "exposed-git-config",
            "title": "Git Config Exposed",
            "severity": "high",
            "host": "my-site.in",
            "evidence": "sample2",
        },
    ]

    deduped = normalize_and_dedupe_findings(raw_findings, scan_id=scan_id)
    assert len(deduped) == 1
    assert deduped[0].severity == "high"
