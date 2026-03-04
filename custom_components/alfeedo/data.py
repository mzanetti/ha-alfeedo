"""Custom types for alfeedo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import AlfeedoApiClient
    from .coordinator import AlfeedoDataUpdateCoordinator


type AlfeedoConfigEntry = ConfigEntry[AlfeedoData]


@dataclass
class AlfeedoData:
    """Data for the Alfeedo integration."""

    client: AlfeedoApiClient
    coordinator: AlfeedoDataUpdateCoordinator
    integration: Integration
