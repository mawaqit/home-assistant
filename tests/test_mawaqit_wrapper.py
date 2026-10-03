"""Tests for the Mawaqit API wrapper."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.mawaqit import mawaqit_wrapper
from custom_components.mawaqit.const import MOSQUES_PER_PAGE
from custom_components.mawaqit.types import MawaqitMosqueData


async def test_all_mosques_neighborhood_converts_api_payload(
    mock_mosques_search_api_raw: list[dict],
    mock_mosques_search_api_wrapper: list[MawaqitMosqueData],
) -> None:
    """Test the raw API payload is converted to MawaqitMosqueData objects."""
    client = MagicMock()
    client.all_mosques_neighborhood = AsyncMock(
        return_value=mock_mosques_search_api_raw
    )

    result = await mawaqit_wrapper.all_mosques_neighborhood(client)

    assert result == mock_mosques_search_api_wrapper
    client.all_mosques_neighborhood.assert_awaited_once_with()


async def test_all_mosques_neighborhood_empty_result() -> None:
    """Test an empty API response yields an empty list."""
    client = MagicMock()
    client.all_mosques_neighborhood = AsyncMock(return_value=[])

    assert await mawaqit_wrapper.all_mosques_neighborhood(client) == []


async def test_fetch_mosques_by_keyword_converts_api_payload(
    mock_mosques_search_api_raw: list[dict],
    mock_mosques_search_api_wrapper: list[MawaqitMosqueData],
) -> None:
    """Test a page of keyword results is converted to MawaqitMosqueData objects."""
    client = MagicMock()
    client.fetch_mosques_by_keyword = AsyncMock(
        return_value=mock_mosques_search_api_raw
    )

    result = await mawaqit_wrapper.fetch_mosques_by_keyword(client, "Paris", 2)

    assert result == mock_mosques_search_api_wrapper
    client.fetch_mosques_by_keyword.assert_awaited_once_with(
        "Paris", 2, MOSQUES_PER_PAGE
    )
