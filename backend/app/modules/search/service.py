from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.search.providers import PostgresSearchProvider, SearchProvider
from app.modules.search.schemas import (
    SearchFilterOptionsResponse,
    SearchProductsResponse,
    SearchQueryParams,
)


class SearchService:
    """Service layer orchestrating marketplace search and discovery operations."""

    def __init__(self, provider: Optional[SearchProvider] = None) -> None:
        self._provider = provider or PostgresSearchProvider()

    @property
    def provider(self) -> SearchProvider:
        return self._provider

    def set_provider(self, provider: SearchProvider) -> None:
        """Allow switching search backend (e.g. from PostgreSQL to Meilisearch) at runtime."""
        self._provider = provider

    async def search_products(
        self,
        db: AsyncSession,
        params: SearchQueryParams,
    ) -> SearchProductsResponse:
        return await self._provider.search_products(db, params)

    async def get_filter_options(
        self,
        db: AsyncSession,
    ) -> SearchFilterOptionsResponse:
        return await self._provider.get_filter_options(db)


# Global singleton instance for injection
search_service = SearchService()
