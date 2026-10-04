"""Coordinators for the Mawaqit integration."""

from abc import abstractmethod
from datetime import datetime, time, timedelta, tzinfo
import logging
from typing import override

from mawaqit import (
    APIConnectionError,
    AsyncMawaqitClient,
    AuthenticationError,
    MawaqitError,
    hijri,
)
from mawaqit.hijri import HijriDate
from mawaqit.types import HijriSettings

from homeassistant.const import CONF_UUID
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator,
    UpdateFailed,
)
import homeassistant.util.dt as dt_util

from . import utils
from .const import DOMAIN, IMSAK_CALENDAR
from .types import MawaqitConfigEntry

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(hours=12)
HIJRI_UPDATE_INTERVAL = timedelta(hours=1)
RETRY_INTERVAL = timedelta(minutes=15)


class MawaqitCoordinator[_DataT](TimestampDataUpdateCoordinator[_DataT]):
    """Base coordinator of a mosque.

    It fetches its data again every 15 minutes after a failure, until it
    succeeds. Its listeners are also updated when the data changes over time,
    without a refresh, at the time returned by `_next_change`.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: MawaqitConfigEntry,
        client: AsyncMawaqitClient,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.mosque_uuid: str = config_entry.data[CONF_UUID]
        self._success_interval = update_interval
        self._unsub_change: CALLBACK_TYPE | None = None

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=name,
            update_interval=update_interval,
        )

    @abstractmethod
    async def _async_fetch(self) -> _DataT:
        """Fetch the data from MAWAQIT."""

    @abstractmethod
    def _next_change(self) -> datetime | None:
        """Return when the data changes without a refresh, if it does."""

    @callback
    @override
    def async_update_listeners(self) -> None:
        """Update listeners, then schedule their next update."""
        super().async_update_listeners()
        self._cancel_change()
        if self.data is None:
            return
        if next_change := self._next_change():
            self._unsub_change = async_track_point_in_utc_time(
                self.hass, self._async_changed, next_change
            )

    @callback
    def _async_changed(self, _now: datetime) -> None:
        """Update the listeners when the data changes over time."""
        self._unsub_change = None
        self.async_update_listeners()

    def _cancel_change(self) -> None:
        """Cancel the pending update of the listeners."""
        if self._unsub_change:
            self._unsub_change()
            self._unsub_change = None

    @override
    async def async_shutdown(self) -> None:
        """Cancel the pending update of the listeners and any scheduled refresh."""
        self._cancel_change()
        await super().async_shutdown()

    @override
    async def _async_update_data(self) -> _DataT:
        """Fetch the data, and retry sooner after a failure."""
        try:
            data = await self._async_fetch()
        except AuthenticationError as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from err
        except MawaqitError as err:
            self.update_interval = RETRY_INTERVAL
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="network_error"
                if isinstance(err, APIConnectionError)
                else "mawaqit_error",
                translation_placeholders={"error": str(err)},
            ) from err
        self.update_interval = self._success_interval
        return data


class PrayerTimeCoordinator(MawaqitCoordinator[dict]):
    """Coordinator of the prayer times of a mosque.

    It fetches the prayer times of the whole year twice a day. Listeners are
    also updated at the middle of the night, when prayer times move to the
    next day, and at Fajr, when night times move to the next night.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: MawaqitConfigEntry,
        client: AsyncMawaqitClient,
    ) -> None:
        """Initialize the prayer time coordinator."""
        super().__init__(hass, config_entry, client, "Prayer Times", UPDATE_INTERVAL)

    @override
    def _next_change(self) -> datetime | None:
        """Return the next middle of the night or Fajr ending the night."""
        changes = (
            utils.get_next_middle_of_the_night(self.data),
            utils.get_night_end(self.data),
        )
        return min((change for change in changes if change), default=None)

    @override
    async def _async_fetch(self) -> dict:
        """Fetch the prayer times and the screen settings of the mosque."""
        response = await self.client.mosques.prayer_times(self.mosque_uuid)
        config = await self.client.mosques.config(self.mosque_uuid)

        # The API JSON, which the sensors and the calendar read.
        prayer_times = response.model_dump(
            mode="json", by_alias=True, exclude_unset=True
        )
        if calendar := prayer_times.get("calendar"):
            if invalid_days := utils.find_invalid_times(calendar):
                _LOGGER.warning(
                    "Invalid prayer times from MAWAQIT, ignored on: %s",
                    ", ".join(invalid_days),
                )
            if config.displaying_sabah_imsak:
                prayer_times[IMSAK_CALENDAR], prayer_times["calendar"] = (
                    utils.split_imsak_column(calendar)
                )

        return prayer_times


class HijriCoordinator(MawaqitCoordinator[HijriSettings]):
    """Coordinator of the Hijri date of a mosque.

    It fetches the Hijri settings every hour, since mosques change them after
    the moon sighting. Listeners are also updated at midnight in the time zone
    of the mosque, when the date changes.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: MawaqitConfigEntry,
        client: AsyncMawaqitClient,
        prayer_time_coordinator: PrayerTimeCoordinator,
    ) -> None:
        """Initialize the Hijri date coordinator."""
        self._prayer_time_coordinator = prayer_time_coordinator
        super().__init__(
            hass, config_entry, client, "Hijri Date", HIJRI_UPDATE_INTERVAL
        )

    def _time_zone(self) -> tzinfo:
        """Return the time zone of the mosque, or Home Assistant's if unknown."""
        timezone = (self._prayer_time_coordinator.data or {}).get("timezone")
        return (
            timezone and dt_util.get_time_zone(timezone)
        ) or dt_util.get_default_time_zone()

    def today(self) -> HijriDate:
        """Return today's Hijri date of the mosque."""
        return hijri.today(self.data, self._time_zone())

    @override
    def _next_change(self) -> datetime:
        """Return the next midnight in the time zone of the mosque."""
        tz = self._time_zone()
        tomorrow = dt_util.now(tz).date() + timedelta(days=1)
        return datetime.combine(tomorrow, time(), tz)

    @override
    async def _async_fetch(self) -> HijriSettings:
        """Fetch the Hijri settings of the mosque."""
        return await self.client.mosques.hijri_settings(self.mosque_uuid)
