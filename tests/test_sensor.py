"""Tests for the Mawaqit sensor platform."""

from collections.abc import Generator
from datetime import datetime
import json
import logging
from pathlib import Path
import time
from unittest.mock import MagicMock

from freezegun import freeze_time
from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.mawaqit.const import PRAYER_NAMES
from custom_components.mawaqit.coordinator import PrayerTimeCoordinator
from custom_components.mawaqit.sensor import (
    PRAYER_TIME_SENSOR_DESCRIPTIONS,
    MawaqitPrayerTimeSensor,
    MawaqitPrayerTimeSensorEntityDescription,
    NextPrayerSensor,
)
from homeassistant.components.sensor import (
    ATTR_OPTIONS,
    SensorDeviceClass,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_DEVICE_CLASS, STATE_UNKNOWN
from homeassistant.core import HomeAssistant

from .conftest import (
    MOCK_UUID,
    PRAYER_TIMES_ROW,
    build_prayer_data,
    hijri_settings_response,
    make_month_data,
    prayer_times_response,
)

HIJRI_MONTHS = [
    "muharram",
    "safar",
    "rabi_al_awwal",
    "rabi_al_thani",
    "jumada_al_ula",
    "jumada_al_akhirah",
    "rajab",
    "shaban",
    "ramadan",
    "shawwal",
    "dhu_al_qidah",
    "dhu_al_hijjah",
]

# ---------------------------------------------------------------------------
# Sensor setup tests
# ---------------------------------------------------------------------------


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    ("prayer_data_kwargs", "expected_count"),
    [
        ({}, 21),  # 6 prayers + 2 jumua + 5 iqama + 3 night + 2 next + 3 hijri
        ({"iqama_enabled": False}, 16),  # no iqama sensors
        ({"with_iqama_calendar": False}, 16),  # no iqama sensors
        ({"jumua2": None}, 20),  # only 1 Jumua
        ({"jumua3": "15:00"}, 22),  # 3 Jumua prayers
        ({"jumua2": None, "iqama_enabled": False}, 15),  # 1 Jumua, no iqama
        ({"imsak_nb_min_before_fajr": 10}, 22),  # Imsak
        ({"imsak_nb_min_before_fajr": 0}, 21),  # no Imsak
    ],
)
async def test_sensor_setup_creates_entities(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    prayer_data_kwargs: dict,
    expected_count: int,
) -> None:
    """Test that the correct number of entities is created based on mosque capabilities."""
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(fill_all_months=False, **prayer_data_kwargs)
    )
    assert len(hass.states.async_all("sensor")) == expected_count


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    ("prayer_data_kwargs", "entity_id", "should_exist"),
    [
        ({}, "sensor.test_mosque_fajr_iqama", True),
        ({"iqama_enabled": False}, "sensor.test_mosque_fajr_iqama", False),
        ({"with_iqama_calendar": False}, "sensor.test_mosque_fajr_iqama", False),
        ({}, "sensor.test_mosque_jumua_prayer", True),
        ({"jumua": None}, "sensor.test_mosque_jumua_prayer", False),
        ({}, "sensor.test_mosque_second_jumua_prayer", True),
        ({"jumua2": None}, "sensor.test_mosque_second_jumua_prayer", False),
        ({"jumua3": "15:00"}, "sensor.test_mosque_third_jumua_prayer", True),
        ({"jumua3": None}, "sensor.test_mosque_third_jumua_prayer", False),
        ({"imsak_nb_min_before_fajr": 10}, "sensor.test_mosque_imsak", True),
        ({"imsak_nb_min_before_fajr": 0}, "sensor.test_mosque_imsak", False),
        ({}, "sensor.test_mosque_imsak", False),
    ],
)
async def test_conditional_sensor_creation(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    prayer_data_kwargs: dict,
    entity_id: str,
    should_exist: bool,
) -> None:
    """Test the Imsak, Jumua and iqama sensors are created only when the API reports them."""
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(fill_all_months=False, **prayer_data_kwargs)
    )
    assert (hass.states.get(entity_id) is not None) == should_exist


PUBLISHED_SENSORS = [
    "sensor.test_mosque_imsak",
    "sensor.test_mosque_fajr_iqama",
    "sensor.test_mosque_isha_iqama",
    "sensor.test_mosque_jumua_prayer",
    "sensor.test_mosque_second_jumua_prayer",
]


