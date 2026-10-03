"""Tests for the Mawaqit adhan media source."""

import pytest

from homeassistant.components import media_source
from homeassistant.components.media_player import BrowseError, MediaClass
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

ROOT = "media-source://mawaqit"


@pytest.fixture(autouse=True)
async def setup_media_source(hass: HomeAssistant, setup_mawaqit_integration) -> None:
    """Set up the integration and the media source component."""
    await setup_mawaqit_integration()
    assert await async_setup_component(hass, media_source.DOMAIN, {})
    # Older Home Assistant releases load media source platforms in a background task.
    await hass.async_block_till_done()


async def test_media_source_is_listed(hass: HomeAssistant) -> None:
    """Test MAWAQIT appears among the media sources."""
    root = await media_source.async_browse_media(hass, None)

    assert ROOT in [child.media_content_id for child in root.children]


async def test_browse_adhans(hass: HomeAssistant) -> None:
    """Test the media source lists every voice, each followed by its Fajr version."""
    browse = await media_source.async_browse_media(hass, ROOT)

    assert browse.title == "MAWAQIT"
    assert browse.can_expand
    assert not browse.can_play
    assert [(child.identifier, child.title) for child in browse.children] == [
        ("adhan-maquah", "Adhan of Makkah"),
        ("adhan-maquah-fajr", "Adhan of Makkah (Fajr)"),
        ("adhan-madina", "Adhan of Madinah"),
        ("adhan-madina-fajr", "Adhan of Madinah (Fajr)"),
        ("adhan-quds", "Adhan of Al-Quds"),
        ("adhan-quds-fajr", "Adhan of Al-Quds (Fajr)"),
        ("adhan-afassy", "Adhan by Al-Afassy"),
        ("adhan-afassy-fajr", "Adhan by Al-Afassy (Fajr)"),
        ("adhan-algeria", "Adhan of Algeria"),
        ("adhan-algeria-fajr", "Adhan of Algeria (Fajr)"),
        ("adhan-egypt", "Adhan of Egypt"),
        ("adhan-egypt-fajr", "Adhan of Egypt (Fajr)"),
        ("bip", "Beep"),
    ]
    for child in browse.children:
        assert child.can_play
        assert not child.can_expand
        assert child.media_class == MediaClass.MUSIC
        assert child.media_content_type == "audio/mpeg"


async def test_browse_adhans_translated(hass: HomeAssistant) -> None:
    """Test the adhans are titled in the Home Assistant language."""
    hass.config.language = "fr"

    browse = await media_source.async_browse_media(hass, ROOT)

    assert [child.title for child in browse.children[:2]] == [
        "Adhan de La Mecque",
        "Adhan de La Mecque (Fajr)",
    ]


async def test_browse_one_adhan(hass: HomeAssistant) -> None:
    """Test browsing an adhan returns it."""
    browse = await media_source.async_browse_media(hass, f"{ROOT}/adhan-egypt-fajr")

    assert browse.title == "Adhan of Egypt (Fajr)"
    assert browse.can_play


async def test_browse_unknown_adhan(hass: HomeAssistant) -> None:
    """Test browsing an unknown adhan fails."""
    with pytest.raises(BrowseError, match="Unknown adhan: bip-fajr"):
        await media_source.async_browse_media(hass, f"{ROOT}/bip-fajr")


@pytest.mark.parametrize(
    ("adhan", "url"),
    [
        ("adhan-maquah", "https://cdn.mawaqit.net/audio/adhan-maquah.mp3"),
        ("adhan-egypt-fajr", "https://cdn.mawaqit.net/audio/adhan-egypt-fajr.mp3"),
        ("bip", "https://cdn.mawaqit.net/audio/bip.mp3"),
    ],
)
async def test_resolve_adhan(hass: HomeAssistant, adhan: str, url: str) -> None:
    """Test an adhan resolves to its mp3 on the MAWAQIT CDN."""
    media = await media_source.async_resolve_media(hass, f"{ROOT}/{adhan}", None)

    assert media.url == url
    assert media.mime_type == "audio/mpeg"


@pytest.mark.parametrize(
    "media_id", [f"{ROOT}/hayya-ala-assalat", f"{ROOT}/custom", ROOT]
)
async def test_resolve_unknown_adhan(hass: HomeAssistant, media_id: str) -> None:
    """Test an unknown adhan, or the folder of adhans, cannot be played."""
    with pytest.raises(media_source.Unresolvable, match="Unknown adhan"):
        await media_source.async_resolve_media(hass, media_id, None)
