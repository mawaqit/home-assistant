"""Tests for the Mawaqit utility functions."""

from datetime import date, datetime, time, timedelta
from unittest.mock import MagicMock, patch
from zoneinfo import ZoneInfo

from freezegun import freeze_time
from mawaqit.hijri import HijriDate, HijriMonth
import pytest

from custom_components.mawaqit import utils
from custom_components.mawaqit.const import IMSAK_CALENDAR
from homeassistant.const import CONF_API_KEY, CONF_LATITUDE, CONF_LONGITUDE, CONF_UUID

# Shared calendar helpers from conftest — avoids re-defining month_data inline.
from .conftest import (
    IQAMA_ABSOLUTE_TIMES_ROW,
    IQAMA_OFFSET_TIMES_ROW,
    PRAYER_TIMES_ROW,
    build_prayer_data,
    make_iqama_month_data,
    make_month_data,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

PARIS = ZoneInfo("Europe/Paris")
UTC = ZoneInfo("UTC")

# Middle of the night at 23:45, before 00:00.
WINTER_ROW = ["06:30", "08:00", "12:45", "14:45", "17:00", "18:30"]
# Middle of the night at 01:00, after 00:00.
SUMMER_ROW = ["04:30", "06:00", "13:45", "17:45", "21:30", "23:00"]


def _daily_data(row: list[str]) -> dict:
    """Return prayer data with the same times every day."""
    return {
        **build_prayer_data(),
        "calendar": [make_month_data(row) for _ in range(12)],
    }


def _calendar_with_april(extra_days: dict | None = None) -> list[dict]:
    """Return a 12-month calendar that only has April (index 3) filled.

    Args:
        extra_days: Optional extra day entries merged into the April dict
                    (e.g. ``{"11": [...]}`` to add the following day).

    """
    month = make_month_data()
    if extra_days:
        month.update(extra_days)
    calendar = [{} for _ in range(12)]
    calendar[3] = month
    return calendar


def _two_day_april_calendar() -> list[dict]:
    """April calendar with day 10 AND day 11 filled (for next-day look-ahead)."""
    return _calendar_with_april(
        extra_days={"11": ["05:29", "06:44", "12:29", "15:44", "18:29", "19:59"]}
    )


# ---------------------------------------------------------------------------
# _to_utc
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("time_str", ["", None])
def test_to_utc_falsy_time_string_returns_none(time_str) -> None:
    """Test _to_utc returns None for empty / None inputs."""
    assert utils._to_utc("Europe/Paris", date(2025, 4, 10), time_str) is None


# ---------------------------------------------------------------------------
# compute_middle_of_the_night
# ---------------------------------------------------------------------------


def test_compute_middle_of_the_night() -> None:
    """Test the middle of the night between Maghrib (18:30) and Fajr (05:30)."""
    assert utils.compute_middle_of_the_night(
        build_prayer_data(), date(2025, 4, 10), "Europe/Paris"
    ) == datetime(2025, 4, 11, 0, 0, tzinfo=PARIS)


def test_compute_middle_of_the_night_dst_change() -> None:
    """Test the night lasts an hour less when clocks go forward (10 hours)."""
    assert utils.compute_middle_of_the_night(
        build_prayer_data(), date(2025, 3, 29), "Europe/Paris"
    ) == datetime(2025, 3, 29, 23, 30, tzinfo=PARIS)


@pytest.mark.parametrize("failing", [0, 1], ids=["maghrib", "fajr"])
def test_compute_middle_of_the_night_localization_fails(failing: int) -> None:
    """Test compute_middle_of_the_night returns None when a time cannot be localized."""
    times = [
        datetime(2025, 4, 10, 18, 30, tzinfo=PARIS),
        datetime(2025, 4, 11, 5, 29, tzinfo=PARIS),
    ]
    times[failing] = None
    with patch("custom_components.mawaqit.utils.time_with_timezone", side_effect=times):
        assert (
            utils.compute_middle_of_the_night(
                {"calendar": _two_day_april_calendar()},
                date(2025, 4, 10),
                "Europe/Paris",
            )
            is None
        )


@pytest.mark.parametrize(
    ("day", "index"), [("10", 4), ("11", 0)], ids=["maghrib", "fajr"]
)
def test_compute_middle_of_the_night_invalid_time(day: str, index: int) -> None:
    """Test compute_middle_of_the_night returns None when Maghrib or Fajr is invalid."""
    calendar = _two_day_april_calendar()
    calendar[3][day][index] = "invalid"

    assert (
        utils.compute_middle_of_the_night(
            {"calendar": calendar}, date(2025, 4, 10), "Europe/Paris"
        )
        is None
    )


def test_compute_middle_of_the_night_no_calendar() -> None:
    """Test compute_middle_of_the_night returns None without a calendar."""
    assert (
        utils.compute_middle_of_the_night({}, date(2025, 4, 10), "Europe/Paris") is None
    )


# ---------------------------------------------------------------------------
# get_islamic_date
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("row", "now", "expected"),
    [
        (PRAYER_TIMES_ROW, "2025-04-10 12:00:00+02:00", date(2025, 4, 10)),
        (WINTER_ROW, "2025-04-10 23:44:59+02:00", date(2025, 4, 10)),
        (WINTER_ROW, "2025-04-10 23:45:00+02:00", date(2025, 4, 11)),
        (SUMMER_ROW, "2025-04-11 00:59:59+02:00", date(2025, 4, 10)),
        (SUMMER_ROW, "2025-04-11 01:00:00+02:00", date(2025, 4, 11)),
    ],
    ids=[
        "afternoon",
        "before_middle_before_00",
        "at_middle_before_00",
        "before_middle_after_00",
        "at_middle_after_00",
    ],
)
def test_get_islamic_date(row: list[str], now: str, expected: date) -> None:
    """Test the day of the prayer times changes at the middle of the night."""
    with freeze_time(now):
        assert utils.get_islamic_date(_daily_data(row), "Europe/Paris") == expected


