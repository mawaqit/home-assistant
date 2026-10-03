"""Diagnostics support for the Mawaqit integration."""

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import (
    CONF_API_KEY,
    CONF_EMAIL,
    CONF_ID,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_URL,
    CONF_UUID,
)
from homeassistant.core import HomeAssistant

from .types import MawaqitConfigEntry

# Everything identifying the mosque is redacted too, as it locates the user.
# The entry title is left out: it holds the mosque name and the distance from home.
TO_REDACT = {
    CONF_API_KEY,
    CONF_EMAIL,
    CONF_ID,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_URL,
    CONF_UUID,
    "announcements",
    "association",
    "events",
    "exteriorPicture",
    "flash",
    "image",
    "interiorPicture",
    "label",
    "localisation",
    "logo",
    "otherInfo",
    "paymentWebsite",
    "phone",
    "site",
    "streamUrl",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: MawaqitConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = config_entry.runtime_data.prayer_time_coordinator

    return async_redact_data(
        {
            "entry": {
                "version": config_entry.version,
                "minor_version": config_entry.minor_version,
                "data": config_entry.data,
            },
            "coordinator": {
                "last_update_success": coordinator.last_update_success,
                "last_update_success_time": coordinator.last_update_success_time,
                # Kept after a later successful update.
                "last_exception": str(coordinator.last_exception)
                if coordinator.last_exception
                else None,
            },
            "prayer_times": coordinator.data,
        },
        TO_REDACT,
    )
