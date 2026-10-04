"""Tests for the automation blueprints of blueprints/automation/mawaqit."""

import asyncio
from datetime import timedelta
from pathlib import Path
import shutil
from typing import Any
from urllib.parse import quote

from freezegun.api import FrozenDateTimeFactory
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_mock_service,
)

from homeassistant.components.automation import DOMAIN as AUTOMATION_DOMAIN
from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.setup import async_setup_component
import homeassistant.util.dt as dt_util

ROOT = Path(__file__).parent.parent
BLUEPRINTS = ROOT / "blueprints/automation/mawaqit"
CALENDAR = "calendar.test_mosque_prayer_times"
PLAYERS = ["media_player.living_room", "media_player.kitchen"]
# A Thursday: the test data has Dhuhr at 12:30 and its iqama at 12:45.
THURSDAY = "2025-04-10 12:00:00+02:00"


@pytest.fixture
def expected_lingering_timers() -> bool:
    """Let the calendar triggers wait for the next events after a test."""
    return True


@pytest.fixture(autouse=True)
async def mosque(
    hass: HomeAssistant,
    tmp_path: Path,
    setup_mawaqit_integration,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Set up the mosque, with the blueprints in the configuration directory."""
    await hass.config.async_set_time_zone("Europe/Paris")
    hass.config.config_dir = str(tmp_path)
    shutil.copytree(BLUEPRINTS, tmp_path / "blueprints/automation/mawaqit")
    freezer.move_to(THURSDAY)
    await setup_mawaqit_integration()


async def use_blueprint(hass: HomeAssistant, name: str, **inputs: Any) -> None:
    """Create an automation from a blueprint."""
    assert await async_setup_component(
        hass,
        AUTOMATION_DOMAIN,
        {
            AUTOMATION_DOMAIN: {
                "use_blueprint": {
                    "path": f"mawaqit/{name}.yaml",
                    "input": {"calendar": CALENDAR, **inputs},
                }
            }
        },
    )
    await hass.async_block_till_done()
    automations = hass.states.async_all(AUTOMATION_DOMAIN)
    assert [state.state for state in automations] == [STATE_ON]


async def move_to(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory, time: str, *, wait: bool = True
) -> None:
    """Move the clock forward to a time, minute by minute, and run what is due.

    Without waiting, automations waiting in a delay are not awaited.
    """
    # The calendar trigger reads the events 15 minutes ahead, so the clock cannot jump.
    target = dt_util.parse_datetime(time) + timedelta(seconds=1)
    while (now := dt_util.utcnow()) < target:
        freezer.move_to(min(now + timedelta(minutes=1), target))
        async_fire_time_changed(hass)
        if wait:
            await hass.async_block_till_done()
        else:
            for _ in range(10):
                await asyncio.sleep(0)


def test_all_blueprints_tested() -> None:
    """Test every blueprint has tests below."""
    assert sorted(path.stem for path in BLUEPRINTS.glob("*.yaml")) == [
        "adhan",
        "pause_media_during_prayer",
        "prayer_actions",
        "prayer_notification",
    ]


@pytest.mark.parametrize(
    "path", sorted(BLUEPRINTS.glob("*.yaml")), ids=lambda p: p.stem
)
def test_blueprint_links(path: Path) -> None:
    """Test each blueprint links to itself and is imported from every README."""
    url = (
        f"https://github.com/mawaqit/home-assistant/blob/main/{path.relative_to(ROOT)}"
    )
    assert f"source_url: {url}\n" in path.read_text()
    for readme in ROOT.glob("README*.md"):
        assert f"blueprint_url={quote(url, safe='')})" in readme.read_text(), (
            readme.name
        )


async def test_adhan(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Test the adhan plays at the chosen prayers, with its Fajr version."""
    play = async_mock_service(hass, "media_player", "play_media")
    volume = async_mock_service(hass, "media_player", "volume_set")
    await use_blueprint(hass, "adhan", media_players=PLAYERS, volume=40)

    await move_to(hass, freezer, "2025-04-10 12:30:00+02:00")
    assert [call.data for call in play] == [
        {
            "entity_id": PLAYERS,
            "media_content_id": "media-source://mawaqit/adhan-maquah",
            "media_content_type": "audio/mpeg",
        }
    ]
    assert [call.data for call in volume] == [
        {"entity_id": PLAYERS, "volume_level": 0.4}
    ]


async def test_adhan_fajr(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Test Fajr has its own adhan, and the volume is kept by default."""
    freezer.move_to("2025-04-11 05:00:00+02:00")
    play = async_mock_service(hass, "media_player", "play_media")
    volume = async_mock_service(hass, "media_player", "volume_set")
    await use_blueprint(
        hass,
        "adhan",
        media_players=PLAYERS[:1],
        fajr_adhan="media-source://mawaqit/adhan-afassy-fajr",
    )

    await move_to(hass, freezer, "2025-04-11 05:30:00+02:00")
    assert [call.data["media_content_id"] for call in play] == [
        "media-source://mawaqit/adhan-afassy-fajr"
    ]
    assert volume == []

    # Shuruq is not chosen.
    await move_to(hass, freezer, "2025-04-11 06:45:00+02:00")
    assert len(play) == 1


async def test_adhan_jumua(hass: HomeAssistant, freezer: FrozenDateTimeFactory) -> None:
    """Test each Jumua of a Friday plays the adhan when Jumua is chosen."""
    freezer.move_to("2025-04-11 12:50:00+02:00")
    play = async_mock_service(hass, "media_player", "play_media")
    await use_blueprint(hass, "adhan", media_players=PLAYERS, prayers=["Jumua"])

    await move_to(hass, freezer, "2025-04-11 13:00:00+02:00")
    await move_to(hass, freezer, "2025-04-11 14:00:00+02:00")
    assert len(play) == 2


async def test_notification_before_iqama(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test a notification 5 minutes before the iqama, to a phone and an entity."""
    phone_entry = MockConfigEntry(domain="mobile_app")
    phone_entry.add_to_hass(hass)
    phone = dr.async_get(hass).async_get_or_create(
        config_entry_id=phone_entry.entry_id,
        identifiers={("mobile_app", "phone")},
        name="My Phone",
    )
    mobile = async_mock_service(hass, "notify", "mobile_app_my_phone")
    send = async_mock_service(hass, "notify", "send_message")
    await use_blueprint(
        hass,
        "prayer_notification",
        moment="end",
        offset=-5,
        mobile_devices=[phone.id],
        notify_entities=["notify.kitchen_display"],
    )

    await move_to(hass, freezer, "2025-04-10 12:40:00+02:00")
    notification = {"title": "Dhuhr", "message": "Iqama Dhuhr at 12:45"}
    assert [call.data for call in mobile] == [notification]
    assert [call.data for call in send] == [
        {"entity_id": ["notify.kitchen_display"], **notification}
    ]


async def test_notification_at_adhan_with_custom_text(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test a notification at the adhan, without iqama, with a custom text."""
    send = async_mock_service(hass, "notify", "send_message")
    await use_blueprint(
        hass,
        "prayer_notification",
        prayers=["Shuruq"],
        notify_entities=["notify.kitchen_display"],
        title="Sunrise",
        message="{{ prayer }} is at {{ time }}, the time of Fajr is over",
    )

    await move_to(hass, freezer, "2025-04-11 06:45:00+02:00")
    assert [call.data for call in send] == [
        {
            "entity_id": ["notify.kitchen_display"],
            "title": "Sunrise",
            "message": "Shuruq is at 06:45, the time of Fajr is over",
        }
    ]


async def test_no_notification_at_iqama_without_iqama(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test no notification at the iqama of a prayer that has none."""
    send = async_mock_service(hass, "notify", "send_message")
    await use_blueprint(
        hass,
        "prayer_notification",
        prayers=["Shuruq"],
        moment="end",
        notify_entities=["notify.kitchen_display"],
    )

    await move_to(hass, freezer, "2025-04-11 06:45:00+02:00")
    assert send == []


async def test_prayer_actions(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test the actions run before a time of the night, with the prayer name."""
    calls: list[ServiceCall] = async_mock_service(hass, "test", "automation")
    await use_blueprint(
        hass,
        "prayer_actions",
        prayers=["Start of the last third", "Fajr"],
        offset=-20,
        actions=[{"action": "test.automation", "data": {"prayer": "{{ prayer }}"}}],
    )

    # The night from Maghrib at 18:30 to Fajr at 05:30 has its last third at 01:50.
    await move_to(hass, freezer, "2025-04-11 01:30:00+02:00")
    await move_to(hass, freezer, "2025-04-11 05:10:00+02:00")
    assert [call.data for call in calls] == [
        {"prayer": "Start of the last third"},
        {"prayer": "Fajr"},
    ]


async def test_pause_media_during_prayer(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test the playing media players pause at the adhan and resume after the iqama."""
    pause = async_mock_service(hass, "media_player", "media_pause")
    play = async_mock_service(hass, "media_player", "media_play")
    hass.states.async_set(PLAYERS[0], "playing")
    hass.states.async_set(PLAYERS[1], "idle")
    await use_blueprint(hass, "pause_media_during_prayer", media_players=PLAYERS)

    await move_to(hass, freezer, "2025-04-10 12:30:00+02:00", wait=False)
    assert [call.data for call in pause] == [{"entity_id": PLAYERS[:1]}]
    hass.states.async_set(PLAYERS[0], "paused")

    # The iqama is at 12:45, and the players resume 10 minutes later.
    await move_to(hass, freezer, "2025-04-10 12:54:00+02:00", wait=False)
    assert play == []
    await move_to(hass, freezer, "2025-04-10 12:55:00+02:00")
    assert [call.data for call in play] == [{"entity_id": PLAYERS[:1]}]


async def test_pause_media_nothing_playing(
    hass: HomeAssistant, freezer: FrozenDateTimeFactory
) -> None:
    """Test nothing happens when no media player is playing."""
    pause = async_mock_service(hass, "media_player", "media_pause")
    hass.states.async_set(PLAYERS[0], "idle")
    await use_blueprint(hass, "pause_media_during_prayer", media_players=PLAYERS[:1])

    await move_to(hass, freezer, "2025-04-10 12:30:00+02:00")
    assert pause == []
