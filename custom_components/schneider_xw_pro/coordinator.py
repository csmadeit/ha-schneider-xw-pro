"""Data update coordinator for Schneider Conext devices."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL
from .modbus_client import SchneiderModbusClient
from .registers import (
    CONTROL_REGISTERS_BY_DEVICE,
    SENSOR_REGISTERS_BY_DEVICE,
    ModbusRegisterDefinition,
)

_LOGGER = logging.getLogger(__name__)


class SchneiderDeviceCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for a single Schneider Conext device."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: SchneiderModbusClient,
        device_name: str,
        device_type: str,
        slave_id: int,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.device_name = device_name
        self.device_type = device_type
        self.slave_id = slave_id

        self._sensor_registers = SENSOR_REGISTERS_BY_DEVICE.get(device_type, [])
        self._control_registers = CONTROL_REGISTERS_BY_DEVICE.get(device_type, [])

        super().__init__(
            hass,
            _LOGGER,
            name=f"Schneider {device_name} (slave {slave_id})",
            update_interval=timedelta(seconds=scan_interval),
        )

    @property
    def sensor_registers(self) -> list[ModbusRegisterDefinition]:
        """Return sensor register definitions."""
        return self._sensor_registers

    @property
    def control_registers(self) -> list[ModbusRegisterDefinition]:
        """Return control register definitions."""
        return self._control_registers

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Modbus device."""
        try:
            # Read all sensor (input) registers
            sensor_data = await self.client.read_all_registers(
                self._sensor_registers, self.slave_id
            )

            # Read all control (holding) registers to get current values
            control_data = await self.client.read_all_registers(
                self._control_registers, self.slave_id
            )

            # Merge both datasets
            data = {**sensor_data, **control_data}

            if not data:
                raise UpdateFailed(
                    f"No data received from {self.device_name} (slave {self.slave_id})"
                )

            return data

        except Exception as exc:
            raise UpdateFailed(
                f"Error communicating with {self.device_name} "
                f"(slave {self.slave_id}): {exc}"
            ) from exc

    async def async_write_register(
        self,
        register: ModbusRegisterDefinition,
        value: Any,
    ) -> bool:
        """Write a value to a register and refresh data."""
        success = await self.client.write_register(register, self.slave_id, value)
        if success:
            # Refresh data after write
            await self.async_request_refresh()
        return success
