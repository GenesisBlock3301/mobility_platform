"""Score, rank and "what if" for one profile against many opportunities."""

import math
from dataclasses import replace

from app.matching import explain as ex
from app.matching.criteria import SCORERS
from app.matching.eligibility import check_eligibility, overall
from app.matching.normalise import same_language
from app.matching.types import (
    Band,
    Language,
    MatchResult,
    Opportunity,
    OverallEligibility,
    Profile,
    WhatIf,
)

STRONG_THRESHOLD = 75
PARTIAL_THRESHOLD = 50


def _round(value: float) -> int:
    """Round half up, so 70.5 becomes 71 (Python's round() would give 70)."""
    return math.floor(value + 0.5)


def band_for(score: int) -> Band:
    if score >= STRONG_THRESHOLD:
        return Band.STRONG
    if score >= PARTIAL_THRESHOLD:
        return Band.PARTIAL
    return Band.POOR


def score_match(profile: Profile, opp: Opportunity) -> MatchResult:
    criteria = tuple(scorer(profile, opp) for scorer in SCORERS)
    score = _round(sum(c.points_earned for c in criteria))
    band = band_for(score)
    checks = check_eligibility(profile, opp)
    eligibility = overall(checks)
    return MatchResult(
        opportunity=opp,
        score=score,
        band=band,
        criteria=criteria,
        eligibility=eligibility,
        eligibility_checks=checks,
        eligibility_summary=ex.eligibility_summary(eligibility, checks),
        explanation=ex.explain(score, band, criteria, checks),
        strengths=ex.strengths(criteria),
        gaps=ex.gaps(criteria),
        verification_checklist=ex.checklist(checks),
    )


def _sort_key(result: MatchResult) -> tuple[bool, int, str]:
    return (result.eligibility is OverallEligibility.BLOCKED, -result.score, result.opportunity.slug)


def rank(profile: Profile, opportunities: list[Opportunity]) -> list[MatchResult]:
    """Not blocked before blocked, then score descending, then slug for stable ties."""
    return sorted((score_match(profile, o) for o in opportunities), key=_sort_key)


def what_if(
    profile: Profile, opp: Opportunity, limit: int = 3, base: MatchResult | None = None
) -> tuple[WhatIf, ...]:
    """Re-score with one missing skill or language added; report the largest gains.

    Pass ``base`` when the current result is already known, to avoid scoring it twice."""
    base = base or score_match(profile, opp)
    candidates: list[tuple[str, Profile]] = []
    for skill in opp.required_skills + opp.preferred_skills:
        trial = replace(profile, skills=profile.skills + (skill,))
        candidates.append((f"Add the skill {skill.lower()}", trial))
    for req in opp.language_requirements:
        kept = tuple(lang for lang in profile.languages if not same_language(lang.language, req.language))
        trial = replace(profile, languages=kept + (Language(req.language, req.level),))
        candidates.append((f"Add {req.language} at {req.level.label} level", trial))

    results: list[WhatIf] = []
    for change, trial in candidates:
        after = score_match(trial, opp)
        unblocks = (
            base.eligibility is OverallEligibility.BLOCKED
            and after.eligibility is not OverallEligibility.BLOCKED
        )
        gain = after.score - base.score
        if gain > 0 or unblocks:
            results.append(WhatIf(change, after.score, gain, after.eligibility, unblocks))
    results.sort(key=lambda w: (not w.unblocks, -w.gain, w.change))
    return tuple(results[:limit])
