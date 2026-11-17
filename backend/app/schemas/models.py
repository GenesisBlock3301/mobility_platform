"""Pydantic request and response models. Unknown fields are rejected."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from app.matching.types import (
    Band,
    CriterionStatus,
    EligibilityKind,
    EligibilityStatus,
    OverallEligibility,
    Sponsorship,
)
from app.schemas.countries import ISO_COUNTRY_CODES

LanguageLevelName = Literal["basic", "conversational", "professional", "fluent", "native"]
OpportunityType = Literal["job", "internship"]
WorkMode = Literal["onsite", "hybrid", "remote"]
EducationLevelName = Literal["secondary", "diploma", "bachelor", "master", "doctorate"]
ShortText = Annotated[str, Field(min_length=1, max_length=60)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def _country(value: str) -> str:
    code = value.strip().upper()
    if code not in ISO_COUNTRY_CODES:
        raise ValueError(f"'{value}' is not a valid ISO country code")
    return code


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result = []
    for value in values:
        key = value.casefold()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


class LanguageSkill(StrictModel):
    language: Annotated[str, Field(min_length=1, max_length=40)]
    level: LanguageLevelName


class WorkAuthorisation(StrictModel):
    country_code: str
    status: Literal["authorised", "not_authorised"]

    @field_validator("country_code")
    @classmethod
    def _check_country(cls, value: str) -> str:
        return _country(value)


class ProfileFields(StrictModel):
    """The stored profile fields. Every field may be empty here, so profiles saved
    before some fields became required can still be read."""

    education_level: EducationLevelName | None = None
    field_of_study: Annotated[str | None, Field(max_length=120)] = None
    years_experience: Annotated[Decimal | None, Field(ge=0, le=60, decimal_places=1)] = None
    experience_summary: Annotated[str | None, Field(max_length=500)] = None
    skills: Annotated[list[ShortText], Field(max_length=50)] = []
    languages: Annotated[list[LanguageSkill], Field(max_length=15)] = []
    preferred_countries: Annotated[list[str], Field(max_length=20)] = []
    career_interests: Annotated[list[ShortText], Field(max_length=20)] = []
    work_authorisations: Annotated[list[WorkAuthorisation], Field(max_length=50)] = []
    is_current_student: bool | None = None

    @field_validator("field_of_study", "experience_summary")
    @classmethod
    def _blank_to_none(cls, value: str | None) -> str | None:
        return value or None

    @field_validator("skills", "career_interests")
    @classmethod
    def _unique(cls, values: list[str]) -> list[str]:
        return _dedupe(values)

    @field_validator("preferred_countries")
    @classmethod
    def _countries(cls, values: list[str]) -> list[str]:
        return _dedupe([_country(v) for v in values])

    @field_validator("languages")
    @classmethod
    def _unique_languages(cls, values: list[LanguageSkill]) -> list[LanguageSkill]:
        names = [lang.language.casefold() for lang in values]
        if len(names) != len(set(names)):
            raise ValueError("Each language can be listed only once")
        return values

    @field_validator("work_authorisations")
    @classmethod
    def _unique_countries(cls, values: list[WorkAuthorisation]) -> list[WorkAuthorisation]:
        codes = [auth.country_code for auth in values]
        if len(codes) != len(set(codes)):
            raise ValueError("Each country can have only one work authorisation status")
        return values


# The fields that drive most of the score (85 of 100 points). A profile cannot be
# saved without them. The rest stay optional and are scored as "unknown" when empty.
REQUIRED_PROFILE_FIELDS: dict[str, str] = {
    "education_level": "Choose your highest education",
    "years_experience": "Enter your years of work experience",
    "skills": "Add at least one skill",
    "languages": "Add at least one language",
}


class ProfileIn(ProfileFields):
    # validate_default: a missing required field must reach _required, not silently default.
    model_config = ConfigDict(validate_default=True)

    @field_validator(*REQUIRED_PROFILE_FIELDS)
    @classmethod
    def _required(cls, value: object, info: ValidationInfo) -> object:
        if value is None or value == []:
            raise ValueError(REQUIRED_PROFILE_FIELDS[info.field_name or ""])
        return value


class Completeness(BaseModel):
    percent: int
    missing: list[str]


class ProfileOut(ProfileFields):
    model_config = ConfigDict(extra="ignore")

    id: uuid.UUID
    completeness: Completeness
    updated_at: datetime


class LanguageRequirement(BaseModel):
    language: str
    level: LanguageLevelName


class OpportunityOut(BaseModel):
    id: uuid.UUID
    slug: str
    title: str
    organisation: str
    opportunity_type: OpportunityType
    country_code: str
    city: str
    work_mode: WorkMode
    description: str
    required_skills: list[str]
    preferred_skills: list[str]
    min_years_experience: float | None
    max_years_experience: float | None
    min_education_level: EducationLevelName | None
    education_fields: list[str]
    language_requirements: list[LanguageRequirement]
    requires_local_work_authorisation: bool
    visa_sponsorship: Sponsorship
    requires_current_student: bool
    interest_tags: list[str]


class OpportunitySeed(StrictModel):
    """One record in data/opportunities.json, validated before it is inserted."""

    slug: Annotated[str, Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$", max_length=80)]
    title: Annotated[str, Field(min_length=1, max_length=120)]
    organisation: Annotated[str, Field(min_length=1, max_length=120)]
    opportunity_type: OpportunityType
    country_code: str
    city: Annotated[str, Field(min_length=1, max_length=80)]
    work_mode: WorkMode
    description: Annotated[str, Field(min_length=1, max_length=1000)]
    required_skills: list[ShortText]
    preferred_skills: list[ShortText] = []
    min_years_experience: Annotated[Decimal | None, Field(ge=0, le=60)] = None
    max_years_experience: Annotated[Decimal | None, Field(ge=0, le=60)] = None
    min_education_level: EducationLevelName | None = None
    education_fields: list[ShortText] = []
    language_requirements: list[LanguageSkill] = []
    requires_local_work_authorisation: bool
    visa_sponsorship: Sponsorship
    requires_current_student: bool
    interest_tags: list[ShortText] = []

    @field_validator("country_code")
    @classmethod
    def _check_country(cls, value: str) -> str:
        return _country(value)


# Response models read the engine's dataclasses directly (from_attributes) and
# reuse its enums, so a status added in the engine needs no copy here.
class EngineModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CriterionOut(EngineModel):
    criterion: str
    points_earned: float
    points_possible: int
    status: CriterionStatus
    note: str
    matched: list[str]
    missing: list[str]


class EligibilityCheckOut(EngineModel):
    kind: EligibilityKind
    status: EligibilityStatus
    message: str


class WhatIfOut(EngineModel):
    change: str
    new_score: int
    gain: int
    new_eligibility: OverallEligibility
    unblocks: bool


class MatchSummary(BaseModel):
    rank: int
    opportunity: OpportunityOut
    score: int
    band: Band
    eligibility: OverallEligibility
    headline_strengths: list[str]
    headline_gaps: list[str]
    # The message behind the overall eligibility: the blocking reason, or what to verify.
    eligibility_summary: str | None
    verification_checklist: list[str]
    shortlisted: bool


MatchFilter = Literal["all", "strong", "verify", "clear", "blocked"]


class MatchCounts(BaseModel):
    """Counts over the whole ranking, before filtering and paging, for summary tiles and filter chips."""

    all: int
    strong: int  # strong band and not blocked
    partial: int  # partial band and not blocked
    verify: int
    clear: int
    blocked: int


class MatchPage(BaseModel):
    items: list[MatchSummary]
    page: int
    page_size: int
    total: int  # matches after the filter, across all pages
    total_pages: int
    filter: MatchFilter
    counts: MatchCounts


class MatchDetail(MatchSummary):
    criteria: list[CriterionOut]
    eligibility_checks: list[EligibilityCheckOut]
    explanation: str
    what_if: list[WhatIfOut]
