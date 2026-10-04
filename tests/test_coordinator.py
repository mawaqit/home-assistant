"""Tests for the Mawaqit coordinators."""

from datetime import timedelta
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from mawaqit import AuthenticationError, InternalServerError, PermissionDeniedError
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from .conftest import (
    CONNECTION_ERROR,
    MOCK_UUID,
    TIMEOUT_ERROR,
    build_prayer_data,
    status_error,
)

# All shared data and setup are provided by conftest:
#   - mock_prayer_data                    ->  standard data dict
#   - setup_mawaqit_integration           ->  async callable, see conftest docstring


FAJR = "sensor.test_mosque_fajr_prayer"
CALENDAR = "calendar.test_mosque_prayer_times"

# --- PrayerTimeCoordinator ---


async def test_prayer_time_coordinator_update_interval_is_12_hours(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    mock_prayer_data: dict,
) -> None:
    """Test prayer time coordinator polls twice daily (12 hours)."""
    await setup_mawaqit_integration(prayer_data=mock_prayer_data)
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    assert coordinator.update_interval == timedelta(hours=12)


async def test_prayer_time_coordinator_unload_cancels_day_change(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the middle of the night update does not run after the entry is unloaded."""
    freezer.move_to("2025-04-10 20:30:00+02:00")
    await setup_mawaqit_integration()
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    with patch.object(coordinator, "async_update_listeners") as update_listeners:
        freezer.move_to("2025-04-11 00:45:00+02:00")
        async_fire_time_changed(hass)
        await hass.async_block_till_done()

    update_listeners.assert_not_called()


async def test_prayer_time_coordinator_success(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    mock_prayer_data: dict,
) -> None:
    """Test successful prayer time fetch."""
    await setup_mawaqit_integration(prayer_data=mock_prayer_data)
    assert mock_config_entry.state is ConfigEntryState.LOADED
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    assert coordinator.data == mock_prayer_data


@pytest.mark.parametrize(
    "prayer_side_effect",
    [
        CONNECTION_ERROR,
        TIMEOUT_ERROR,
        status_error(InternalServerError, 503),
        status_error(PermissionDeniedError, 403),
    ],
    ids=["connection", "timeout", "server", "quota"],
)
async def test_prayer_time_coordinator_errors_cause_setup_retry(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    prayer_side_effect: Exception,
) -> None:
    """Test prayer time coordinator non-auth errors all cause setup retry."""
    await setup_mawaqit_integration(prayer_side_effect=prayer_side_effect)
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_prayer_time_coordinator_auth_error_starts_reauth(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test a rejected token fails the setup and starts a reauth flow."""
    await setup_mawaqit_integration(
        prayer_side_effect=status_error(AuthenticationError, 401)
    )
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_REAUTH
    assert flows[0]["context"]["entry_id"] == mock_config_entry.entry_id


@pytest.mark.parametrize(
    "prayer_side_effect",
    [
        CONNECTION_ERROR,
        TIMEOUT_ERROR,
        status_error(InternalServerError, 503),
        status_error(PermissionDeniedError, 403),
    ],
    ids=["connection", "timeout", "server", "quota"],
)
async def test_prayer_time_coordinator_failure_keeps_entities_available(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
    prayer_side_effect: Exception,
) -> None:
    """Test a failed refresh keeps the last times and retries every 15 minutes."""
    freezer.move_to("2025-04-10 12:00:00+02:00")
    await setup_mawaqit_integration()
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    fetch_prayer_times = coordinator.client.mosques.prayer_times
    fetch_prayer_times.side_effect = prayer_side_effect

    freezer.tick(timedelta(hours=12))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert fetch_prayer_times.call_count == 2
    assert not coordinator.last_update_success
    assert coordinator.update_interval == timedelta(minutes=15)
    assert hass.states.get(FAJR).state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
    assert hass.states.get(CALENDAR).state != STATE_UNAVAILABLE

    fetch_prayer_times.side_effect = None
    freezer.tick(timedelta(minutes=15))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert fetch_prayer_times.call_count == 3
    assert coordinator.last_update_success
    assert coordinator.update_interval == timedelta(hours=12)


async def test_prayer_time_coordinator_failure_keeps_changing_days(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the sensors move to the next days with the last times while MAWAQIT is down."""
    prayer_data = build_prayer_data()
    prayer_data["calendar"][3]["11"][0] = "05:28"
    prayer_data["calendar"][3]["12"][0] = "05:26"
    freezer.move_to("2025-04-10 11:00:00+02:00")
    await setup_mawaqit_integration(prayer_data=prayer_data)
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    fetch_prayer_times = coordinator.client.mosques.prayer_times
    fetch_prayer_times.side_effect = CONNECTION_ERROR

    async def move_to(time: str) -> str:
        freezer.move_to(time)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        return hass.states.get(FAJR).state

    assert await move_to("2025-04-10 23:00:00+02:00") == "2025-04-10T03:30:00+00:00"
    assert not coordinator.last_update_success
    assert await move_to("2025-04-11 00:30:00+02:00") == "2025-04-11T03:28:00+00:00"
    await move_to("2025-04-11 06:00:00+02:00")
    assert await move_to("2025-04-12 00:30:00+02:00") == "2025-04-12T03:26:00+00:00"
    assert not coordinator.last_update_success
    assert fetch_prayer_times.call_count > 2


async def test_prayer_time_coordinator_config_failure(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test a failure to fetch the screen settings fails the refresh."""
    await setup_mawaqit_integration()
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    coordinator.client.mosques.config.assert_awaited_once_with(MOCK_UUID)
    coordinator.client.mosques.config.side_effect = CONNECTION_ERROR

    await coordinator.async_refresh()

    assert not coordinator.last_update_success
    assert coordinator.update_interval == timedelta(minutes=15)
    assert hass.states.get(FAJR).state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)


async def test_prayer_time_coordinator_auth_error_after_setup(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test a token rejected after setup starts a reauth flow and keeps the times."""
    await setup_mawaqit_integration()
    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    coordinator.client.mosques.prayer_times.side_effect = status_error(
        AuthenticationError, 401
    )

    await coordinator.async_refresh()
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    assert flows[0]["context"]["source"] == SOURCE_REAUTH
    assert coordinator.update_interval == timedelta(hours=12)
    assert hass.states.get(FAJR).state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)
