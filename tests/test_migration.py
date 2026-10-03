"""Tests for the migration of entries created by the legacy custom integration."""

from typing import Any
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mawaqit.const import DOMAIN
from custom_components.mawaqit.migration import LEGACY_STORAGE_KEY
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_FRIENDLY_NAME,
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_UUID,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .conftest import (
    MOCK_LATITUDE,
    MOCK_LONGITUDE,
    MOCK_TOKEN,
    MOCK_UUID,
    build_prayer_data,
)


def _legacy_entry(data: dict[str, Any] | None = None) -> MockConfigEntry:
    """Return a config entry as saved by the legacy integration."""
    return MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=1,
        title="MAWAQIT - Test Mosque",
        data=data
        or {
            CONF_API_KEY: MOCK_TOKEN,
            CONF_UUID: MOCK_UUID,
            CONF_LATITUDE: MOCK_LATITUDE,
            CONF_LONGITUDE: MOCK_LONGITUDE,
        },
        options={"calculation_method": "Test Mosque"},
    )


async def _setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    with patch("custom_components.mawaqit.AsyncMawaqitClient") as mock_client_class:
        mock_client_class.return_value.fetch_prayer_times = AsyncMock(
            return_value=build_prayer_data()
        )
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()


async def test_migrate_legacy_entities(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test legacy entities keep their entity_id, get the new unique_id and the device."""
    entry = _legacy_entry()
    entry.add_to_hass(hass)
    for unique_id, object_id in (
        ("Fajr", "fajr_adhan"),
        ("Jumua 2", "jumua_2_adhan"),
        ("Isha Iqama", "isha_iqama"),
        ("Next Salat Name", "next_salat_name"),
        ("Next Salat Preparation", "next_salat_preparation"),
    ):
        entity_registry.async_get_or_create(
            "sensor",
            DOMAIN,
            unique_id,
            config_entry=entry,
            suggested_object_id=object_id,
        )

    await _setup(hass, entry)

    assert entry.state is ConfigEntryState.LOADED
    assert entry.minor_version == 2
    assert entry.options == {}
    [device] = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    for object_id, suffix in (
        ("fajr_adhan", "fajr"),
        ("jumua_2_adhan", "jumua 2"),
        ("isha_iqama", "isha_iqama"),
        ("next_salat_name", "next_prayer_next_salat_name"),
    ):
        entity = entity_registry.async_get(f"sensor.{object_id}")
        assert entity is not None
        assert entity.unique_id == f"{MOCK_UUID}_{suffix}"
        assert entity.device_id == device.id
        assert hass.states.get(f"sensor.{object_id}") is not None
    assert entity_registry.async_get("sensor.next_salat_preparation") is None
    state = hass.states.get("sensor.fajr_adhan")
    assert state is not None
    assert state.attributes[ATTR_FRIENDLY_NAME] == "Test Mosque Fajr Prayer"


async def test_migrate_drops_duplicate_legacy_entity(
    hass: HomeAssistant, entity_registry: er.EntityRegistry
) -> None:
    """Test a legacy entity is removed when its new unique_id is already taken."""
    entry = _legacy_entry()
    entry.add_to_hass(hass)
    entity_registry.async_get_or_create(
        "sensor", DOMAIN, "Fajr", config_entry=entry, suggested_object_id="fajr_adhan"
    )
    entity_registry.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{MOCK_UUID}_fajr",
        config_entry=entry,
        suggested_object_id="fajr_prayer",
    )

    await _setup(hass, entry)

    assert entity_registry.async_get("sensor.fajr_adhan") is None
    assert entity_registry.async_get("sensor.fajr_prayer") is not None


async def test_migrate_legacy_storage(
    hass: HomeAssistant, hass_storage: dict[str, Any]
) -> None:
    """Test the mosque and token are taken from the legacy store, then dropped."""
    hass_storage[LEGACY_STORAGE_KEY] = {
        "version": 1,
        "key": LEGACY_STORAGE_KEY,
        "data": {
            "my_mosque_NN": {"uuid": MOCK_UUID, "name": "Test Mosque"},
            "MAWAQIT_API_KEY": "legacy-token",
        },
    }
    # Early releases saved the mosque name instead of its uuid.
    entry = _legacy_entry({CONF_API_KEY: MOCK_TOKEN, CONF_UUID: "Test Mosque"})

    await _setup(hass, entry)

    assert entry.state is ConfigEntryState.LOADED
    assert entry.data[CONF_UUID] == MOCK_UUID
    assert entry.data[CONF_API_KEY] == "legacy-token"
    assert LEGACY_STORAGE_KEY not in hass_storage


async def test_no_migration_for_current_entries(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Test entries created by this version are not migrated again."""
    mock_config_entry = MockConfigEntry(
        domain=DOMAIN,
        version=1,
        minor_version=2,
        data=dict(mock_config_entry.data),
    )

    with patch("custom_components.mawaqit.async_migrate_legacy_entry") as mock_migrate:
        await _setup(hass, mock_config_entry)

    mock_migrate.assert_not_called()
    assert mock_config_entry.state is ConfigEntryState.LOADED
