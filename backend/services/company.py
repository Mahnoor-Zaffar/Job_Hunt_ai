from backend.models.company import Company
from backend.repositories.company import CompanyRepository
from backend.services.base import BaseService


class CompanyService(BaseService):
    """Business logic for company discovery and management."""

    def __init__(self, company_repo: CompanyRepository) -> None:
        super().__init__()
        self._companies = company_repo

    async def get_or_create(self, name: str) -> Company:
        return await self._companies.get_or_create(name)

    async def get_active_companies(self, skip: int = 0, limit: int = 50) -> list[Company]:
        return await self._companies.get_active(skip, limit)

    async def find_by_name(self, name: str) -> Company | None:
        return await self._companies.get_by_name(name)

    async def deactivate(self, company_name: str) -> Company | None:
        company = await self._companies.get_by_name(company_name)
        if company:
            company.is_active = False
            await self._companies.session.flush()
        return company

    async def update_metadata(
        self,
        name: str,
        *,
        website: str | None = None,
        description: str | None = None,
        industry: str | None = None,
    ) -> Company | None:
        company = await self._companies.get_by_name(name)
        if company is None:
            return None
        if website is not None:
            company.website = website
        if description is not None:
            company.description = description
        if industry is not None:
            company.industry = industry
        await self._companies.session.flush()
        return company