@pytest.mark.parametrize(
    ("now", "day", "index"),
    [
        ("2025-04-11 00:30:00+02:00", "10", 4),
        ("2025-04-10 12:00:00+02:00", "11", 0),
    ],
    ids=["last_night", "next_night"],
)
def test_get_islamic_date_invalid_night(now: str, day: str, index: int) -> None:
    """Test an invalid night falls back to the civil date, never a day ahead."""
    prayer_data = _daily_data(SUMMER_ROW)
    prayer_data["calendar"][3][day][index] = "invalid"
    with freeze_time(now):
        assert utils.get_islamic_date(
            prayer_data, "Europe/Paris"
        ) == date.fromisoformat(now[:10])


# ---------------------------------------------------------------------------
# get_night_time / get_night_end
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("now", "night"),
    [
        ("2025-04-10 12:00:00+02:00", date(2025, 4, 10)),
        ("2025-04-11 03:00:00+02:00", date(2025, 4, 10)),
        ("2025-04-11 05:30:00+02:00", date(2025, 4, 11)),
    ],
    ids=["afternoon", "after_last_third", "at_fajr"],
)
def test_get_night_time(now: str, night: date) -> None:
    """Test the night times are kept until Fajr (05:30), then move to the next night."""
    next_day = night + timedelta(days=1)
    with freeze_time(now):
        prayer_data = build_prayer_data()
        assert [
            utils.get_night_time(prayer_data, fraction)
            for fraction in ((1, 3), (1, 2), (2, 3))
        ] == [
            datetime.combine(night, time(22, 10), PARIS),
            datetime.combine(next_day, time(0, 0), PARIS),
            datetime.combine(next_day, time(1, 50), PARIS),
        ]
        assert utils.get_night_end(prayer_data) == datetime.combine(
            next_day, time(5, 30), PARIS
        )


def test_get_night_time_dst_change() -> None:
    """Test the last third starts after 2/3 of a night shortened by DST (10 hours)."""
    with freeze_time("2025-03-29 12:00:00+01:00"):
        assert utils.get_night_time(build_prayer_data(), (2, 3)) == datetime(
            2025, 3, 30, 0, 10, tzinfo=UTC
        )


