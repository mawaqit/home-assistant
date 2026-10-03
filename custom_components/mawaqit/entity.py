"""Base entity for the Mawaqit integration."""

from typing import override

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MAWAQIT_URL
from .coordinator import PrayerTimeCoordinator


class MawaqitEntity(CoordinatorEntity[PrayerTimeCoordinator]):
    """Defines a base Mawaqit entity, tied to the configured mosque."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: PrayerTimeCoordinator,
        mosque_uuid: str,
    ) -> None:
        """Initialize the Mawaqit entity."""
        super().__init__(coordinator)
        mosque_data = coordinator.data
        # The API returns http:// links to pages served over https.
        url = mosque_data.get("url")
        if url and url.startswith("http://"):
            url = "https://" + url.removeprefix("http://")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, mosque_uuid)},
            name=mosque_data.get("name"),
            manufacturer="MAWAQIT",
            entry_type=DeviceEntryType.SERVICE,
            # Mosques without a public page fall back to the MAWAQIT home page.
            configuration_url=url or MAWAQIT_URL,
        )

    @property
    @override
    def available(self) -> bool:
        """Return True if entity is available."""
        # The data covers the whole year: keep using it when a refresh fails.
        return self.coordinator.data is not None
