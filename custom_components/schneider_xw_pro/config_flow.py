"""Config flow for Schneider Electric Conext XW Pro integration.

Supports two modes:
1. Auto-discovery: Scans all known Modbus slave address ranges to find devices.
2. Manual: User manually specifies device type and slave address.

NOTE: Modbus TCP has NO authentication per the official protocol spec.
The gateway/InsightHome web UI may have a login, but the Modbus port (502/503)
is unauthenticated by design.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    ALL_SCAN_RANGES,
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
    DEVICE_TYPE_LABELS,
    DOMAIN,
)
from .modbus_client import SchneiderModbusClient

_LOGGER = logging.getLogger(__name__)

# Timeout per slave probe (seconds) — devices on local LAN respond fast
_PROBE_TIMEOUT = 1.0

# Max addresses to scan per range. Schneider spec says devices are assigned
# sequentially starting from the range start, so we only need to scan a few.
_MAX_SCAN_PER_RANGE = 5


class SchneiderXWProConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Schneider XW Pro."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize."""
        self._host: str = ""
        self._port: int = DEFAULT_PORT
        self._scan_interval: int = DEFAULT_SCAN_INTERVAL
        self._devices: list[dict[str, Any]] = []
        self._discovered_devices: list[dict[str, Any]] = []
        self._client: SchneiderModbusClient | None = None

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

            # Prevent duplicate entries for the same gateway
            unique_id = f"schneider_xw_pro_{self._host}_{self._port}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            # Test connection and validate by reading gateway device name
            client = SchneiderModbusClient(self._host, self._port)
            try:
                connected = await client.connect()
                if connected:
                    # Validate the connection by reading the gateway's device name
                    device_name = await client.read_device_name(slave_id=1)
                    if device_name:
                        _LOGGER.info(
                            "Connected to gateway: %s at %s:%s",
                            device_name,
                            self._host,
                            self._port,
                        )
                    else:
                        _LOGGER.warning(
                            "Connected to %s:%s but could not read gateway device name. "
                            "Proceeding anyway.",
                            self._host,
                            self._port,
                        )
                    self._client = client
                    # Proceed to discovery step
                    return await self.async_step_discover()
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Error testing connection")
                errors["base"] = "cannot_connect"

            # Disconnect on failure
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

    async def async_step_discover(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Auto-discover devices by scanning known Modbus slave address ranges.

        Uses Device Name register (0x0000) as universal probe — it exists on ALL
        Schneider Conext device types. Only scans the first few addresses per
        range since the spec says devices are assigned sequentially.
        """
        if user_input is not None:
            # User chose to use discovered devices or skip to manual
            if user_input.get("use_discovered", True) and self._discovered_devices:
                self._devices = list(self._discovered_devices)
                return self._create_entry()
            # User wants to manually add devices
            return await self.async_step_devices()

        # Perform the scan
        assert self._client is not None
        self._discovered_devices = []

        for device_type, start_addr, end_addr in ALL_SCAN_RANGES:
            # Only scan first _MAX_SCAN_PER_RANGE addresses per range.
            # Per Schneider spec, devices are assigned sequentially from
            # the range start, so if address N has no device, N+1 won't either.
            scan_end = min(start_addr + _MAX_SCAN_PER_RANGE - 1, end_addr)
            found_gap = False
            for slave_id in range(start_addr, scan_end + 1):
                if found_gap:
                    break
                try:
                    name = await asyncio.wait_for(
                        self._client.probe_slave(slave_id),
                        timeout=_PROBE_TIMEOUT,
                    )
                except asyncio.TimeoutError:
                    found_gap = True
                    continue

                if name:
                    device_label = DEVICE_TYPE_LABELS.get(device_type, device_type)

                    self._discovered_devices.append(
                        {
                            CONF_DEVICE_TYPE: device_type,
                            CONF_DEVICE_NAME: name,
                            CONF_SLAVE_ID: slave_id,
                        }
                    )
                    _LOGGER.info(
                        "Discovered device: %s (type=%s, slave=%d)",
                        name,
                        device_type,
                        slave_id,
                    )
                else:
                    # No device at this address, stop scanning this range
                    found_gap = True

        if self._discovered_devices:
            # Show discovered devices and let user confirm
            device_list = "\n".join(
                f"- {d[CONF_DEVICE_NAME]} ({DEVICE_TYPE_LABELS.get(d[CONF_DEVICE_TYPE], d[CONF_DEVICE_TYPE])}, slave {d[CONF_SLAVE_ID]})"
                for d in self._discovered_devices
            )
            return self.async_show_form(
                step_id="discover",
                data_schema=vol.Schema(
                    {
                        vol.Required("use_discovered", default=True): bool,
                    }
                ),
                description_placeholders={
                    "device_count": str(len(self._discovered_devices)),
                    "device_list": device_list,
                },
            )
        else:
            # No devices found, fall back to manual
            _LOGGER.warning(
                "No devices discovered on %s:%s. Falling back to manual setup.",
                self._host,
                self._port,
            )
            return await self.async_step_devices()

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle adding devices manually."""
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

        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_DEVICE_TYPE): vol.In(DEVICE_TYPE_LABELS),
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
        # Clean up the client - it will be re-created during setup
        if self._client is not None:
            self.hass.async_create_task(self._client.disconnect())

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