@freeze_time("2025-04-10 12:00:00+02:00")
async def test_published_sensors_added_at_refresh(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the Imsak, iqama and Jumua sensors appear when the mosque starts publishing them."""
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(
            fill_all_months=False, iqama_enabled=False, jumua=None, jumua2=None
        )
    )
    assert len(hass.states.async_all("sensor")) == 14
    for entity_id in PUBLISHED_SENSORS:
        assert hass.states.get(entity_id) is None

    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    coordinator.client.mosques.prayer_times.return_value = prayer_times_response(
        build_prayer_data(fill_all_months=False, imsak_nb_min_before_fajr=10)
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 22
    for entity_id in PUBLISHED_SENSORS:
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state not in ("unavailable", "unknown")

    # Later refreshes do not add them twice.
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    assert len(hass.states.async_all("sensor")) == 22
    assert "does not generate unique IDs" not in caplog.text


@freeze_time("2025-04-10 12:00:00+02:00")
async def test_published_sensors_kept_unknown_when_no_longer_published(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test the Imsak, iqama and Jumua sensors stay, as unknown, when the mosque stops publishing them."""
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(
            fill_all_months=False, imsak_nb_min_before_fajr=10
        )
    )

    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    coordinator.client.mosques.prayer_times.return_value = prayer_times_response(
        build_prayer_data(
            fill_all_months=False, iqama_enabled=False, jumua=None, jumua2=None
        )
    )
    await coordinator.async_refresh()
    await hass.async_block_till_done()

    assert len(hass.states.async_all("sensor")) == 22
    for entity_id in PUBLISHED_SENSORS:
        state = hass.states.get(entity_id)
        assert state is not None
        assert state.state == "unknown"
    assert "Missing calendar data" not in caplog.text


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    ("coordinator_attr", "entity_id"),
    [
        ("prayer_time_coordinator", "sensor.test_mosque_fajr_prayer"),
        ("prayer_time_coordinator", "sensor.test_mosque_next_salat_name"),
        ("hijri_coordinator", "sensor.test_mosque_hijri_month"),
    ],
)
async def test_sensor_unavailable_when_no_coordinator_data(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    coordinator_attr: str,
    entity_id: str,
) -> None:
    """Test sensors become unavailable when coordinator data is None."""
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(fill_all_months=False)
    )
    coordinator = getattr(mock_config_entry.runtime_data, coordinator_attr)
    coordinator.async_set_updated_data(None)
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state == "unavailable"


@freeze_time("2025-04-10 12:00:00+02:00")
async def test_prayer_time_sensor_get_value_error(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test prayer time sensor when get_value raises an exception."""
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(fill_all_months=False)
    )

    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    coordinator.async_set_updated_data({"invalid": "data"})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_mosque_fajr_prayer")
    assert state is not None
    assert state.state == "unknown"


@freeze_time("2025-04-10 12:00:00+02:00")
async def test_next_prayer_sensors(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test next salat sensors: at 12:00 Paris the next prayer is Dhuhr at 12:30."""
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(fill_all_months=False)
    )

    name_state = hass.states.get("sensor.test_mosque_next_salat_name")
    assert name_state is not None
    assert name_state.state == "dhuhr"
    assert name_state.attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENUM
    assert name_state.attributes[ATTR_OPTIONS] == PRAYER_NAMES

    time_state = hass.states.get("sensor.test_mosque_next_salat_time")
    assert time_state is not None
    assert time_state.state not in ("unavailable", "unknown")


