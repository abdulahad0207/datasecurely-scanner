from typing import Dict, List, Tuple
from app.schemas.finding import Finding

PENALTIES = {
    "critical": 25,
    "high": 15,
    "medium": 7,
    "low": 2,
    "info": 0,
}


def calculate_security_grade(findings: List[Finding]) -> Tuple[str, int, Dict[str, int]]:
    """
    Computes a deterministic, defensible security grade (A through F)
    based on normalized findings and penalty thresholds.
    """
    base_score = 100
    counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}

    for f in findings:
        sev = f.severity.lower()
        if sev in counts:
            counts[sev] += 1

    total_deductions = sum(counts[sev] * PENALTIES[sev] for sev in counts)
    final_score = max(0, base_score - total_deductions)

    # Determine baseline grade from score
    if final_score >= 90:
        grade = "A"
    elif final_score >= 80:
        grade = "B"
    elif final_score >= 70:
        grade = "C"
    elif final_score >= 60:
        grade = "D"
    else:
        grade = "F"

    # Enforce severe issue caps:
    # Any Critical issue caps the security posture at D
    if counts["critical"] >= 2:
        grade = "F"
    elif counts["critical"] == 1 and grade in ["A", "B", "C"]:
        grade = "D"

    # 3 or more High issues cap posture at C
    if counts["high"] >= 3 and grade in ["A", "B"]:
        grade = "C"

    # Any High issue caps posture at B
    if counts["high"] >= 1 and grade == "A":
        grade = "B"

    breakdown = {
        "final_score": final_score,
        "deductions": total_deductions,
        "counts": counts,
    }

    return grade, final_score, breakdown
