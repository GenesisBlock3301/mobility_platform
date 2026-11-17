"""Narrow the application role's rights to what the app actually does.

The role script grants row access by default. Here the app role keeps full row
access to the tables it writes (profiles, shortlist_entries), gets read-only
access to opportunities, and none to alembic_version.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-17
"""

import os
import re
from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _app_role() -> str | None:
    role = os.environ.get("APP_DB_USER")
    if not role:
        return None  # e.g. the test database, which has no separate app role
    if not re.fullmatch(r"[a-z_][a-z0-9_]{0,62}", role):
        raise RuntimeError("APP_DB_USER must be a plain lower-case identifier")
    return role


def upgrade() -> None:
    role = _app_role()
    if role is None:
        return
    op.execute(f'REVOKE INSERT, UPDATE, DELETE ON opportunities FROM "{role}"')
    op.execute(f'REVOKE ALL ON alembic_version FROM "{role}"')
    op.execute(f'GRANT SELECT ON opportunities TO "{role}"')
    op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON profiles, shortlist_entries TO "{role}"')


def downgrade() -> None:
    role = _app_role()
    if role is None:
        return
    op.execute(f'GRANT SELECT, INSERT, UPDATE, DELETE ON opportunities, alembic_version TO "{role}"')
