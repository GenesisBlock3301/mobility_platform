"""Initial schema: profiles, opportunities, shortlist_entries.

Revision ID: 0001
Revises:
Create Date: 2026-11-17
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TEXT_ARRAY = postgresql.ARRAY(sa.Text())


def upgrade() -> None:
    op.create_table(
        "profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("education_level", sa.Text()),
        sa.Column("field_of_study", sa.Text()),
        sa.Column("years_experience", sa.Numeric(3, 1)),
        sa.Column("experience_summary", sa.Text()),
        sa.Column("skills", TEXT_ARRAY, nullable=False, server_default="{}"),
        sa.Column("languages", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("preferred_countries", TEXT_ARRAY, nullable=False, server_default="{}"),
        sa.Column("career_interests", TEXT_ARRAY, nullable=False, server_default="{}"),
        sa.Column("work_authorisations", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("is_current_student", sa.Boolean()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "education_level IS NULL OR education_level IN "
            "('secondary', 'diploma', 'bachelor', 'master', 'doctorate')",
            name="ck_profiles_education_level",
        ),
        sa.CheckConstraint(
            "years_experience IS NULL OR (years_experience >= 0 AND years_experience <= 60)",
            name="ck_profiles_years_experience",
        ),
        sa.CheckConstraint("char_length(field_of_study) <= 120", name="ck_profiles_field_of_study_len"),
        sa.CheckConstraint("char_length(experience_summary) <= 500", name="ck_profiles_summary_len"),
        sa.CheckConstraint("cardinality(skills) <= 50", name="ck_profiles_skills_count"),
    )

    op.create_table(
        "opportunities",
        sa.Column(
            "id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.func.gen_random_uuid()
        ),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("organisation", sa.Text(), nullable=False),
        sa.Column("opportunity_type", sa.Text(), nullable=False),
        sa.Column("country_code", sa.Text(), nullable=False),
        sa.Column("city", sa.Text(), nullable=False),
        sa.Column("work_mode", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_skills", TEXT_ARRAY, nullable=False, server_default="{}"),
        sa.Column("preferred_skills", TEXT_ARRAY, nullable=False, server_default="{}"),
        sa.Column("min_years_experience", sa.Numeric(3, 1)),
        sa.Column("max_years_experience", sa.Numeric(3, 1)),
        sa.Column("min_education_level", sa.Text()),
        sa.Column("education_fields", TEXT_ARRAY, nullable=False, server_default="{}"),
        sa.Column("language_requirements", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("requires_local_work_authorisation", sa.Boolean(), nullable=False),
        sa.Column("visa_sponsorship", sa.Text(), nullable=False),
        sa.Column("requires_current_student", sa.Boolean(), nullable=False),
        sa.Column("interest_tags", TEXT_ARRAY, nullable=False, server_default="{}"),
        sa.CheckConstraint("work_mode IN ('onsite', 'hybrid', 'remote')", name="ck_opportunities_work_mode"),
        sa.CheckConstraint("opportunity_type IN ('job', 'internship')", name="ck_opportunities_type"),
        sa.CheckConstraint(
            "visa_sponsorship IN ('available', 'not_available', 'unknown')",
            name="ck_opportunities_visa_sponsorship",
        ),
    )

    op.create_table(
        "shortlist_entries",
        sa.Column(
            "profile_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("profiles.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "opportunity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("opportunities.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("shortlist_entries")
    op.drop_table("opportunities")
    op.drop_table("profiles")
