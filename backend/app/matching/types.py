"""Input and output types for the matching engine. Plain dataclasses only."""

from dataclasses import dataclass, field
from enum import IntEnum, StrEnum


class LanguageLevel(IntEnum):
    BASIC = 1
    CONVERSATIONAL = 2
    PROFESSIONAL = 3
    FLUENT = 4
    NATIVE = 5

    @classmethod
    def parse(cls, value: str) -> LanguageLevel:
        return cls[value.strip().upper()]

    @property
    def label(self) -> str:
        return self.name.lower()


class EducationLevel(IntEnum):
    SECONDARY = 1
    DIPLOMA = 2
    BACHELOR = 3
    MASTER = 4
    DOCTORATE = 5

    @classmethod
    def parse(cls, value: str) -> EducationLevel:
        return cls[value.strip().upper()]

    @property
    def label(self) -> str:
        return {
            EducationLevel.SECONDARY: "secondary school",
            EducationLevel.DIPLOMA: "diploma",
            EducationLevel.BACHELOR: "bachelor's degree",
            EducationLevel.MASTER: "master's degree",
            EducationLevel.DOCTORATE: "doctorate",
        }[self]


class WorkAuthStatus(StrEnum):
    AUTHORISED = "authorised"
    NOT_AUTHORISED = "not_authorised"


class Sponsorship(StrEnum):
    AVAILABLE = "available"
    NOT_AVAILABLE = "not_available"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class Language:
    language: str
    level: LanguageLevel

    @property
    def label(self) -> str:
        return f"{self.language} ({self.level.label})"


@dataclass(frozen=True, slots=True)
class WorkAuthorisation:
    country_code: str
    status: WorkAuthStatus


@dataclass(frozen=True, slots=True)
class Profile:
    """A candidate profile. ``None`` and empty tuples mean "not stated"."""

    education_level: EducationLevel | None = None
    field_of_study: str | None = None
    years_experience: float | None = None
    skills: tuple[str, ...] = ()
    languages: tuple[Language, ...] = ()
    preferred_countries: tuple[str, ...] = ()
    career_interests: tuple[str, ...] = ()
    # A country missing from this tuple means the status is unknown.
    work_authorisations: tuple[WorkAuthorisation, ...] = ()
    # None means unknown.
    is_current_student: bool | None = None

    def work_status_for(self, country_code: str) -> WorkAuthStatus | None:
        for auth in self.work_authorisations:
            if auth.country_code.upper() == country_code.upper():
                return auth.status
        return None


@dataclass(frozen=True, slots=True)
class Opportunity:
    id: str
    slug: str
    title: str
    organisation: str
    country_code: str
    city: str
    work_mode: str  # onsite | hybrid | remote
    required_skills: tuple[str, ...] = ()
    preferred_skills: tuple[str, ...] = ()
    min_years_experience: float | None = None
    max_years_experience: float | None = None
    min_education_level: EducationLevel | None = None
    education_fields: tuple[str, ...] = ()
    language_requirements: tuple[Language, ...] = ()
    requires_local_work_authorisation: bool = False
    visa_sponsorship: Sponsorship = Sponsorship.UNKNOWN
    requires_current_student: bool = False
    interest_tags: tuple[str, ...] = ()


class CriterionStatus(StrEnum):
    MET = "met"
    PARTLY_MET = "partly_met"
    NOT_MET = "not_met"
    NO_REQUIREMENT = "no_requirement"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CriterionResult:
    criterion: str
    points_earned: float
    points_possible: int
    status: CriterionStatus
    note: str
    matched: tuple[str, ...] = ()
    missing: tuple[str, ...] = ()

    @property
    def points_lost(self) -> float:
        return self.points_possible - self.points_earned


class EligibilityKind(StrEnum):
    LANGUAGE = "language"
    WORK_AUTHORISATION = "work_authorisation"
    ENROLMENT = "enrolment"


class EligibilityStatus(StrEnum):
    MET = "met"
    NOT_MET = "not_met"
    VERIFICATION_REQUIRED = "verification_required"


@dataclass(frozen=True, slots=True)
class EligibilityCheck:
    kind: EligibilityKind
    status: EligibilityStatus
    message: str
    # Steps the user should take themselves. Empty when nothing needs checking.
    verification_steps: tuple[str, ...] = ()


class OverallEligibility(StrEnum):
    NO_KNOWN_BLOCKERS = "no_known_blockers"
    REQUIRES_VERIFICATION = "requires_verification"
    BLOCKED = "blocked"


class Band(StrEnum):
    STRONG = "strong"
    PARTIAL = "partial"
    POOR = "poor"


@dataclass(frozen=True, slots=True)
class WhatIf:
    change: str
    new_score: int
    gain: int
    new_eligibility: OverallEligibility
    unblocks: bool


@dataclass(frozen=True, slots=True)
class MatchResult:
    opportunity: Opportunity
    score: int
    band: Band
    criteria: tuple[CriterionResult, ...]
    eligibility: OverallEligibility
    eligibility_checks: tuple[EligibilityCheck, ...]
    explanation: str
    strengths: tuple[str, ...]
    gaps: tuple[str, ...]
    # The message behind the overall eligibility: the blocking reason, or what to verify.
    eligibility_summary: str | None = None
    verification_checklist: tuple[str, ...] = field(default=())
