"""Idempotent seed: validate data/opportunities.json, then upsert each record by slug.

Run with: python -m app.seed  (uses MIGRATION_DATABASE_URL, the owner role)
"""

import asyncio
import json
import os
import sys
from pathlib import Path

from pydantic import ValidationError
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import create_async_engine

from app.models import Opportunity
from app.schemas.models import OpportunitySeed

SEED_FILE = Path(__file__).resolve().parent.parent / "data" / "opportunities.json"


def load_seed(path: Path = SEED_FILE) -> list[OpportunitySeed]:
    """Validate every record first; one bad record stops the whole seed."""
    raw = json.loads(path.read_text(encoding="utf-8"))
    records = []
    for index, item in enumerate(raw):
        try:
            records.append(OpportunitySeed.model_validate(item))
        except ValidationError as exc:
            raise SystemExit(f"Seed record {index} ({item.get('slug', '?')}) is invalid:\n{exc}") from exc
    slugs = [r.slug for r in records]
    if len(slugs) != len(set(slugs)):
        raise SystemExit("Seed file contains duplicate slugs")
    return records


async def seed(database_url: str, path: Path = SEED_FILE) -> int:
    records = load_seed(path)
    engine = create_async_engine(database_url)
    try:
        async with engine.begin() as conn:
            for record in records:
                values = record.model_dump(mode="json")
                statement = insert(Opportunity).values(**values)
                statement = statement.on_conflict_do_update(
                    index_elements=[Opportunity.slug],
                    set_={k: statement.excluded[k] for k in values if k != "slug"},
                )
                await conn.execute(statement)
    finally:
        await engine.dispose()
    return len(records)


def main() -> None:
    url = os.environ.get("MIGRATION_DATABASE_URL")
    if not url:
        sys.exit("MIGRATION_DATABASE_URL is not set")
    count = asyncio.run(seed(url))
    print(f"Seeded {count} opportunities")  # noqa: T201


if __name__ == "__main__":
    main()
