"""The mawaqit_prayer_times component."""
import logging
import os
import json
# import sys
import shutil

from datetime import datetime, timedelta
from dateutil import parser as date_parser

from .mawaqit import BadCredentialsException #, MawaqitClient

from requests.exceptions import ConnectionError as ConnError

import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_call_later, async_track_point_in_time
import homeassistant.util.dt as dt_util
# from homeassistant.helpers import aiohttp_client


from .const import (
    API,
    CONF_CALC_METHOD,
    DATA_UPDATED,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    USERNAME,
    PASSWORD,
    CONF_UUID,
)

from .mosq_list import (
    CALC_METHODS,
)

# from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_PASSWORD, CONF_USERNAME, CONF_API_KEY, CONF_TOKEN

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


def is_date_parsing(date_str):
    try:
        return bool(date_parser.parse(date_str))
    except ValueError:
        return False


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

    hass.data.setdefault(DOMAIN, {})
    client = MawaqitPrayerClient(hass, config_entry)

    if not await client.async_setup():
        return False

    hass.data[DOMAIN] = client
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)
    return True


async def async_unload_entry(hass, config_entry):
    """Unload Mawaqit Prayer entry from config_entry."""
    current_dir = os.path.dirname(os.path.realpath(__file__))
    dir_path = '{}/data'.format(current_dir)
    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        print("Error: %s : %s" % (dir_path, e.strerror))
        
    dir_path = '{}/__pycache__'.format(current_dir)
    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        print("Error: %s : %s" % (dir_path, e.strerror))

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
        mawaqit_latitude = self.config_entry.data.get("latitude")
        mawaqit_longitude = self.config_entry.data.get("longitude")

        mosque = self.config_entry.options.get("calculation_method")

        current_dir = os.path.dirname(os.path.realpath(__file__))
        
        name_servers=[]
        uuid_servers=[]
        CALC_METHODS=[]

        with open('{}/data/all_mosquee_NN.txt'.format(current_dir), "r") as f:
          distros_dict = json.load(f)

        for distro in distros_dict:
          name_servers.extend([distro["label"]])
          uuid_servers.extend([distro["uuid"]])
          CALC_METHODS.extend([distro["label"]])

        if mosque == "nearest" or mosque == "no mosque in neighborhood":
            indice = 0
        else:
            indice = name_servers.index(mosque)

        mosque_id = uuid_servers[indice]
        
        # We get the prayer times of the year from pray_time.txt
        f = open('{dir}/data/pray_time.txt'.format(dir=current_dir, name=""))

        data = json.load(f)
        calendar = data["calendar"]
        
        # Then, we get the prayer times of the day into this file
        today = datetime.today()
        index_month = today.month - 1
        month_times = calendar[index_month] # Calendar of the month

        index_day = today.day
        day_times = month_times[str(index_day)] # Today's times
        
        prayer_names = ["Fajr", "Shurouq", "Dhuhr", "Asr", "Maghrib", "Isha" ]
        res = {prayer_names[i]: day_times[i] for i in range(len(prayer_names))}

        try:
            day_times_tomorrow = month_times[str(index_day + 1)]
        except KeyError:
            # If index_day + 1 == 32 (or 31) and the month contains only 31 (or 30) days
            # We take the first prayer of the following month
            day_times_tomorrow = calendar[index_month + 1]["1"]

        now = today.time().strftime("%H:%M")

        today = datetime.today().strftime("%Y-%m-%d")
        tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        prayers = []
        for j in range(len(prayer_names)):
            if prayer_names[j] == "Shurouq":
                pray = tomorrow + " " + "23:59:00" # We never take in account shurouq in the calculation of next_salat
            else:    
                if datetime.strptime(day_times[j], '%H:%M') < datetime.strptime(now, '%H:%M'):
                    pray = tomorrow + " " + day_times_tomorrow[j] + ":00"
                else:
                    pray = today + " " + day_times[j] + ":00"

            prayers.append(pray)
        
        # Then the next prayer is the nearest prayer time, so the min of the prayers list
        next_prayer = min(prayers)
        res['Next Salat Time'] = next_prayer.split(" ", 1)[1].rsplit(':', 1)[0]
        res['Next Salat Name'] = prayer_names[prayers.index(next_prayer)]

        minutes_bnp = 15
        # 15 minutes Before Next Prayer
        res['Next Salat Preparation'] = (datetime.strptime(next_prayer, '%Y-%m-%d %H:%M:%S')-timedelta(minutes=minutes_bnp)).strftime('%Y-%m-%d %H:%M:%S').split(" ", 1)[1].rsplit(':', 1)[0]
        
        # if Jumu'a is set as Dhuhr, then Jumu'a time is the same as Friday's Dhuhr time
        if data["jumuaAsDuhr"]:
            # Then, Jumu'a time should be the Dhuhr time of the next Friday
            today = datetime.today()
            # We get the next Friday
            next_friday = today + timedelta((4 - today.weekday() + 7) % 7)
            # We get the next Friday's Dhuhr time from the calendar
            next_friday_dhuhr = calendar[next_friday.month - 1][str(next_friday.day)][2]
            res['Jumua'] = next_friday_dhuhr

        # If jumu'a is set as a specific time, then we use that time
        elif data["jumua"] is not None:
            res['Jumua'] = data["jumua"]

        # if mosque has only one jumu'a, then 'Jumua 2' can be None.
        if data["jumua2"] is not None:
            res['Jumua 2'] = data["jumua2"]

        res['Mosque_label']=data["label"]
        res['Mosque_localisation']=data["localisation"]
        res['Mosque_url']=data["url"]
        res['Mosque_image']=data["image"]

        # The Iqama countdown from Adhan is stored in pray_time.txt as well.
        iqamaCalendar = data["iqamaCalendar"]
        iqamas = iqamaCalendar[index_month][str(index_day)] # Today's iqama times.
        try:
            # The iqama countdown is stored as a string with a + sign.
            # So, we need to remove the + and convert the countdown to an int.
            iqamas = [int(countdown.replace("+", "")) for countdown in iqamas]
        except ValueError:
            iqamas = [0, 0, 0, 0, 0]
            
        # We store the prayer times of the day in HH:MM format.
        prayers = [datetime.strptime(prayer, '%H:%M') for prayer in day_times]
        del prayers[1] # Because there's no iqama for shurouq.

        # We store the iqama times of the day in HH:MM format.
        iqama_times = []

        for (prayer, iqama) in zip(prayers, iqamas):
            iqama_times.append((prayer + timedelta(minutes=iqama)).strftime("%H:%M"))     

        iqama_names = ["Fajr Iqama", "Dhuhr Iqama", "Asr Iqama", "Maghrib Iqama", "Isha Iqama"]

        res1 = {iqama_names[i]: iqama_times[i] for i in range(len(iqama_names))}

        res2 = {**res, **res1}
        
        return res2


    async def async_schedule_future_update(self):
        """Schedule future update for sensors.

        Midnight is a calculated time.  The specifics of the calculation
        depends on the method of the prayer time calculation.  This calculated
        midnight is the time at which the time to pray the Isha prayers have
        expired.

        Calculated Midnight: The Mawaqit midnight.
        Traditional Midnight: Isha time + 1 minute

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
        now = dt_util.now()

        midnight_dt = self.prayer_times_info["Next Salat Time"]
        Fajr_dt = self.prayer_times_info["Fajr"]
        Dhuhr_dt = self.prayer_times_info["Dhuhr"]
        Asr_dt = self.prayer_times_info["Asr"]
        Maghrib_dt = self.prayer_times_info["Maghrib"]
        Isha_dt = self.prayer_times_info["Isha"]

        prayer_times = [Fajr_dt, Dhuhr_dt, Asr_dt, Maghrib_dt, Isha_dt]

        midnight_dt = min(prayer_times)

        if now > dt_util.as_utc(midnight_dt):
            next_update_at = midnight_dt + timedelta(days=0, minutes=1, seconds=0)
            _LOGGER.debug(
                "Midnight is after day the changes so schedule update for after Midnight the next day"
            )
        else:
            _LOGGER.debug(
                "Midnight is before the day changes so schedule update for the next start of day"
            )
            next_update_at = dt_util.start_of_local_day(now + timedelta(days=1))
            next_update_at = midnight_dt + timedelta(days=0, minutes=1)

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
        except (BadCredentialsException, ConnError):
            self.available = False
            _LOGGER.debug("Error retrieving prayer times")
            async_call_later(self.hass, 60, self.async_update)
            return

        for prayer, time in prayer_times.items():

            tomorrow = (dt_util.now().date() + timedelta(days=1)).strftime("%Y-%m-%d")
            today = dt_util.now().date().strftime("%Y-%m-%d")

            now = dt_util.now().time().strftime("%H:%M")

            if is_date_parsing(time):
              if datetime.strptime(time, '%H:%M') < datetime.strptime(now, '%H:%M'):
                  pray = tomorrow
              else:
                  pray = today

              if prayer == "Jumua" or prayer == "Jumua 2":
                  # We convert the date to datetime to be able to do calculations on it.
                  pray_date = datetime.strptime(pray, "%Y-%m-%d")
                  # The calculation below allows to add the number of days necessary to arrive at the next Friday.
                  pray_date += timedelta(days=(4 - pray_date.weekday() + 7) % 7)
                  # We convert the date to string to be able to put it in the dictionary.
                  pray = pray_date.strftime("%Y-%m-%d")
              self.prayer_times_info[prayer] = dt_util.parse_datetime(
                  f"{pray} {time}"
                  )
            else:
                self.prayer_times_info[prayer] = time
            
            
        await self.async_schedule_future_update()

        _LOGGER.debug("New prayer times retrieved. Updating sensors.")
        async_dispatcher_send(self.hass, DATA_UPDATED)

    async def async_setup(self):
        """Set up the Mawaqit prayer client."""

        await self.async_add_options()

        try:
            await self.hass.async_add_executor_job(self.get_new_prayer_times)
        except (BadCredentialsException, ConnError) as err:
            raise ConfigEntryNotReady from err

        await self.async_update()
        self.config_entry.add_update_listener(self.async_options_updated)

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
