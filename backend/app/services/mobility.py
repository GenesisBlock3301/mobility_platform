"""Use cases: profiles, matches and the shortlist.

Services own transactions and translate between database rows, API schemas and
the pure matching engine.
"""

import math
import uuid
from collections.abc import Callable
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app import matching
from app.matching.completeness import completeness
from app.matching.convert import opportunity_from_mapping, profile_from_mapping
from app.matching.types import Band, MatchResult, OverallEligibility
from app.models import Opportunity, Profile
from app.repositories.store import OpportunityRepository, ProfileRepository, ShortlistRepository
from app.schemas.models import (
    Completeness,
    CriterionOut,
    EligibilityCheckOut,
    MatchCounts,
    MatchDetail,
    MatchFilter,
    MatchPage,
    MatchSummary,
    OpportunityOut,
    ProfileIn,
    ProfileOut,
    WhatIfOut,
)
from app.services.errors import NotFoundError

PROFILE_FIELDS = tuple(ProfileIn.model_fields)
OPPORTUNITY_FIELDS = tuple(OpportunityOut.model_fields)


def _profile_dict(row: Profile) -> dict[str, Any]:
    return {name: getattr(row, name) for name in PROFILE_FIELDS}


def _opportunity_dict(row: Opportunity) -> dict[str, Any]:
    return {name: getattr(row, name) for name in OPPORTUNITY_FIELDS}


def profile_out(row: Profile) -> ProfileOut:
    data = _profile_dict(row)
    report = completeness(profile_from_mapping(data))
    return ProfileOut(
        id=row.id,
        updated_at=row.updated_at,
        completeness=Completeness(percent=report.percent, missing=list(report.missing)),
        **data,
    )


def opportunity_out(row: Opportunity) -> OpportunityOut:
    return OpportunityOut.model_validate(_opportunity_dict(row))


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.profiles = ProfileRepository(session)

    async def require(self, profile_id: uuid.UUID) -> Profile:
        profile = await self.profiles.get(profile_id)
        if profile is None:
            raise NotFoundError("Profile")
        return profile

    async def create(self, data: ProfileIn) -> ProfileOut:
        row = await self.profiles.create(data.model_dump(mode="json"))
        await self.session.commit()
        await self.session.refresh(row)
        return profile_out(row)

    async def get(self, profile_id: uuid.UUID) -> ProfileOut:
        return profile_out(await self.require(profile_id))

    async def update(self, profile_id: uuid.UUID, data: ProfileIn) -> ProfileOut:
        row = await self.require(profile_id)
        row = await self.profiles.update(row, data.model_dump(mode="json"))
        await self.session.commit()
        return profile_out(row)

    async def delete(self, profile_id: uuid.UUID) -> None:
        row = await self.require(profile_id)
        await self.profiles.delete(row)  # shortlist rows go with it (ON DELETE CASCADE)
        await self.session.commit()


class OpportunityService:
    def __init__(self, session: AsyncSession) -> None:
        self.opportunities = OpportunityRepository(session)

    async def list(self) -> list[OpportunityOut]:
        return [opportunity_out(r) for r in await self.opportunities.list_all()]

    async def get(self, opportunity_id: uuid.UUID) -> OpportunityOut:
        row = await self.opportunities.get(opportunity_id)
        if row is None:
            raise NotFoundError("Opportunity")
        return opportunity_out(row)


DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


def _open(r: MatchResult) -> bool:
    return r.eligibility != OverallEligibility.BLOCKED


MATCH_FILTERS: dict[str, Callable[[MatchResult], bool]] = {
    "all": lambda r: True,
    "strong": lambda r: r.band == Band.STRONG and _open(r),
    "verify": lambda r: r.eligibility == OverallEligibility.REQUIRES_VERIFICATION,
    "clear": lambda r: r.eligibility == OverallEligibility.NO_KNOWN_BLOCKERS,
    "blocked": lambda r: not _open(r),
}
COUNTS: dict[str, Callable[[MatchResult], bool]] = {
    **MATCH_FILTERS,
    "partial": lambda r: r.band == Band.PARTIAL and _open(r),
}


def _summary(
    result: MatchResult, rank: int, rows: dict[str, Opportunity], shortlisted: set[uuid.UUID]
) -> MatchSummary:
    row = rows[result.opportunity.id]
    return MatchSummary(
        rank=rank,
        opportunity=opportunity_out(row),
        score=result.score,
        band=result.band,
        eligibility=result.eligibility,
        headline_strengths=list(result.strengths),
        headline_gaps=list(result.gaps),
        eligibility_summary=result.eligibility_summary,
        verification_checklist=list(result.verification_checklist),
        shortlisted=row.id in shortlisted,
    )


