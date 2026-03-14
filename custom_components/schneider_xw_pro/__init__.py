"""The Schneider Electric Conext XW Pro integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICES,
    CONF_DEVICE_NAME,
    CONF_DEVICE_TYPE,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    CONF_SLAVE_ID,
    COORDINATOR,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from .coordinator import SchneiderDeviceCoordinator
from .modbus_client import SchneiderModbusClient

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.SELECT,
    Platform.NUMBER,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Schneider XW Pro from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    devices = entry.data.get(CONF_DEVICES, [])

    # Create a single shared Modbus client for the gateway
    client = SchneiderModbusClient(host, port)
    connected = await client.connect()
    if not connected:
        _LOGGER.error("Failed to connect to Schneider Gateway at %s:%s", host, port)
        return False

    # Create a coordinator for each configured device
    coordinators: dict[str, SchneiderDeviceCoordinator] = {}
    for device_config in devices:
        device_type = device_config[CONF_DEVICE_TYPE]
        device_name = device_config.get(CONF_DEVICE_NAME, device_type)
        slave_id = device_config[CONF_SLAVE_ID]

        coordinator = SchneiderDeviceCoordinator(
            hass=hass,
            client=client,
            device_name=device_name,
            device_type=device_type,
            slave_id=slave_id,
            scan_interval=scan_interval,
        )

        # Initial data fetch - continue setup even if a device is temporarily offline
        try:
            await coordinator.async_config_entry_first_refresh()
        except Exception:
            _LOGGER.warning(
                "Failed initial data fetch for %s (slave %d), will retry on next poll",
                device_name,
                slave_id,
            )

        # Key by "type_slaveId" for unique identification
        coordinator_key = f"{device_type}_{slave_id}"
        coordinators[coordinator_key] = coordinator

    hass.data[DOMAIN][entry.entry_id] = {
        COORDINATOR: coordinators,
        "client": client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        entry_data = hass.data[DOMAIN].pop(entry.entry_id)
        client: SchneiderModbusClient = entry_data["client"]
        await client.disconnect()

    return unload_ok