@freeze_time("2025-04-11 03:00:00+02:00")
def test_get_night_time_skips_invalid_night() -> None:
    """Test an invalid night is skipped for the next one."""
    prayer_data = build_prayer_data()
    prayer_data["calendar"][3]["10"][4] = "invalid"

    assert utils.get_night_time(prayer_data, (1, 2)) == datetime(
        2025, 4, 12, 0, 0, tzinfo=PARIS
    )


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    "prayer_data",
    [
        {"calendar": [make_month_data() for _ in range(12)]},
        {"calendar": [make_month_data() for _ in range(12)], "timezone": "Invalid/Tz"},
        {"calendar": [{} for _ in range(12)], "timezone": "Europe/Paris"},
    ],
    ids=["no_timezone", "invalid_timezone", "empty_calendar"],
)
def test_get_night_time_missing_data(prayer_data: dict) -> None:
    """Test the night times are None without usable data."""
    assert utils.get_night_time(prayer_data, (1, 2)) is None
    assert utils.get_night_end(prayer_data) is None


# ---------------------------------------------------------------------------
# save_mosque
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("kwargs", "expected_data"),
    [
        (
            {"lat": 48.0, "longi": 2.0},
            {
                CONF_API_KEY: "token",
                CONF_UUID: "uuid1",
                CONF_LATITUDE: 48.0,
                CONF_LONGITUDE: 2.0,
            },
        ),
        (
            {},
            {CONF_API_KEY: "token", CONF_UUID: "uuid1"},
        ),
    ],
)
def test_save_mosque(kwargs: dict, expected_data: dict) -> None:
    """Test saving mosque data with and without coordinates."""
    title, data = utils.save_mosque(
        mosque_name="My Mosque",
        mosque_id="uuid1",
        mawaqit_token="token",
        **kwargs,
    )
    assert title == "My Mosque"
    assert data == expected_data


def test_save_mosque_no_token() -> None:
    """Test saving mosque data with no token raises ValueError."""
    with pytest.raises(ValueError):
        utils.save_mosque(
            mosque_name="My Mosque",
            mosque_id="uuid1",
            mawaqit_token=None,
        )


# ---------------------------------------------------------------------------
# extract_time_from_calendar
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("month_data", "mode_iqama", "expected"),
    [
        (make_month_data(), False, PRAYER_TIMES_ROW[0]),
        (make_iqama_month_data(), True, IQAMA_OFFSET_TIMES_ROW[0]),
    ],
)
def test_extract_time_from_calendar_success(month_data, mode_iqama, expected) -> None:
    """Test successful time extraction for standard and iqama modes."""
    calendar = [{} for _ in range(12)]
    calendar[3] = month_data  # April (index 3)
    result = utils.extract_time_from_calendar(
        calendar, "Fajr", date(2025, 4, 10), mode_iqama=mode_iqama
    )
    assert result == expected


@pytest.mark.parametrize(
    ("calendar", "prayer_name", "target_date", "mode_iqama"),
    [
        (
            [{"1": list(PRAYER_TIMES_ROW)}],
            "InvalidPrayer",
            date(2025, 1, 1),
            False,
        ),
        ([], "Fajr", date(2025, 1, 1), False),
        ([{}], "Fajr", date(2025, 1, 1), False),
        ([{"1": ["05:30"]}], "Fajr", date(2025, 1, 1), False),
    ],
)
def test_extract_time_from_calendar_returns_none(
    calendar, prayer_name, target_date, mode_iqama
) -> None:
    """Test extraction returns None for invalid / missing / incomplete data."""
    assert (
        utils.extract_time_from_calendar(
            calendar, prayer_name, target_date, mode_iqama=mode_iqama
        )
        is None
    )


# ---------------------------------------------------------------------------
# time_with_timezone
# ---------------------------------------------------------------------------


def test_time_with_timezone_valid() -> None:
    """Test converting time with valid timezone."""
    result = utils.time_with_timezone("Europe/Paris", "2025-04-10", "12:30")
    assert result is not None
    assert isinstance(result, datetime)


def test_time_with_timezone_invalid() -> None:
    """Test converting time with invalid timezone."""
    assert utils.time_with_timezone("Invalid/Timezone", "2025-04-10", "12:30") is None


def test_time_with_timezone_invalid_time() -> None:
    """Test converting a time that is not HH:MM."""
    assert utils.time_with_timezone("Europe/Paris", "2025-04-10", "invalid") is None


