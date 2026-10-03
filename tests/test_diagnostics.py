"""Tests for the Mawaqit diagnostics."""

from mawaqit.exceptions import MawaqitException
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mawaqit.diagnostics import async_get_config_entry_diagnostics
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from .conftest import build_prayer_data


async def test_diagnostics(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test the diagnostics redact the token, the home and the mosque."""
    await setup_mawaqit_integration()
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diagnostics == {
        "entry": {
            "version": 1,
            "minor_version": 3,
            "data": {
                CONF_API_KEY: "**REDACTED**",
                "uuid": "**REDACTED**",
                CONF_LATITUDE: "**REDACTED**",
                CONF_LONGITUDE: "**REDACTED**",
            },
        },
        "coordinator": {
            "last_update_success": True,
            "last_update_success_time": coordinator.last_update_success_time,
            "last_exception": None,
        },
        "prayer_times": {
            **build_prayer_data(),
            "uuid": "**REDACTED**",
            "name": "**REDACTED**",
            "url": "**REDACTED**",
            "announcements": "**REDACTED**",
        },
    }


async def test_diagnostics_after_failed_update(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test the diagnostics show the error and the data of the last success."""
    await setup_mawaqit_integration()
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    last_success_time = coordinator.last_update_success_time
    coordinator.client.fetch_prayer_times.side_effect = MawaqitException("boom")
    await coordinator.async_refresh()

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diagnostics["coordinator"] == {
        "last_update_success": False,
        "last_update_success_time": last_success_time,
        "last_exception": "Error communicating with MAWAQIT: boom",
    }
    assert diagnostics["prayer_times"]["calendar"] == build_prayer_data()["calendar"]
