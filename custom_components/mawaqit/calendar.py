"""Calendar of the mosque prayer times for the Mawaqit integration."""

from datetime import date, datetime, time, timedelta, tzinfo
import logging
from typing import override

from homeassistant.components.calendar import (
    CalendarEntity,
    CalendarEntityDescription,
    CalendarEvent,
)
from homeassistant.const import CONF_UUID
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
import homeassistant.util.dt as dt_util

from . import MawaqitConfigEntry, utils
from .const import NIGHT_TIMES, PRAYER_NAMES, PRAYER_NAMES_IQAMA
from .coordinator import PrayerTimeCoordinator
from .entity import MawaqitEntity

_LOGGER = logging.getLogger(__name__)

PARALLEL_UPDATES = 0

# Not translated: automations filter on them whatever the user's language.
PRAYER_SUMMARIES = {
    "fajr": "Fajr",
    "shuruq": "Shuruq",
    "dhuhr": "Dhuhr",
    "asr": "Asr",
    "maghrib": "Maghrib",
    "isha": "Isha",
}
JUMUA_SUMMARIES = {"jumua": "Jumua", "jumua2": "Jumua 2", "jumua3": "Jumua 3"}
NIGHT_SUMMARIES = {
    "first_third_end": "End of the first third",
    "middle_of_the_night": "Middle of the night",
    "last_third_start": "Start of the last third",
}

CALENDAR_DESCRIPTION = CalendarEntityDescription(
    key="prayer_times",
    translation_key="prayer_times",
)


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: MawaqitConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Mawaqit calendar platform."""
    async_add_entities(
        [
            MawaqitPrayerCalendar(
                config_entry.runtime_data.prayer_time_coordinator,
                CALENDAR_DESCRIPTION,
                config_entry.data[CONF_UUID],
            )
        ]
    )


def _at(day: date, time_str: str | None, tz: tzinfo) -> datetime | None:
    """Return the HH:MM time on the given day, or None if it is invalid."""
    if not time_str:
        return None
    try:
        return datetime.combine(day, datetime.strptime(time_str, "%H:%M").time(), tz)
    except ValueError:
        _LOGGER.debug("Invalid time %s on %s", time_str, day)
        return None


def _day_row(calendar: list[dict[str, list[str]]] | None, day: date) -> list[str]:
    """Return the times of a day in a yearly calendar, or [] if missing."""
    if not calendar or len(calendar) < day.month:
        return []
    return calendar[day.month - 1].get(str(day.day)) or []


def _day_events(prayer_data: dict, day: date, tz: tzinfo) -> list[CalendarEvent]:
    """Return the prayers of a day, each one lasting until its iqama if known.

    Also return the times of the night after it, which last no time.
    """
    times = _day_row(prayer_data["calendar"], day)
    if len(times) != len(PRAYER_NAMES):
        return []

    iqamas: list[str] = []
    if prayer_data.get("iqamaEnabled"):
        iqamas = _day_row(prayer_data.get("iqamaCalendar"), day)
    if len(iqamas) != len(PRAYER_NAMES_IQAMA):
        iqamas = []

    starts: list[tuple[str, str, str | None]] = [
        (name, PRAYER_SUMMARIES[name], time_str)
        for name, time_str in zip(PRAYER_NAMES, times, strict=True)
    ]
    if day.weekday() == 4:
        starts += [
            (key, summary, prayer_data.get(key))
            for key, summary in JUMUA_SUMMARIES.items()
        ]

    events = []
    for key, summary, time_str in starts:
        if not time_str or (start := _at(day, time_str, tz)) is None:
            continue
        end = start
        if iqamas and key in PRAYER_NAMES_IQAMA:
            try:
                iqama = utils.parse_iqama_time(
                    time_str, iqamas[PRAYER_NAMES_IQAMA.index(key)]
                )
            except ValueError:
                iqama = None
            if (iqama_dt := _at(day, iqama, tz)) is not None:
                if iqama_dt >= start:
                    end = iqama_dt
                elif key == "isha":  # An Isha iqama can be after midnight.
                    end = iqama_dt + timedelta(days=1)
        events.append(
            CalendarEvent(
                start=start, end=end, summary=summary, uid=f"{day.isoformat()}_{key}"
            )
        )

    # The night after the day, until the next Fajr.
    if night := utils.get_night(prayer_data, day, prayer_data["timezone"]):
        for key, fraction in NIGHT_TIMES.items():
            start = utils.night_time(night, fraction).astimezone(tz)
            events.append(
                CalendarEvent(
                    start=start,
                    end=start,
                    summary=NIGHT_SUMMARIES[key],
                    uid=f"{day.isoformat()}_{key}",
                )
            )
    # Sorted: the end of the first third can be before Isha in summer.
    return sorted(events, key=lambda event: event.start)


class MawaqitPrayerCalendar(MawaqitEntity, CalendarEntity):
    """Calendar with one event per prayer of the current and next month.

    The API returns a calendar without year, so other months are not shown.
    """

    def __init__(
        self,
        coordinator: PrayerTimeCoordinator,
        description: CalendarEntityDescription,
        mosque_uuid: str,
    ) -> None:
        """Initialize the calendar."""
        super().__init__(coordinator, mosque_uuid)
        self.entity_description = description
        self._attr_unique_id = f"{mosque_uuid}_{description.key}"

    def _events(self, first_day: date, end_day: date) -> list[CalendarEvent]:
        """Return the events from first_day to end_day (excluded)."""
        data = self.coordinator.data
        if (
            not data
            or not data.get("calendar")
            or not (tz := dt_util.get_time_zone(data.get("timezone") or ""))
        ):
            return []

        # From the first day of this month to the last day of the next one:
        # two months last 59 to 62 days, so +62 days lands in the month after.
        window_start = dt_util.now(tz).date().replace(day=1)
        window_end = (window_start + timedelta(days=62)).replace(day=1)

        # The day before only for its times after midnight: night, Isha iqama.
        window_start_time = datetime.combine(window_start, time.min, tz)
        day = max(first_day, window_start - timedelta(days=1))
        events: list[CalendarEvent] = []
        while day < min(end_day, window_end):
            events.extend(
                event
                for event in _day_events(data, day, tz)
                if event.end > window_start_time
            )
            day += timedelta(days=1)
        return events

    @property
    @override
    def event(self) -> CalendarEvent | None:
        """Return the current or next prayer."""
        now = dt_util.now()
        today = now.date()
        events = self._events(today - timedelta(days=1), today + timedelta(days=3))
        return next((event for event in events if event.end > now), None)

    @override
    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Return the prayers between start_date and end_date."""
        events = self._events(
            start_date.date() - timedelta(days=1), end_date.date() + timedelta(days=2)
        )
        return [
            event
            for event in events
            if event.start < end_date and event.end >= start_date
        ]