async def test_next_prayer_sensor_moves_on_at_prayer_time(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the next prayer switches to Asr once Dhuhr (12:30 Paris) is reached."""
    freezer.move_to("2025-04-10 12:00:00+02:00")
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(fill_all_months=False)
    )
    assert hass.states.get("sensor.test_mosque_next_salat_name").state == "dhuhr"

    freezer.move_to("2025-04-10 12:30:01+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.test_mosque_next_salat_name").state == "asr"


async def test_prayer_sensors_move_to_next_day_at_middle_of_the_night(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test prayer times switch day at the middle of the night, not at a refresh."""
    prayer_data = build_prayer_data(imsak_nb_min_before_fajr=10)
    prayer_data["calendar"][3]["11"][1] = "06:43"  # Shuruq, 06:45 the day before
    entity_ids = (
        "sensor.test_mosque_fajr_prayer",
        "sensor.test_mosque_shuruq",
        "sensor.test_mosque_fajr_iqama",
        "sensor.test_mosque_imsak",
    )

    # Maghrib at 18:30 and Fajr at 05:30: the middle of the night is at 00:00.
    freezer.move_to("2025-04-10 20:30:00+02:00")
    await setup_mawaqit_integration(prayer_data=prayer_data)

    freezer.move_to("2025-04-10 23:59:59+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert [hass.states.get(entity_id).state for entity_id in entity_ids] == [
        "2025-04-10T03:30:00+00:00",
        "2025-04-10T04:45:00+00:00",
        "2025-04-10T03:40:00+00:00",
        "2025-04-10T03:20:00+00:00",
    ]

    freezer.move_to("2025-04-11 00:00:00+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert [hass.states.get(entity_id).state for entity_id in entity_ids] == [
        "2025-04-11T03:30:00+00:00",
        "2025-04-11T04:43:00+00:00",
        "2025-04-11T03:40:00+00:00",
        "2025-04-11T03:20:00+00:00",
    ]


async def test_night_sensors_move_to_next_night_at_fajr(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test the night times are kept after the middle of the night, until Fajr."""
    entity_ids = (
        "sensor.test_mosque_end_of_the_first_third",
        "sensor.test_mosque_middle_of_the_night",
        "sensor.test_mosque_start_of_the_last_third",
    )

    # Maghrib at 18:30 and Fajr at 05:30: the night lasts 11 hours.
    freezer.move_to("2025-04-10 20:30:00+02:00")
    await setup_mawaqit_integration()
    tonight = [
        "2025-04-10T20:10:00+00:00",
        "2025-04-10T22:00:00+00:00",
        "2025-04-10T23:50:00+00:00",
    ]
    assert [hass.states.get(entity_id).state for entity_id in entity_ids] == tonight

    # The prayer times move to the next day, the last third is still ahead.
    freezer.move_to("2025-04-11 00:00:00+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.test_mosque_fajr_prayer").state == (
        "2025-04-11T03:30:00+00:00"
    )
    assert [hass.states.get(entity_id).state for entity_id in entity_ids] == tonight

    freezer.move_to("2025-04-11 05:29:59+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert [hass.states.get(entity_id).state for entity_id in entity_ids] == tonight

    freezer.move_to("2025-04-11 05:30:00+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert [hass.states.get(entity_id).state for entity_id in entity_ids] == [
        "2025-04-11T20:10:00+00:00",
        "2025-04-11T22:00:00+00:00",
        "2025-04-11T23:50:00+00:00",
    ]


@pytest.mark.parametrize(
    ("now", "day", "index", "next_prayer"),
    [
        ("2025-04-10 00:30:00+02:00", "9", 5, "fajr"),
        ("2025-04-10 00:30:00+02:00", "10", 0, "shuruq"),
        ("2025-04-10 12:00:00+02:00", "10", 2, "asr"),
        ("2025-04-10 21:00:00+02:00", "10", 5, "fajr"),
        ("2025-04-10 21:00:00+02:00", "11", 0, "shuruq"),
        ("2025-04-10 21:00:00+02:00", "11", 2, "fajr"),
    ],
    ids=[
        "isha_yesterday",
        "fajr_today",
        "dhuhr_today",
        "isha_today",
        "fajr_tomorrow",
        "dhuhr_tomorrow",
    ],
)
async def test_invalid_prayer_time_is_ignored(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
    now: str,
    day: str,
    index: int,
    next_prayer: str,
) -> None:
    """Test a time that is not HH:MM is logged and skipped instead of failing (#134)."""
    prayer_data = build_prayer_data(fill_all_months=False)
    prayer_data["calendar"][3][day][index] = "invalid"

    freezer.move_to(now)
    await setup_mawaqit_integration(prayer_data=prayer_data)

    assert mock_config_entry.state is ConfigEntryState.LOADED
    assert hass.states.get("sensor.test_mosque_next_salat_name").state == next_prayer
    assert [
        record.getMessage()
        for record in caplog.records
        if record.levelno >= logging.WARNING
        and record.name.startswith("custom_components.mawaqit")
    ] == [f"Invalid prayer times from MAWAQIT, ignored on: 4/{day}"]


async def test_invalid_imsak(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test an invalid Imsak is reported and only makes the Imsak sensor unknown."""
    prayer_data = build_prayer_data()
    prayer_data["calendar"] = [
        make_month_data(["05:00", *PRAYER_TIMES_ROW]) for _ in range(12)
    ]
    prayer_data["calendar"][3]["10"][0] = "invalid"

    freezer.move_to("2025-04-10 12:00:00+02:00")
    await setup_mawaqit_integration(
        prayer_data=prayer_data, displaying_sabah_imsak=True
    )

    assert hass.states.get("sensor.test_mosque_imsak").state == STATE_UNKNOWN
    assert hass.states.get("sensor.test_mosque_fajr_prayer").state == (
        "2025-04-10T03:30:00+00:00"
    )
    assert hass.states.get("sensor.test_mosque_next_salat_name").state == "dhuhr"
    assert "Invalid prayer times from MAWAQIT, ignored on: 4/10" in caplog.text


@freeze_time("2025-04-10 12:00:00+02:00")
async def test_next_prayer_sensor_no_calendar(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
) -> None:
    """Test next prayer sensor when calendar is missing from data."""
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(fill_all_months=False)
    )

    coordinator = mock_config_entry.runtime_data.prayer_time_coordinator
    coordinator.async_set_updated_data({"timezone": "Europe/Paris"})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_mosque_next_salat_name")
    assert state is not None
    assert state.state == "unknown"


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    "entity_id",
    [
        "sensor.test_mosque_fajr_prayer",
        "sensor.test_mosque_shuruq",
        "sensor.test_mosque_jumua_prayer",
    ],
)
async def test_prayer_sensors_return_valid_state(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    setup_mawaqit_integration,
    entity_id: str,
) -> None:
    """Test prayer, shuruq and jumua sensors return a valid datetime state."""
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(fill_all_months=False)
    )
    state = hass.states.get(entity_id)
    assert state is not None
    assert state.state not in ("unavailable", "unknown")


@pytest.fixture
def system_time_zone_utc(monkeypatch: pytest.MonkeyPatch) -> Generator[None]:
    """Run the system clock in UTC, like the Home Assistant container in #82."""
    monkeypatch.setenv("TZ", "UTC")
    time.tzset()
    yield
    monkeypatch.undo()
    time.tzset()


@pytest.mark.usefixtures("system_time_zone_utc")
@pytest.mark.parametrize(
    ("now", "expected"),
    [
        (
            "2025-01-15 11:00:00+01:00",
            {
                "sensor.test_mosque_fajr_prayer": "2025-01-15T04:30:00+00:00",
                "sensor.test_mosque_shuruq": "2025-01-15T05:45:00+00:00",
                "sensor.test_mosque_asr_iqama": "2025-01-15T14:55:00+00:00",
                "sensor.test_mosque_jumua_prayer": "2025-01-17T12:00:00+00:00",
                "sensor.test_mosque_next_salat_time": "2025-01-15T11:30:00+00:00",
            },
        ),
        (
            "2025-07-15 11:00:00+02:00",
            {
                "sensor.test_mosque_fajr_prayer": "2025-07-15T03:30:00+00:00",
                "sensor.test_mosque_shuruq": "2025-07-15T04:45:00+00:00",
                "sensor.test_mosque_asr_iqama": "2025-07-15T13:55:00+00:00",
                "sensor.test_mosque_jumua_prayer": "2025-07-18T11:00:00+00:00",
                "sensor.test_mosque_next_salat_time": "2025-07-15T10:30:00+00:00",
            },
        ),
    ],
    ids=["winter", "summer"],
)
async def test_prayer_sensors_use_mosque_time_zone(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
    now: str,
    expected: dict[str, str],
) -> None:
    """Test times follow the mosque time zone, not the system or Home Assistant one."""
    freezer.move_to(now)
    await setup_mawaqit_integration()

    assert {entity_id: hass.states.get(entity_id).state for entity_id in expected} == (
        expected
    )


async def test_prayer_sensors_with_sabah_and_imsak(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test mosques displaying Sabah and Imsak, whose days start with Imsak (#93)."""
    prayer_data = build_prayer_data()
    imsak_row = ["05:00", *PRAYER_TIMES_ROW]  # Imsak, then Sabah at 05:30
    prayer_data["calendar"] = [make_month_data(imsak_row) for _ in range(12)]

    freezer.move_to("2025-04-10 19:00:00+02:00")
    await setup_mawaqit_integration(
        prayer_data=prayer_data, displaying_sabah_imsak=True
    )

    expected = {
        "sensor.test_mosque_imsak": "2025-04-10T03:00:00+00:00",
        "sensor.test_mosque_fajr_prayer": "2025-04-10T03:30:00+00:00",
        "sensor.test_mosque_shuruq": "2025-04-10T04:45:00+00:00",
        "sensor.test_mosque_maghrib_prayer": "2025-04-10T16:30:00+00:00",
        "sensor.test_mosque_isha_prayer": "2025-04-10T18:00:00+00:00",
        "sensor.test_mosque_fajr_iqama": "2025-04-10T03:40:00+00:00",
        "sensor.test_mosque_next_salat_name": "isha",
    }
    assert {entity_id: hass.states.get(entity_id).state for entity_id in expected} == (
        expected
    )


@pytest.mark.parametrize(
    ("now", "adjustment", "force_30", "expected"),
    [
        ("2026-02-17 12:00:00+01:00", 0, False, ["1", "ramadan", "1447"]),
        ("2026-02-17 12:00:00+01:00", -1, False, ["29", "shaban", "1447"]),
        # 1 Shawwal forced to 30 is the 30th of Ramadan, not of Shawwal.
        ("2026-03-19 12:00:00+01:00", 0, True, ["30", "ramadan", "1447"]),
        ("2026-06-16 12:00:00+02:00", 0, True, ["30", "dhu_al_hijjah", "1447"]),
    ],
    ids=["ramadan", "adjusted", "forced_to_30", "forced_to_30_last_month"],
)
async def test_hijri_sensors(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
    now: str,
    adjustment: int,
    force_30: bool,
    expected: list[str],
) -> None:
    """Test the Hijri sensors show the date of the mosque, with its settings."""
    freezer.move_to(now)
    await setup_mawaqit_integration(
        hijri_settings=hijri_settings_response(adjustment, force_30=force_30)
    )

    states = [
        hass.states.get(f"sensor.test_mosque_hijri_{part}")
        for part in ("day", "month", "year")
    ]
    assert [state.state for state in states] == expected
    assert states[1].attributes[ATTR_DEVICE_CLASS] == SensorDeviceClass.ENUM
    assert states[1].attributes[ATTR_OPTIONS] == HIJRI_MONTHS


# ---------------------------------------------------------------------------
# Direct unit tests for sensor class property branches
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("sensor_cls", "coordinator_spec", "extra_args"),
    [
        (
            MawaqitPrayerTimeSensor,
            PrayerTimeCoordinator,
            [PRAYER_TIME_SENSOR_DESCRIPTIONS[0], MOCK_UUID],
        ),
    ],
)
def test_sensor_native_value_none_when_no_data(
    sensor_cls, coordinator_spec, extra_args
) -> None:
    """Test native_value returns None when coordinator data is None."""
    coordinator = MagicMock(spec=coordinator_spec)
    coordinator.data = {}
    sensor = sensor_cls(coordinator, *extra_args)
    coordinator.data = None
    assert sensor.native_value is None


def test_prayer_time_sensor_native_value_raises() -> None:
    """Test MawaqitPrayerTimeSensor.native_value returns None on exception."""
    coordinator = MagicMock(spec=PrayerTimeCoordinator)
    coordinator.data = {"some": "data"}
    desc = MawaqitPrayerTimeSensorEntityDescription(
        key="test",
        translation_key="test",
        device_class=SensorDeviceClass.TIMESTAMP,
        get_value=MagicMock(side_effect=KeyError("missing")),
    )
    sensor = MawaqitPrayerTimeSensor(coordinator, desc, MOCK_UUID)
    assert sensor.native_value is None


def test_next_prayer_sensor_native_value_unhandled_key() -> None:
    """Test NextPrayerSensor returns None for a description key it does not handle."""
    coordinator = MagicMock(spec=PrayerTimeCoordinator)
    coordinator.data = {}
    sensor = NextPrayerSensor(
        coordinator, SensorEntityDescription(key="unhandled"), MOCK_UUID
    )
    sensor._next_prayer_index = 2
    sensor._next_prayer_time = datetime(2025, 4, 10, 12, 30)
    assert sensor.native_value is None


@pytest.mark.parametrize(
    ("translation_key", "options"),
    [("next_salat_name", PRAYER_NAMES), ("hijri_month", HIJRI_MONTHS)],
)
@pytest.mark.parametrize(
    "translation_file",
    sorted(
        (Path(__file__).parents[1] / "custom_components/mawaqit/translations").glob(
            "*.json"
        )
    ),
    ids=lambda path: path.stem,
)
def test_enum_states_translated(
    translation_file: Path, translation_key: str, options: list[str]
) -> None:
    """Test every translation file translates every state of the enum sensors."""
    translations = json.loads(translation_file.read_text(encoding="utf-8"))
    states = translations["entity"]["sensor"][translation_key]["state"]
    assert sorted(states) == sorted(options)
