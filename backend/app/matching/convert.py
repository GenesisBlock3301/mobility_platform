"""Build engine dataclasses from plain dictionaries (seed JSON or database rows)."""

from collections.abc import Mapping
from typing import Any

from app.matching.types import (
    EducationLevel,
    Language,
    LanguageLevel,
    Opportunity,
    Profile,
    Sponsorship,
    WorkAuthorisation,
    WorkAuthStatus,
)


def _languages(items: list[Mapping[str, Any]] | None) -> tuple[Language, ...]:
    return tuple(Language(i["language"], LanguageLevel.parse(i["level"])) for i in items or [])


def _float(value: Any) -> float | None:
    return None if value is None else float(value)


def opportunity_from_mapping(data: Mapping[str, Any]) -> Opportunity:
    level = data.get("min_education_level")
    return Opportunity(
        id=str(data.get("id") or data["slug"]),
        slug=data["slug"],
        title=data["title"],
        organisation=data["organisation"],
        country_code=data["country_code"],
        city=data["city"],
        work_mode=data["work_mode"],
        required_skills=tuple(data.get("required_skills") or ()),
        preferred_skills=tuple(data.get("preferred_skills") or ()),
        min_years_experience=_float(data.get("min_years_experience")),
        max_years_experience=_float(data.get("max_years_experience")),
        min_education_level=EducationLevel.parse(level) if level else None,
        education_fields=tuple(data.get("education_fields") or ()),
        language_requirements=_languages(data.get("language_requirements")),
        requires_local_work_authorisation=bool(data.get("requires_local_work_authorisation")),
        visa_sponsorship=Sponsorship(data.get("visa_sponsorship") or "unknown"),
        requires_current_student=bool(data.get("requires_current_student")),
        interest_tags=tuple(data.get("interest_tags") or ()),
    )


def profile_from_mapping(data: Mapping[str, Any]) -> Profile:
    level = data.get("education_level")
    return Profile(
        education_level=EducationLevel.parse(level) if level else None,
        field_of_study=data.get("field_of_study") or None,
        years_experience=_float(data.get("years_experience")),
        skills=tuple(data.get("skills") or ()),
        languages=_languages(data.get("languages")),
        preferred_countries=tuple(data.get("preferred_countries") or ()),
        career_interests=tuple(data.get("career_interests") or ()),
        work_authorisations=tuple(
            WorkAuthorisation(a["country_code"], WorkAuthStatus(a["status"]))
            for a in data.get("work_authorisations") or []
        ),
        is_current_student=data.get("is_current_student"),
    )
