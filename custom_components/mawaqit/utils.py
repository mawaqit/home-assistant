"""Utility functions for the Mawaqit integration."""

from datetime import date, datetime, time, timedelta
import logging
import re

from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_UUID
import homeassistant.util.dt as dt_util

from .const import NIGHT_TIMES, PRAYER_NAMES, PRAYER_NAMES_IQAMA

_LOGGER = logging.getLogger(__name__)

_TIME_ABSOLUTE_RE = re.compile(r"^\d{2}:\d{2}$")  # Matches HH:MM format


def save_mosque(
    mosque_display_name: str,
    mosque_id: str,
    mawaqit_token: str | None = None,
    lat: float | None = None,
    longi: float | None = None,
) -> tuple[str, dict]:
    """Create a data entry to simplify the process of saving mosque data.

    Args:
        mosque_display_name (str): The display name of the mosque.
        mosque_id (str): The unique ID of the mosque.
        mawaqit_token (str, optional): Token for Mawaqit API authentication.
        lat (float, optional): Latitude of the mosque.
        longi (float, optional): Longitude of the mosque.

    Returns:
        tuple[str, dict]: A tuple containing the title and data entry dictionary.

    """

    if mawaqit_token is None:
        _LOGGER.error("Token should not be None !")
        raise ValueError("Token should not be None !")

    title = "MAWAQIT" + " - " + mosque_display_name
    data_entry: dict[str, str | float] = {
        CONF_API_KEY: mawaqit_token,
        CONF_UUID: mosque_id,
    }
    if lat is not None and longi is not None:
        data_entry[CONF_LATITUDE] = lat
        data_entry[CONF_LONGITUDE] = longi

    return title, data_entry


def drop_imsak_column(
    calendar: list[dict[str, list[str]]],
) -> list[dict[str, list[str]]]:
    """Return the calendar without the Imsak column of some mosques.

    Mosques displaying Sabah and Imsak have 7 times a day: Imsak, Sabah, Shuruq,
    Dhuhr, Asr, Maghrib, Isha. Like the MAWAQIT app, Sabah is used as Fajr.
    """
    return [
        {
            day: times[1:] if len(times) == len(PRAYER_NAMES) + 1 else times
            for day, times in month.items()
        }
        for month in calendar
    ]


def extract_time_from_calendar(
    calendar: list[dict[str, list[str]]],
    prayer_name: str,
    target_date: date,
    mode_iqama: bool = False,
) -> str | None:
    """Extract the time of a specific prayer for a given date.

    :param calendar: List containing 12 dictionaries (one for each month).
    :param prayer_name: The name of the prayer to extract (e.g., "Fajr", "Dhuhr").
    :param target_date: The date for which to extract the prayer time (datetime.date object).
    :param mode_iqama: Whether to extract iqama times instead of prayer times.
    :return: The prayer time as a string , or None if missing.
    """

    prayer_name = prayer_name.lower()
    try:
        mode_prayer_name = PRAYER_NAMES_IQAMA if mode_iqama else PRAYER_NAMES

        # Validate prayer name
        if prayer_name.lower() not in mode_prayer_name:
            _LOGGER.error("Invalid prayer name: %s", prayer_name)
            return None

        # Extract month and day from the target_date
        target_month = target_date.month  # Extract month (1-12)
        target_day = str(target_date.day)  # Extract day as a string

        # Validate month data
        if target_month - 1 >= len(calendar):
            _LOGGER.error("Calendar data for month %s is missing", target_month)
            return None

        month_data = calendar[target_month - 1]  # Convert month to 0-based index

        # Get the prayer times for the given day
        target_prayer_times = month_data.get(target_day)

        if not target_prayer_times or len(target_prayer_times) != len(mode_prayer_name):
            _LOGGER.error(
                "Incomplete or missing prayer times for %s-%s", target_month, target_day
            )
            return None

        # Get the index of the requested prayer
        prayer_index = mode_prayer_name.index(prayer_name)

        return target_prayer_times[prayer_index]  # represents the prayer time

    except KeyError as e:
        _LOGGER.error(
            "Key error extracting prayer time for %s on %s: %s",
            prayer_name,
            target_date,
            e,
        )
        return None
    except ValueError as e:
        _LOGGER.error(
            "Value error extracting prayer time for %s on %s: %s",
            prayer_name,
            target_date,
            e,
        )
        return None
    except IndexError as e:
        _LOGGER.error(
            "Index error extracting prayer time for %s on %s: %s",
            prayer_name,
            target_date,
            e,
        )
        return None


