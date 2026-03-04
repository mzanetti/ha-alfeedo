"""Adds config flow for Blueprint."""

from __future__ import annotations
from dis import disco

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.components import zeroconf
from homeassistant.data_entry_flow import FlowResult
from homeassistant.const import CONF_HOST
from typing import Any
from slugify import slugify

from .api import (
    AlfeedoApiClient,
    AlfeedoApiClientAuthenticationError,
    AlfeedoApiClientCommunicationError,
    AlfeedoApiClientError,
)
from .const import DOMAIN, LOGGER


class AlfeedoFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Blueprint."""

    VERSION = 1

    async def async_step_zeroconf(
        self, discovery_info: zeroconf.ZeroconfServiceInfo
    ) -> FlowResult:
        if discovery_info.properties.get("model") != "alfeedo":
            return self.async_abort(reason="not_my_device")

        unique_id = discovery_info.properties.get("hwaddr")
        await self.async_set_unique_id(unique_id)
        self._abort_if_unique_id_configured(
            updates={CONF_HOST: discovery_info.hostname.rstrip(".")}
        )

        self.context.update(
            {
                "title_placeholders": {
                    "name": discovery_info.properties.get("name", "Alfeedo")
                },
                "port": discovery_info.port,
                "host": discovery_info.hostname.rstrip("."),
            }
        )

        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery. No form fields shown, just a 'Submit' button."""
        if user_input is not None:
            return self.async_create_entry(
                title=self.context["title_placeholders"]["name"],
                data={CONF_HOST: self.context["host"]},
            )

        return self.async_show_form(
            step_id="discovery_confirm",
            description_placeholders={"name": "aaabbbccc"},
            data_schema=None,  # This removes the input fields
        )

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            try:
                await self._test_host(
                    host=user_input[CONF_HOST],
                )
            except AlfeedoApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except AlfeedoApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except AlfeedoApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(unique_id=slugify(user_input[CONF_HOST]))
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=user_input[CONF_HOST],
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=(user_input or {}).get(CONF_HOST, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_host(self, host: str) -> None:
        """Validate credentials."""
        client = AlfeedoApiClient(
            host=host,
            session=async_create_clientsession(self.hass),
        )
        await client.async_get_data()