# ---------------------------------------------------------------------------
# parse_time / find_invalid_times
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("time_str", "expected"),
    [
        ("05:30", time(5, 30)),
        ("invalid", None),
        ("", None),
        ("25:00", None),
        (None, None),
    ],
)
def test_parse_time(time_str: str | None, expected: time | None) -> None:
    """Test parse_time returns None for times that are not HH:MM."""
    assert utils.parse_time(time_str) == expected


def test_find_invalid_times() -> None:
    """Test find_invalid_times returns the days with an invalid time."""
    calendar = _calendar_with_april(
        extra_days={"11": ["05:29", "06:44", "invalid", "15:44", "18:29", "19:59"]}
    )
    calendar[11] = {"31": ["", "06:44", "12:29", "15:44", "18:29", "19:59"]}

    assert utils.find_invalid_times(calendar) == ["4/11", "12/31"]


# ---------------------------------------------------------------------------
# add_minutes_to_time
# ---------------------------------------------------------------------------


def test_add_minutes_to_time_valid() -> None:
    """Test adding minutes to time."""
    assert utils.add_minutes_to_time("12:30", "+15") == "12:45"


@pytest.mark.parametrize(
    ("time_str", "minutes_str", "match"),
    [
        (None, "+15", "Both time_str and minutes_str must be"),
        ("12:30", None, "Both time_str and minutes_str must be"),
        ("12:30", "15", "Invalid minutes format"),
        ("12:30", "+abc", "Invalid minutes format"),
    ],
)
def test_add_minutes_to_time_errors(time_str, minutes_str, match) -> None:
    """Test error cases for add_minutes_to_time."""
    with pytest.raises(ValueError, match=match):
        utils.add_minutes_to_time(time_str, minutes_str)


def test_add_minutes_to_time_internal_error() -> None:
    """Test add_minutes_to_time handles internal TypeError gracefully."""
    with patch(
        "custom_components.mawaqit.utils.timedelta",
        side_effect=TypeError("mock error"),
    ):
        assert utils.add_minutes_to_time("12:30", "+15") is None


# ---------------------------------------------------------------------------
# get_next_middle_of_the_night
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        ("2025-04-10 12:00:00+02:00", datetime(2025, 4, 10, 23, 45, tzinfo=PARIS)),
        ("2025-04-10 23:45:00+02:00", datetime(2025, 4, 11, 23, 45, tzinfo=PARIS)),
        ("2025-04-11 00:30:00+02:00", datetime(2025, 4, 11, 23, 45, tzinfo=PARIS)),
    ],
    ids=["afternoon", "at_middle_of_the_night", "after_00"],
)
def test_get_next_middle_of_the_night(now: str, expected: datetime) -> None:
    """Test the next middle of the night, between Maghrib (17:00) and Fajr (06:30)."""
    with freeze_time(now):
        assert utils.get_next_middle_of_the_night(_daily_data(WINTER_ROW)) == expected


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    "prayer_data",
    [
        {"calendar": [make_month_data() for _ in range(12)]},
        {"calendar": [make_month_data() for _ in range(12)], "timezone": "Invalid/Tz"},
        {"calendar": [{} for _ in range(12)], "timezone": "Europe/Paris"},
    ],
    ids=["no_timezone", "invalid_timezone", "empty_calendar"],
)
def test_get_next_middle_of_the_night_missing_data(prayer_data: dict) -> None:
    """Test get_next_middle_of_the_night returns None without usable data."""
    assert utils.get_next_middle_of_the_night(prayer_data) is None


# ---------------------------------------------------------------------------
# get_prayer_times_for_two_days
# ---------------------------------------------------------------------------


def test_get_prayer_times_for_two_days() -> None:
    """Test getting prayer times for today and tomorrow."""
    tz = ZoneInfo("Europe/Paris")
    today = datetime(2025, 4, 10, 12, 0, tzinfo=tz)

    result = utils.get_prayer_times_for_two_days(
        _two_day_april_calendar(), today, "Europe/Paris"
    )

    assert result["today"]["date"] == "2025-04-10"
    assert result["today"]["prayer_times"] == list(PRAYER_TIMES_ROW)
    assert result["tomorrow"]["date"] == "2025-04-11"


