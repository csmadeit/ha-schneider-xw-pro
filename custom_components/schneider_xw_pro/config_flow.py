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
    CONF_REGISTER_TYPE,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID,
    DEFAULT_PORT,
    DEFAULT_REGISTER_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE_ADDRESSES,
    DEVICE_TYPE_LABELS,
    DOMAIN,
    REGISTER_TYPE_LABELS,
)
from .modbus_client import SchneiderModbusClient

_LOGGER = logging.getLogger(__name__)

# Modbus response timeout for discovery probes (seconds).
# The Schneider Conext Gateway is embedded hardware; 10s is safe.
# The proven conext-api project uses 30s — we use 10s as a compromise.
_DISCOVERY_TIMEOUT = 10

# Delay between probes in seconds.  The gateway has limited TCP resources;
# opening/closing connections too fast can overwhelm it.
_PROBE_DELAY = 0.15

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
        self._register_type: str = DEFAULT_REGISTER_TYPE
        self._devices: list[dict[str, Any]] = []
        self._discovered_devices: list[dict[str, Any]] = []
        self._reconfigure_entry: ConfigEntry | None = None

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
            self._register_type = user_input.get(
                CONF_REGISTER_TYPE, DEFAULT_REGISTER_TYPE
            )

            # Check for existing entry with same gateway.
            # Instead of aborting with "already configured", we allow
            # re-discovery so users can add/update devices without
            # removing the entire installation.
            unique_id = f"schneider_xw_pro_{self._host}_{self._port}"
            await self.async_set_unique_id(unique_id)
            for entry in self._async_current_entries():
                if entry.unique_id == unique_id:
                    self._reconfigure_entry = entry
                    break

            # Validate the gateway is reachable by probing slave 1
            # using a fresh connection (open -> read -> close).
            # The Schneider Gateway is embedded hardware with limited TCP
            # resources.  A fresh connection per probe is the only
            # reliable pattern (matches the proven conext-api project).
            try:
                gateway_name = await SchneiderModbusClient.probe_slave_fresh(
                    self._host, self._port, slave_id=1,
                    timeout=_DISCOVERY_TIMEOUT,
                )
                if gateway_name:
                    _LOGGER.info(
                        "Connected to gateway: %s at %s:%s",
                        gateway_name, self._host, self._port,
                    )
                else:
                    _LOGGER.warning(
                        "TCP connect to %s:%s succeeded but could not "
                        "read gateway device name (slave 1). Will still "
                        "attempt discovery on other slave addresses.",
                        self._host, self._port,
                    )
                # Proceed to discovery step — no persistent client needed
                return await self.async_step_discover()
            except Exception:
                _LOGGER.exception(
                    "Error testing connection to %s:%s",
                    self._host, self._port,
                )
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Optional(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
                    vol.Optional(
                        CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_REGISTER_TYPE, default=DEFAULT_REGISTER_TYPE
                    ): vol.In(REGISTER_TYPE_LABELS),
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

        # Perform the scan using a FRESH TCP connection per probe.
        # The Schneider Conext Gateway is embedded hardware with limited
        # TCP resources.  Re-using a single persistent connection for
        # rapid-fire probes across many slave IDs overwhelms the gateway
        # and causes it to stop responding.  Opening a new connection per
        # probe (with a small delay between probes) mirrors the proven
        # conext-api project (pyModbusTCP auto_open/auto_close pattern).
        self._discovered_devices = []

        _LOGGER.info(
            "Starting device discovery on %s:%s "
            "(timeout=%ds, delay=%.2fs, max_per_range=%d)",
            self._host, self._port,
            _DISCOVERY_TIMEOUT, _PROBE_DELAY, _MAX_SCAN_PER_RANGE,
        )

        for device_type, start_addr, end_addr in ALL_SCAN_RANGES:
            # Only scan first _MAX_SCAN_PER_RANGE addresses per range.
            # Per Schneider spec, devices are assigned sequentially from
            # the range start, so if address N has no device, N+1 won't either.
            scan_end = min(start_addr + _MAX_SCAN_PER_RANGE - 1, end_addr)
            device_label = DEVICE_TYPE_LABELS.get(device_type, device_type)
            _LOGGER.debug(
                "Scanning %s range: slave %d-%d", device_label, start_addr, scan_end
            )
            for slave_id in range(start_addr, scan_end + 1):
                # Fresh connection per probe — the only reliable pattern
                # for the Schneider Gateway's embedded TCP stack.
                name = await SchneiderModbusClient.probe_slave_fresh(
                    self._host, self._port, slave_id,
                    timeout=_DISCOVERY_TIMEOUT,
                )

                if name:
                    self._discovered_devices.append(
                        {
                            CONF_DEVICE_TYPE: device_type,
                            CONF_DEVICE_NAME: name,
                            CONF_SLAVE_ID: slave_id,
                        }
                    )
                    _LOGGER.info(
                        "Discovered device: %s (type=%s, slave=%d)",
                        name, device_type, slave_id,
                    )
                else:
                    # No device at this address, stop scanning this range
                    _LOGGER.debug(
                        "No device at slave %d, stopping %s range scan",
                        slave_id, device_label,
                    )
                    break

                # Small delay between probes to let the gateway recover
                await asyncio.sleep(_PROBE_DELAY)

        _LOGGER.info(
            "Discovery complete: found %d device(s)", len(self._discovered_devices)
        )

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
        """Create or update the config entry."""
        new_data = {
            CONF_HOST: self._host,
            CONF_PORT: self._port,
            CONF_SCAN_INTERVAL: self._scan_interval,
            CONF_REGISTER_TYPE: self._register_type,
            CONF_DEVICES: self._devices,
        }

        if self._reconfigure_entry is not None:
            # Update existing entry and reload it
            self.hass.config_entries.async_update_entry(
                self._reconfigure_entry,
                data=new_data,
            )
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(
                    self._reconfigure_entry.entry_id
                )
            )
            return self.async_abort(reason="reconfigure_successful")

        title = f"Schneider XW Pro ({self._host}:{self._port})"
        return self.async_create_entry(
            title=title,
            data=new_data,
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
        current_options = self._config_entry.options

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=current_options.get(
                            CONF_SCAN_INTERVAL,
                            current.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                        ),
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_REGISTER_TYPE,
                        default=current_options.get(
                            CONF_REGISTER_TYPE,
                            current.get(CONF_REGISTER_TYPE, DEFAULT_REGISTER_TYPE),
                        ),
                    ): vol.In(REGISTER_TYPE_LABELS),
                }
            ),
        )
