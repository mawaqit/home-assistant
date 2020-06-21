"""The Mawaqit_prayer_times component."""
import os
from datetime import timedelta
import logging

from custom_components.mawaqit.mawaqit import PrayerTimesCalculator


from requests.exceptions import ConnectionError as ConnError
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_point_in_time
import homeassistant.util.dt as dt_util
from homeassistant.helpers import config_validation as cv
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_API_KEY, CONF_TOKEN


    
from .const import (
    DATA_UPDATED,
    DOMAIN,
    API_KEY,
    DEFAULT_API_KEY,
)

_LOGGER = logging.getLogger(__name__)

my_api = CONF_API_KEY




CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: {
            vol.Optional(API_KEY, default=DEFAULT_API_KEY): cv.string,
        }
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Import the Mawaqit Prayer component from config."""
    if DOMAIN in config:
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN, context={"source": SOURCE_IMPORT}, data=config[DOMAIN]
            )
        )

    return True


async def async_setup_entry(hass, config_entry):
    """Set up the Mawaqit Prayer Component."""
    client = MawaqitPrayerClient(hass, config_entry)

    if not await client.async_setup():
        return False

    hass.data.setdefault(DOMAIN, client)
    return True


async def async_unload_entry(hass, config_entry):
    """Unload Mawaqit Prayer entry from config_entry."""
    if hass.data[DOMAIN].event_unsub:
        hass.data[DOMAIN].event_unsub()
    hass.data.pop(DOMAIN)
    await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")

    return True



class MawaqitPrayerClient:
    """Mawaqit Prayer Client Object."""

    def __init__(self, hass, config_entry):
        """Initialize the Mawaqit Prayer client."""
        self.hass = hass
        self.config_entry = config_entry
        self.prayer_times_info = {}
        self.available = True
        self.event_unsub = None
        
        

    
    

    def get_new_prayer_times(self):
        """Fetch prayer times for today."""
        calc = PrayerTimesCalculator(
            latitude=self.hass.config.latitude,
            longitude=self.hass.config.longitude,
            api_key=my_api,
            date=str(dt_util.now().date()),
        )
        return calc.fetch_prayer_times()

    async def async_schedule_future_update(self):

        _LOGGER.debug("Scheduling next update for Mawaqit prayer times")

        now = dt_util.utcnow()

        midnight_dt = self.prayer_times_info["Midnight"]

        if now > dt_util.as_utc(midnight_dt):
            next_update_at = midnight_dt + timedelta(days=1, minutes=1)
            _LOGGER.debug(
                "Midnight is after day the changes so schedule update for after Midnight the next day"
            )
        else:
            _LOGGER.debug(
                "Midnight is before the day changes so schedule update for the next start of day"
            )
            next_update_at = dt_util.start_of_local_day(now + timedelta(days=1))

        _LOGGER.info("Next update scheduled for: %s", next_update_at)

        self.event_unsub = async_track_point_in_time(
            self.hass, self.async_update, next_update_at
        )

    async def async_update(self, *_):
        """Update sensors with new prayer times."""
        try:
            prayer_times = await self.hass.async_add_executor_job(
                self.get_new_prayer_times
            )
            self.available = True
        except (exceptions.InvalidResponseError, ConnError):
            self.available = False
            _LOGGER.debug("Error retrieving prayer times.")
            async_call_later(self.hass, 60, self.async_update)
            return

        for prayer, time in prayer_times.items():
            self.prayer_times_info[prayer] = dt_util.parse_datetime(
                f"{dt_util.now().date()} {time}"
            )
        await self.async_schedule_future_update()

        _LOGGER.debug("New prayer times retrieved. Updating sensors.")
        async_dispatcher_send(self.hass, DATA_UPDATED)

    async def async_setup(self):
        """Set up the Mawaqit prayer client."""
        """await self.async_add_options()"""

        try:
            await self.hass.async_add_executor_job(self.get_new_prayer_times)
        except (exceptions.InvalidResponseError, ConnError):
            raise ConfigEntryNotReady

        await self.async_update()
        """self.config_entry.add_update_listener(self.async_options_updated)"""

        self.hass.async_create_task(
            self.hass.config_entries.async_forward_entry_setup(
                self.config_entry, "sensor"
            )
        )

        return True
