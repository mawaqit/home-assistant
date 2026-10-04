"""Tests for several mosques set up side by side."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from mawaqit import AuthenticationError

from custom_components.mawaqit.const import DOMAIN
from custom_components.mawaqit.diagnostics import async_get_config_entry_diagnostics
from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from .conftest import (
    MOCK_TOKEN,
    MOCK_UUID,
    build_prayer_data,
    config_response,
    hijri_settings_response,
    make_config_entry,
    make_month_data,
    prayer_times_response,
    status_error,
)

OTHER_UUID = "bbbbb-cccccc-ddddd-0000"
OTHER_TOKEN = "other-api-token"
OTHER_TIMES = ["05:00", "06:15", "12:15", "15:30", "18:15", "19:45"]


def _other_prayer_data(name: str = "Other Mosque") -> dict[str, Any]:
    """Return the prayer data of a second mosque, with other times."""
    return build_prayer_data() | {
        "uuid": OTHER_UUID,
        "name": name,
        "url": "https://mawaqit.net/en/other-mosque",
        "calendar": [make_month_data(OTHER_TIMES) for _ in range(12)],
    }


def _client(prayer_data: dict | None = None, side_effect: Any = None) -> MagicMock:
    """Return a client returning the prayer data of one mosque."""
    client = MagicMock()
    client.mosques.prayer_times = AsyncMock(
        return_value=prayer_data and prayer_times_response(prayer_data),
        side_effect=side_effect,
    )
    client.mosques.config = AsyncMock(return_value=config_response())
    client.mosques.hijri_settings = AsyncMock(return_value=hijri_settings_response())
    return client


async def _set_up(hass: HomeAssistant, clients: dict[str, MagicMock]) -> MagicMock:
    """Set up the entries added to hass, each mosque answered by its client."""

    async def prayer_times(uuid: str) -> Any:
        return await clients[uuid].mosques.prayer_times(uuid)

    with patch("custom_components.mawaqit.AsyncMawaqitClient") as mock_client_class:
        mock_client_class.return_value.mosques.prayer_times = AsyncMock(
            side_effect=prayer_times
        )
        mock_client_class.return_value.mosques.config = AsyncMock(
            return_value=config_response()
        )
        mock_client_class.return_value.mosques.hijri_settings = AsyncMock(
            return_value=hijri_settings_response()
        )
        assert await async_setup_component(hass, DOMAIN, {})
        await hass.async_block_till_done()
    return mock_client_class


def _entity_ids(entity_registry: er.EntityRegistry, entry_id: str) -> set[str]:
    """Return the entity IDs of an entry."""
    return {
        entity.entity_id
        for entity in er.async_entries_for_config_entry(entity_registry, entry_id)
    }


async def test_two_mosques_side_by_side(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test each mosque has its own client, device, entities and data."""
    entry = make_config_entry()
    other = make_config_entry(OTHER_UUID, "Other Mosque", OTHER_TOKEN)
    entry.add_to_hass(hass)
    other.add_to_hass(hass)

    mock_client_class = await _set_up(
        hass,
        {
            MOCK_UUID: _client(build_prayer_data()),
            OTHER_UUID: _client(_other_prayer_data()),
        },
    )

    assert entry.state is ConfigEntryState.LOADED
    assert other.state is ConfigEntryState.LOADED
    assert sorted(
        call.kwargs["token"] for call in mock_client_class.call_args_list
    ) == sorted([MOCK_TOKEN, OTHER_TOKEN])
    coordinator = entry.runtime_data.prayer_time_coordinator
    other_coordinator = other.runtime_data.prayer_time_coordinator
    assert coordinator is not other_coordinator
    assert (coordinator.mosque_uuid, other_coordinator.mosque_uuid) == (
        MOCK_UUID,
        OTHER_UUID,
    )
    assert coordinator.data["name"] == "Test Mosque"
    assert other_coordinator.data["name"] == "Other Mosque"

    [device] = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    [other_device] = dr.async_entries_for_config_entry(device_registry, other.entry_id)
    assert device.identifiers == {(DOMAIN, MOCK_UUID)}
    assert device.name == "Test Mosque"
    assert other_device.identifiers == {(DOMAIN, OTHER_UUID)}
    assert other_device.name == "Other Mosque"

    entity_ids = _entity_ids(entity_registry, entry.entry_id)
    other_entity_ids = _entity_ids(entity_registry, other.entry_id)
    assert len(entity_ids) == 22
    assert {
        entity_id.replace(".other_mosque_", ".test_mosque_")
        for entity_id in other_entity_ids
    } == entity_ids
    for entry_id, mosque_uuid, device_id in (
        (entry.entry_id, MOCK_UUID, device.id),
        (other.entry_id, OTHER_UUID, other_device.id),
    ):
        for entity in er.async_entries_for_config_entry(entity_registry, entry_id):
            assert entity.unique_id.startswith(f"{mosque_uuid}_")
            assert entity.device_id == device_id

    for entity_id in entity_ids | other_entity_ids:
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state != STATE_UNAVAILABLE
    fajr = hass.states.get("sensor.test_mosque_fajr_prayer")
    other_fajr = hass.states.get("sensor.other_mosque_fajr_prayer")
    assert fajr is not None and other_fajr is not None
    assert fajr.state != other_fajr.state

    diagnostics = await async_get_config_entry_diagnostics(hass, other)
    assert diagnostics["prayer_times"]["calendar"] == _other_prayer_data()["calendar"]


