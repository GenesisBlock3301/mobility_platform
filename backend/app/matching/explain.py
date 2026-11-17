"""Explanation text, built only from scoring results.

These functions receive CriterionResult and EligibilityCheck objects, never the
profile or the opportunity, so the text cannot claim anything the score does
not contain.
"""

from app.matching.types import (
    Band,
    CriterionResult,
    CriterionStatus,
    EligibilityCheck,
    EligibilityStatus,
    OverallEligibility,
)

BAND_LABEL = {Band.STRONG: "Strong fit", Band.PARTIAL: "Partial fit", Band.POOR: "Poor fit"}

_POSITIVE = {CriterionStatus.MET}
_NEGATIVE = {CriterionStatus.NOT_MET, CriterionStatus.PARTLY_MET, CriterionStatus.UNKNOWN}


def strengths(criteria: tuple[CriterionResult, ...], limit: int = 2) -> tuple[str, ...]:
    good = [c for c in criteria if c.status in _POSITIVE]
    good.sort(key=lambda c: -c.points_possible)
    return tuple(c.note for c in good[:limit])


def gaps(criteria: tuple[CriterionResult, ...], limit: int = 2) -> tuple[str, ...]:
    bad = [c for c in criteria if c.status in _NEGATIVE]
    bad.sort(key=lambda c: -c.points_lost)
    return tuple(c.note for c in bad[:limit])


def explain(
    score: int, band: Band, criteria: tuple[CriterionResult, ...], checks: tuple[EligibilityCheck, ...]
) -> str:
    sentences = [f"{BAND_LABEL[band]} ({score}/100)."]
    ordered = sorted(criteria, key=lambda c: -c.points_possible)
    sentences += [c.note for c in ordered if c.status in _POSITIVE]
    sentences += [c.note for c in ordered if c.status in _NEGATIVE]
    for check in checks:
        if check.status is EligibilityStatus.NOT_MET:
            sentences.append(f"Blocked: {check.message}")
        elif check.status is EligibilityStatus.VERIFICATION_REQUIRED:
            sentences.append(f"To verify: {check.message}")
    return " ".join(sentences)


def eligibility_summary(overall: OverallEligibility, checks: tuple[EligibilityCheck, ...]) -> str | None:
    """The message behind the overall result: the blocking reason, or the first thing to verify."""
    wanted = {
        OverallEligibility.BLOCKED: EligibilityStatus.NOT_MET,
        OverallEligibility.REQUIRES_VERIFICATION: EligibilityStatus.VERIFICATION_REQUIRED,
    }.get(overall)
    return next((c.message for c in checks if c.status is wanted), None)


def checklist(checks: tuple[EligibilityCheck, ...]) -> tuple[str, ...]:
    steps: list[str] = []
    for check in checks:
        for step in check.verification_steps:
            if step not in steps:
                steps.append(step)
    return tuple(steps)
