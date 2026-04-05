"""Data update coordinator for Schneider Conext devices."""

from __future__ import annotations

import logging
from dataclasses import replace
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_REGISTER_TYPE, DEFAULT_SCAN_INTERVAL, REGISTER_TYPE_INPUT
from .modbus_client import SchneiderModbusClient
from .registers import (
    CONTROL_REGISTERS_BY_DEVICE,
    SENSOR_REGISTERS_BY_DEVICE,
    ModbusRegisterDefinition,
    RegisterType,
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
        register_type: str = DEFAULT_REGISTER_TYPE,
    ) -> None:
        """Initialize the coordinator."""
        self.client = client
        self.device_name = device_name
        self.device_type = device_type
        self.slave_id = slave_id

        base_sensor_registers = SENSOR_REGISTERS_BY_DEVICE.get(device_type, [])
        self._control_registers = CONTROL_REGISTERS_BY_DEVICE.get(device_type, [])

        # Override register type for read-only sensor registers when the user
        # selects INPUT (FC 0x04) mode.  Control (writable) registers always
        # stay HOLDING because writes require FC 0x06/0x10.
        if register_type == REGISTER_TYPE_INPUT:
            self._sensor_registers = [
                self._with_register_type(reg, RegisterType.INPUT)
                for reg in base_sensor_registers
            ]
        else:
            self._sensor_registers = list(base_sensor_registers)

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
        """Fetch data from the Modbus device.

        Uses a fresh TCP connection for each poll cycle to avoid
        overwhelming the Schneider Gateway's embedded TCP stack.
        The proven conext-api project uses the same pattern:
        open → read all registers → close, with small delays.
        """
        try:
            # Combine sensor + control registers into one list so we
            # read them all in a single fresh connection cycle.
            all_registers = list(self._sensor_registers) + list(
                self._control_registers
            )

            data = await self.client.read_all_registers_fresh(
                all_registers, self.slave_id
            )

            if not data:
                raise UpdateFailed(
                    f"No data received from {self.device_name} (slave {self.slave_id})"
                )

            return data

        except UpdateFailed:
            raise
        except Exception as exc:
            raise UpdateFailed(
                f"Error communicating with {self.device_name} "
                f"(slave {self.slave_id}): {exc}"
            ) from exc

    @staticmethod
    def _with_register_type(
        reg: ModbusRegisterDefinition, rtype: RegisterType,
    ) -> ModbusRegisterDefinition:
        """Return a copy of *reg* with a different register_type."""
        return replace(reg, register_type=rtype)

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
