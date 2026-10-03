"""Tests for the Mawaqit sensor platform."""

from collections.abc import Generator
from datetime import datetime
import time
from unittest.mock import MagicMock

from freezegun import freeze_time
from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.mawaqit.coordinator import PrayerTimeCoordinator
from custom_components.mawaqit.sensor import (
    PRAYER_TIME_SENSOR_DESCRIPTIONS,
    MawaqitPrayerTimeSensor,
    MawaqitPrayerTimeSensorEntityDescription,
    NextPrayerSensor,
)
from homeassistant.components.sensor import SensorDeviceClass, SensorEntityDescription
from homeassistant.core import HomeAssistant

from .conftest import MOCK_UUID, build_prayer_data

# ---------------------------------------------------------------------------
# Sensor setup tests
# ---------------------------------------------------------------------------


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    ("prayer_data_kwargs", "expected_count"),
    [
        ({}, 15),  # 6 prayers + 2 jumua + 5 iqama + 2 next = 15
        ({"iqama_enabled": False}, 10),  # no iqama sensors
        ({"with_iqama_calendar": False}, 10),  # no iqama sensors
        ({"jumua2": None}, 14),  # only 1 Jumua
        ({"jumua3": "15:00"}, 16),  # 3 Jumua prayers
        ({"jumua2": None, "iqama_enabled": False}, 9),  # 1 Jumua, no iqama
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
        ({}, "sensor.fajr_iqama", True),
        ({"iqama_enabled": False}, "sensor.fajr_iqama", False),
        ({"with_iqama_calendar": False}, "sensor.fajr_iqama", False),
        ({}, "sensor.jumua_prayer", True),
        ({"jumua": None}, "sensor.jumua_prayer", False),
        ({}, "sensor.second_jumua_prayer", True),
        ({"jumua2": None}, "sensor.second_jumua_prayer", False),
        ({"jumua3": "15:00"}, "sensor.third_jumua_prayer", True),
        ({"jumua3": None}, "sensor.third_jumua_prayer", False),
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
    """Test that Jumua and iqama sensors are created only when the API reports them."""
    await setup_mawaqit_integration(
        prayer_data=build_prayer_data(fill_all_months=False, **prayer_data_kwargs)
    )
    assert (hass.states.get(entity_id) is not None) == should_exist


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    ("coordinator_attr", "entity_id"),
    [
        ("prayer_time_coordinator", "sensor.fajr_prayer"),
        ("prayer_time_coordinator", "sensor.next_salat_name"),
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

    state = hass.states.get("sensor.fajr_prayer")
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

    name_state = hass.states.get("sensor.next_salat_name")
    assert name_state is not None
    assert name_state.state == "dhuhr"

    time_state = hass.states.get("sensor.next_salat_time")
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
    assert hass.states.get("sensor.next_salat_name").state == "dhuhr"

    freezer.move_to("2025-04-10 12:30:01+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.next_salat_name").state == "asr"


async def test_prayer_sensors_move_to_next_day_at_islamic_midnight(
    hass: HomeAssistant,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test prayer times switch day at Islamic midnight, not at the next API refresh."""
    prayer_data = build_prayer_data()
    prayer_data["calendar"][3]["11"][1] = "06:43"  # Shuruq, 06:45 the day before
    entity_ids = ("sensor.fajr_prayer", "sensor.shuruq", "sensor.fajr_iqama")

    # Isha at 20:00 and Fajr at 05:30: Islamic midnight is at 00:45.
    freezer.move_to("2025-04-10 20:30:00+02:00")
    await setup_mawaqit_integration(prayer_data=prayer_data)

    freezer.move_to("2025-04-11 00:44:59+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert [hass.states.get(entity_id).state for entity_id in entity_ids] == [
        "2025-04-10T03:30:00+00:00",
        "2025-04-10T04:45:00+00:00",
        "2025-04-10T03:40:00+00:00",
    ]

    freezer.move_to("2025-04-11 00:45:00+02:00")
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert [hass.states.get(entity_id).state for entity_id in entity_ids] == [
        "2025-04-11T03:30:00+00:00",
        "2025-04-11T04:43:00+00:00",
        "2025-04-11T03:40:00+00:00",
    ]


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

    state = hass.states.get("sensor.next_salat_name")
    assert state is not None
    assert state.state == "unknown"


@freeze_time("2025-04-10 12:00:00+02:00")
@pytest.mark.parametrize(
    "entity_id",
    ["sensor.fajr_prayer", "sensor.shuruq", "sensor.jumua_prayer"],
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
                "sensor.fajr_prayer": "2025-01-15T04:30:00+00:00",
                "sensor.shuruq": "2025-01-15T05:45:00+00:00",
                "sensor.asr_iqama": "2025-01-15T14:55:00+00:00",
                "sensor.jumua_prayer": "2025-01-17T12:00:00+00:00",
                "sensor.next_salat_time": "2025-01-15T11:30:00+00:00",
            },
        ),
        (
            "2025-07-15 11:00:00+02:00",
            {
                "sensor.fajr_prayer": "2025-07-15T03:30:00+00:00",
                "sensor.shuruq": "2025-07-15T04:45:00+00:00",
                "sensor.asr_iqama": "2025-07-15T13:55:00+00:00",
                "sensor.jumua_prayer": "2025-07-18T11:00:00+00:00",
                "sensor.next_salat_time": "2025-07-15T10:30:00+00:00",
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
    coordinator.data = None
    sensor = sensor_cls(coordinator, *extra_args)
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
    sensor = NextPrayerSensor(
        coordinator, SensorEntityDescription(key="unhandled"), MOCK_UUID
    )
    sensor._next_prayer_index = 2
    sensor._next_prayer_time = datetime(2025, 4, 10, 12, 30)
    assert sensor.native_value is None