# ---------------------------------------------------------------------------
# find_next_prayer
# ---------------------------------------------------------------------------


def test_find_next_prayer_today() -> None:
    """Test finding next prayer when there is one remaining today."""
    tz = ZoneInfo("Europe/Paris")
    current_time = datetime(2025, 4, 10, 14, 0, tzinfo=tz)

    index, prayer_time = utils.find_next_prayer(
        current_time, _two_day_april_calendar(), "Europe/Paris"
    )
    assert index == 3  # Asr at 15:45 is next after 14:00
    assert prayer_time is not None


def test_find_next_prayer_tomorrow() -> None:
    """Test finding next prayer when all today's prayers have passed."""
    tz = ZoneInfo("Europe/Paris")
    current_time = datetime(2025, 4, 10, 23, 0, tzinfo=tz)

    index, prayer_time = utils.find_next_prayer(
        current_time, _two_day_april_calendar(), "Europe/Paris"
    )
    assert index == 0  # First prayer tomorrow
    assert prayer_time is not None


@pytest.mark.parametrize(
    ("day", "index", "hour", "expected_index"),
    [
        ("10", 3, 14, 4),  # Asr invalid: Maghrib
        ("10", 5, 19, 0),  # Isha invalid: Fajr tomorrow
        ("11", 0, 21, 1),  # Fajr tomorrow invalid: Shuruq tomorrow
    ],
    ids=["today", "last_today", "first_tomorrow"],
)
def test_find_next_prayer_skips_invalid_time(
    day: str, index: int, hour: int, expected_index: int
) -> None:
    """Test finding the next prayer skips times that are not HH:MM."""
    calendar = _two_day_april_calendar()
    calendar[3][day][index] = "invalid"
    current_time = datetime(2025, 4, 10, hour, 0, tzinfo=PARIS)

    next_index, prayer_time = utils.find_next_prayer(
        current_time, calendar, "Europe/Paris"
    )
    assert next_index == expected_index
    assert prayer_time is not None


def test_find_next_prayer_no_valid_time() -> None:
    """Test finding the next prayer when no time of today or tomorrow is valid."""
    calendar = _calendar_with_april()
    calendar[3]["10"] = ["invalid"] * 6
    calendar[3]["11"] = ["invalid"] * 6
    current_time = datetime(2025, 4, 10, 12, 0, tzinfo=PARIS)

    assert utils.find_next_prayer(current_time, calendar, "Europe/Paris") == (
        None,
        None,
    )


def test_find_next_prayer_invalid_timezone() -> None:
    """Test finding next prayer with an invalid timezone."""
    tz = ZoneInfo("Europe/Paris")
    current_time = datetime(2025, 4, 10, 12, 0, tzinfo=tz)

    index, prayer_time = utils.find_next_prayer(current_time, [{}], "Invalid/Timezone")
    assert index is None
    assert prayer_time is None


# ---------------------------------------------------------------------------
# get_regular_prayer_time
# ---------------------------------------------------------------------------


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    ("prayer_data", "expect_datetime"),
    [
        (
            {
                "calendar": [make_month_data() for _ in range(12)],
                "timezone": "Europe/Paris",
            },
            True,
        ),
        ({}, False),
        ({"calendar": [{}], "timezone": "Europe/Paris"}, False),
    ],
)
def test_get_regular_prayer_time(prayer_data, expect_datetime) -> None:
    """Test get_regular_prayer_time with valid and missing data."""
    result = utils.get_regular_prayer_time(prayer_data, "Fajr")
    if expect_datetime:
        assert isinstance(result, datetime)
    else:
        assert result is None


@freeze_time("2025-04-10 12:00:00+02:00")
def test_get_regular_prayer_time_invalid_timezone() -> None:
    """Test get_regular_prayer_time when time_with_timezone returns None."""
    prayer_data = {"calendar": _calendar_with_april(), "timezone": "Europe/Paris"}
    with patch(
        "custom_components.mawaqit.utils.time_with_timezone",
        return_value=None,
    ):
        assert utils.get_regular_prayer_time(prayer_data, "Fajr") is None


