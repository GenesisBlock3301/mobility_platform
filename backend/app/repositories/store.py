"""SQLAlchemy queries. Bound parameters only; no SQL is built from strings."""

import uuid
from collections.abc import Sequence
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Opportunity, Profile, ShortlistEntry


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, profile_id: uuid.UUID) -> Profile | None:
        return await self.session.get(Profile, profile_id)

    async def create(self, values: dict[str, Any]) -> Profile:
        profile = Profile(id=uuid.uuid4(), **values)
        self.session.add(profile)
        await self.session.flush()
        return profile

    async def update(self, profile: Profile, values: dict[str, Any]) -> Profile:
        for key, value in values.items():
            setattr(profile, key, value)
        await self.session.flush()
        await self.session.refresh(profile)
        return profile

    async def delete(self, profile: Profile) -> None:
        await self.session.delete(profile)
        await self.session.flush()


class OpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_all(self) -> Sequence[Opportunity]:
        result = await self.session.execute(select(Opportunity).order_by(Opportunity.slug))
        return result.scalars().all()

    async def get(self, opportunity_id: uuid.UUID) -> Opportunity | None:
        return await self.session.get(Opportunity, opportunity_id)


class ShortlistRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def ids_for(self, profile_id: uuid.UUID) -> set[uuid.UUID]:
        result = await self.session.execute(
            select(ShortlistEntry.opportunity_id).where(ShortlistEntry.profile_id == profile_id)
        )
        return set(result.scalars().all())

    async def add(self, profile_id: uuid.UUID, opportunity_id: uuid.UUID) -> None:
        statement = (
            insert(ShortlistEntry)
            .values(profile_id=profile_id, opportunity_id=opportunity_id)
            .on_conflict_do_nothing(index_elements=["profile_id", "opportunity_id"])
        )
        await self.session.execute(statement)

    async def remove(self, profile_id: uuid.UUID, opportunity_id: uuid.UUID) -> None:
        await self.session.execute(
            delete(ShortlistEntry).where(
                ShortlistEntry.profile_id == profile_id,
                ShortlistEntry.opportunity_id == opportunity_id,
            )
        )
