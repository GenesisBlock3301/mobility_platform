"""The three cases the brief requires: strong match, partial match, critical gap."""

from app.matching import score_match
from app.matching.types import Band, EligibilityKind, EligibilityStatus, OverallEligibility


def _criterion(result, name):
    return next(c for c in result.criteria if c.criterion == name)


def test_strong_match_programme_assistant(sample_profile, by_slug):
    result = score_match(sample_profile, by_slug["programme-assistant-ngo-berlin"])

    assert result.band is Band.STRONG
    assert result.score == 91
    skills = _criterion(result, "skills")
    assert set(skills.matched) == {"reporting", "project coordination", "stakeholder communication"}
    assert skills.missing == ("budget tracking",)
    # A strong fit is still not "eligible": work authorisation is unknown.
    assert result.eligibility is OverallEligibility.REQUIRES_VERIFICATION
    work = next(c for c in result.eligibility_checks if c.kind is EligibilityKind.WORK_AUTHORISATION)
    assert work.status is EligibilityStatus.VERIFICATION_REQUIRED


def test_partial_match_operations_analyst(sample_profile, by_slug):
    result = score_match(sample_profile, by_slug["operations-analyst-fintech-amsterdam"])

    assert result.band is Band.PARTIAL
    assert "sql" in _criterion(result, "skills").missing
    assert _criterion(result, "location").points_earned == 0


def test_critical_gap_german_client_associate(sample_profile, by_slug):
    result = score_match(sample_profile, by_slug["german-speaking-client-associate-munich"])

    assert result.eligibility is OverallEligibility.BLOCKED
    blocking = [c for c in result.eligibility_checks if c.status is EligibilityStatus.NOT_MET]
    assert len(blocking) == 1
    assert "German" in blocking[0].message
    # The fit score is still calculated and reported.
    assert result.score == 57
    assert result.band is Band.PARTIAL
    assert "Blocked:" in result.explanation