# ---------------------------------------------------------------------------
# get_jumua_time
# ---------------------------------------------------------------------------


def test_get_jumua_time_success() -> None:
    """Test getting jumua time successfully."""
    result = utils.get_jumua_time(
        {"timezone": "Europe/Paris", "jumua": "13:00"}, "jumua"
    )
    assert isinstance(result, datetime)


@pytest.mark.parametrize(
    ("now", "expected"),
    [
        ("2025-04-10 12:00:00+02:00", date(2025, 4, 11)),  # Thursday
        ("2025-04-11 14:00:00+02:00", date(2025, 4, 11)),  # Friday, after Jumua
        (
            "2025-04-11 23:59:00+02:00",
            date(2025, 4, 11),
        ),  # before the middle of the night
        ("2025-04-12 12:00:00+02:00", date(2025, 4, 18)),  # Saturday
    ],
)
def test_get_jumua_time_keeps_friday_until_middle_of_the_night(
    now: str, expected: date
) -> None:
    """Test Jumua stays on Friday until the middle of the night, then a week ahead."""
    with freeze_time(now):
        result = utils.get_jumua_time(build_prayer_data(), "jumua")
    assert result == datetime.combine(expected, time(13), PARIS)


def test_get_jumua_time_no_timezone() -> None:
    """Test getting jumua time without timezone returns None."""
    assert utils.get_jumua_time({"jumua": "13:00"}, "jumua") is None


def test_get_jumua_time_no_jumua() -> None:
    """Test getting jumua time when jumua key is absent returns None."""
    assert utils.get_jumua_time({"timezone": "Europe/Paris"}, "jumua") is None


def test_get_jumua_time_invalid_localization() -> None:
    """Test getting jumua time when localization fails."""
    with patch(
        "custom_components.mawaqit.utils.time_with_timezone",
        return_value=None,
    ):
        assert (
            utils.get_jumua_time(
                {"timezone": "Europe/Paris", "jumua": "13:00"}, "jumua"
            )
            is None
        )


# ---------------------------------------------------------------------------
# parse_iqama_time
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("prayer_time", "iqama_time", "expected"),
    [
        ("05:30", "+10", "05:40"),  # offset
        ("05:30", "+0", "05:30"),  # zero offset
        ("05:30", "06:15", "06:15"),  # absolute
        ("20:00", "06:15", "06:15"),  # absolute ignores prayer_time
    ],
)
def test_parse_iqama_time_valid(prayer_time, iqama_time, expected) -> None:
    """Test parse_iqama_time with valid formats."""
    assert utils.parse_iqama_time(prayer_time, iqama_time) == expected


@pytest.mark.parametrize(
    "iqama_time",
    ["", "invalid", "5:30", "05:3"],
)
def test_parse_iqama_time_returns_none(iqama_time) -> None:
    """Test parse_iqama_time with invalid / empty formats returns None."""
    assert utils.parse_iqama_time("05:30", iqama_time) is None


def test_parse_iqama_time_invalid_prayer_time() -> None:
    """Test an iqama offset from a prayer time that is not HH:MM returns None."""
    assert utils.parse_iqama_time("invalid", "+10") is None


