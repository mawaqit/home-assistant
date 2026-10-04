"""Coordinators for the Mawaqit integration."""

from datetime import datetime, timedelta
import logging
from typing import override

from mawaqit import (
    APIConnectionError,
    AsyncMawaqitClient,
    AuthenticationError,
    MawaqitError,
)

from homeassistant.const import CONF_UUID
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator,
    UpdateFailed,
)

from . import utils
from .const import DOMAIN
from .types import MawaqitConfigEntry

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=12)
RETRY_INTERVAL = timedelta(minutes=15)


class PrayerTimeCoordinator(TimestampDataUpdateCoordinator[dict]):
    """Coordinator to fetch prayer times from the Mawaqit API.

    The API is called twice a day to fetch the full prayer calendar, and every
    15 minutes after a failure until it succeeds again. Listeners are also
    updated at the middle of the night, when prayer times move to the next day,
    and at Fajr, when night times move to the next night.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: MawaqitConfigEntry,
        client: AsyncMawaqitClient,
    ) -> None:
        """Initialize the prayer time coordinator."""
        self.client = client
        self.mosque_uuid: str = config_entry.data[CONF_UUID]
        self._unsub_day_change: CALLBACK_TYPE | None = None

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="Prayer Times",
            update_method=self._async_update_data,
            update_interval=UPDATE_INTERVAL,
        )

    @callback
    @override
    def async_update_listeners(self) -> None:
        """Update listeners, then schedule their next update."""
        super().async_update_listeners()
        self._cancel_day_change()
        if not self.data:
            return
        changes = (
            utils.get_next_middle_of_the_night(self.data),
            utils.get_night_end(self.data),
        )
        if next_change := min((change for change in changes if change), default=None):
            self._unsub_day_change = async_track_point_in_utc_time(
                self.hass, self._async_day_changed, next_change
            )

    @callback
    def _async_day_changed(self, _now: datetime) -> None:
        """Refresh the sensors with the times of the new day or night."""
        self._unsub_day_change = None
        self.async_update_listeners()

    def _cancel_day_change(self) -> None:
        """Cancel the pending day change update."""
        if self._unsub_day_change:
            self._unsub_day_change()
            self._unsub_day_change = None

    @override
    async def async_shutdown(self) -> None:
        """Cancel the day change update and any scheduled refresh."""
        self._cancel_day_change()
        await super().async_shutdown()

    @override
    async def _async_update_data(self) -> dict:
        """Fetch prayer times, and retry sooner after a failure."""
        try:
            prayer_times = await self._async_fetch_prayer_times()
        except UpdateFailed:
            self.update_interval = RETRY_INTERVAL
            raise
        self.update_interval = UPDATE_INTERVAL
        return prayer_times

    async def _async_fetch_prayer_times(self) -> dict:
        """Fetch prayer times from the API."""
        try:
            response = await self.client.mosques.prayer_times(self.mosque_uuid)
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from err
        except APIConnectionError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="network_error",
                translation_placeholders={"error": str(err)},
            ) from err
        except MawaqitError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="mawaqit_error",
                translation_placeholders={"error": str(err)},
            ) from err

        # The API JSON, which the sensors and the calendar read.
        prayer_times = response.model_dump(
            mode="json", by_alias=True, exclude_unset=True
        )
        if calendar := prayer_times.get("calendar"):
            prayer_times["calendar"] = utils.drop_imsak_column(calendar)
            if invalid_days := utils.find_invalid_times(prayer_times["calendar"]):
                _LOGGER.warning(
                    "Invalid prayer times from MAWAQIT, ignored on: %s",
                    ", ".join(invalid_days),
                )

        # return fresh data when fetched
        return prayer_times
