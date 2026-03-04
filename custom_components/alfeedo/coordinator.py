"""DataUpdateCoordinator for alfeedo."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Coroutine
from datetime import timedelta
from logging import Logger
from typing import TYPE_CHECKING, Any
import asyncio

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.debounce import Debouncer
from homeassistant.helpers.typing import UNDEFINED, UndefinedType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    AlfeedoApiClientAuthenticationError,
    AlfeedoApiClientError,
)

if TYPE_CHECKING:
    from .data import AlfeedoConfigEntry


# https://developers.home-assistant.io/docs/integration_fetching_data#coordinated-single-api-poll-for-data-for-all-entities
class AlfeedoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: AlfeedoConfigEntry

    _burst_task: asyncio.Task | None = None

    async def async_start_burst_refresh(self, seconds: int = 15):
        if self._burst_task:
            self._burst_task.cancel()
        self.update_interval = timedelta(seconds=1)
        await self.async_request_refresh()

        async def _reset_after_delay():
            await asyncio.sleep(seconds)
            self.update_interval = timedelta(seconds=30)
            await self.async_request_refresh()
            self._burst_task = None

        self._burst_task = self.hass.async_create_task(_reset_after_delay())

    async def _async_update_data(self) -> Any:
        try:
            return await self.config_entry.runtime_data.client.async_get_data()
        except AlfeedoApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except AlfeedoApiClientError as exception:
            raise UpdateFailed(exception) from exception
