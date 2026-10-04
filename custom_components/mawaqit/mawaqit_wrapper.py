"""Provides a wrapper for interacting with the MAWAQIT API."""

from mawaqit import AsyncMawaqitClient
from mawaqit.types import Mosque

from .const import MOSQUES_PER_PAGE
from .types import MawaqitMosqueData


def _to_mosque_data(mosques: list[Mosque]) -> list[MawaqitMosqueData]:
    return [MawaqitMosqueData.from_dict(mosque.model_dump()) for mosque in mosques]


async def all_mosques_neighborhood(
    client: AsyncMawaqitClient, latitude: float, longitude: float
) -> list[MawaqitMosqueData]:
    """Return the mosques around a position, nearest first."""
    return _to_mosque_data(await client.mosques.search(lat=latitude, lon=longitude))


async def fetch_mosques_by_keyword(
    client: AsyncMawaqitClient, keyword: str, page: int
) -> list[MawaqitMosqueData]:
    """Return a page of the mosques matching the keyword."""
    mosques = await client.mosques.search(
        word=keyword, page=page, items_per_page=MOSQUES_PER_PAGE
    )
    return _to_mosque_data(mosques)
