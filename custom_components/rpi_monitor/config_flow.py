"""Config flow and Options flow for Raspberry Pi Monitor."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DISPLAY_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_DISPLAY_NAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
    MAX_UPDATE_INTERVAL,
    MIN_UPDATE_INTERVAL,
)


class RpiMonitorConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the initial setup config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle setup initiated by the user."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}

        if user_input is not None:
            interval = user_input.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)
            if not (MIN_UPDATE_INTERVAL <= interval <= MAX_UPDATE_INTERVAL):
                errors[CONF_UPDATE_INTERVAL] = "invalid_interval"
            else:
                return self.async_create_entry(
                    title=user_input.get(CONF_DISPLAY_NAME, DEFAULT_DISPLAY_NAME),
                    data={
                        CONF_DISPLAY_NAME: user_input[CONF_DISPLAY_NAME],
                        CONF_UPDATE_INTERVAL: interval,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DISPLAY_NAME, default=DEFAULT_DISPLAY_NAME): str,
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=DEFAULT_UPDATE_INTERVAL
                    ): vol.All(
                        int,
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> RpiMonitorOptionsFlow:
        return RpiMonitorOptionsFlow(config_entry)


class RpiMonitorOptionsFlow(OptionsFlow):
    """Allow changing the update interval after setup."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        current_interval = self._config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            self._config_entry.data.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL),
        )

        if user_input is not None:
            interval = user_input.get(CONF_UPDATE_INTERVAL, current_interval)
            if not (MIN_UPDATE_INTERVAL <= interval <= MAX_UPDATE_INTERVAL):
                errors[CONF_UPDATE_INTERVAL] = "invalid_interval"
            else:
                return self.async_create_entry(
                    title="",
                    data={CONF_UPDATE_INTERVAL: interval},
                )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL, default=current_interval
                    ): vol.All(
                        int,
                        vol.Range(min=MIN_UPDATE_INTERVAL, max=MAX_UPDATE_INTERVAL),
                    ),
                }
            ),
            errors=errors,
        )
