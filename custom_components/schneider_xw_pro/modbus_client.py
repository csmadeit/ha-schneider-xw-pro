"""Modbus TCP client wrapper for Schneider Conext devices."""

from __future__ import annotations

import asyncio
import logging
import struct
from typing import Any

from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

from .registers import DataType, ModbusRegisterDefinition, RegisterType

_LOGGER = logging.getLogger(__name__)


class SchneiderModbusClient:
    """Manages Modbus TCP communication with a Schneider Conext Gateway."""

    def __init__(
        self,
        host: str,
        port: int,
        timeout: int = 15,
        delay: int = 2,
    ) -> None:
        """Initialize the Modbus client."""
        self._host = host
        self._port = port
        self._timeout = timeout
        self._delay = delay
        self._client: AsyncModbusTcpClient | None = None
        self._lock = asyncio.Lock()

    @property
    def host(self) -> str:
        """Return the host."""
        return self._host

    @property
    def port(self) -> int:
        """Return the port."""
        return self._port

    @property
    def connected(self) -> bool:
        """Return True if connected."""
        return self._client is not None and self._client.connected

    async def connect(self) -> bool:
        """Connect to the Modbus TCP server."""
        if self._client is not None and self._client.connected:
            return True

        try:
            self._client = AsyncModbusTcpClient(
                host=self._host,
                port=self._port,
                timeout=self._timeout,
            )
            connected = await self._client.connect()
            if connected:
                _LOGGER.info(
                    "Connected to Schneider Gateway at %s:%s",
                    self._host,
                    self._port,
                )
            else:
                _LOGGER.error(
                    "Failed to connect to Schneider Gateway at %s:%s",
                    self._host,
                    self._port,
                )
            return connected
        except Exception:
            _LOGGER.exception(
                "Error connecting to Schneider Gateway at %s:%s",
                self._host,
                self._port,
            )
            return False

    async def disconnect(self) -> None:
        """Disconnect from the Modbus TCP server."""
        if self._client is not None:
            self._client.close()
            self._client = None
            _LOGGER.info("Disconnected from Schneider Gateway")

    async def read_register(
        self,
        register: ModbusRegisterDefinition,
        slave_id: int,
    ) -> Any:
        """Read a single register value from a device."""
        async with self._lock:
            if not self.connected:
                if not await self.connect():
                    return None

            try:
                assert self._client is not None
                if register.register_type == RegisterType.INPUT:
                    result = await self._client.read_input_registers(
                        address=register.address,
                        count=register.count,
                        slave=slave_id,
                    )
                else:
                    result = await self._client.read_holding_registers(
                        address=register.address,
                        count=register.count,
                        slave=slave_id,
                    )

                if result.isError():
                    _LOGGER.warning(
                        "Error reading register %s (addr=%d) from slave %d: %s",
                        register.key,
                        register.address,
                        slave_id,
                        result,
                    )
                    return None

                return self._decode_value(register, result.registers)

            except ModbusException as exc:
                _LOGGER.warning(
                    "Modbus exception reading %s from slave %d: %s",
                    register.key,
                    slave_id,
                    exc,
                )
                return None
            except Exception:
                _LOGGER.exception(
                    "Unexpected error reading %s from slave %d",
                    register.key,
                    slave_id,
                )
                return None

    async def write_register(
        self,
        register: ModbusRegisterDefinition,
        slave_id: int,
        value: Any,
    ) -> bool:
        """Write a value to a holding register on a device."""
        if not register.writable:
            _LOGGER.error("Register %s is not writable", register.key)
            return False

        async with self._lock:
            if not self.connected:
                if not await self.connect():
                    return False

            try:
                assert self._client is not None
                encoded = self._encode_value(register, value)

                if register.count == 1:
                    result = await self._client.write_register(
                        address=register.address,
                        value=encoded[0],
                        slave=slave_id,
                    )
                else:
                    result = await self._client.write_registers(
                        address=register.address,
                        values=encoded,
                        slave=slave_id,
                    )

                if result.isError():
                    _LOGGER.error(
                        "Error writing register %s (addr=%d) on slave %d: %s",
                        register.key,
                        register.address,
                        slave_id,
                        result,
                    )
                    return False

                _LOGGER.debug(
                    "Successfully wrote %s=%s to slave %d",
                    register.key,
                    value,
                    slave_id,
                )
                return True

            except ModbusException as exc:
                _LOGGER.error(
                    "Modbus exception writing %s to slave %d: %s",
                    register.key,
                    slave_id,
                    exc,
                )
                return False
            except Exception:
                _LOGGER.exception(
                    "Unexpected error writing %s to slave %d",
                    register.key,
                    slave_id,
                )
                return False

    async def read_all_registers(
        self,
        registers: list[ModbusRegisterDefinition],
        slave_id: int,
    ) -> dict[str, Any]:
        """Read all registers for a device and return as a dict."""
        data: dict[str, Any] = {}
        for register in registers:
            value = await self.read_register(register, slave_id)
            if value is not None:
                # If register has options mapping, resolve the label
                if register.options and isinstance(value, (int, float)):
                    int_val = int(value)
                    data[register.key] = register.options.get(int_val, str(int_val))
                    data[f"{register.key}_raw"] = int_val
                else:
                    data[register.key] = value
        return data

    def _decode_value(
        self,
        register: ModbusRegisterDefinition,
        raw_registers: list[int],
    ) -> int | float | str:
        """Decode raw Modbus register values into a Python value."""
        value: int | float
        if register.data_type == DataType.UINT16:
            value = raw_registers[0]
        elif register.data_type == DataType.INT16:
            value = raw_registers[0]
            if value >= 0x8000:
                value -= 0x10000
        elif register.data_type == DataType.UINT32:
            value = (raw_registers[0] << 16) | raw_registers[1]
        elif register.data_type == DataType.INT32:
            value = (raw_registers[0] << 16) | raw_registers[1]
            if value >= 0x80000000:
                value -= 0x100000000
        elif register.data_type == DataType.FLOAT32:
            packed = struct.pack(">HH", raw_registers[0], raw_registers[1])
            value = struct.unpack(">f", packed)[0]
        elif register.data_type == DataType.STRING:
            chars: list[str] = []
            for reg in raw_registers:
                chars.append(chr((reg >> 8) & 0xFF))
                chars.append(chr(reg & 0xFF))
            return "".join(chars).strip("\x00").strip()
        else:
            value = raw_registers[0]

        # Apply scale and offset (e.g., Kelvin to Celsius: scale=0.01, offset=-273.0)
        if register.scale != 1.0:
            value = value * register.scale
        if register.offset != 0.0:
            value = value + register.offset
        if register.scale != 1.0 or register.offset != 0.0:
            value = round(value, register.precision)

        return value

    async def probe_slave(self, slave_id: int) -> bool:
        """Probe a slave address to check if a device responds.

        Reads the 'Device Present' register (addr 0x0041, common to all devices)
        to determine if a device exists at the given slave address.
        """
        async with self._lock:
            if not self.connected:
                if not await self.connect():
                    return False

            try:
                assert self._client is not None
                result = await self._client.read_holding_registers(
                    address=0x0041,  # Device Present register (common)
                    count=1,
                    slave=slave_id,
                )
                if result.isError():
                    return False
                # Device Present: 1 = Active
                return result.registers[0] == 1
            except Exception:
                return False

    async def read_device_name(self, slave_id: int) -> str | None:
        """Read the Device Name string register from a device.

        Device Name is at register 1 (addr 0x0000), 8 registers (16 chars).
        Common across all Schneider Conext devices.
        """
        async with self._lock:
            if not self.connected:
                if not await self.connect():
                    return None

            try:
                assert self._client is not None
                result = await self._client.read_holding_registers(
                    address=0x0000,  # Device Name register
                    count=8,         # 8 registers = 16 chars
                    slave=slave_id,
                )
                if result.isError():
                    return None
                chars: list[str] = []
                for reg in result.registers:
                    chars.append(chr((reg >> 8) & 0xFF))
                    chars.append(chr(reg & 0xFF))
                return "".join(chars).strip("\x00").strip()
            except Exception:
                return None

    def _encode_value(
        self,
        register: ModbusRegisterDefinition,
        value: Any,
    ) -> list[int]:
        """Encode a Python value into raw Modbus register values."""
        # Undo offset and scaling
        raw_float = float(value)
        if register.offset != 0.0:
            raw_float = raw_float - register.offset
        if register.scale != 1.0:
            raw_value = round(raw_float / register.scale)
        else:
            raw_value = int(raw_float)

        if register.data_type in (DataType.UINT16, DataType.INT16):
            if register.data_type == DataType.INT16 and raw_value < 0:
                raw_value = raw_value + 0x10000
            return [raw_value & 0xFFFF]
        elif register.data_type in (DataType.UINT32, DataType.INT32):
            if register.data_type == DataType.INT32 and raw_value < 0:
                raw_value = raw_value + 0x100000000
            return [(raw_value >> 16) & 0xFFFF, raw_value & 0xFFFF]
        elif register.data_type == DataType.FLOAT32:
            packed = struct.pack(">f", float(value))
            regs = struct.unpack(">HH", packed)
            return list(regs)
        else:
            return [raw_value & 0xFFFF]
