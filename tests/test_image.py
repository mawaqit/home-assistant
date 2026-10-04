"""Tests for the Mawaqit image platform."""

from http import HTTPStatus

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator
import respx

from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

from .conftest import build_prayer_data, prayer_times_response

PICTURE_URL = "https://mawaqit.net/upload/picture.jpg"
EXTERIOR_URL = "https://mawaqit.net/upload/exterior.jpg"
LOGO_URL = "https://mawaqit.net/upload/logo.png"

PICTURE = "image.test_mosque_picture"
LOGO = "image.test_mosque_logo"


def _prayer_data(**images: str | None) -> dict:
    """Return prayer data with these image fields."""
    return {**build_prayer_data(fill_all_months=False), **images}


async def _refresh(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry, prayer_data: dict
) -> None:
    """Refresh the prayer times with this data."""
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    coordinator.client.mosques.prayer_times.return_value = prayer_times_response(
        prayer_data
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()


async def _fetch_image(
    hass_client: ClientSessionGenerator, hass: HomeAssistant, entity_id: str
) -> bytes:
    """Return the image served by Home Assistant."""
    client = await hass_client()
    response = await client.get(f"/api/image_proxy/{entity_id}")
    assert response.status == HTTPStatus.OK
    return await response.read()


@respx.mock
async def test_images(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test the picture and the logo of the mosque are served from MAWAQIT."""
    respx.get(PICTURE_URL).respond(content=b"picture", content_type="image/jpeg")
    respx.get(LOGO_URL).respond(content=b"logo", content_type="image/png")
    await setup_mawaqit_integration(
        prayer_data=_prayer_data(image=PICTURE_URL, logo=LOGO_URL)
    )

    assert hass.states.get(PICTURE).attributes["friendly_name"] == (
        "Test Mosque Picture"
    )
    assert await _fetch_image(hass_client, hass, PICTURE) == b"picture"
    assert await _fetch_image(hass_client, hass, LOGO) == b"logo"


@respx.mock
async def test_picture_falls_back_to_exterior_picture(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    hass_client: ClientSessionGenerator,
) -> None:
    """Test the picture is the exterior one when the mosque has no main picture."""
    respx.get(EXTERIOR_URL).respond(content=b"exterior", content_type="image/jpeg")
    await setup_mawaqit_integration(
        prayer_data=_prayer_data(image=None, exteriorPicture=EXTERIOR_URL)
    )

    assert await _fetch_image(hass_client, hass, PICTURE) == b"exterior"
    assert hass.states.get(LOGO) is None


async def test_images_added_when_published(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the images appear when the mosque starts publishing them."""
    await setup_mawaqit_integration(prayer_data=_prayer_data(image=None, logo=None))
    assert hass.states.async_all("image") == []

    await _refresh(hass, mock_config_entry, _prayer_data(image=PICTURE_URL))
    assert hass.states.get(PICTURE) is not None
    assert hass.states.get(LOGO) is None

    await _refresh(
        hass, mock_config_entry, _prayer_data(image=PICTURE_URL, logo=LOGO_URL)
    )
    assert len(hass.states.async_all("image")) == 2
    assert "does not generate unique IDs" not in caplog.text


@respx.mock
async def test_image_changed_by_the_mosque(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    hass_client: ClientSessionGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test a new picture is loaded when the mosque changes it."""
    respx.get(PICTURE_URL).respond(content=b"picture", content_type="image/jpeg")
    respx.get(EXTERIOR_URL).respond(content=b"exterior", content_type="image/jpeg")
    await setup_mawaqit_integration(prayer_data=_prayer_data(image=PICTURE_URL))
    assert await _fetch_image(hass_client, hass, PICTURE) == b"picture"
    first_update = hass.states.get(PICTURE).state

    # Unchanged: the state, which is when the image last changed, stays.
    freezer.tick(60)
    await _refresh(hass, mock_config_entry, _prayer_data(image=PICTURE_URL))
    assert hass.states.get(PICTURE).state == first_update

    freezer.tick(60)
    await _refresh(hass, mock_config_entry, _prayer_data(image=EXTERIOR_URL))
    assert hass.states.get(PICTURE).state != first_update
    assert await _fetch_image(hass_client, hass, PICTURE) == b"exterior"


async def test_image_unavailable_when_no_longer_published(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test an image stays, as unavailable, when the mosque stops publishing it."""
    await setup_mawaqit_integration(prayer_data=_prayer_data(image=PICTURE_URL))

    await _refresh(hass, mock_config_entry, _prayer_data(image=None))
    assert hass.states.get(PICTURE).state == STATE_UNAVAILABLE