async def test_mosques_with_the_same_name(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test two mosques with the same name get distinct entity IDs."""
    entry = make_config_entry()
    other = make_config_entry(OTHER_UUID, "Test Mosque")
    entry.add_to_hass(hass)
    other.add_to_hass(hass)

    await _set_up(
        hass,
        {
            MOCK_UUID: _client(build_prayer_data()),
            OTHER_UUID: _client(_other_prayer_data(name="Test Mosque")),
        },
    )

    entity_ids = _entity_ids(entity_registry, entry.entry_id)
    other_entity_ids = _entity_ids(entity_registry, other.entry_id)
    assert len(entity_ids) == len(other_entity_ids) == 22
    assert not entity_ids & other_entity_ids
    assert {f"{entity_id}_2" for entity_id in entity_ids} == other_entity_ids
    for entity_id in entity_ids | other_entity_ids:
        assert hass.states.get(entity_id) is not None


async def test_unload_and_remove_one_mosque(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test unloading or deleting a mosque leaves the other one working."""
    entry = make_config_entry()
    other = make_config_entry(OTHER_UUID, "Other Mosque")
    entry.add_to_hass(hass)
    other.add_to_hass(hass)
    await _set_up(
        hass,
        {
            MOCK_UUID: _client(build_prayer_data()),
            OTHER_UUID: _client(_other_prayer_data()),
        },
    )
    other_entity_ids = _entity_ids(entity_registry, other.entry_id)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.NOT_LOADED
    assert other.state is ConfigEntryState.LOADED
    fajr = hass.states.get("sensor.test_mosque_fajr_prayer")
    assert fajr is not None and fajr.state == STATE_UNAVAILABLE
    for entity_id in other_entity_ids:
        state = hass.states.get(entity_id)
        assert state is not None and state.state != STATE_UNAVAILABLE

    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.config_entries.async_entries(DOMAIN) == [other]
    assert not _entity_ids(entity_registry, entry.entry_id)
    assert not dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    assert _entity_ids(entity_registry, other.entry_id) == other_entity_ids
    [other_device] = dr.async_entries_for_config_entry(device_registry, other.entry_id)
    assert other_device.identifiers == {(DOMAIN, OTHER_UUID)}
    assert other.state is ConfigEntryState.LOADED


async def test_one_mosque_with_a_rejected_login(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test a rejected login asks to log in again for that mosque only."""
    entry = make_config_entry()
    other = make_config_entry(OTHER_UUID, "Other Mosque", OTHER_TOKEN)
    entry.add_to_hass(hass)
    other.add_to_hass(hass)

    await _set_up(
        hass,
        {
            MOCK_UUID: _client(side_effect=status_error(AuthenticationError, 401)),
            OTHER_UUID: _client(_other_prayer_data()),
        },
    )

    assert entry.state is ConfigEntryState.SETUP_ERROR
    assert other.state is ConfigEntryState.LOADED
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [
        (flow["context"]["source"], flow["context"]["entry_id"]) for flow in flows
    ] == [(SOURCE_REAUTH, entry.entry_id)]
    for entity_id in _entity_ids(entity_registry, other.entry_id):
        state = hass.states.get(entity_id)
        assert state is not None and state.state != STATE_UNAVAILABLE


async def test_refresh_of_one_mosque(hass: HomeAssistant) -> None:
    """Test refreshing a mosque updates its sensors only."""
    entry = make_config_entry()
    other = make_config_entry(OTHER_UUID, "Other Mosque")
    entry.add_to_hass(hass)
    other.add_to_hass(hass)
    client = _client(build_prayer_data())
    other_client = _client(_other_prayer_data())
    await _set_up(hass, {MOCK_UUID: client, OTHER_UUID: other_client})
    other_fajr = hass.states.get("sensor.other_mosque_fajr_prayer")
    assert other_fajr is not None
    fajr = hass.states.get("sensor.test_mosque_fajr_prayer")
    assert fajr is not None and fajr.state != other_fajr.state

    client.mosques.prayer_times.return_value = prayer_times_response(
        _other_prayer_data(name="Test Mosque")
    )
    await entry.runtime_data.prayer_time_coordinator.async_refresh()
    await hass.async_block_till_done()

    fajr = hass.states.get("sensor.test_mosque_fajr_prayer")
    assert fajr is not None and fajr.state == other_fajr.state
    assert other_client.mosques.prayer_times.await_count == 1
    assert hass.states.get("sensor.other_mosque_fajr_prayer") == other_fajr
