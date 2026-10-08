"""Tests for the Mawaqit API wrapper."""

from collections.abc import Awaitable, Callable
from unittest.mock import AsyncMock, MagicMock

from mawaqit import AsyncMawaqitClient
from mawaqit.types import MosqueSummary
import pytest
import respx

from custom_components.mawaqit import mawaqit_wrapper
from custom_components.mawaqit.const import MOSQUES_PER_PAGE
from custom_components.mawaqit.types import MawaqitMosqueData
from homeassistant.core import HomeAssistant
from homeassistant.helpers.httpx_client import get_async_client

from .conftest import search_response


async def test_all_mosques_neighborhood_converts_api_payload(
    mock_mosques_search_api_raw: list[dict],
    mock_mosques_search_api_wrapper: list[MawaqitMosqueData],
) -> None:
    """Test the mosques of the library are converted to MawaqitMosqueData objects."""
    client = MagicMock()
    client.mosques.search = AsyncMock(
        return_value=search_response(mock_mosques_search_api_raw)
    )

    result = await mawaqit_wrapper.all_mosques_neighborhood(client, 48.85, 2.35)

    assert result == mock_mosques_search_api_wrapper
    client.mosques.search.assert_awaited_once_with(lat=48.85, lon=2.35)


async def test_all_mosques_neighborhood_empty_result() -> None:
    """Test an empty API response yields an empty list."""
    client = MagicMock()
    client.mosques.search = AsyncMock(return_value=[])

    assert await mawaqit_wrapper.all_mosques_neighborhood(client, 48.85, 2.35) == []


async def test_fetch_mosques_by_keyword_converts_api_payload(
    mock_mosques_search_api_raw: list[dict],
    mock_mosques_search_api_wrapper: list[MawaqitMosqueData],
) -> None:
    """Test a page of keyword results is converted to MawaqitMosqueData objects."""
    client = MagicMock()
    client.mosques.search = AsyncMock(
        return_value=search_response(mock_mosques_search_api_raw)
    )

    result = await mawaqit_wrapper.fetch_mosques_by_keyword(client, "Paris", 2)

    assert result == mock_mosques_search_api_wrapper
    client.mosques.search.assert_awaited_once_with(
        word="Paris", page=2, items_per_page=MOSQUES_PER_PAGE
    )


async def test_fetch_mosque_by_id_converts_api_payload() -> None:
    """Test a mosque found by its ID is converted, labelled with its name."""
    client = MagicMock()
    client.mosques.get = AsyncMock(
        return_value=MosqueSummary(
            id=1234,
            uuid="home-uuid",
            name="My home",
            type="HOME",
            localisation=" 75005 Paris France",
            image="https://mawaqit.net/default.jpg",
        )
    )

    result = await mawaqit_wrapper.fetch_mosque_by_id(client, 1234)

    assert result == MawaqitMosqueData(
        uuid="home-uuid",
        label="My home",
        name="My home",
        localisation=" 75005 Paris France",
    )
    client.mosques.get.assert_awaited_once_with(1234)


@pytest.mark.parametrize(
    "search",
    [
        lambda client: mawaqit_wrapper.all_mosques_neighborhood(client, 48.85, 2.35),
        lambda client: mawaqit_wrapper.fetch_mosques_by_keyword(client, "Paris", 1),
    ],
    ids=["neighborhood", "keyword"],
)
@respx.mock
async def test_search_sends_the_api_token(
    hass: HomeAssistant,
    search: Callable[[AsyncMawaqitClient], Awaitable[list[MawaqitMosqueData]]],
) -> None:
    """Test the searches send the API token, required by MAWAQIT since October 2026."""
    route = respx.get("https://mawaqit.net/api/2.0/mosque/search").respond(json=[])
    client = AsyncMawaqitClient(token="api-token", http_client=get_async_client(hass))

    assert await search(client) == []
    assert route.calls.last.request.headers["Api-Access-Token"] == "api-token"
