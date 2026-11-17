"""Pure matching engine.

This package must not import FastAPI, SQLAlchemy or anything else from the app.
It takes plain dataclasses in and returns plain dataclasses out, so it can be
tested without a database. ``tests/matching/test_layering.py`` enforces this.
"""

from app.matching.engine import rank, score_match, what_if
from app.matching.types import (
    Band,
    EducationLevel,
    Language,
    LanguageLevel,
    MatchResult,
    Opportunity,
    OverallEligibility,
    Profile,
    WorkAuthorisation,
    WorkAuthStatus,
)

__all__ = [
    "Band",
    "EducationLevel",
    "Language",
    "LanguageLevel",
    "MatchResult",
    "Opportunity",
    "OverallEligibility",
    "Profile",
    "WorkAuthStatus",
    "WorkAuthorisation",
    "rank",
    "score_match",
    "what_if",
]
