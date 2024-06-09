"""The mawaqit_prayer_times component."""

from datetime import datetime, timedelta
import json
import logging
import os

# import sys
import shutil

from dateutil import parser as date_parser
from mawaqit.consts import BadCredentialsException
from requests.exceptions import ConnectionError as ConnError
import voluptuous as vol

from homeassistant.config_entries import SOURCE_IMPORT
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import (
    async_call_later,
    async_track_point_in_time,
    async_track_time_change,
)
import homeassistant.util.dt as dt_util

# from homeassistant.helpers import aiohttp_client
from .const import (
    CONF_CALC_METHOD,
    DATA_UPDATED,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    UPDATE_TIME,
)

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
file_path = f"{CURRENT_DIR}/data/mosq_list_data"

try:
    with open(file_path, "r") as text_file:
        data = json.load(text_file)

    # Accessing the CALC_METHODS object
    CALC_METHODS = data["CALC_METHODS"]
except FileNotFoundError:
    # First Run
    print(f"The file {file_path} was not found.")
    CALC_METHODS = []

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

    if hass.data[DOMAIN].event_unsub:
        hass.data[DOMAIN].event_unsub()
    hass.data.pop(DOMAIN)

    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)


async def async_remove_entry(hass, config_entry):
    """Remove Mawaqit Prayer entry from config_entry."""

    current_dir = os.path.dirname(os.path.realpath(__file__))
    dir_path = "{}/data".format(current_dir)
    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        print("Error: %s : %s" % (dir_path, e.strerror))

    dir_path = "{}/__pycache__".format(current_dir)
    try:
        shutil.rmtree(dir_path)
    except OSError as e:
        print("Error: %s : %s" % (dir_path, e.strerror))


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

        name_servers = []
        uuid_servers = []
        CALC_METHODS = []

        # We get the prayer times of the year from pray_time.txt
        f = open("{dir}/data/pray_time.txt".format(dir=current_dir), "r")

        data = json.load(f)
        calendar = data["calendar"]

        # Then, we get the prayer times of the day into this file
        today = datetime.today()
        index_month = today.month - 1
        month_times = calendar[index_month]  # Calendar of the month

        index_day = today.day
        day_times = month_times[str(index_day)]  # Today's times

        try:
            day_times_tomorrow = month_times[str(index_day + 1)]
        except KeyError:
            # If index_day + 1 == 32 (or 31) and the month contains only 31 (or 30) days
            # We take the first day of the following month (reset 0 if we're in december)
            if index_month == 11:
                index_next_month = 0
            else:
                index_next_month = index_month + 1
            day_times_tomorrow = calendar[index_next_month]["1"]

        now = today.time().strftime("%H:%M")

        today = datetime.today().strftime("%Y-%m-%d")
        tomorrow = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        prayer_names = ["Fajr", "Shurouq", "Dhuhr", "Asr", "Maghrib", "Isha"]
        prayers = []
        res = {}

        for i in range(len(prayer_names)):
            if datetime.strptime(day_times[i], "%H:%M") < datetime.strptime(
                now, "%H:%M"
            ):
                res[prayer_names[i]] = day_times_tomorrow[i]
                pray = tomorrow + " " + day_times_tomorrow[i] + ":00"
            else:
                res[prayer_names[i]] = day_times[i]
                pray = today + " " + day_times[i] + ":00"

            # # We never take in account shurouq in the calculation of next_salat
            if prayer_names[i] == "Shurouq":
                pray = tomorrow + " " + "23:59:59"

            prayers.append(pray)

        # Then the next prayer is the nearest prayer time, so the min of the prayers list
        next_prayer = min(prayers)
        res["Next Salat Time"] = next_prayer.split(" ", 1)[1].rsplit(":", 1)[0]
        res["Next Salat Name"] = prayer_names[prayers.index(next_prayer)]

        countdown_next_prayer = 15
        # 15 minutes Before Next Prayer
        res["Next Salat Preparation"] = (
            (
                datetime.strptime(next_prayer, "%Y-%m-%d %H:%M:%S")
                - timedelta(minutes=countdown_next_prayer)
            )
            .strftime("%Y-%m-%d %H:%M:%S")
            .split(" ", 1)[1]
            .rsplit(":", 1)[0]
        )

        # if Jumu'a is set as Dhuhr, then Jumu'a time is the same as Friday's Dhuhr time
        if data["jumuaAsDuhr"]:
            # Then, Jumu'a time should be the Dhuhr time of the next Friday
            today = datetime.today()
            # We get the next Friday
            next_friday = today + timedelta((4 - today.weekday() + 7) % 7)
            # We get the next Friday's Dhuhr time from the calendar
            next_friday_dhuhr = calendar[next_friday.month - 1][str(next_friday.day)][2]
            res["Jumua"] = next_friday_dhuhr

        # If jumu'a is set as a specific time, then we use that time
        elif data["jumua"] is not None:
            res["Jumua"] = data["jumua"]

        # if mosque has only one jumu'a, then 'Jumua 2' can be None.
        if data["jumua2"] is not None:
            res["Jumua 2"] = data["jumua2"]

        res["Mosque_label"] = data["label"]
        res["Mosque_localisation"] = data["localisation"]
        res["Mosque_url"] = data["url"]
        res["Mosque_image"] = data["image"]

        # We store the prayer times of the day in HH:MM format.
        prayers = [datetime.strptime(prayer, "%H:%M") for prayer in day_times]
        del prayers[1]  # Because there's no iqama for shurouq.

        # The Iqama countdown from Adhan is stored in pray_time.txt as well.
        iqamaCalendar = data["iqamaCalendar"]
        iqamas = iqamaCalendar[index_month][str(index_day)]  # Today's iqama times.

        # We store the iqama times of the day in HH:MM format.
        iqama_times = []

        for prayer, iqama in zip(prayers, iqamas):
            # The iqama can be either stored as a minutes countdown starting by a '+', or as a fixed time (HH:MM).
            if "+" in iqama:
                iqama = int(iqama.replace("+", ""))
                iqama_times.append(
                    (prayer + timedelta(minutes=iqama)).strftime("%H:%M")
                )
            elif ":" in iqama:
                iqama_times.append(iqama)
            else:
                # if there's a bug, we just append the prayer time for now.
                iqama.append(prayer)

        iqama_names = [
            "Fajr Iqama",
            "Dhuhr Iqama",
            "Asr Iqama",
            "Maghrib Iqama",
            "Isha Iqama",
        ]

        res1 = {iqama_names[i]: iqama_times[i] for i in range(len(iqama_names))}

        res2 = {**res, **res1}

        return res2

    async def async_update_next_salat_sensor(self, *_):
        salat_before_update = self.prayer_times_info["Next Salat Name"]
        prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]

        if salat_before_update != "Isha":  # We just retrieve the next salat of the day.
            index = prayers.index(salat_before_update) + 1
            self.prayer_times_info["Next Salat Name"] = prayers[index]
            self.prayer_times_info["Next Salat Time"] = self.prayer_times_info[
                prayers[index]
            ]

        else:  # We retrieve the next Fajr (more calcualtions).
            current_dir = os.path.dirname(os.path.realpath(__file__))
            f = open("{dir}/data/pray_time.txt".format(dir=current_dir), "r")
            data = json.load(f)
            calendar = data["calendar"]

            today = datetime.today()
            index_month = today.month - 1
            month_times = calendar[index_month]

            maghrib_hour = self.prayer_times_info["Maghrib"]
            maghrib_hour = maghrib_hour.strftime("%H:%M")

            # isha + 1 minute because this function is launched 1 minute after 'Isha, (useful only if 'Isha is at 11:59 PM)
            isha_hour = self.prayer_times_info["Isha"] + timedelta(minutes=1)
            isha_hour = isha_hour.strftime("%H:%M")

            # If 'Isha is before 12 AM (Maghrib hour < 'Isha hour), we need to get the next day's Fajr.
            # Else, we get the current day's Fajr.
            if maghrib_hour < isha_hour:
                index_day = today.day + 1
            else:
                index_day = today.day

            try:
                day_times = month_times[str(index_day)]
            except KeyError:
                # If index_day + 1 == 32 (or 31) and the month contains only 31 (or 30) days
                # We take the first day of the following month (reset 0 if we're in december)
                if index_month == 11:
                    index_next_month = 0
                else:
                    index_next_month = index_month + 1
                day_times = calendar[index_next_month]["1"]
            fajr_hour = day_times[0]

            self.prayer_times_info["Next Salat Name"] = "Fajr"
            self.prayer_times_info["Next Salat Time"] = dt_util.parse_datetime(
                f"{today.year}-{today.month}-{index_day} {fajr_hour}:00"
            )

        countdown_next_prayer = 15
        self.prayer_times_info["Next Salat Preparation"] = self.prayer_times_info[
            "Next Salat Time"
        ] - timedelta(minutes=countdown_next_prayer)

        _LOGGER.debug("Next salat info updated, updating sensors")
        async_dispatcher_send(self.hass, DATA_UPDATED)

    async def async_update(self, *_):
        # TODO : Reload pray_time.txt so we avoid bugs if prayer_times changes (for example if the mosque decides to change the iqama delay of a prayer)
        # get ID from my_mosque.txt, then create AsyncMawaqitClient and generate the dict with the prayer times.

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
                if datetime.strptime(time, "%H:%M") < datetime.strptime(now, "%H:%M"):
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

        # We schedule updates for next_salat_time and next_salat_name at each prayer time + 1 minute.
        prayers = ["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"]
        prayer_times = [self.prayer_times_info[prayer] for prayer in prayers]

        # We cancel the previous scheduled updates (if there is any) to avoid multiple updates for the same prayer.
        try:
            for cancel_event in self.cancel_events_next_salat:
                cancel_event()
        except AttributeError:
            pass

        self.cancel_events_next_salat = []

        for prayer in prayer_times:
            next_update_at = prayer + timedelta(minutes=1)
            cancel_event = async_track_point_in_time(
                self.hass, self.async_update_next_salat_sensor, next_update_at
            )
            self.cancel_events_next_salat.append(cancel_event)

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

        # We update time prayers every day.
        h, m, s = UPDATE_TIME
        async_track_time_change(
            self.hass, self.async_update, hour=h, minute=m, second=s
        )

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
