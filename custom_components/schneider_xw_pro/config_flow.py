"""Config flow for Schneider Electric Conext XW Pro integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
    CONF_DEVICES,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ADDRESSES,
    DEVICE_TYPE_AGS,
    DEVICE_TYPE_BATTERY_MONITOR,
    DEVICE_TYPE_GATEWAY,
    DEVICE_TYPE_LABELS,
    DEVICE_TYPE_MPPT,
    DEVICE_TYPE_SCP,
    DEVICE_TYPE_XW_PRO,
    DOMAIN,
)
from .modbus_client import SchneiderModbusClient

_LOGGER = logging.getLogger(__name__)


class SchneiderXWProConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Schneider XW Pro."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._host: str = ""
        self._port: int = DEFAULT_PORT
        self._scan_interval: int = DEFAULT_SCAN_INTERVAL
        self._devices: list[dict[str, Any]] = []

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow handler."""
        return SchneiderXWProOptionsFlow(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step: gateway connection details."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._host = user_input[CONF_HOST]
            self._port = user_input.get(CONF_PORT, DEFAULT_PORT)
            self._scan_interval = user_input.get(
                CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
            )

            # Test connection
            client = SchneiderModbusClient(self._host, self._port)
            try:
                connected = await client.connect()
                if connected:
                    return await self.async_step_devices()
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Error testing connection")
                errors["base"] = "cannot_connect"
            finally:
                await client.disconnect()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.Coerce(int),
                }
            ),
            errors=errors,
            description_placeholders={
                "default_port": str(DEFAULT_PORT),
            },
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding devices."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device_type = user_input[CONF_DEVICE_TYPE]
            device = {
                CONF_DEVICE_TYPE: device_type,
                CONF_DEVICE_NAME: user_input.get(
                    CONF_DEVICE_NAME, DEVICE_TYPE_LABELS[device_type]
                ),
                CONF_SLAVE_ID: user_input.get(
                    CONF_SLAVE_ID, DEFAULT_SLAVE_ADDRESSES.get(device_type, 10)
                ),
            }
            self._devices.append(device)

            # Ask if they want to add more devices
            return await self.async_step_add_another()

        device_type_options = {k: v for k, v in DEVICE_TYPE_LABELS.items()}

        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_TYPE): vol.In(device_type_options),
                    vol.Optional(CONF_DEVICE_NAME, default=""): str,
                    vol.Optional(CONF_SLAVE_ID, default=10): vol.Coerce(int),
                }
            ),
            errors=errors,
        )

    async def async_step_add_another(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask if user wants to add another device."""
        if user_input is not None:
            if user_input.get("add_another", False):
                return await self.async_step_devices()
            # Done adding devices, create the entry
            return self._create_entry()

        return self.async_show_form(
            step_id="add_another",
            data_schema=vol.Schema(
                {
                    vol.Required("add_another", default=False): bool,
                }
            ),
            description_placeholders={
                "device_count": str(len(self._devices)),
            },
        )

    def _create_entry(self) -> FlowResult:
        """Create the config entry."""
        title = f"Schneider XW Pro ({self._host}:{self._port})"

        return self.async_create_entry(
            title=title,
            data={
                CONF_HOST: self._host,
                CONF_PORT: self._port,
                CONF_SCAN_INTERVAL: self._scan_interval,
                CONF_DEVICES: self._devices,
            },
        )


class SchneiderXWProOptionsFlow(OptionsFlow):
    """Handle options flow for Schneider XW Pro."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = self._config_entry.data

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.Coerce(int),
                }
            ),
        )
