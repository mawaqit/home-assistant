"""The mawaqit_prayer_times component."""
from datetime import timedelta
import logging
import os
import json
import sys
from mawaqit_times_calculator import MawaqitTimesCalculator
from requests.exceptions import ConnectionError as ConnError
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_point_in_time
import homeassistant.util.dt as dt_util

from .const import (
    CONF_CALC_METHOD,
    DATA_UPDATED,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    USERNAME,
    PASSWORD,
)

from .mosq_list import (
    CALC_METHODS,
)

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_PASSWORD, CONF_USERNAME, CONF_API_KEY, CONF_TOKEN


_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

CONFIG_SCHEMA = vol.Schema(
    vol.All(
        cv.deprecated(DOMAIN),
        {
            DOMAIN: {
                vol.Optional(CONF_CALC_METHOD, default=DEFAULT_CALC_METHOD): vol.In(
                    CALC_METHODS
                ),
            }
        },
    ),
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
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


class MawaqitPrayerClient:
    """Mawaqit Prayer Client Object."""

    def __init__(self, hass, config_entry):
        """Initialize the Mawaqit Prayer client."""
        self.hass = hass
        self.config_entry = config_entry
        self.prayer_times_info = {}
        self.available = True
        self.event_unsub = None



    @property
    def calc_method(self):
        """Return the calculation method."""
        return self.config_entry.options[CONF_CALC_METHOD]

    def get_new_prayer_times(self):
        """Fetch prayer times for today."""
        mawaqit_login = self.config_entry.data.get("username")
        mawaqit_password = self.config_entry.data.get("password")
        mawaqit_latitude = self.config_entry.data.get("latitude") # self.hass.config.latitude
        mawaqit_longitude = self.config_entry.data.get("longitude") #self.hass.config.longitude

        mosquee = self.config_entry.options.get("calculation_method")

 
        calc = MawaqitTimesCalculator(
            mawaqit_latitude,
            mawaqit_longitude,
            '',
            mawaqit_login,
            mawaqit_password,
            ''
        )

        


        current_dir = os.path.dirname(os.path.realpath(__file__))
        if not os.path.exists('{}/data'.format(current_dir)):
          os.makedirs('{}/data'.format(current_dir))




        text_file = open('{}/data/all_mosquee.txt'.format(current_dir), "w")
        json.dump(calc.all_mosques_neighberhood(), text_file)
        text_file.close()

       

        name_servers=[]
        uuid_servers=[]
        CALC_METHODS=[]
        with open('{}/data/all_mosquee.txt'.format(current_dir), "r") as f:
          distros_dict = json.load(f)
        for distro in distros_dict:
          name_servers.extend([distro["label"]])
          uuid_servers.extend([distro["uuid"]])
          CALC_METHODS.extend([distro["label"]])

        no_mawaqit_mosque = False
        if len(uuid_servers)==0:
            #text_file = open('{}/data/test5.py'.format(current_dir), "w")
            #n = text_file.write("pas de mosque")
            #text_file.close()
            uuid_servers=["no mosque in neighborhood"]
            CALC_METHODS=["no mosque in neighborhood"]
            name_servers=["no mosque in neighborhood"]
            no_mawaqit_mosque = True
            


        text_file = open('{}/mosq_list.py'.format(current_dir), "w")
        n = text_file.write("CALC_METHODS = " + str(CALC_METHODS))
        text_file.close() 
 
        #text_file = open('{}/mosq_list_uuid.py'.format(current_dir), "w")
        #n = text_file.write("uuid = " + str(uuid_servers))
        #text_file.close() 
        if mosquee=="nearest" or mosquee=="no mosque in neighborhood" :
            indice = 0
        else:
            indice = name_servers.index(mosquee)
        mosque_id = uuid_servers[indice]
        #text_file = open('{}/data/indice.txt'.format(current_dir), "w")
        #n = text_file.write(str(mosque_id))
        #text_file.close()

        if no_mawaqit_mosque == False:
            text_file = open('{}/data/my_mosquee.txt'.format(current_dir), "w")
            json.dump(calc.all_mosques_neighberhood()[indice], text_file)
            text_file.close()
            calc = MawaqitTimesCalculator(
            self.hass.config.latitude,
            self.hass.config.longitude,
            mosque_id,
            mawaqit_login,
            mawaqit_password, '',
            )
            text_file = open('{}/data/pray_time.txt'.format(current_dir), "w")
            n = text_file.write(str(calc.fetch_prayer_times()))
            text_file.close() 
            return calc.fetch_prayer_times()            
        else:
            data = {"uuid": "neighborhood", "label": "no mawaqit mosque in neighborhood", "name": "no mawaqit mosque in neighborhood", "id": 000, "slug": "no-mosque" }
            text_file = open('{}/data/my_mosquee.txt'.format(current_dir), "w")
            json.dump(data, text_file)
            text_file.close()
            data1 = {'Fajr': '00:00', 'Sunrise': '00:00', 'Dhuhr': '00:00', 'Asr': '00:00', 'Sunset': '00:00', 'Maghrib': '00:00', 'Isha': '00:00', 'Imsak': '00:00', 'Midnight': '00:00', 'Jumua': '00:00', 'Shuruq': '00:00'}
            return data1


    



    async def async_schedule_future_update(self):
        """Schedule future update for sensors.

        Midnight is a calculated time.  The specifics of the calculation
        depends on the method of the prayer time calculation.  This calculated
        midnight is the time at which the time to pray the Isha prayers have
        expired.

        Calculated Midnight: The Mawaqit midnight.
        Traditional Midnight: 12:00AM

        Update logic for prayer times:

        If the Calculated Midnight is before the traditional midnight then wait
        until the traditional midnight to run the update.  This way the day
        will have changed over and we don't need to do any fancy calculations.

        If the Calculated Midnight is after the traditional midnight, then wait
        until after the calculated Midnight.  We don't want to update the prayer
        times too early or else the timings might be incorrect.

        Example:
        calculated midnight = 11:23PM (before traditional midnight)
        Update time: 12:00AM

        calculated midnight = 1:35AM (after traditional midnight)
        update time: 1:36AM.

        """
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
            _LOGGER.debug("Error retrieving prayer times")
            async_call_later(self.hass, 60, self.async_update)
            return

        for prayer, time in prayer_times.items():
            self.prayer_times_info[prayer] = dt_util.parse_datetime(
                f"{dt_util.now().date()} {time}"
            )
        await self.async_schedule_future_update()

        _LOGGER.debug("New prayer times retrieved. Updating sensors")
        async_dispatcher_send(self.hass, DATA_UPDATED)

    async def async_setup(self):
        """Set up the Mawaqit prayer client."""
        await self.async_add_options()

        try:
            await self.hass.async_add_executor_job(self.get_new_prayer_times)
        except (exceptions.InvalidResponseError, ConnError) as err:
            raise ConfigEntryNotReady from err

        await self.async_update()
        self.config_entry.add_update_listener(self.async_options_updated)

        self.hass.config_entries.async_setup_platforms(self.config_entry, PLATFORMS)

        return True

    async def async_add_options(self):
        """Add options for entry."""
        if not self.config_entry.options:
            data = dict(self.config_entry.data)
            calc_method = data.pop(CONF_CALC_METHOD, DEFAULT_CALC_METHOD)

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=data, options={CONF_CALC_METHOD: calc_method}
            )

    @staticmethod
    async def async_options_updated(hass, entry):
        """Triggered by config entry options updates."""
        if hass.data[DOMAIN].event_unsub:
            hass.data[DOMAIN].event_unsub()
        await hass.data[DOMAIN].async_update()
