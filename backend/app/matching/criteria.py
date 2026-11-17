"""One scoring function per criterion. The weights live here and add up to 100.

Missing-data rule, applied by every function:
- the role states no requirement            -> full points, NO_REQUIREMENT
- the role states one and the profile is empty -> 0 points, UNKNOWN
Missing data is never scored as satisfied.
"""

import re
from collections.abc import Callable, Iterable

from app.matching.normalise import country_name, normalise_skill, normalise_text, same_language
from app.matching.types import CriterionResult, CriterionStatus, Opportunity, Profile

WEIGHTS: dict[str, int] = {
    "skills": 35,
    "experience": 20,
    "education": 15,
    "language": 15,
    "location": 10,
    "interests": 5,
}

# Share of the skills weight that comes from required skills when the role
# also lists preferred skills.
REQUIRED_SKILL_SHARE = 0.8
# Years above the stated maximum before the "may be overqualified" rule applies.
OVERQUALIFIED_MARGIN = 3
OVERQUALIFIED_POINTS = 14
REMOTE_OUTSIDE_PREFERENCES_POINTS = 5
EDUCATION_LEVEL_POINTS = 9
EDUCATION_FIELD_POINTS = 6

assert sum(WEIGHTS.values()) == 100, "criterion weights must add up to 100"  # noqa: S101
assert EDUCATION_LEVEL_POINTS + EDUCATION_FIELD_POINTS == WEIGHTS["education"]  # noqa: S101


def _join(items: Iterable[str]) -> str:
    items = list(items)
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def _no_requirement(name: str, note: str) -> CriterionResult:
    return CriterionResult(name, WEIGHTS[name], WEIGHTS[name], CriterionStatus.NO_REQUIREMENT, note)


def _unknown(name: str, note: str, missing: Iterable[str] = ()) -> CriterionResult:
    return CriterionResult(name, 0, WEIGHTS[name], CriterionStatus.UNKNOWN, note, missing=tuple(missing))


def _scored(
    name: str, earned: float, note: str, matched: Iterable[str] = (), missing: Iterable[str] = ()
) -> CriterionResult:
    """Round once, then derive the status from the rounded points."""
    weight = WEIGHTS[name]
    points = round(earned, 1)
    if points >= weight:
        status = CriterionStatus.MET
    elif points <= 0:
        status = CriterionStatus.NOT_MET
    else:
        status = CriterionStatus.PARTLY_MET
    return CriterionResult(name, points, weight, status, note, tuple(matched), tuple(missing))


def _partition[T](items: Iterable[T], test: Callable[[T], bool]) -> tuple[list[T], list[T]]:
    yes: list[T] = []
    no: list[T] = []
    for item in items:
        (yes if test(item) else no).append(item)
    return yes, no


def score_skills(profile: Profile, opp: Opportunity) -> CriterionResult:
    if not opp.required_skills and not opp.preferred_skills:
        return _no_requirement("skills", "No skills requirement stated.")
    if not profile.skills:
        return _unknown(
            "skills",
            "Unknown: add your skills to your profile.",
            (s.lower() for s in opp.required_skills + opp.preferred_skills),
        )

    have = {normalise_skill(s) for s in profile.skills}

    def held(skill: str) -> bool:
        return normalise_skill(skill) in have

    req_matched, req_missing = _partition([s.lower() for s in opp.required_skills], held)
    pref_matched, pref_missing = _partition([s.lower() for s in opp.preferred_skills], held)

    req_cov = len(req_matched) / len(opp.required_skills) if opp.required_skills else 1.0
    if opp.preferred_skills:
        pref_cov = len(pref_matched) / len(opp.preferred_skills)
        coverage = REQUIRED_SKILL_SHARE * req_cov + (1 - REQUIRED_SKILL_SHARE) * pref_cov
    else:
        coverage = req_cov

    parts = []
    if opp.required_skills:
        sentence = f"You match {len(req_matched)} of {len(opp.required_skills)} required skills"
        sentence += f" ({_join(req_matched)})." if req_matched else "."
        parts.append(sentence)
        if req_missing:
            parts.append(f"Missing required: {_join(req_missing)}.")
    if pref_matched:
        parts.append(f"Preferred skills you have: {_join(pref_matched)}.")
    if pref_missing:
        parts.append(f"Missing preferred: {_join(pref_missing)}.")

    return _scored(
        "skills",
        WEIGHTS["skills"] * coverage,
        " ".join(parts),
        req_matched + pref_matched,
        req_missing + pref_missing,
    )


def _years(value: float) -> str:
    number = f"{value:g}"
    return f"{number} year" if value == 1 else f"{number} years"


def _range(opp: Opportunity) -> str:
    lo, hi = opp.min_years_experience, opp.max_years_experience
    if lo is not None and hi is not None:
        return f"{lo:g} to {hi:g} years"
    if lo is not None:
        return f"at least {_years(lo)}"
    return f"up to {_years(hi or 0)}"