# ---------------------------------------------------------------------------
# get_iqama_time
# ---------------------------------------------------------------------------


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    ("iqama_day_data", "expected_hour", "expected_minute"),
    [
        (
            list(IQAMA_ABSOLUTE_TIMES_ROW),
            3,
            45,
        ),  # absolute: 05:45 Paris = 03:45 UTC
        (
            list(IQAMA_OFFSET_TIMES_ROW),
            3,
            40,
        ),  # offset: 05:30+10m Paris = 03:40 UTC
    ],
)
def test_get_iqama_time_formats(iqama_day_data, expected_hour, expected_minute) -> None:
    """Test get_iqama_time with absolute and offset iqama formats."""
    calendar = _calendar_with_april()
    iqama_calendar = [{} for _ in range(12)]
    iqama_calendar[3] = {"10": iqama_day_data}

    prayer_data = {
        "calendar": calendar,
        "iqamaCalendar": iqama_calendar,
        "iqamaEnabled": True,
        "timezone": "Europe/Paris",
    }
    result = utils.get_iqama_time(prayer_data, "Fajr")
    assert isinstance(result, datetime)
    assert result.hour == expected_hour
    assert result.minute == expected_minute


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    "prayer_data",
    [
        {},
        {"iqamaCalendar": [{}], "iqamaEnabled": True},
        {
            "calendar": [{}],
            "iqamaCalendar": [{}],
            "iqamaEnabled": True,
            "timezone": "Europe/Paris",
        },
        {
            "calendar": _calendar_with_april(),
            "iqamaCalendar": [{}],
            "iqamaEnabled": True,
            "timezone": "Europe/Paris",
        },
        {
            "calendar": _calendar_with_april(),
            "iqamaCalendar": [make_iqama_month_data() for _ in range(12)],
            "iqamaEnabled": False,
            "timezone": "Europe/Paris",
        },
    ],
)
def test_get_iqama_time_returns_none(prayer_data) -> None:
    """Test get_iqama_time returns None when required data is absent."""
    assert utils.get_iqama_time(prayer_data, "Fajr") is None


@freeze_time("2025-04-10 12:00:00+02:00")
def test_get_iqama_time_parse_returns_none() -> None:
    """Test get_iqama_time when parse_iqama_time returns None."""
    iqama_calendar = [{} for _ in range(12)]
    iqama_calendar[3] = make_iqama_month_data()
    prayer_data = {
        "calendar": _calendar_with_april(),
        "iqamaCalendar": iqama_calendar,
        "iqamaEnabled": True,
        "timezone": "Europe/Paris",
    }
    with patch("custom_components.mawaqit.utils.parse_iqama_time", return_value=None):
        assert utils.get_iqama_time(prayer_data, "Fajr") is None


@freeze_time("2025-04-10 12:00:00+02:00")
def test_get_iqama_time_invalid_localization() -> None:
    """Test get_iqama_time when localization fails."""
    iqama_calendar = [{} for _ in range(12)]
    iqama_calendar[3] = make_iqama_month_data()
    prayer_data = {
        "calendar": _calendar_with_april(),
        "iqamaCalendar": iqama_calendar,
        "iqamaEnabled": True,
        "timezone": "Europe/Paris",
    }
    with patch("custom_components.mawaqit.utils.time_with_timezone", return_value=None):
        assert utils.get_iqama_time(prayer_data, "Fajr") is None


# ---------------------------------------------------------------------------
# split_imsak_column / has_imsak / get_imsak_time
# ---------------------------------------------------------------------------


def test_split_imsak_column() -> None:
    """Test the Imsak is split from the times of mosques displaying Sabah and Imsak."""
    calendar = [{"1": ["05:00", *PRAYER_TIMES_ROW], "2": []}, {}]
    assert utils.split_imsak_column(calendar) == (
        [{"1": "05:00"}, {}],
        [{"1": PRAYER_TIMES_ROW, "2": []}, {}],
    )


