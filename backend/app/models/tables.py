"""SQLAlchemy table models. The schema itself is created only by Alembic migrations."""

import uuid
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    ARRAY,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

EDUCATION_LEVELS = ("secondary", "diploma", "bachelor", "master", "doctorate")


def _now() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class Profile(Base):
    __tablename__ = "profiles"
    __table_args__ = (
        CheckConstraint(
            "education_level IS NULL OR education_level IN ({})".format(
                ", ".join(f"'{level}'" for level in EDUCATION_LEVELS)
            ),
            name="ck_profiles_education_level",
        ),
        CheckConstraint(
            "years_experience IS NULL OR (years_experience >= 0 AND years_experience <= 60)",
            name="ck_profiles_years_experience",
        ),
        CheckConstraint("char_length(field_of_study) <= 120", name="ck_profiles_field_of_study_len"),
        CheckConstraint("char_length(experience_summary) <= 500", name="ck_profiles_summary_len"),
        CheckConstraint("cardinality(skills) <= 50", name="ck_profiles_skills_count"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    education_level: Mapped[str | None] = mapped_column(Text)
    field_of_study: Mapped[str | None] = mapped_column(Text)
    years_experience: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    experience_summary: Mapped[str | None] = mapped_column(Text)
    skills: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    languages: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False, server_default="[]")
    preferred_countries: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    career_interests: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    work_authorisations: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    is_current_student: Mapped[bool | None] = mapped_column(Boolean)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, onupdate=_now, server_default=func.now()
    )


class Opportunity(Base):
    __tablename__ = "opportunities"
    __table_args__ = (
        CheckConstraint("work_mode IN ('onsite', 'hybrid', 'remote')", name="ck_opportunities_work_mode"),
        CheckConstraint("opportunity_type IN ('job', 'internship')", name="ck_opportunities_type"),
        CheckConstraint(
            "visa_sponsorship IN ('available', 'not_available', 'unknown')",
            name="ck_opportunities_visa_sponsorship",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid()
    )
    slug: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    organisation: Mapped[str] = mapped_column(Text, nullable=False)
    opportunity_type: Mapped[str] = mapped_column(Text, nullable=False)
    country_code: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(Text, nullable=False)
    work_mode: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    required_skills: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    preferred_skills: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    min_years_experience: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    max_years_experience: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    min_education_level: Mapped[str | None] = mapped_column(Text)
    education_fields: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")
    language_requirements: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB, nullable=False, server_default="[]"
    )
    requires_local_work_authorisation: Mapped[bool] = mapped_column(Boolean, nullable=False)
    visa_sponsorship: Mapped[str] = mapped_column(Text, nullable=False)
    requires_current_student: Mapped[bool] = mapped_column(Boolean, nullable=False)
    interest_tags: Mapped[list[str]] = mapped_column(ARRAY(Text), nullable=False, server_default="{}")


class ShortlistEntry(Base):
    __tablename__ = "shortlist_entries"

    profile_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    opportunity_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=_now, server_default=func.now()
    )