def parse_time(time_str: str) -> time | None:
    """Return a HH:MM time, or None if it is invalid."""
    try:
        return datetime.strptime(time_str, "%H:%M").time()
    except (TypeError, ValueError):
        return None


def find_invalid_times(calendar: list[dict[str, list[str]]]) -> list[str]:
    """Return the days of a yearly calendar with invalid times, as month/day."""
    return [
        f"{month}/{day}"
        for month, days in enumerate(calendar, 1)
        for day, times in days.items()
        if any(parse_time(time_str) is None for time_str in times)
    ]


def time_with_timezone(
    timezone: str, target_date: str | date, time: str
) -> datetime | None:
    """Convert a naive datetime to a timezone-aware datetime.

    Args:
        timezone (str): The timezone string (e.g., "Europe/Paris").
        target_date (str | date): The date in "YYYY-MM-DD" format.
        time (str): The time string in "HH:MM" format.

    Returns:
        datetime: The timezone-aware datetime object, or None if the timezone or
            the time is invalid.

    """
    tz = dt_util.get_time_zone(timezone)
    if not tz:
        _LOGGER.error("Invalid timezone: %s", timezone)
        return None
    try:
        naive_time = datetime.strptime(f"{target_date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        return None
    return dt_util.as_local(naive_time.replace(tzinfo=tz))


def _to_utc(timezone: str, day: date, time_str: str | None) -> datetime | None:
    """Localize a HH:MM time string on a given date and return it in UTC."""
    if not time_str:
        return None
    localized = time_with_timezone(timezone, day, time_str)
    if localized:
        return localized.astimezone(dt_util.UTC)
    return None


def add_minutes_to_time(time_str: str, minutes_str: str) -> str | None:
    """Add minutes to a time string (HH:MM) based on a string input like "+xx".

    :param time_str: Time in "HH:MM" format (e.g., "06:49").
    :param minutes_str: String representing minutes to add (e.g., "+15").
    :return: New time as a string in "HH:MM" format.
    """
    if time_str is None or minutes_str is None:
        raise ValueError("Both time_str and minutes_str must be provided")
    # Parse the base time
    base_time = datetime.strptime(time_str, "%H:%M")

    # Extract minutes from the input string
    if not minutes_str.startswith("+") or not minutes_str[1:].isdigit():
        raise ValueError(f"Invalid minutes format, expected '+xx' got '{minutes_str}'")

    try:
        minutes_to_add = int(minutes_str[1:])  # Extract the integer part

        # Add minutes
        new_time = base_time + timedelta(minutes=minutes_to_add)

        # Format back to string
        return new_time.strftime("%H:%M")

    except (ValueError, TypeError) as e:
        _LOGGER.error("Error in add_minutes_to_time: %s", e)
        return None


def parse_iqama_time(prayer_time: str, iqama_value: str) -> str | None:
    """Return the iqama time as HH:MM.

    Handles two formats:
    - '+xx' : offset in minutes from the prayer time (e.g. '+5', '+15')
    - 'HH:MM': absolute time in mosque local timezone (e.g. '04:32')
    """
    if not iqama_value:
        return None

    if iqama_value.startswith("+"):
        # The coordinator already warns about invalid prayer times.
        if parse_time(prayer_time) is None:
            return None
        return add_minutes_to_time(prayer_time, iqama_value)

    # If it's not an offset, it should be an absolute time in HH:MM format
    if _TIME_ABSOLUTE_RE.match(iqama_value):
        return iqama_value

    _LOGGER.error("Unrecognised iqama format: %s", iqama_value)
    return None


def get_night(
    prayer_data: dict, night: date, timezone: str
) -> tuple[datetime, datetime] | None:
    """Return the night starting on a day: from its Maghrib to the next Fajr, in UTC."""
    calendar = prayer_data.get("calendar")
    if not calendar:
        return None

    next_day = night + timedelta(days=1)
    # In UTC: subtracting datetimes of the same time zone ignores DST changes.
    maghrib = _to_utc(
        timezone, night, extract_time_from_calendar(calendar, "maghrib", night)
    )
    fajr = _to_utc(
        timezone, next_day, extract_time_from_calendar(calendar, "fajr", next_day)
    )
    return (maghrib, fajr) if maghrib and fajr else None


def night_time(night: tuple[datetime, datetime], fraction: tuple[int, int]) -> datetime:
    """Return the time at a fraction of a night, e.g. (1, 2) for its middle."""
    maghrib, fajr = night
    numerator, denominator = fraction
    return maghrib + (fajr - maghrib) * numerator / denominator


def compute_middle_of_the_night(
    prayer_data: dict, night: date, timezone: str
) -> datetime | None:
    """Return the middle of the night from Maghrib of `night` to the next Fajr."""
    bounds = get_night(prayer_data, night, timezone)
    return night_time(bounds, NIGHT_TIMES["middle_of_the_night"]) if bounds else None


def _next_middle_of_the_night(
    prayer_data: dict, now: datetime, timezone: str
) -> tuple[date, datetime] | None:
    """Return the next middle of the night and the day its night starts on."""
    # It can be before or after 00:00, tomorrow's is always ahead.
    today = now.date()
    for night in (today - timedelta(days=1), today, today + timedelta(days=1)):
        middle = compute_middle_of_the_night(prayer_data, night, timezone)
        # Skipping an invalid night could move prayer times a day ahead.
        if middle is None or middle > now:
            break
    return (night, middle) if middle else None


def get_islamic_date(prayer_data: dict, timezone: str) -> date:
    """Return the day whose prayer times are shown, until the middle of its night."""
    tz = dt_util.get_time_zone(timezone)
    now = dt_util.now(tz) if tz else dt_util.now()

    if next_middle := _next_middle_of_the_night(prayer_data, now, timezone):
        return next_middle[0]

    # Debug: called by every sensor update, the cause is logged elsewhere.
    _LOGGER.debug(
        "Could not compute the middle of the night, falling back to civil date"
    )
    return now.date()


def get_next_middle_of_the_night(prayer_data: dict) -> datetime | None:
    """Return the next middle of the night, when prayer times move to the next day."""
    timezone = prayer_data.get("timezone")
    if not timezone or not (tz := dt_util.get_time_zone(timezone)):
        return None

    next_middle = _next_middle_of_the_night(prayer_data, dt_util.now(tz), timezone)
    return next_middle[1] if next_middle else None


def _current_night(prayer_data: dict) -> tuple[datetime, datetime] | None:
    """Return the night in progress, or the next one once Fajr has passed."""
    timezone = prayer_data.get("timezone")
    if not timezone or not (tz := dt_util.get_time_zone(timezone)):
        return None

    now = dt_util.now(tz)
    for night in (now.date() - timedelta(days=1), now.date()):
        # A night with invalid times is skipped.
        if (bounds := get_night(prayer_data, night, timezone)) and bounds[1] > now:
            return bounds
    return None


def get_night_time(prayer_data: dict, fraction: tuple[int, int]) -> datetime | None:
    """Return a time of the current night, kept until Fajr like the prayer times."""
    bounds = _current_night(prayer_data)
    return night_time(bounds, fraction) if bounds else None


def get_night_end(prayer_data: dict) -> datetime | None:
    """Return the Fajr ending the current night, when night times move on."""
    bounds = _current_night(prayer_data)
    return bounds[1] if bounds else None


def get_prayer_times_for_two_days(
    prayer_calendar: list[dict[str, list[str]]], today: datetime, timezone: str
) -> dict[str, dict[str, str | list[str]]]:
    """Extract prayer times for today and tomorrow from the provided calendar.

    Args:
        prayer_calendar (dict): The yearly prayer times calendar.
        today (datetime): The datetime object representing 'today', not timezone-aware.
        timezone (str): String representing the timezone, e.g., 'Europe/Paris'.

    Returns:
        dict: A dictionary containing prayer times for today and tomorrow.

    """
    tz = dt_util.get_time_zone(timezone)
    today = today.astimezone(tz)
    tomorrow = today + timedelta(days=1)

    # Extracting times for today and tomorrow
    today_times = prayer_calendar[today.month - 1].get(str(today.day), [])
    tomorrow_times = prayer_calendar[tomorrow.month - 1].get(str(tomorrow.day), [])

    return {
        "today": {"date": today.strftime("%Y-%m-%d"), "prayer_times": today_times},
        "tomorrow": {
            "date": tomorrow.strftime("%Y-%m-%d"),
            "prayer_times": tomorrow_times,
        },
    }


def find_next_prayer(
    current_time: datetime,
    prayer_calendar: list[dict[str, list[str]]],
    timezone: str,
) -> tuple[int | None, datetime | None]:
    """Find the next prayer name and its exact time based on the provided calendar.

    Args:
        current_time (datetime): The current time, expected to be timezone-aware.
        prayer_calendar (dict): The yearly prayer times calendar.
        timezone (str): String representing the timezone, e.g., 'Europe/Paris'.

    Returns:
        tuple: (Next prayer index, Next prayer datetime (timezone-aware))

    """

    # Ensure current time is timezone aware
    tz = dt_util.get_time_zone(timezone)
    if not tz:
        _LOGGER.error("Invalid timezone: %s", timezone)
        return None, None

    current_time = current_time.astimezone(tz)

    # Get prayer times for today and tomorrow
    prayer_times_two_days = get_prayer_times_for_two_days(
        prayer_calendar, current_time, timezone
    )
    today_prayer_times = prayer_times_two_days["today"]["prayer_times"]
    tomorrow_prayer_times = prayer_times_two_days["tomorrow"]["prayer_times"]

    # The first valid time after now, today or tomorrow
    tomorrow = current_time.date() + timedelta(days=1)
    for day, times in (
        (current_time.date(), today_prayer_times),
        (tomorrow, tomorrow_prayer_times),
    ):
        for index, time_str in enumerate(times):
            if (prayer_time := parse_time(time_str)) is None:
                continue
            prayer_datetime = datetime.combine(day, prayer_time, tz)
            if prayer_datetime > current_time:
                return index, prayer_datetime.astimezone(dt_util.UTC)

    return None, None


def get_regular_prayer_time(prayer_data: dict, prayer_name: str) -> datetime | None:
    """Get a prayer time from the calendar (Fajr, Shuruq, Dhuhr, Asr, Maghrib, Isha)."""
    calendar = prayer_data.get("calendar")
    timezone = prayer_data.get("timezone")

    if not calendar or not timezone:
        _LOGGER.warning("Missing calendar or timezone data for %s", prayer_name)
        return None

    day = get_islamic_date(prayer_data, timezone)
    prayer_time = extract_time_from_calendar(calendar, prayer_name, day)

    return _to_utc(timezone, day, prayer_time) if prayer_time else None


def get_jumua_time(prayer_data: dict, jumua_name: str) -> datetime | None:
    """Get the Jumua prayer time of the coming Friday, today included."""
    jumua_time = prayer_data.get(jumua_name)
    timezone = prayer_data.get("timezone")

    if not timezone:
        _LOGGER.warning("Missing timezone data")
        return None

    if not jumua_time:
        return None

    # Like the other prayers, today's Jumua is kept until the middle of the night.
    day = get_islamic_date(prayer_data, timezone)
    friday = day + timedelta(days=(4 - day.weekday()) % 7)
    return _to_utc(timezone, friday, jumua_time)


def get_iqama_time(prayer_data: dict, prayer_name: str) -> datetime | None:
    """Get Iqama prayer time."""
    calendar = prayer_data.get("calendar")
    iqama_calendar = prayer_data.get("iqamaCalendar")
    timezone = prayer_data.get("timezone")

    if not calendar or not iqama_calendar or not timezone:
        _LOGGER.warning("Missing calendar data for %s Iqama", prayer_name)
        return None

    day = get_islamic_date(prayer_data, timezone)

    # Get base prayer time
    prayer_time = extract_time_from_calendar(calendar, prayer_name, day)
    if not prayer_time:
        return None

    # Get iqama data and compute iqama time
    iqama_raw = extract_time_from_calendar(
        iqama_calendar, prayer_name, day, mode_iqama=True
    )
    if not iqama_raw:
        return None

    iqama_time = parse_iqama_time(prayer_time, iqama_raw)
    if not iqama_time:
        return None

    return _to_utc(timezone, day, iqama_time)