@pytest.mark.parametrize(
    ("prayer_data", "expected"),
    [
        ({}, False),
        ({"imsakNbMinBeforeFajr": None}, False),
        ({"imsakNbMinBeforeFajr": 0}, False),
        ({"imsakNbMinBeforeFajr": -10}, False),
        ({"imsakNbMinBeforeFajr": 10}, True),
        ({IMSAK_CALENDAR: []}, False),
        ({IMSAK_CALENDAR: [{"1": "05:00"}]}, True),
    ],
)
def test_has_imsak(prayer_data: dict, expected: bool) -> None:
    """Test Imsak is published with the Imsak calendar or minutes before Fajr."""
    assert utils.has_imsak(prayer_data) is expected


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    ("extra_data", "expected"),
    [
        ({"imsakNbMinBeforeFajr": 10}, time(5, 20)),
        ({IMSAK_CALENDAR: [{"10": "04:00"}] * 12}, time(4)),
        # Like in the MAWAQIT app, the calendar comes first.
        ({IMSAK_CALENDAR: [{"10": "04:00"}] * 12, "imsakNbMinBeforeFajr": 10}, time(4)),
    ],
    ids=["minutes_before_fajr", "calendar", "both"],
)
def test_get_imsak_time(extra_data: dict, expected: time) -> None:
    """Test the Imsak of today, from the calendar or minutes before Fajr."""
    prayer_data = {**build_prayer_data(), **extra_data}
    assert utils.get_imsak_time(prayer_data) == datetime.combine(
        date(2025, 4, 10), expected, PARIS
    )


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    "extra_data",
    [
        {"timezone": None, "imsakNbMinBeforeFajr": 10},
        {"imsakNbMinBeforeFajr": 0},
        {
            "imsakNbMinBeforeFajr": 10,
            "calendar": [make_month_data(["invalid", *PRAYER_TIMES_ROW[1:]])] * 12,
        },
        {IMSAK_CALENDAR: [{"10": "04:00"}] * 3},
        {IMSAK_CALENDAR: [{"9": "04:00"}] * 12},
        {IMSAK_CALENDAR: [{"10": "invalid"}] * 12},
    ],
    ids=[
        "no_timezone",
        "not_published",
        "invalid_fajr",
        "missing_month",
        "missing_day",
        "invalid_imsak",
    ],
)
def test_get_imsak_time_returns_none(extra_data: dict) -> None:
    """Test the Imsak is unknown when it cannot be computed."""
    assert utils.get_imsak_time({**build_prayer_data(), **extra_data}) is None


# ---------------------------------------------------------------------------
# extract_time_from_calendar - error branches
# ---------------------------------------------------------------------------


def test_extract_time_key_error() -> None:
    """Test extract_time_from_calendar handles KeyError."""
    mock_month = MagicMock()
    mock_month.get = MagicMock(side_effect=KeyError("missing"))
    result = utils.extract_time_from_calendar([mock_month], "Fajr", date(2025, 1, 1))
    assert result is None


def test_extract_time_value_error() -> None:
    """Test extract_time_from_calendar handles ValueError from list.index()."""

    class FailIndexList(list):
        def index(self, value, *args):
            raise ValueError("not found")

    month_data = {"1": list(PRAYER_TIMES_ROW)}
    with patch(
        "custom_components.mawaqit.utils.PRAYER_NAMES",
        new=FailIndexList(["fajr", "shuruq", "dhuhr", "asr", "maghrib", "isha"]),
    ):
        result = utils.extract_time_from_calendar(
            [month_data], "Fajr", date(2025, 1, 1)
        )
    assert result is None


def test_extract_time_index_error() -> None:
    """Test extract_time_from_calendar handles IndexError from list subscript."""

    class FailGetitemList(list):
        def __getitem__(self, index):
            raise IndexError("out of range")

    month_data = {"1": FailGetitemList(list(PRAYER_TIMES_ROW))}
    result = utils.extract_time_from_calendar([month_data], "Fajr", date(2025, 1, 1))
    assert result is None


# ---------------------------------------------------------------------------
# get_eid
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("month", "day", "expected"),
    [
        (HijriMonth.SHABAN, 23, None),
        (HijriMonth.RAMADAN, 22, None),
        (HijriMonth.RAMADAN, 23, ("eid_al_fitr", date(2026, 3, 19))),
        (HijriMonth.RAMADAN, 29, ("eid_al_fitr", date(2026, 3, 13))),
        (HijriMonth.RAMADAN, 30, ("eid_al_fitr", date(2026, 3, 12))),
        (HijriMonth.SHAWWAL, 1, ("eid_al_fitr", date(2026, 3, 11))),
        (HijriMonth.SHAWWAL, 2, None),
        (HijriMonth.DHU_AL_HIJJAH, 2, None),
        (HijriMonth.DHU_AL_HIJJAH, 3, ("eid_al_adha", date(2026, 3, 18))),
        (HijriMonth.DHU_AL_HIJJAH, 10, ("eid_al_adha", date(2026, 3, 11))),
        (HijriMonth.DHU_AL_HIJJAH, 11, None),
    ],
)
def test_get_eid(
    month: HijriMonth, day: int, expected: tuple[str, date] | None
) -> None:
    """Test the Eid shown on 11 March 2026 for a given Hijri date."""
    assert utils.get_eid(date(2026, 3, 11), HijriDate(1447, month, day)) == expected
