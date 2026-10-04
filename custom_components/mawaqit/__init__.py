"""The mawaqit_prayer_times component."""

from mawaqit import AsyncMawaqitClient

from homeassistant.const import CONF_API_KEY, CONF_UUID, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.httpx_client import get_async_client

from .coordinator import PrayerTimeCoordinator
from .migration import async_migrate_legacy_entry, migrate_title
from .types import MawaqitConfigEntry, MawaqitData

PLATFORMS = [Platform.CALENDAR, Platform.SENSOR]


async def async_setup_entry(
    hass: HomeAssistant, config_entry: MawaqitConfigEntry
) -> bool:
    """Set up the Mawaqit Prayer Component."""
    client = AsyncMawaqitClient(
        token=config_entry.data[CONF_API_KEY], http_client=get_async_client(hass)
    )

    prayer_time_coordinator = PrayerTimeCoordinator(hass, config_entry, client)
    await prayer_time_coordinator.async_config_entry_first_refresh()

    config_entry.runtime_data = MawaqitData(
        prayer_time_coordinator=prayer_time_coordinator,
    )

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, config_entry: MawaqitConfigEntry
) -> bool:
    """Unload Mawaqit Prayer entry from config_entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_migrate_entry(
    hass: HomeAssistant, config_entry: MawaqitConfigEntry
) -> bool:
    """Migrate config entries created by older versions."""
    if config_entry.version == 1 and config_entry.minor_version < 2:
        await async_migrate_legacy_entry(hass, config_entry)
        hass.config_entries.async_update_entry(
            config_entry, options={}, minor_version=2
        )
    if config_entry.version == 1 and config_entry.minor_version < 3:
        # After the legacy migration, which can change the mosque.
        hass.config_entries.async_update_entry(
            config_entry,
            title=migrate_title(config_entry.title),
            unique_id=config_entry.data[CONF_UUID],
            minor_version=3,
        )
    return True
