"""Migration of config entries created by the legacy (v3 and older) custom integration."""

from functools import partial
import logging
from pathlib import Path
import shutil

from homeassistant.const import CONF_API_KEY, CONF_UUID
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.storage import Store

from .const import DOMAIN
from .types import MawaqitConfigEntry

_LOGGER = logging.getLogger(__name__)

LEGACY_STORAGE_KEY = "mawaqit_storage"
LEGACY_STORAGE_VERSION = 1
LEGACY_STORAGE_MOSQUE_KEY = "my_mosque_NN"
LEGACY_STORAGE_TOKEN_KEY = "MAWAQIT_API_KEY"
LEGACY_DATA_DIR = Path(__file__).parent / "data"

# Legacy unique_id (the sensor type) -> suffix of the new "<mosque uuid>_<suffix>" unique_id.
# Legacy sensors missing from this map no longer exist and are removed.
LEGACY_UNIQUE_ID_SUFFIXES = {
    "Fajr": "fajr",
    "Shurouq": "shuruq",
    "Dhuhr": "dhuhr",
    "Asr": "asr",
    "Maghrib": "maghrib",
    "Isha": "isha",
    "Jumua": "jumua",
    "Jumua 2": "jumua 2",
    "Fajr Iqama": "fajr_iqama",
    "Dhuhr Iqama": "dhuhr_iqama",
    "Asr Iqama": "asr_iqama",
    "Maghrib Iqama": "maghrib_iqama",
    "Isha Iqama": "isha_iqama",
    "Next Salat Name": "next_prayer_next_salat_name",
    "Next Salat Time": "next_prayer_next_salat_time",
}


async def async_migrate_legacy_entry(
    hass: HomeAssistant, entry: MawaqitConfigEntry
) -> None:
    """Fix legacy entry data, move entities to the new unique_ids, drop legacy storage."""
    store: Store[dict] = Store(hass, LEGACY_STORAGE_VERSION, LEGACY_STORAGE_KEY)
    legacy_data = await store.async_load() or {}

    # The legacy integration read the mosque and token from its store, and old
    # releases saved the mosque name (not its uuid) in the entry data.
    data = dict(entry.data)
    if mosque_uuid := (legacy_data.get(LEGACY_STORAGE_MOSQUE_KEY) or {}).get("uuid"):
        data[CONF_UUID] = mosque_uuid
    if token := legacy_data.get(LEGACY_STORAGE_TOKEN_KEY):
        data[CONF_API_KEY] = token
    hass.config_entries.async_update_entry(entry, data=data)

    mosque_uuid = data[CONF_UUID]
    ent_reg = er.async_get(hass)

    for entity in er.async_entries_for_config_entry(ent_reg, entry.entry_id):
        if entity.unique_id.startswith(f"{mosque_uuid}_"):
            continue
        suffix = LEGACY_UNIQUE_ID_SUFFIXES.get(entity.unique_id)
        new_unique_id = f"{mosque_uuid}_{suffix}" if suffix else None
        if new_unique_id is None or ent_reg.async_get_entity_id(
            entity.domain, DOMAIN, new_unique_id
        ):
            _LOGGER.debug("Removing legacy entity %s", entity.entity_id)
            ent_reg.async_remove(entity.entity_id)
            continue
        _LOGGER.debug("Migrating %s to unique_id %s", entity.entity_id, new_unique_id)
        ent_reg.async_update_entity(entity.entity_id, new_unique_id=new_unique_id)

    await store.async_remove()
    await hass.async_add_executor_job(
        partial(shutil.rmtree, LEGACY_DATA_DIR, ignore_errors=True)
    )
