"""Image entities of the Mawaqit integration: the picture and the logo of the mosque.

They are added when the mosque publishes them, at setup or at a later refresh.
"""

from collections.abc import Callable
from dataclasses import dataclass
from typing import override

from homeassistant.components.image import ImageEntity, ImageEntityDescription
from homeassistant.const import CONF_UUID
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
import homeassistant.util.dt as dt_util

from . import MawaqitConfigEntry
from .coordinator import PrayerTimeCoordinator
from .entity import MawaqitEntity

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class MawaqitImageEntityDescription(ImageEntityDescription):
    """Describes Mawaqit image entity."""

    get_url: Callable[[dict], str | None]


IMAGE_DESCRIPTIONS = [
    MawaqitImageEntityDescription(
        key="picture",
        translation_key="picture",
        get_url=lambda data: data.get("image") or data.get("exteriorPicture"),
    ),
    MawaqitImageEntityDescription(
        key="logo",
        translation_key="logo",
        get_url=lambda data: data.get("logo"),
    ),
]


async def async_setup_entry(
    _hass: HomeAssistant,
    config_entry: MawaqitConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the Mawaqit image platform."""
    coordinator = config_entry.runtime_data.prayer_time_coordinator
    mosque_uuid = config_entry.data[CONF_UUID]
    added_keys: set[str] = set()

    @callback
    def _async_add_published_images() -> None:
        """Add the images the mosque has started publishing."""
        if not (prayer_data := coordinator.data):
            return
        if new_descriptions := [
            desc
            for desc in IMAGE_DESCRIPTIONS
            if desc.key not in added_keys and desc.get_url(prayer_data)
        ]:
            added_keys.update(desc.key for desc in new_descriptions)
            async_add_entities(
                MawaqitImage(coordinator, desc, mosque_uuid)
                for desc in new_descriptions
            )

    _async_add_published_images()
    config_entry.async_on_unload(
        coordinator.async_add_listener(_async_add_published_images)
    )


class MawaqitImage(MawaqitEntity[PrayerTimeCoordinator], ImageEntity):
    """Representation of a picture of the mosque, served from MAWAQIT."""

    entity_description: MawaqitImageEntityDescription

    def __init__(
        self,
        coordinator: PrayerTimeCoordinator,
        description: MawaqitImageEntityDescription,
        mosque_uuid: str,
    ) -> None:
        """Initialize the image entity."""
        super().__init__(coordinator, mosque_uuid, coordinator.data)
        ImageEntity.__init__(self, coordinator.hass)
        self.entity_description = description
        self._attr_unique_id = f"{mosque_uuid}_{description.key}"
        self._attr_image_url = description.get_url(coordinator.data)
        self._attr_image_last_updated = dt_util.utcnow()

    @property
    @override
    def available(self) -> bool:
        """Return True if the mosque still publishes the image."""
        return super().available and bool(self._attr_image_url)

    @callback
    @override
    def _handle_coordinator_update(self) -> None:
        """Load the image again when the mosque changes it."""
        # The data is kept when a refresh fails.
        url = self.entity_description.get_url(self.coordinator.data)
        if url != self._attr_image_url:
            self._attr_image_url = url
            self._attr_image_last_updated = dt_util.utcnow()
            self._cached_image = None
        super()._handle_coordinator_update()
