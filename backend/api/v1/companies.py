"""Companies API — list, detail, watchlist, statistics, sync, email verification."""

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
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
    hr_email: str | None = None
    hr_email_confidence: int | None = None
    hr_email_source: str | None = None
    hr_email_verified_at: str | None = None
    job_count: int = 0


class CompanyListResponse(BaseSchema):
    items: list[CompanyResponse]
    total: int
    page: int
    per_page: int
    pages: int


class SyncCompaniesResponse(BaseSchema):
    synced: int
    message: str


class EmailVerificationStatusResponse(BaseSchema):
    total: int
    verified: int
    unverified: int


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


class ToggleWatchRequest(BaseModel):
    company_name: str
    watch: bool = True


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
        hr_email=c.hr_email,
        hr_email_confidence=c.hr_email_confidence,
        hr_email_source=c.hr_email_source,
        hr_email_verified_at=str(c.hr_email_verified_at) if c.hr_email_verified_at else None,
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


# -- Sync Companies (must be before /{company_id}) ------------------------


@router.post("/sync-it-companies", response_model=SyncCompaniesResponse)
async def sync_it_companies(
    db: AsyncSession = Depends(get_db),
) -> SyncCompaniesResponse:
    """Import curated IT companies into the companies table."""
    from backend.automation.it_company_scraper import discover_companies

    raw = await discover_companies()
    repo = CompanyRepository(db)
    synced = 0
    for entry in raw:
        existing = await repo.get_by_name(entry["name"])
        if existing:
            if not existing.website:
                existing.website = entry.get("website")
                existing.industry = entry.get("industry")
                existing.size = entry.get("size")
                existing.headquarters = entry.get("city")
            continue
        company = Company(
            name=entry["name"],
            website=entry.get("website"),
            industry=entry.get("industry"),
            size=entry.get("size"),
            headquarters=entry.get("city"),
        )
        await repo.create(company)
        synced += 1
    await db.commit()

    # Auto-watch all companies in the dataset
    wl_repo = CompanyWatchlistRepository(db)
    default_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    for company in raw:
        existing_wl = await wl_repo.get_by_user_and_company(default_user_id, company["name"])
        if not existing_wl:
            await wl_repo.create(CompanyWatchlist(
                user_id=default_user_id,
                company_name=company["name"],
                is_active=True,
                notify_on_new_jobs=True,
                auto_watched=True,
            ))
    await db.commit()

    return SyncCompaniesResponse(
        synced=synced,
        message=f"Synced {synced} IT companies (total {len(raw)})",
    )


