from typing import Dict, List, Optional
from app.core.logging import logger
from app.db.models import ScanDiffModel, ScanModel
from app.db.repository import repo
from app.schemas.finding import Finding

GRADE_RANK = {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}


def compare_grades(previous_grade: Optional[str], current_grade: Optional[str]) -> str:
    if not previous_grade or not current_grade:
        return "first_scan"
    prev_r = GRADE_RANK.get(previous_grade.upper(), 3)
    curr_r = GRADE_RANK.get(current_grade.upper(), 3)
    if curr_r > prev_r:
        return "improved"
    elif curr_r < prev_r:
        return "degraded"
    return "unchanged"


async def compute_and_save_scan_diff(
    current_scan: ScanModel,
    previous_scan: Optional[ScanModel] = None,
) -> ScanDiffModel:
    """
    Computes delta between current scan and previous scan:
    - new_findings: present in current, not in previous
    - resolved_findings: present in previous, not in current
    - persistent_findings: present in both
    """
    current_findings = await repo.list_findings_by_scan(current_scan.id)

    if previous_scan is None:
        previous_scan = await repo.get_previous_completed_scan(
            domain_id=current_scan.domain_id,
            current_scan_id=current_scan.id,
        )

    if previous_scan is None:
        diff_payload = {
            "new_findings": [f.model_dump() for f in current_findings],
            "resolved_findings": [],
            "persistent_findings": [],
            "previous_grade": None,
            "current_grade": current_scan.grade,
        }
        return await repo.save_scan_diff(
            scan_id=current_scan.id,
            domain_id=current_scan.domain_id,
            previous_scan_id=None,
            grade_change="first_scan",
            new_findings_count=len(current_findings),
            resolved_findings_count=0,
            persistent_findings_count=0,
            diff_json=diff_payload,
        )

    previous_findings = await repo.list_findings_by_scan(previous_scan.id)

    prev_by_fp: Dict[str, Finding] = {f.fingerprint: f for f in previous_findings}
    curr_by_fp: Dict[str, Finding] = {f.fingerprint: f for f in current_findings}

    new_findings = [f for fp, f in curr_by_fp.items() if fp not in prev_by_fp]
    resolved_findings = [f for fp, f in prev_by_fp.items() if fp not in curr_by_fp]
    persistent_findings = [f for fp, f in curr_by_fp.items() if fp in prev_by_fp]

    grade_change = compare_grades(previous_scan.grade, current_scan.grade)

    diff_payload = {
        "new_findings": [f.model_dump() for f in new_findings],
        "resolved_findings": [f.model_dump() for f in resolved_findings],
        "persistent_findings": [f.model_dump() for f in persistent_findings],
        "previous_grade": previous_scan.grade,
        "current_grade": current_scan.grade,
    }

    diff_record = await repo.save_scan_diff(
        scan_id=current_scan.id,
        domain_id=current_scan.domain_id,
        previous_scan_id=previous_scan.id,
        grade_change=grade_change,
        new_findings_count=len(new_findings),
        resolved_findings_count=len(resolved_findings),
        persistent_findings_count=len(persistent_findings),
        diff_json=diff_payload,
    )

    logger.info(
        f"Scan diff computed for {current_scan.hostname}: "
        f"{len(new_findings)} new, {len(resolved_findings)} resolved, {len(persistent_findings)} persistent. "
        f"Grade: {previous_scan.grade} -> {current_scan.grade} ({grade_change})"
    )

    return diff_record
