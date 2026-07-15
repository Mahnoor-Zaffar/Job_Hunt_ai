from fastapi import APIRouter

from backend.api.v1.health import router as health_router
from backend.api.v1.jobs import router as jobs_router
from backend.api.v1.scrapers import router as scrapers_router

api_v1_router = APIRouter()
api_v1_router.include_router(health_router, tags=["health"])
api_v1_router.include_router(scrapers_router, tags=["scrapers"])
api_v1_router.include_router(jobs_router, tags=["jobs"])
