"""HTTP routes. Status codes and wiring only; the work happens in services."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response, status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.db import get_session
from app.schemas.models import (
    MatchDetail,
    MatchFilter,
    MatchPage,
    MatchSummary,
    OpportunityOut,
    ProfileIn,
    ProfileOut,
)
from app.services.mobility import (
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    MatchService,
    OpportunityService,
    ProfileService,
    ShortlistService,
)

Session = Annotated[AsyncSession, Depends(get_session)]
NOT_FOUND = {404: {"description": "Profile or opportunity not found"}}

health = APIRouter(prefix="/health", tags=["health"])
router = APIRouter()


@health.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


@health.get("/ready")
async def ready(session: Session) -> JSONResponse:
    try:
        await session.execute(text("SELECT 1"))
    except Exception:  # noqa: BLE001 - any failure means "not ready"
        return JSONResponse({"status": "unavailable", "postgres": "down"}, status_code=503)
    return JSONResponse({"status": "ok", "postgres": "up"})


@router.post("/profiles", status_code=status.HTTP_201_CREATED, tags=["profiles"])
async def create_profile(body: ProfileIn, session: Session) -> ProfileOut:
    return await ProfileService(session).create(body)


@router.get("/profiles/{profile_id}", responses=NOT_FOUND, tags=["profiles"])
async def get_profile(profile_id: uuid.UUID, session: Session) -> ProfileOut:
    return await ProfileService(session).get(profile_id)


@router.put("/profiles/{profile_id}", responses=NOT_FOUND, tags=["profiles"])
async def update_profile(profile_id: uuid.UUID, body: ProfileIn, session: Session) -> ProfileOut:
    return await ProfileService(session).update(profile_id, body)


@router.delete("/profiles/{profile_id}", status_code=204, responses=NOT_FOUND, tags=["profiles"])
async def delete_profile(profile_id: uuid.UUID, session: Session) -> Response:
    await ProfileService(session).delete(profile_id)
    return Response(status_code=204)


@router.get("/opportunities", tags=["opportunities"])
async def list_opportunities(session: Session) -> list[OpportunityOut]:
    return await OpportunityService(session).list()


@router.get("/opportunities/{opportunity_id}", responses=NOT_FOUND, tags=["opportunities"])
async def get_opportunity(opportunity_id: uuid.UUID, session: Session) -> OpportunityOut:
    return await OpportunityService(session).get(opportunity_id)


@router.get("/profiles/{profile_id}/matches", responses=NOT_FOUND, tags=["matches"])
async def list_matches(
    profile_id: uuid.UUID,
    session: Session,
    page: Annotated[int, Query(ge=1, le=10_000)] = 1,
    page_size: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    filter: MatchFilter = "all",  # noqa: A002 - public query parameter name
) -> MatchPage:
    """Ranked matches, one page at a time. A page past the end returns no items, not an error."""
    return await MatchService(session).list(profile_id, page=page, page_size=page_size, match_filter=filter)


@router.get("/profiles/{profile_id}/matches/{opportunity_id}", responses=NOT_FOUND, tags=["matches"])
async def get_match(profile_id: uuid.UUID, opportunity_id: uuid.UUID, session: Session) -> MatchDetail:
    return await MatchService(session).detail(profile_id, opportunity_id)


@router.get("/profiles/{profile_id}/shortlist", responses=NOT_FOUND, tags=["shortlist"])
async def list_shortlist(profile_id: uuid.UUID, session: Session) -> list[MatchSummary]:
    return await MatchService(session).shortlisted(profile_id)


@router.get("/profiles/{profile_id}/shortlist/ids", responses=NOT_FOUND, tags=["shortlist"])
async def list_shortlist_ids(profile_id: uuid.UUID, session: Session) -> list[uuid.UUID]:
    return await ShortlistService(session).ids(profile_id)


@router.put(
    "/profiles/{profile_id}/shortlist/{opportunity_id}",
    status_code=204,
    responses=NOT_FOUND,
    tags=["shortlist"],
)
async def add_to_shortlist(profile_id: uuid.UUID, opportunity_id: uuid.UUID, session: Session) -> Response:
    await ShortlistService(session).add(profile_id, opportunity_id)
    return Response(status_code=204)


@router.delete(
    "/profiles/{profile_id}/shortlist/{opportunity_id}",
    status_code=204,
    responses=NOT_FOUND,
    tags=["shortlist"],
)
async def remove_from_shortlist(
    profile_id: uuid.UUID, opportunity_id: uuid.UUID, session: Session
) -> Response:
    await ShortlistService(session).remove(profile_id, opportunity_id)
    return Response(status_code=204)
