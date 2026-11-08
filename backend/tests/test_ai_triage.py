import pytest
from app.schemas.finding import Finding
from app.worker.ai.client import GeminiAIClient
from app.worker.ai.report_writer import generate_executive_report_summary
from app.worker.ai.triage import triage_all_findings


@pytest.fixture
def gemini_client():
    return GeminiAIClient()


@pytest.mark.asyncio
async def test_triage_finding_english(gemini_client: GeminiAIClient):
    finding_data = {
        "title": "Missing Content-Security-Policy",
        "template_id": "canonical:missing-csp",
        "severity": "medium",
        "host": "my-company.in",
        "evidence_block": "<untrusted_evidence>No CSP header found</untrusted_evidence>",
        "fingerprint": "fp-test-csp-en",
    }
    result = await gemini_client.triage_finding(finding_data, language="en")
    assert result.plain_summary != ""
    assert result.business_impact != ""
    assert len(result.fix_steps) >= 1
    assert 1 <= result.priority <= 5
    assert 0.0 <= result.confidence <= 1.0
    assert result.effort in ["low", "medium", "high"]


@pytest.mark.asyncio
async def test_triage_finding_hinglish(gemini_client: GeminiAIClient):
    finding_data = {
        "title": "Missing HTTP Strict Transport Security",
        "template_id": "canonical:missing-hsts",
        "severity": "medium",
        "host": "my-company.in",
        "evidence_block": "<untrusted_evidence>HSTS not enforced</untrusted_evidence>",
        "fingerprint": "fp-test-hsts-hi",
    }
    result = await gemini_client.triage_finding(finding_data, language="hi-Latn")
    assert result.plain_summary != ""
    assert "Aapki website" in result.plain_summary or "Aapke" in result.plain_summary
    assert len(result.fix_steps) >= 1


@pytest.mark.asyncio
async def test_triage_cache_hit(gemini_client: GeminiAIClient):
    finding_data = {
        "title": "Exposed .git",
        "template_id": "canonical:exposed-git",
        "severity": "high",
        "host": "my-company.in",
        "evidence_block": "<untrusted_evidence>ref: refs/heads/main</untrusted_evidence>",
        "fingerprint": "fp-cached-git-1",
    }
    res1 = await gemini_client.triage_finding(finding_data, language="en")
    res2 = await gemini_client.triage_finding(finding_data, language="en")
    assert res1 is res2  # Same cached instance


@pytest.mark.asyncio
async def test_triage_all_findings_wrapper():
    findings = [
        Finding(
            source_tool="custom_headers",
            template_id="canonical:missing-csp",
            title="Missing CSP",
            severity="medium",
            host="shop.in",
            fingerprint="fp-batch-1",
        ),
        Finding(
            source_tool="custom_tls",
            template_id="canonical:tls-cert-expired",
            title="Expired Certificate",
            severity="high",
            host="shop.in",
            fingerprint="fp-batch-2",
        ),
    ]
    triaged = await triage_all_findings(findings, language="en")
    assert len(triaged) == 2
    assert triaged[0].ai_json is not None
    assert triaged[1].ai_json is not None


@pytest.mark.asyncio
async def test_generate_executive_report_summary():
    findings = [
        Finding(
            source_tool="custom_headers",
            template_id="canonical:missing-csp",
            title="Missing CSP",
            severity="medium",
            host="shop.in",
            fingerprint="fp-exec-1",
        )
    ]
    summary_en = await generate_executive_report_summary("shop.in", "B", findings, language="en")
    assert summary_en.executive_summary != ""
    assert len(summary_en.top_actions) == 3
    assert summary_en.language == "en"

    summary_hi = await generate_executive_report_summary("shop.in", "B", findings, language="hi-Latn")
    assert summary_hi.executive_summary != ""
    assert "Aapki website" in summary_hi.executive_summary
    assert summary_hi.language == "hi-Latn"
