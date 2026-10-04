"""Base entity for the Mawaqit integration."""

from typing import Any, override

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MAWAQIT_URL
from .coordinator import MawaqitCoordinator


class MawaqitEntity[_CoordinatorT: MawaqitCoordinator[Any]](
    CoordinatorEntity[_CoordinatorT]
):
    """Defines a base Mawaqit entity, tied to the configured mosque."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: _CoordinatorT,
        mosque_uuid: str,
        mosque_data: dict,
    ) -> None:
        """Initialize the Mawaqit entity, with the prayer times of its mosque."""
        super().__init__(coordinator)
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
        # Keep using the last data when a refresh fails.
        return self.coordinator.data is not None
