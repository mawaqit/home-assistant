"""Tests for the Mawaqit base entity and its mosque device."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mawaqit.const import DOMAIN, MAWAQIT_URL
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from .conftest import MOCK_MOSQUE_URL, MOCK_UUID, build_prayer_data


def _mosque_device(
    device_registry: dr.DeviceRegistry, entry: MockConfigEntry
) -> dr.DeviceEntry:
    """Return the only device of the entry."""
    devices = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    assert len(devices) == 1
    return devices[0]


async def test_entities_belong_to_the_mosque_device(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test every entity belongs to a service device named after the mosque."""
    await setup_mawaqit_integration()

    device = _mosque_device(device_registry, mock_config_entry)
    assert device.identifiers == {(DOMAIN, MOCK_UUID)}
    assert device.name == "Test Mosque"
    assert device.manufacturer == "MAWAQIT"
    assert device.entry_type is dr.DeviceEntryType.SERVICE
    assert device.configuration_url == MOCK_MOSQUE_URL

    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert {entity.domain for entity in entities} == {"calendar", "sensor"}
    assert {entity.device_id for entity in entities} == {device.id}


async def test_mosque_device_without_url(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test the device links to the MAWAQIT home page when the mosque has no page."""
    prayer_data = build_prayer_data()
    del prayer_data["url"]
    await setup_mawaqit_integration(prayer_data=prayer_data)

    device = _mosque_device(device_registry, mock_config_entry)
    assert device.configuration_url == MAWAQIT_URL


async def test_mosque_device_url_uses_https(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    device_registry: dr.DeviceRegistry,
) -> None:
    """Test the http:// link returned by the API is turned into https://."""
    prayer_data = build_prayer_data()
    prayer_data["url"] = MOCK_MOSQUE_URL.replace("https://", "http://")
    await setup_mawaqit_integration(prayer_data=prayer_data)

    device = _mosque_device(device_registry, mock_config_entry)
    assert device.configuration_url == MOCK_MOSQUE_URL


async def test_new_install_entity_ids(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    entity_registry: er.EntityRegistry,
) -> None:
    """Test new installs name the entities after the mosque, as in the README."""
    await setup_mawaqit_integration()

    entities = er.async_entries_for_config_entry(
        entity_registry, mock_config_entry.entry_id
    )
    assert sorted(entity.entity_id for entity in entities) == [
        "calendar.test_mosque_prayer_times",
        "sensor.test_mosque_asr_iqama",
        "sensor.test_mosque_asr_prayer",
        "sensor.test_mosque_dhuhr_iqama",
        "sensor.test_mosque_dhuhr_prayer",
        "sensor.test_mosque_end_of_the_first_third",
        "sensor.test_mosque_fajr_iqama",
        "sensor.test_mosque_fajr_prayer",
        "sensor.test_mosque_flash_message",
        "sensor.test_mosque_hijri_day",
        "sensor.test_mosque_hijri_month",
        "sensor.test_mosque_hijri_year",
        "sensor.test_mosque_isha_iqama",
        "sensor.test_mosque_isha_prayer",
        "sensor.test_mosque_jumua_prayer",
        "sensor.test_mosque_maghrib_iqama",
        "sensor.test_mosque_maghrib_prayer",
        "sensor.test_mosque_middle_of_the_night",
        "sensor.test_mosque_next_salat_name",
        "sensor.test_mosque_next_salat_time",
        "sensor.test_mosque_second_jumua_prayer",
        "sensor.test_mosque_shuruq",
        "sensor.test_mosque_start_of_the_last_third",
    ]
    state = hass.states.get("sensor.test_mosque_fajr_prayer")
    assert state is not None
    assert state.attributes[ATTR_FRIENDLY_NAME] == "Test Mosque Fajr Prayer"
