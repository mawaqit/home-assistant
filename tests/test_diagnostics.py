"""Tests for the Mawaqit diagnostics."""

from mawaqit import InternalServerError
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mawaqit.diagnostics import async_get_config_entry_diagnostics
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from .conftest import (
    CONNECTION_ERROR,
    build_prayer_data,
    flash_message_response,
    status_error,
)


async def test_diagnostics(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test the diagnostics redact the token, the home and the mosque."""
    await setup_mawaqit_integration()
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    hijri_coordinator = mock_config_entry.runtime_data.hijri_coordinator
    flash_message_coordinator = mock_config_entry.runtime_data.flash_message_coordinator

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
        "hijri_coordinator": {
            "last_update_success": True,
            "last_update_success_time": hijri_coordinator.last_update_success_time,
            "last_exception": None,
        },
        "hijri_settings": {"hijriAdjustment": 0, "hijriDateForceTo30": False},
        "flash_message_coordinator": {
            "last_update_success": True,
            "last_update_success_time": (
                flash_message_coordinator.last_update_success_time
            ),
            "last_exception": None,
        },
        "flash_message": None,
    }


async def test_diagnostics_with_flash_message(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test the diagnostics show the flash message without its text."""
    await setup_mawaqit_integration(
        flash_message=flash_message_response(end_date="2026-02-20")
    )

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diagnostics["flash_message"] == {
        "content": "**REDACTED**",
        "uuid": "**REDACTED**",
        "expire": None,
        "startDate": None,
        "endDate": "2026-02-20",
        "color": "#d9ad0f",
        "orientation": "ltr",
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
    coordinator.client.mosques.prayer_times.side_effect = status_error(
        InternalServerError, 503
    )
    await coordinator.async_refresh()

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diagnostics["coordinator"] == {
        "last_update_success": False,
        "last_update_success_time": last_success_time,
        "last_exception": "Error communicating with MAWAQIT: MAWAQIT error. (HTTP 503)",
    }
    assert diagnostics["prayer_times"]["calendar"] == build_prayer_data()["calendar"]


async def test_diagnostics_without_hijri_settings(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test the diagnostics when the Hijri settings could not be fetched."""
    await setup_mawaqit_integration(hijri_side_effect=CONNECTION_ERROR)

    diagnostics = await async_get_config_entry_diagnostics(hass, mock_config_entry)

    assert diagnostics["hijri_coordinator"] == {
        "last_update_success": False,
        "last_update_success_time": None,
        "last_exception": (
            "Network error while connecting to MAWAQIT: Could not reach MAWAQIT."
        ),
    }
    assert diagnostics["hijri_settings"] is None
