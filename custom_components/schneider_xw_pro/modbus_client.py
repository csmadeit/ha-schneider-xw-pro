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
                    _LOGGER.debug(
                        "Error reading register %s (addr=%d) from slave %d: %s",
                        register.key,
                        register.address,
                        slave_id,
                        result,
                    )
                    return None

                return self._decode_value(register, result.registers)

            except ModbusException as exc:
                _LOGGER.debug(
                    "Modbus exception reading %s from slave %d: %s",
                    register.key,
                    slave_id,
                    exc,
                )
                return None
            except Exception:
                _LOGGER.debug(
                    "Unexpected error reading %s from slave %d",
                    register.key,
                    slave_id,
                    exc_info=True,
                )
                return None

    async def write_register(
        self,
        register: ModbusRegisterDefinition,
        slave_id: int,
        value: Any,
    ) -> bool:
        """Write a value to a holding register on a device.

        Uses a fresh TCP connection (open → write → close) to avoid
        overwhelming the Schneider Gateway's embedded TCP stack.
        """
        if not register.writable:
            _LOGGER.error("Register %s is not writable", register.key)
            return False

        client: AsyncModbusTcpClient | None = None
        try:
            client = AsyncModbusTcpClient(
                host=self._host, port=self._port, timeout=self._timeout,
            )
            connected = await client.connect()
            if not connected:
                _LOGGER.error(
                    "write_register: connect failed to %s:%s for slave %d",
                    self._host, self._port, slave_id,
                )
                return False

            encoded = self._encode_value(register, value)

            if register.count == 1:
                result = await client.write_register(
                    address=register.address,
                    value=encoded[0],
                    slave=slave_id,
                )
            else:
                result = await client.write_registers(
                    address=register.address,
                    values=encoded,
                    slave=slave_id,
                )

            if result.isError():
                _LOGGER.error(
                    "Error writing register %s (addr=0x%04X) on slave %d: %s",
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
        finally:
            if client is not None:
                client.close()

    async def read_all_registers(
        self,
        registers: list[ModbusRegisterDefinition],
        slave_id: int,
    ) -> dict[str, Any]:
        """Read all registers for a device and return as a dict.

        Uses the persistent connection with a small delay between reads
        to avoid overwhelming the gateway.
        """
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
            # Small delay between reads to let the gateway process.
            # The Schneider Gateway is embedded hardware; the proven
            # conext-api project uses sleep(0.1) between every read.
            await asyncio.sleep(0.1)
        return data

    async def read_all_registers_fresh(
        self,
        registers: list[ModbusRegisterDefinition],
        slave_id: int,
    ) -> dict[str, Any]:
        """Read all registers using a FRESH TCP connection.

        Opens a new connection, reads all registers for one device with
        small delays between reads, then closes the connection.  This
        mirrors the proven conext-api project approach and avoids
        overwhelming the Schneider Gateway's embedded TCP stack.
        """
        data: dict[str, Any] = {}
        client: AsyncModbusTcpClient | None = None
        try:
            client = AsyncModbusTcpClient(
                host=self._host, port=self._port, timeout=self._timeout,
            )
            connected = await client.connect()
            if not connected:
                _LOGGER.warning(
                    "read_all_registers_fresh: connect failed to %s:%s for slave %d",
                    self._host, self._port, slave_id,
                )
                return data

            _LOGGER.debug(
                "read_all_registers_fresh: reading %d registers from slave %d",
                len(registers), slave_id,
            )

            for register in registers:
                try:
                    if register.register_type == RegisterType.INPUT:
                        result = await client.read_input_registers(
                            address=register.address,
                            count=register.count,
                            slave=slave_id,
                        )
                    else:
                        result = await client.read_holding_registers(
                            address=register.address,
                            count=register.count,
                            slave=slave_id,
                        )

                    if result.isError():
                        _LOGGER.debug(
                            "read_all_registers_fresh: error reading %s "
                            "(addr=0x%04X) from slave %d: %s",
                            register.key, register.address, slave_id, result,
                        )
                    else:
                        try:
                            value = self._decode_value(register, result.registers)
                        except Exception:
                            _LOGGER.debug(
                                "read_all_registers_fresh: decode error for %s "
                                "from slave %d",
                                register.key, slave_id, exc_info=True,
                            )
                            value = None
                        if value is not None:
                            if register.options and isinstance(value, (int, float)):
                                int_val = int(value)
                                data[register.key] = register.options.get(
                                    int_val, str(int_val)
                                )
                                data[f"{register.key}_raw"] = int_val
                            else:
                                data[register.key] = value
                except ModbusException as exc:
                    _LOGGER.debug(
                        "read_all_registers_fresh: ModbusException reading %s "
                        "from slave %d: %s",
                        register.key, slave_id, exc,
                    )
                except Exception:
                    _LOGGER.debug(
                        "read_all_registers_fresh: unexpected error reading %s "
                        "from slave %d",
                        register.key, slave_id, exc_info=True,
                    )

                # Delay between reads — matches conext-api sleep(0.1)
                await asyncio.sleep(0.1)

        except Exception:
            _LOGGER.debug(
                "read_all_registers_fresh: connection error for slave %d",
                slave_id, exc_info=True,
            )
        finally:
            if client is not None:
                client.close()

        _LOGGER.debug(
            "read_all_registers_fresh: got %d/%d values from slave %d",
            len(data), len(registers), slave_id,
        )
        return data

    def _decode_value(
        self,
        register: ModbusRegisterDefinition,
        raw_registers: list[int],
    ) -> int | float | str | None:
        """Decode raw Modbus register values into a Python value."""
        if len(raw_registers) < register.count:
            _LOGGER.debug(
                "decode: expected %d registers for %s, got %d",
                register.count, register.key, len(raw_registers),
            )
            return None

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

    async def probe_slave(self, slave_id: int) -> str | None:
        """Probe a slave address by reading its Device Name register.

        Device Name (addr 0x0000, str16, 8 registers) is common to ALL
        Schneider Conext device types per the official Modbus 503 specs.
        Returns the device name string if a device responds, None otherwise.

        NOTE: The 'Device Present' register is NOT at the same address for
        all device types (0x0041 for XW/AGS/BatMon/SCP, 0x0042 for MPPT),
        and the Gateway has no Device Present register at all. Reading
        Device Name is the only universal probe method.
        """
        async with self._lock:
            if not self.connected:
                _LOGGER.debug("probe_slave(%d): not connected, reconnecting", slave_id)
                if not await self.connect():
                    _LOGGER.warning("probe_slave(%d): reconnect failed", slave_id)
                    return None

            try:
                assert self._client is not None
                _LOGGER.debug(
                    "probe_slave(%d): reading Device Name (0x0000, 8 regs)", slave_id
                )
                result = await self._client.read_holding_registers(
                    address=0x0000,  # Device Name register (universal)
                    count=8,         # 8 registers = 16 chars
                    slave=slave_id,
                )
                if result.isError():
                    _LOGGER.debug(
                        "probe_slave(%d): error response: %s", slave_id, result
                    )
                    return None
                chars: list[str] = []
                for reg in result.registers:
                    chars.append(chr((reg >> 8) & 0xFF))
                    chars.append(chr(reg & 0xFF))
                name = "".join(chars).strip("\x00").strip()
                _LOGGER.debug("probe_slave(%d): got name=%r", slave_id, name)
                return name if name else None
            except ModbusException as exc:
                _LOGGER.debug(
                    "probe_slave(%d): ModbusException: %s", slave_id, exc
                )
                return None
            except Exception:
                _LOGGER.debug(
                    "probe_slave(%d): unexpected exception", slave_id, exc_info=True
                )
                return None

    @staticmethod
    async def probe_slave_fresh(
        host: str, port: int, slave_id: int, timeout: int = 10
    ) -> str | None:
        """Probe a slave using a FRESH TCP connection (open → read → close).

        The Schneider Conext Gateway is embedded hardware with limited TCP
        resources. Reusing a single persistent connection for rapid-fire
        probes across many slave IDs can overwhelm the gateway, causing it
        to stop responding. This mirrors the approach used by the proven
        conext-api project (pyModbusTCP auto_open=True, auto_close=True).

        Creates a brand-new AsyncModbusTcpClient for each probe, reads
        Device Name (0x0000, 8 regs), then closes the connection.
        """
        client: AsyncModbusTcpClient | None = None
        try:
            client = AsyncModbusTcpClient(
                host=host, port=port, timeout=timeout,
            )
            connected = await client.connect()
            if not connected:
                _LOGGER.debug(
                    "probe_slave_fresh(%d): TCP connect failed to %s:%s",
                    slave_id, host, port,
                )
                return None

            _LOGGER.debug(
                "probe_slave_fresh(%d): reading Device Name (0x0000, 8 regs)",
                slave_id,
            )
            result = await client.read_holding_registers(
                address=0x0000,  # Device Name register (universal)
                count=8,         # 8 registers = 16 chars
                slave=slave_id,
            )
            if result.isError():
                _LOGGER.debug(
                    "probe_slave_fresh(%d): error response: %s", slave_id, result
                )
                return None

            chars: list[str] = []
            for reg in result.registers:
                chars.append(chr((reg >> 8) & 0xFF))
                chars.append(chr(reg & 0xFF))
            name = "".join(chars).strip("\x00").strip()
            _LOGGER.debug("probe_slave_fresh(%d): got name=%r", slave_id, name)
            return name if name else None

        except ModbusException as exc:
            _LOGGER.debug(
                "probe_slave_fresh(%d): ModbusException: %s", slave_id, exc
            )
            return None
        except Exception:
            _LOGGER.debug(
                "probe_slave_fresh(%d): unexpected exception",
                slave_id, exc_info=True,
            )
            return None
        finally:
            if client is not None:
                client.close()

    async def read_device_name(self, slave_id: int) -> str | None:
        """Read the Device Name string register from a device.

        Alias for probe_slave() — both read Device Name at 0x0000.
        Kept for backward compatibility.
        """
        return await self.probe_slave(slave_id)

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