@router.post("/sync-startups", response_model=SyncCompaniesResponse)
async def sync_startups(
    db: AsyncSession = Depends(get_db),
) -> SyncCompaniesResponse:
    """Import curated startups into the companies table."""
    repo = CompanyRepository(db)
    wl_repo = CompanyWatchlistRepository(db)
    default_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    known: list[tuple[str, str, str, str, str, str]] = [
        ("DealCart", "dealcart.pk", "Karachi", "E-commerce", "10-25", "dealcart"),
        ("PriceOye", "priceoye.pk", "Islamabad", "E-commerce", "30-50", "priceoye"),
        ("Markaz", "markaz.app", "Islamabad", "E-commerce", "20-40", "markazapp"),
        ("Byte", "byte.pk", "Lahore", "E-commerce", "10-25", "bytepk"),
        ("Tajir", "tajir.com", "Lahore", "E-commerce", "30-60", "tajir"),
        ("Krave Mart", "kravemart.com", "Karachi", "E-commerce", "50-80", "kravemart"),
        ("Sastaticket", "sastaticket.pk", "Karachi", "Travel", "30-50", "sastaticketpk"),
        ("Rider", "rider.pk", "Karachi", "E-commerce", "40-70", "riderpk"),
        ("CreditBook", "creditbook.pk", "Karachi", "Fintech", "40-60", "creditbookpk"),
        ("Udhaar App", "udhaar.app", "Karachi", "Fintech", "20-40", "udhaarapp"),
        ("QistBazaar", "qistbazaar.pk", "Karachi", "Fintech", "20-40", "qistbazaar"),
        ("Haball", "haball.com", "Karachi", "Fintech", "20-40", "haball"),
        ("AdalFi", "adalfi.com", "Lahore", "Fintech", "15-30", "adalfi"),
        ("SadaPay", "sadapay.co", "Islamabad", "Fintech", "50-80", "sadapay"),
        ("NayaPay", "nayapay.com", "Islamabad", "Fintech", "80-120", "nayapay"),
        ("Abhi", "abhi.com.pk", "Karachi", "Fintech", "60-100", "abhi-pk"),
        ("QisstPay", "qisstpay.com", "Islamabad", "Fintech", "30-50", "qisstpay"),
        ("OneLoad", "oneload.com", "Islamabad", "Fintech", "30-50", "oneload"),
        ("Marham", "marham.pk", "Lahore", "HealthTech", "30-50", "marhampk"),
        ("Oladoc", "oladoc.com", "Lahore", "HealthTech", "40-60", "oladoc"),
        ("Sehat Kahani", "sehatkahani.com", "Karachi", "HealthTech", "30-50", "sehat-kahani"),
        ("Maqsad", "maqsad.pk", "Karachi", "EdTech", "30-60", "maqsadpk"),
        ("Zypl AI", "zypl.ai", "Karachi", "AI/ML", "15-30", "zyplai"),
        ("Dastgyr", "dastgyr.com", "Karachi", "B2B Commerce", "60-100", "dastgyr"),
        ("Bazaar Technologies", "bazaar.tech", "Karachi", "B2B Commerce", "80-120", "bazaar-technologies"),
        ("PostEx", "postex.pk", "Karachi", "Logistics", "50-80", "postexpk"),
        ("BridgeLinx", "bridgelinx.com", "Karachi", "Logistics", "30-50", "bridgelinx"),
        ("Bykea", "bykea.com", "Karachi", "Mobility", "60-100", "bykea"),
        ("PakWheels", "pakwheels.com", "Karachi", "Auto", "80-150", "pakwheels"),
        ("Careem", "careem.com", "Karachi", "Mobility", "500+", "careem"),
        ("Systems Limited", "systemsltd.com", "Karachi", "SaaS", "2000+", "systemsltd"),
        ("Arbisoft", "arbisoft.com", "Lahore", "SaaS", "500+", "arbisoft"),
        ("Contour Software", "contour-software.com", "Lahore", "SaaS", "300+", "contoursoftware"),
        ("Folio3", "folio3.com", "Karachi", "SaaS", "300+", "folio3"),
        ("10Pearls", "10pearls.com", "Karachi", "SaaS", "1400+", "10pearls"),
        ("Zameen.com", "zameen.com", "Lahore", "PropTech", "200-500", "zameen"),
    ]

    synced = 0
    for name, domain, city, industry, size, _ in known:
        existing = await repo.get_by_name(name)
        if existing:
            continue
        company = Company(
            name=name,
            website=f"https://{domain}",
            industry=industry,
            size=size,
            headquarters=city,
        )
        await repo.create(company)
        synced += 1
    await db.commit()

    # Auto-watch all startups
    for name, *_ in known:
        existing_wl = await wl_repo.get_by_user_and_company(default_user_id, name)
        if not existing_wl:
            await wl_repo.create(CompanyWatchlist(
                user_id=default_user_id,
                company_name=name,
                is_active=True,
                notify_on_new_jobs=True,
                auto_watched=True,
            ))
    await db.commit()

    return SyncCompaniesResponse(
        synced=synced,
        message=f"Synced {synced} startups",
    )


@router.get("/email-verification-status", response_model=EmailVerificationStatusResponse)
async def email_verification_status(
    db: AsyncSession = Depends(get_db),
) -> EmailVerificationStatusResponse:
    """Get email verification stats."""
    repo = CompanyRepository(db)
    status = await repo.count_verified_status()
    return EmailVerificationStatusResponse(**status)


# -- Watchlist -------------------------------------------------------------


@router.get("/watchlist", response_model=WatchlistListResponse)
async def get_watchlist(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query(..., description="User ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
) -> WatchlistListResponse:
    """Get a user's company watchlist."""
    repo = CompanyWatchlistRepository(db)
    total = await repo.count_by_user(user_id)
    items = await repo.get_by_user(user_id, skip=skip, limit=limit)
    return WatchlistListResponse(
        items=[_watchlist_to_response(w) for w in items],
        total=total,
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


@router.post("/watchlist/toggle")
async def toggle_watch(
    body: ToggleWatchRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Query("00000000-0000-0000-0000-000000000001", description="User ID"),
) -> dict:
    """Toggle watch/unwatch for a company by name."""
    from backend.models.watchlist import CompanyWatchlist

    repo = CompanyWatchlistRepository(db)
    existing = await repo.get_by_user_and_company(user_id, body.company_name)
    if body.watch:
        if not existing:
            entry = CompanyWatchlist(
                user_id=user_id,
                company_name=body.company_name,
                notify_on_new_jobs=True,
                is_active=True,
            )
            await repo.create(entry)
            await db.commit()
        return {"watched": True, "company_name": body.company_name}
    else:
        if existing:
            await repo.delete(existing)
            await db.commit()
        return {"watched": False, "company_name": body.company_name}


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


@router.post("/{company_id}/verify-email")
async def verify_company_email(
    company_id: uuid.UUID,
) -> dict:
    """Trigger on-demand email verification for a single company."""
    from backend.database.session import get_session_factory
    from backend.services.email_verification_service import EmailVerificationService

    factory = get_session_factory()
    service = EmailVerificationService(factory)
    result = await service.verify_single(company_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Company not found or verification failed")
    return result