def score_experience(profile: Profile, opp: Opportunity) -> CriterionResult:
    if opp.min_years_experience is None and opp.max_years_experience is None:
        return _no_requirement("experience", "No experience requirement stated.")
    if profile.years_experience is None:
        return _unknown("experience", "Unknown: add your years of experience to your profile.")

    weight = WEIGHTS["experience"]
    years = profile.years_experience
    lo = opp.min_years_experience or 0
    hi = opp.max_years_experience
    if years < lo:
        return _scored(
            "experience", weight * years / lo, f"You have {_years(years)}; the role asks for {_range(opp)}."
        )
    if hi is not None and years > hi + OVERQUALIFIED_MARGIN:
        note = f"You have {_years(years)}, well above the {_range(opp)} asked for. You may be overqualified."
        return _scored("experience", OVERQUALIFIED_POINTS, note)
    return _scored(
        "experience", weight, f"Your {_years(years)} of experience meets the {_range(opp)} asked for."
    )


def _field_matches(field_of_study: str, accepted: tuple[str, ...]) -> str | None:
    """An accepted field matches when it appears as whole words in the user's field:
    "Business" matches "Business Administration", but "Science" does not match
    "Computer science". Limit: plurals and synonyms ("Social sciences") do not match."""
    mine = normalise_text(field_of_study)
    for item in accepted:
        theirs = normalise_text(item)
        if theirs and re.search(rf"\b{re.escape(theirs)}\b", mine):
            return item.lower()
    return None


def score_education(profile: Profile, opp: Opportunity) -> CriterionResult:
    if opp.min_education_level is None and not opp.education_fields:
        return _no_requirement("education", "No education requirement stated.")
    if profile.education_level is None and not profile.field_of_study:
        return _unknown("education", "Unknown: add your education to your profile.")

    earned = 0.0
    parts = []
    required_level = opp.min_education_level
    if required_level is None:
        earned += EDUCATION_LEVEL_POINTS
    elif profile.education_level is None:
        parts.append(f"The role asks for a {required_level.label}; your level is not stated.")
    elif profile.education_level >= required_level:
        earned += EDUCATION_LEVEL_POINTS
        parts.append(f"Your {profile.education_level.label} meets the level asked for.")
    else:
        parts.append(
            f"The role asks for a {required_level.label}; you have a {profile.education_level.label}."
        )

    if not opp.education_fields:
        earned += EDUCATION_FIELD_POINTS
    elif not profile.field_of_study:
        parts.append("Your field of study is not stated.")
    elif _field_matches(profile.field_of_study, opp.education_fields):
        earned += EDUCATION_FIELD_POINTS
        parts.append(f"{profile.field_of_study} is a field they accept.")
    else:
        parts.append(
            f"{profile.field_of_study} is not one of the fields they list "
            f"({_join(f.lower() for f in opp.education_fields)})."
        )

    return _scored("education", earned, " ".join(parts))


def language_met(profile: Profile, language: str, level: int) -> bool:
    return any(same_language(lang.language, language) and lang.level >= level for lang in profile.languages)


def score_language(profile: Profile, opp: Opportunity) -> CriterionResult:
    reqs = opp.language_requirements
    if not reqs:
        return _no_requirement("language", "No language requirement stated.")
    if not profile.languages:
        return _unknown("language", "Unknown: add your languages to your profile.", (r.label for r in reqs))
    met, unmet = _partition(reqs, lambda r: language_met(profile, r.language, r.level))
    parts = []
    if met:
        parts.append(f"You meet the language requirement for {_join(r.label for r in met)}.")
    if unmet:
        parts.append(f"Not met: {_join(r.label for r in unmet)}.")
    return _scored(
        "language",
        WEIGHTS["language"] * len(met) / len(reqs),
        " ".join(parts),
        (r.label for r in met),
        (r.label for r in unmet),
    )


def score_location(profile: Profile, opp: Opportunity) -> CriterionResult:
    if not profile.preferred_countries:
        return _unknown("location", "Unknown: add your preferred countries to your profile.")
    place = country_name(opp.country_code)
    preferred = {c.upper() for c in profile.preferred_countries}
    if opp.country_code.upper() in preferred:
        return _scored(
            "location",
            WEIGHTS["location"],
            f"{place[0].upper() + place[1:]} is one of your preferred countries.",
        )
    if opp.work_mode == "remote":
        return _scored(
            "location",
            REMOTE_OUTSIDE_PREFERENCES_POINTS,
            f"Remote role based in {place}, which is not in your preferences.",
        )
    return _scored("location", 0, f"{place[0].upper() + place[1:]} is not in your preferred countries.")


def score_interests(profile: Profile, opp: Opportunity) -> CriterionResult:
    if not opp.interest_tags:
        return _no_requirement("interests", "The role lists no interest areas.")
    if not profile.career_interests:
        return _unknown("interests", "Unknown: add your career interests to your profile.")
    tags = {normalise_text(t) for t in opp.interest_tags}
    matched = [i.lower() for i in profile.career_interests if normalise_text(i) in tags]
    # Divide by the smaller of the two lists, so listing more interests never
    # lowers a role's score, and one matching interest can earn full points.
    possible = min(len(profile.career_interests), len(tags))
    earned = min(WEIGHTS["interests"], WEIGHTS["interests"] * len(matched) / possible)
    if matched:
        note = f"{len(matched)} of a possible {possible} interest matches: {_join(matched)}."
    else:
        note = "None of your career interests match this role."
    return _scored("interests", earned, note, matched)


SCORERS = (score_skills, score_experience, score_education, score_language, score_location, score_interests)
