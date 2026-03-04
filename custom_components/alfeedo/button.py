"""Button platform for alfeedo (momentary feed action)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from .const import DOMAIN, LOGGER

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription

from .entity import AlfeedoEntity

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import AlfeedoDataUpdateCoordinator
    from .data import AlfeedoConfigEntry

ENTITY_DESCRIPTIONS = (
    ButtonEntityDescription(
        key="meal",
        name="Feed Meal",
        icon="mdi:food-drumstick-outline",
    ),
    ButtonEntityDescription(
        key="snack",
        name="Feed Snack",
        icon="mdi:food-apple-outline",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,  # noqa: ARG001 Unused function argument: `hass`
    entry: AlfeedoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    async_add_entities(
        AlfeedoButton(
            coordinator=entry.runtime_data.coordinator,
            entity_description=entity_description,
        )
        for entity_description in ENTITY_DESCRIPTIONS
    )


class AlfeedoButton(AlfeedoEntity, ButtonEntity):
    def __init__(
        self,
        coordinator: AlfeedoDataUpdateCoordinator,
        entity_description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button class."""
        super().__init__(coordinator)
        self.entity_description = entity_description

        entry_uid = (
            getattr(coordinator.config_entry, "unique_id", None)
            or coordinator.config_entry.entry_id
        )
        key = getattr(entity_description, "key", None)
        if key:
            self._attr_unique_id = f"{entry_uid}_{key}"
        else:
            self._attr_unique_id = f"{entry_uid}"

    async def async_press(self, **_: Any) -> None:
        """Press the button: trigger a feed action and refresh data."""
        client = self.coordinator.config_entry.runtime_data.client

        logging.error("AlfeedoButton: Button %s pressed", self.entity_description.key)

        mode = getattr(self.entity_description, "key", None)
        await client.async_feed(mode)

        await self.coordinator.async_start_burst_refresh()
