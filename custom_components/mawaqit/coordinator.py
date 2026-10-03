"""Coordinators for the Mawaqit integration."""

from datetime import datetime, timedelta
import logging
from typing import override

from mawaqit import AsyncMawaqitClient
from mawaqit.exceptions import BadCredentialsException, MawaqitException

from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.event import async_track_point_in_utc_time
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from . import utils
from .const import DOMAIN
from .types import MawaqitConfigEntry

_LOGGER = logging.getLogger(__name__)


class PrayerTimeCoordinator(DataUpdateCoordinator[dict]):
    """Coordinator to fetch prayer times from the Mawaqit API.

    The API is called twice a day to fetch the full prayer calendar. Listeners
    are also updated at Islamic midnight, when prayer times move to the next day.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: MawaqitConfigEntry,
        client: AsyncMawaqitClient,
    ) -> None:
        """Initialize the prayer time coordinator."""
        self.client = client
        self._unsub_day_change: CALLBACK_TYPE | None = None

        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name="Prayer Times",
            update_method=self._async_update_data,
            update_interval=timedelta(hours=12),
        )

    @callback
    @override
    def async_update_listeners(self) -> None:
        """Update listeners, then schedule their next update at Islamic midnight."""
        super().async_update_listeners()
        self._cancel_day_change()
        if self.data and (next_day := utils.get_next_islamic_midnight(self.data)):
            self._unsub_day_change = async_track_point_in_utc_time(
                self.hass, self._async_day_changed, next_day
            )

    @callback
    def _async_day_changed(self, _now: datetime) -> None:
        """Refresh the sensors with the times of the new day."""
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
        """Fetch prayer times from API and notify sensors."""
        prayer_times: dict | None
        try:
            prayer_times = await self.client.fetch_prayer_times()
        except BadCredentialsException as err:
            raise ConfigEntryAuthFailed(
                translation_domain=DOMAIN,
                translation_key="auth_failed",
            ) from err
        except MawaqitException as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="mawaqit_error",
                translation_placeholders={"error": str(err)},
            ) from err
        except (ConnectionError, TimeoutError) as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="network_error",
                translation_placeholders={"error": str(err)},
            ) from err

        if not prayer_times:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="no_prayer_times_data",
            )

        if calendar := prayer_times.get("calendar"):
            prayer_times["calendar"] = utils.drop_imsak_column(calendar)

        # return fresh data when fetched
        return prayer_times
