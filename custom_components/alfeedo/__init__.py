"""
Custom integration to integrate alfeedo with Home Assistant.

For more details about this integration, please refer to
https://github.com/mzanetti/ha-alfeedo
"""

from __future__ import annotations

from datetime import timedelta
from typing import TYPE_CHECKING

from anyio import Path
from homeassistant.const import CONF_HOST, Platform
from homeassistant.const import __version__ as HA_VERSION
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.loader import _LOGGER, async_get_loaded_integration
from homeassistant.components.http import StaticPathConfig
from homeassistant.components.frontend import add_extra_js_url
from homeassistant.util import package
from awesomeversion import AwesomeVersion

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

URL_BASE = "/alfeedo/ui"
CARD_FILENAME = "alfeedo-card.js"


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(
    hass: HomeAssistant,
    entry: AlfeedoConfigEntry,
) -> bool:
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

    frontend_path = Path(__file__).parent / "card"
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path=URL_BASE, path=str(frontend_path), cache_headers=True
            )
        ]
    )
    add_extra_js_url(hass, f"{URL_BASE}/{CARD_FILENAME}")

    # https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    await update_lovelace_resources(hass)

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


async def update_lovelace_resources(hass):
    lovelace_data = hass.data.get("lovelace")
    if not lovelace_data:
        return

    if is_new_lovelace():
        resources = lovelace_data.resources
    else:
        resources = lovelace_data.get("resources")

    if resources is None:
        return

    url = f"{URL_BASE}/{CARD_FILENAME}"

    # Check if already registered
    if not any(res.get("url") == url for res in resources.async_items()):
        _LOGGER.info("Registering Alfeedo card resource")
        await resources.async_create_item(
            {
                "res_type": "module",
                "url": url,
            }
        )


def is_new_lovelace():
    return AwesomeVersion(HA_VERSION) >= AwesomeVersion("2025.2.0")
