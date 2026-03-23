"""Diagnostics support for Schneider Electric Conext XW Pro."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DEVICES,
    CONF_HOST,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    COORDINATOR,
    DOMAIN,
)
from .coordinator import SchneiderDeviceCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinators: dict[str, SchneiderDeviceCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ][COORDINATOR]

    devices_diag: dict[str, Any] = {}
    for coordinator_key, coordinator in coordinators.items():
        devices_diag[coordinator_key] = {
            "device_name": coordinator.device_name,
            "device_type": coordinator.device_type,
            "slave_id": coordinator.slave_id,
            "last_update_success": coordinator.last_update_success,
            "sensor_register_count": len(coordinator.sensor_registers),
            "control_register_count": len(coordinator.control_registers),
            "data_keys": list(coordinator.data.keys()) if coordinator.data else [],
        }

    return {
        "config": {
            "host": entry.data.get(CONF_HOST),
            "port": entry.data.get(CONF_PORT),
            "scan_interval": entry.data.get(CONF_SCAN_INTERVAL),
            "device_count": len(entry.data.get(CONF_DEVICES, [])),
        },
        "devices": devices_diag,
    }
