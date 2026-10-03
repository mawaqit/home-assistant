"""Provides a wrapper for interacting with the MAWAQIT API."""

from mawaqit import AsyncMawaqitClient

from .const import MOSQUES_PER_PAGE
from .types import MawaqitMosqueData


async def all_mosques_neighborhood(
    client: AsyncMawaqitClient,
) -> list[MawaqitMosqueData]:
    """Return the mosques around the coordinates configured on the client."""
    response = await client.all_mosques_neighborhood()
    return [MawaqitMosqueData.from_dict(mosque) for mosque in response]


async def fetch_mosques_by_keyword(
    client: AsyncMawaqitClient, keyword: str, page: int
) -> list[MawaqitMosqueData]:
    """Return a page of the mosques matching the keyword."""
    response = await client.fetch_mosques_by_keyword(keyword, page, MOSQUES_PER_PAGE)
    return [MawaqitMosqueData.from_dict(mosque) for mosque in response]
