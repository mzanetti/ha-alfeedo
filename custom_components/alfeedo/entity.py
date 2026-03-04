from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION
from .coordinator import AlfeedoDataUpdateCoordinator


class AlfeedoEntity(CoordinatorEntity[AlfeedoDataUpdateCoordinator]):
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: AlfeedoDataUpdateCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        # Individual entities should set their own unique_id; the base provides device info.
        entry_uid = (
            getattr(coordinator.config_entry, "unique_id", None)
            or coordinator.config_entry.entry_id
        )
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    coordinator.config_entry.domain,
                    entry_uid,
                ),
            },
            name=(
                coordinator.config_entry.title
                or f"{coordinator.config_entry.domain} {entry_uid}"
            ),
        )
        # Use entity naming derived from the device where possible
        self._attr_has_entity_name = True
