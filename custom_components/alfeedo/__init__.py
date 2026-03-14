"""
Custom integration to integrate alfeedo with Home Assistant.
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from homeassistant.const import CONF_HOST, Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import async_get_loaded_integration

from .api import AlfeedoApiClient
from .const import DOMAIN, LOGGER
from .coordinator import AlfeedoDataUpdateCoordinator
from .data import AlfeedoData

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from .data import AlfeedoConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BUTTON,
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlfeedoConfigEntry,
) -> bool:
    """Set up alfeedo from a config entry."""
    coordinator = AlfeedoDataUpdateCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(seconds=30),
    )

    entry.runtime_data = AlfeedoData(
        client=AlfeedoApiClient(
            host=entry.data[CONF_HOST],
            session=async_get_clientsession(hass),
        ),
        integration=async_get_loaded_integration(hass, entry.domain),
        coordinator=coordinator,
    )

    # 1. Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    # 2. Setup platforms (Sensor, Button)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # 3. Register reload listener
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: AlfeedoConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: AlfeedoConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)
