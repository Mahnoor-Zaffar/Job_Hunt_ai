"""Companies API — list, detail, watchlist, statistics."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.session import get_db
from backend.models.company import Company
from backend.models.watchlist import CompanyWatchlist
from backend.repositories.company import CompanyRepository
from backend.repositories.infrastructure import CompanyWatchlistRepository
from backend.schemas.base import BaseSchema

router = APIRouter(prefix="/companies", tags=["companies"])


class CompanyResponse(BaseSchema):
    id: str
    name: str
    website: str | None = None
    logo_url: str | None = None
    description: str | None = None
    industry: str | None = None
    size: str | None = None
    headquarters: str | None = None
    is_active: bool = True
    job_count: int = 0


class CompanyListResponse(BaseSchema):
    items: list[CompanyResponse]
    total: int
    page: int
    per_page: int
    pages: int


class WatchlistItem(BaseSchema):
    id: str
    company_name: str
    notes: str | None = None
    notify_on_new_jobs: bool = True
    is_active: bool = True


class WatchlistListResponse(BaseSchema):
    items: list[WatchlistItem]
    total: int


class WatchlistCreateRequest(BaseSchema):
    company_name: str
    notes: str | None = None
    notify_on_new_jobs: bool = True


def _company_to_response(c: Company) -> CompanyResponse:
    return CompanyResponse(
        id=str(c.id),
        name=c.name,
        website=c.website,
        logo_url=c.logo_url,
        description=c.description,
        industry=c.industry,
        size=c.size,
        headquarters=c.headquarters,
        is_active=c.is_active,
    )


def _watchlist_to_response(w: CompanyWatchlist) -> WatchlistItem:
    return WatchlistItem(
        id=str(w.id),
        company_name=w.company_name,
        notes=w.notes,
        notify_on_new_jobs=w.notify_on_new_jobs,
        is_active=w.is_active,
    )


@router.get("", response_model=CompanyListResponse)
async def list_companies(
    db: AsyncSession = Depends(get_db),
    name: str | None = Query(None, description="Filter by name"),
    industry: str | None = Query(None, description="Filter by industry"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
) -> CompanyListResponse:
    """List companies."""
    repo = CompanyRepository(db)
    if name:
        company = await repo.get_by_name(name)
        items = [company] if company else []
        total = len(items)
    else:
        items = await repo.get_active(skip=(page - 1) * per_page, limit=per_page)
        total = await repo.count()

    from sqlalchemy import func
    from sqlalchemy import select as sa_select

    from backend.models.job import Job

    cnt_query = sa_select(Job.company, func.count()).group_by(Job.company)
    cnt_result = await db.execute(cnt_query)
    job_counts: dict[str, int] = {str(r[0]): r[1] for r in cnt_result if r[0] is not None}

    enriched = []
    for c in items:
        resp = _company_to_response(c)
        resp.job_count = job_counts.get(c.name, 0)
        enriched.append(resp)

    return CompanyListResponse(
        items=enriched,
        total=total,
        page=page,
        per_page=per_page,
        pages=max(1, (total + per_page - 1) // per_page) if total else 1,
    )


@router.get("/{company_id}", response_model=CompanyResponse)
async def get_company(
    company_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> CompanyResponse:
    """Get a single company."""
    repo = CompanyRepository(db)
    c = await repo.get_by_id(company_id)
    if c is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return _company_to_response(c)


# -- Watchlist -------------------------------------------------------------


@router.get("/watchlist", response_model=WatchlistListResponse)
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> WatchlistListResponse:
    """Get a user's company watchlist."""
    repo = CompanyWatchlistRepository(db)
    items = await repo.get_by_user(user_id)
    return WatchlistListResponse(
        items=[_watchlist_to_response(w) for w in items],
        total=len(items),
    )


@router.post("/watchlist", response_model=WatchlistItem, status_code=201)
async def add_to_watchlist(
    body: WatchlistCreateRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
) -> WatchlistItem:
    """Add a company to the watchlist."""
    repo = CompanyWatchlistRepository(db)
    existing = await repo.get_by_user_and_company(user_id, body.company_name)
    if existing:
        raise HTTPException(status_code=409, detail="Already in watchlist")
    entry = CompanyWatchlist(
        user_id=user_id,
        company_name=body.company_name,
        notes=body.notes,
        notify_on_new_jobs=body.notify_on_new_jobs,
    )
    created = await repo.create(entry)
    return _watchlist_to_response(created)


@router.delete("/watchlist/{watchlist_id}", status_code=204)
async def remove_from_watchlist(
    watchlist_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Remove a company from the watchlist."""
    repo = CompanyWatchlistRepository(db)
    entry = await repo.get_by_id(watchlist_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    await repo.delete(entry)


@router.patch("/watchlist/{watchlist_id}", response_model=WatchlistItem)
async def update_watchlist(
    watchlist_id: uuid.UUID,
    body: WatchlistCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> WatchlistItem:
    """Update a watchlist entry."""
    repo = CompanyWatchlistRepository(db)
    entry = await repo.get_by_id(watchlist_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    entry.company_name = body.company_name
    entry.notes = body.notes
    entry.notify_on_new_jobs = body.notify_on_new_jobs
    await db.flush()
    return _watchlist_to_response(entry)
