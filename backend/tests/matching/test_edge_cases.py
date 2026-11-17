from dataclasses import replace

import pytest

from app.matching import rank, score_match, what_if
from app.matching.completeness import FIELD_LABELS, completeness
from app.matching.criteria import WEIGHTS
from app.matching.types import (
    CriterionStatus,
    EligibilityKind,
    EligibilityStatus,
    Language,
    LanguageLevel,
    Opportunity,
    OverallEligibility,
    Profile,
    Sponsorship,
    WorkAuthorisation,
    WorkAuthStatus,
)


def _work_check(result):
    return next(c for c in result.eligibility_checks if c.kind is EligibilityKind.WORK_AUTHORISATION)


def test_weights_add_up_to_100():
    assert sum(WEIGHTS.values()) == 100


def test_empty_profile_is_never_marked_met(by_slug):
    empty = Profile()
    result = score_match(empty, by_slug["programme-assistant-ngo-berlin"])
    for criterion in result.criteria:
        assert criterion.status is not CriterionStatus.MET
        if criterion.status is not CriterionStatus.NO_REQUIREMENT:
            assert criterion.points_earned == 0
    assert result.eligibility is not OverallEligibility.NO_KNOWN_BLOCKERS
    report = completeness(empty)
    assert report.percent == 0
    assert set(report.missing) == set(FIELD_LABELS)


def test_unknown_work_authorisation_is_never_met(sample_profile, opportunities):
    for opp in opportunities:
        result = score_match(sample_profile, opp)
        for check in result.eligibility_checks:
            if check.kind is EligibilityKind.WORK_AUTHORISATION:
                assert check.status is EligibilityStatus.VERIFICATION_REQUIRED


def test_declared_authorised_still_needs_verification(sample_profile, by_slug):
    profile = replace(
        sample_profile, work_authorisations=(WorkAuthorisation("DE", WorkAuthStatus.AUTHORISED),)
    )
    result = score_match(profile, by_slug["programme-assistant-ngo-berlin"])
    check = _work_check(result)
    assert check.status is EligibilityStatus.VERIFICATION_REQUIRED
    assert "self-declared" in check.message


def test_not_authorised_without_sponsorship_is_blocked(sample_profile, by_slug):
    profile = replace(
        sample_profile, work_authorisations=(WorkAuthorisation("SG", WorkAuthStatus.NOT_AUTHORISED),)
    )
    opp = by_slug["graduate-trainee-business-operations-singapore"]
    assert opp.visa_sponsorship is Sponsorship.NOT_AVAILABLE
    result = score_match(profile, opp)
    assert result.eligibility is OverallEligibility.BLOCKED
    # Eligibility never changes the fit score.
    assert result.score == score_match(sample_profile, opp).score


def test_not_authorised_with_sponsorship_needs_verification(sample_profile, by_slug):
    profile = replace(
        sample_profile, work_authorisations=(WorkAuthorisation("SG", WorkAuthStatus.NOT_AUTHORISED),)
    )
    result = score_match(profile, by_slug["business-operations-associate-singapore"])
    assert _work_check(result).status is EligibilityStatus.VERIFICATION_REQUIRED


@pytest.mark.parametrize(
    ("student", "expected"),
    [
        (True, EligibilityStatus.MET),
        (False, EligibilityStatus.NOT_MET),
        (None, EligibilityStatus.VERIFICATION_REQUIRED),
    ],
)
def test_student_status_three_ways(sample_profile, by_slug, student, expected):
    profile = replace(sample_profile, is_current_student=student)
    result = score_match(profile, by_slug["business-analyst-intern-vancouver"])
    enrolment = next(c for c in result.eligibility_checks if c.kind is EligibilityKind.ENROLMENT)
    assert enrolment.status is expected


@pytest.mark.parametrize("spelling", ["MS Excel", "excel", " Excel ", "Microsoft Excel"])
def test_skill_normalisation(sample_profile, by_slug, spelling):
    profile = replace(sample_profile, skills=(spelling, "Reporting", "Research"))
    result = score_match(profile, by_slug["business-operations-associate-singapore"])
    skills = next(c for c in result.criteria if c.criterion == "skills")
    assert "excel" in skills.matched


def test_role_without_required_skills_does_not_divide_by_zero(sample_profile):
    opp = Opportunity(
        id="x", slug="x", title="X", organisation="O", country_code="DE", city="Berlin", work_mode="onsite"
    )
    result = score_match(sample_profile, opp)
    skills = next(c for c in result.criteria if c.criterion == "skills")
    assert skills.status is CriterionStatus.NO_REQUIREMENT
    assert skills.points_earned == WEIGHTS["skills"]


def test_language_below_required_level_is_not_met(sample_profile, by_slug):
    profile = replace(sample_profile, languages=(Language("English", LanguageLevel.CONVERSATIONAL),))
    result = score_match(profile, by_slug["programme-assistant-ngo-berlin"])
    assert result.eligibility is OverallEligibility.BLOCKED
    language = next(c for c in result.criteria if c.criterion == "language")
    assert language.points_earned == 0


def test_ranking_is_deterministic(sample_profile, opportunities):
    first = [(r.opportunity.slug, r.score) for r in rank(sample_profile, opportunities)]
    second = [(r.opportunity.slug, r.score) for r in rank(sample_profile, list(reversed(opportunities)))]
    assert first == second


def test_ties_are_ordered_by_slug(sample_profile, by_slug):
    a = by_slug["project-coordinator-toronto"]
    b = by_slug["graduate-trainee-business-operations-singapore"]
    ranked = rank(sample_profile, [a, b])
    assert ranked[0].score == ranked[1].score
    assert [r.opportunity.slug for r in ranked] == sorted([a.slug, b.slug])


def test_explanation_only_names_scored_skills(sample_profile, opportunities):
    all_skills = {s.lower() for o in opportunities for s in o.required_skills + o.preferred_skills}
    for opp in opportunities:
        result = score_match(sample_profile, opp)
        skills = next(c for c in result.criteria if c.criterion == "skills")
        text = result.explanation.lower()
        found = {s for s in all_skills if s in text}
        # Ignore a skill that only appears inside a longer one ("reporting" in
        # "campaign reporting").
        named = {s for s in found if not any(s != o and s in o and o in text for o in found)}
        assert named <= set(skills.matched) | set(skills.missing), opp.slug


def test_what_if_adding_german_unblocks(sample_profile, by_slug):
    suggestions = what_if(sample_profile, by_slug["german-speaking-client-associate-munich"])
    top = suggestions[0]
    assert top.unblocks
    assert "German" in top.change
    assert top.new_score == 72


def test_what_if_reports_gain_for_missing_preferred_skill(sample_profile, by_slug):
    suggestions = what_if(sample_profile, by_slug["programme-assistant-ngo-berlin"])
    assert suggestions[0].change == "Add the skill budget tracking"
    assert suggestions[0].new_score == 98


def test_generic_field_of_study_does_not_match_specific_fields(sample_profile, by_slug):
    profile = replace(sample_profile, field_of_study="Science")
    result = score_match(profile, by_slug["software-engineer-backend-berlin"])  # wants Computer science
    education = next(c for c in result.criteria if c.criterion == "education")
    assert "is a field they accept" not in education.note


def test_adding_unrelated_interests_never_lowers_a_score(sample_profile, opportunities):
    more = replace(sample_profile, career_interests=sample_profile.career_interests + ("Gardening", "Chess"))
    for opp in opportunities:
        assert score_match(more, opp).score >= score_match(sample_profile, opp).score, opp.slug
