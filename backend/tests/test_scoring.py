from app.schemas.finding import Finding
from app.worker.pipeline.stages.score import calculate_security_grade


def make_finding(template_id: str, severity: str) -> Finding:
    return Finding(
        source_tool="test",
        template_id=template_id,
        title=f"Finding {template_id}",
        severity=severity,
        host="example.com",
        fingerprint=f"fp-{template_id}-{severity}",
    )


def test_clean_scan_grade_a():
    findings = []
    grade, score, _ = calculate_security_grade(findings)
    assert grade == "A"
    assert score == 100


def test_low_findings_grade_a():
    findings = [
        make_finding("low-1", "low"),
        make_finding("low-2", "low"),
    ]
    grade, score, _ = calculate_security_grade(findings)
    assert grade == "A"
    assert score == 96  # 100 - (2 * 2)


def test_medium_findings_grade_b():
    findings = [
        make_finding("med-1", "medium"),
        make_finding("med-2", "medium"),
    ]
    grade, score, _ = calculate_security_grade(findings)
    assert grade == "B"
    assert score == 86  # 100 - (2 * 7)


def test_single_critical_caps_at_d():
    findings = [
        make_finding("crit-1", "critical"),
    ]
    grade, score, _ = calculate_security_grade(findings)
    # Score is 75 (100 - 25), but capped at D due to Critical vulnerability
    assert grade == "D"
    assert score == 75


def test_multiple_criticals_caps_at_f():
    findings = [
        make_finding("crit-1", "critical"),
        make_finding("crit-2", "critical"),
    ]
    grade, score, _ = calculate_security_grade(findings)
    assert grade == "F"
    assert score == 50


def test_score_is_deterministic():
    findings = [
        make_finding("f1", "high"),
        make_finding("f2", "medium"),
        make_finding("f3", "low"),
    ]
    first_grade, first_score, _ = calculate_security_grade(findings)
    for _ in range(10):
        g, s, _ = calculate_security_grade(findings)
        assert g == first_grade
        assert s == first_score