class MatchService:
    """Matches are computed on every request; nothing is cached, so results are never stale."""

    def __init__(self, session: AsyncSession) -> None:
        self.profiles = ProfileService(session)
        self.opportunities = OpportunityRepository(session)
        self.shortlist = ShortlistRepository(session)

    async def _ranked(self, profile_id: uuid.UUID):
        profile_row = await self.profiles.require(profile_id)
        rows = {str(r.id): r for r in await self.opportunities.list_all()}
        engine_profile = profile_from_mapping(_profile_dict(profile_row))
        opps = [opportunity_from_mapping(_opportunity_dict(r)) for r in rows.values()]
        ranked = matching.rank(engine_profile, opps)
        return engine_profile, ranked, rows, await self.shortlist.ids_for(profile_id)

    async def list(
        self,
        profile_id: uuid.UUID,
        *,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        match_filter: MatchFilter = "all",
    ) -> MatchPage:
        """One page of the ranking.

        The whole ranking is scored first (ranking needs every score), then filtered,
        then sliced. `rank` stays the position in the full ranking, so it does not
        restart on each page or under a filter.
        """
        _, ranked, rows, saved = await self._ranked(profile_id)
        positioned = list(enumerate(ranked, start=1))
        keep = MATCH_FILTERS[match_filter]
        filtered = [(rank, r) for rank, r in positioned if keep(r)]

        start = (page - 1) * page_size
        items = [_summary(r, rank, rows, saved) for rank, r in filtered[start : start + page_size]]
        total = len(filtered)
        return MatchPage(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=max(1, math.ceil(total / page_size)),
            filter=match_filter,
            counts=MatchCounts(**{name: sum(1 for r in ranked if pred(r)) for name, pred in COUNTS.items()}),
        )

    async def detail(self, profile_id: uuid.UUID, opportunity_id: uuid.UUID) -> MatchDetail:
        engine_profile, ranked, rows, saved = await self._ranked(profile_id)
        position = next((i for i, r in enumerate(ranked) if r.opportunity.id == str(opportunity_id)), None)
        if position is None:
            raise NotFoundError("Opportunity")
        result = ranked[position]
        summary = _summary(result, position + 1, rows, saved)
        return MatchDetail(
            **summary.model_dump(),
            criteria=[CriterionOut.model_validate(c) for c in result.criteria],
            eligibility_checks=[EligibilityCheckOut.model_validate(c) for c in result.eligibility_checks],
            explanation=result.explanation,
            what_if=[
                WhatIfOut.model_validate(w)
                for w in matching.what_if(engine_profile, result.opportunity, base=result)
            ],
        )

    async def shortlisted(self, profile_id: uuid.UUID) -> list[MatchSummary]:
        _, ranked, rows, saved = await self._ranked(profile_id)
        # Filter before building response models: only saved roles are serialised.
        return [
            _summary(r, i + 1, rows, saved)
            for i, r in enumerate(ranked)
            if uuid.UUID(r.opportunity.id) in saved
        ]


class ShortlistService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.profiles = ProfileService(session)
        self.opportunities = OpportunityRepository(session)
        self.shortlist = ShortlistRepository(session)

    async def _check(self, profile_id: uuid.UUID, opportunity_id: uuid.UUID) -> None:
        await self.profiles.require(profile_id)
        if await self.opportunities.get(opportunity_id) is None:
            raise NotFoundError("Opportunity")

    async def ids(self, profile_id: uuid.UUID) -> list[uuid.UUID]:
        """Saved opportunity IDs only: cheap enough for the header on every page."""
        await self.profiles.require(profile_id)
        return sorted(await self.shortlist.ids_for(profile_id))

    async def add(self, profile_id: uuid.UUID, opportunity_id: uuid.UUID) -> None:
        await self._check(profile_id, opportunity_id)
        await self.shortlist.add(profile_id, opportunity_id)
        await self.session.commit()

    async def remove(self, profile_id: uuid.UUID, opportunity_id: uuid.UUID) -> None:
        await self._check(profile_id, opportunity_id)
        await self.shortlist.remove(profile_id, opportunity_id)
        await self.session.commit()
