"""Tests for the Mawaqit calendar platform."""

from datetime import timedelta

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from homeassistant.components.calendar import DOMAIN as CALENDAR_DOMAIN
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant
import homeassistant.util.dt as dt_util

from .conftest import build_prayer_data

ENTITY_ID = "calendar.prayer_times"


@pytest.fixture(autouse=True)
async def paris_time_zone(hass: HomeAssistant) -> None:
    """Use the mosque time zone, so event times read like the calendar."""
    await hass.config.async_set_time_zone("Europe/Paris")


async def get_events(hass: HomeAssistant, start: str, end: str) -> list[dict]:
    """Return the events of the calendar between two local datetimes."""
    response = await hass.services.async_call(
        CALENDAR_DOMAIN,
        "get_events",
        {"start_date_time": start, "end_date_time": end},
        target={"entity_id": ENTITY_ID},
        blocking=True,
        return_response=True,
    )
    return response[ENTITY_ID]["events"]


def summaries(events: list[dict]) -> list[str]:
    """Return the summaries of the events."""
    return [event["summary"] for event in events]


async def test_calendar_next_prayer(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the calendar shows the next prayer, until its iqama."""
    freezer.move_to("2025-04-10 12:00:00+02:00")
    await setup_mawaqit_integration()

    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    assert state.attributes["message"] == "Dhuhr"
    assert state.attributes["start_time"] == "2025-04-10 12:30:00"
    assert state.attributes["end_time"] == "2025-04-10 12:45:00"

    freezer.move_to("2025-04-10 12:30:00+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY_ID).state == STATE_ON

    freezer.move_to("2025-04-10 12:45:00+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    assert state.attributes["message"] == "Asr"


async def test_calendar_events_of_a_friday(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the events of a day, with the Jumua of the mosque on Fridays."""
    freezer.move_to("2025-04-10 12:00:00+02:00")
    await setup_mawaqit_integration()

    events = await get_events(hass, "2025-04-11 00:00:00", "2025-04-12 00:00:00")

    assert [(event["summary"], event["start"], event["end"]) for event in events] == [
        ("Fajr", "2025-04-11T05:30:00+02:00", "2025-04-11T05:40:00+02:00"),
        ("Shuruq", "2025-04-11T06:45:00+02:00", "2025-04-11T06:45:00+02:00"),
        ("Dhuhr", "2025-04-11T12:30:00+02:00", "2025-04-11T12:45:00+02:00"),
        ("Jumua", "2025-04-11T13:00:00+02:00", "2025-04-11T13:00:00+02:00"),
        ("Jumua 2", "2025-04-11T14:00:00+02:00", "2025-04-11T14:00:00+02:00"),
        ("Asr", "2025-04-11T15:45:00+02:00", "2025-04-11T15:55:00+02:00"),
        ("Maghrib", "2025-04-11T18:30:00+02:00", "2025-04-11T18:35:00+02:00"),
        ("Isha", "2025-04-11T20:00:00+02:00", "2025-04-11T20:10:00+02:00"),
    ]


async def test_calendar_covers_current_and_next_month(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test events cover the current and the next month only."""
    freezer.move_to("2025-04-10 12:00:00+02:00")
    await setup_mawaqit_integration()

    assert await get_events(hass, "2025-03-31 00:00:00", "2025-04-01 00:00:00") == []
    assert (
        len(await get_events(hass, "2025-04-01 00:00:00", "2025-07-01 00:00:00"))
        == 61 * 6 + 9 * 2  # 61 days, and the Jumua 1 and 2 of 9 Fridays
    )


async def test_calendar_without_iqama(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test events end when they start if the mosque has no iqama."""
    freezer.move_to("2025-04-10 12:00:00+02:00")
    await setup_mawaqit_integration(prayer_data=build_prayer_data(iqama_enabled=False))

    events = await get_events(hass, "2025-04-10 12:00:00", "2025-04-10 13:00:00")

    assert [(event["start"], event["end"]) for event in events] == [
        ("2025-04-10T12:30:00+02:00", "2025-04-10T12:30:00+02:00")
    ]


async def test_calendar_isha_iqama_after_midnight(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test an Isha iqama after midnight ends the event on the next day."""
    prayer_data = build_prayer_data(fill_all_months=False)
    prayer_data["calendar"][3]["10"][5] = "23:55"
    freezer.move_to("2025-04-10 12:00:00+02:00")
    await setup_mawaqit_integration(prayer_data=prayer_data)

    events = await get_events(hass, "2025-04-11 00:00:00", "2025-04-11 01:00:00")

    assert [(event["summary"], event["end"]) for event in events] == [
        ("Isha", "2025-04-11T00:05:00+02:00")
    ]


async def test_calendar_skips_invalid_data(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test invalid times, iqamas and days are left out of the calendar."""
    prayer_data = build_prayer_data(fill_all_months=False)
    prayer_data["calendar"][3]["10"][1] = "invalid"
    prayer_data["iqamaCalendar"][3]["10"][1] = "+invalid"
    prayer_data["iqamaCalendar"][3]["10"][2] = "invalid"
    prayer_data["iqamaCalendar"][3]["11"] = ["+10"]
    prayer_data["calendar"][3]["12"] = ["05:30"]
    prayer_data["jumua"] = "13h"
    del prayer_data["jumua2"]
    freezer.move_to("2025-04-10 00:00:00+02:00")
    await setup_mawaqit_integration(prayer_data=prayer_data)

    events = await get_events(hass, "2025-04-10 00:00:00", "2025-04-13 00:00:00")

    assert summaries(events) == [
        *["Fajr", "Dhuhr", "Asr", "Maghrib", "Isha"],
        *["Fajr", "Shuruq", "Dhuhr", "Asr", "Maghrib", "Isha"],
    ]
    # Invalid iqamas and the incomplete iqamas of the 11th are ignored.
    assert [event["end"] == event["start"] for event in events] == [
        False,
        True,
        True,
        False,
        False,
        *[True] * 6,
    ]


async def test_calendar_with_missing_months(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test months missing from the calendar have no events."""
    prayer_data = build_prayer_data()
    prayer_data["calendar"] = prayer_data["calendar"][:4]
    prayer_data["iqamaCalendar"] = prayer_data["iqamaCalendar"][:4]
    freezer.move_to("2025-04-30 12:00:00+02:00")
    await setup_mawaqit_integration(prayer_data=prayer_data)

    events = await get_events(hass, "2025-04-30 00:00:00", "2025-05-02 00:00:00")

    assert len(events) == 6


@pytest.mark.parametrize(
    "data",
    [{"timezone": "Europe/Paris"}, {**build_prayer_data(), "timezone": "Mars/Base"}],
    ids=["no_calendar", "invalid_timezone"],
)
async def test_calendar_without_usable_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
    data: dict,
) -> None:
    """Test the calendar is empty when the data cannot be used."""
    freezer.move_to("2025-04-10 12:00:00+02:00")
    await setup_mawaqit_integration()

    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    coordinator.async_set_updated_data(data)
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_ID)
    assert state.state == STATE_OFF
    assert "message" not in state.attributes
    assert await get_events(hass, "2025-04-10 00:00:00", "2025-04-11 00:00:00") == []


async def test_calendar_unavailable_without_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test the calendar is unavailable when the coordinator has no data."""
    await setup_mawaqit_integration()

    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    coordinator.async_set_updated_data(None)
    await hass.async_block_till_done()

    assert hass.states.get(ENTITY_ID).state == STATE_UNAVAILABLE


async def test_calendar_moves_to_the_next_month(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the covered months move on with the current date."""
    freezer.move_to("2025-04-30 21:00:00+02:00")
    await setup_mawaqit_integration()
    june = ("2025-06-01 00:00:00", "2025-06-02 00:00:00")
    assert await get_events(hass, *june) == []

    freezer.tick(timedelta(hours=4))
    assert dt_util.now().month == 5
    assert len(await get_events(hass, *june)) == 6


async def test_calendar_in_december_shows_january(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test January of the next year uses the January of the yearly calendar."""
    prayer_data = build_prayer_data()
    prayer_data["calendar"][0]["5"] = [
        "07:00",
        "08:40",
        "12:50",
        "15:00",
        "17:20",
        "18:50",
    ]
    freezer.move_to("2025-12-20 12:00:00+01:00")
    await setup_mawaqit_integration(prayer_data=prayer_data)

    events = await get_events(hass, "2026-01-05 00:00:00", "2026-01-06 00:00:00")
    assert events[0]["start"] == "2026-01-05T07:00:00+01:00"
    assert len(events) == 6
    assert await get_events(hass, "2026-02-01 00:00:00", "2026-02-02 00:00:00") == []
