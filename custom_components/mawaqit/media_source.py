"""Media source with the adhans of the MAWAQIT mosque screens."""

from typing import override

from homeassistant.components.media_player import BrowseError, MediaClass, MediaType
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.translation import async_get_translations

from .const import DOMAIN

CDN_URL = "https://cdn.mawaqit.net/audio"
MIME_TYPE = "audio/mpeg"

# Voices of the mosque screens (adhanVoice), and whether the CDN has a Fajr version.
VOICES = {
    "adhan-maquah": True,
    "adhan-madina": True,
    "adhan-quds": True,
    "adhan-afassy": True,
    "adhan-algeria": True,
    "adhan-egypt": True,
    "bip": False,
}

# CDN file name -> voice, each Fajr version right after its voice.
ADHANS = {
    adhan: voice
    for voice, has_fajr in VOICES.items()
    for adhan in ((voice, f"{voice}-fajr") if has_fajr else (voice,))
}


async def async_get_media_source(_hass: HomeAssistant) -> MediaSource:
    """Set up the MAWAQIT media source."""
    return MawaqitMediaSource(DOMAIN)


class MawaqitMediaSource(MediaSource):
    """Adhans played from the MAWAQIT CDN."""

    name = "MAWAQIT"

    @override
    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve an adhan to its mp3 on the CDN."""
        if item.identifier not in ADHANS:
            raise Unresolvable(
                translation_domain=DOMAIN,
                translation_key="unknown_adhan",
                translation_placeholders={"adhan": item.identifier},
            )
        return PlayMedia(f"{CDN_URL}/{item.identifier}.mp3", MIME_TYPE)

    @override
    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Return the list of adhans, or one adhan."""
        translations = await async_get_translations(
            item.hass, item.hass.config.language, "common", {DOMAIN}
        )
        if item.identifier:
            if item.identifier not in ADHANS:
                raise BrowseError(
                    translation_domain=DOMAIN,
                    translation_key="unknown_adhan",
                    translation_placeholders={"adhan": item.identifier},
                )
            return _adhan(item.identifier, translations)

        return BrowseMediaSource(
            domain=DOMAIN,
            identifier=None,
            media_class=MediaClass.DIRECTORY,
            media_content_type=MediaType.MUSIC,
            title=self.name,
            can_play=False,
            can_expand=True,
            children_media_class=MediaClass.MUSIC,
            children=[_adhan(adhan, translations) for adhan in ADHANS],
        )


def _adhan(adhan: str, translations: dict[str, str]) -> BrowseMediaSource:
    """Return the playable item of an adhan, titled in the Home Assistant language."""
    prefix = f"component.{DOMAIN}.common."
    title = translations[prefix + ADHANS[adhan].replace("-", "_")]
    if adhan != ADHANS[adhan]:
        title = translations[prefix + "fajr_adhan"].format(adhan=title)
    return BrowseMediaSource(
        domain=DOMAIN,
        identifier=adhan,
        media_class=MediaClass.MUSIC,
        media_content_type=MIME_TYPE,
        title=title,
        can_play=True,
        can_expand=False,
    )
