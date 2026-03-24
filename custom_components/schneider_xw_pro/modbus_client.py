"""Modbus TCP client wrapper for Schneider Conext devices.

Uses pyModbusTCP -- the same library proven to work with Schneider Conext
Gateway hardware by the conext-api project (https://github.com/shorawitz/conext-api).

Key design decisions:
- auto_open=True / auto_close=True: each read/write opens a fresh TCP
  connection, performs the operation, then closes.  The Schneider Gateway is
  embedded hardware with limited TCP resources; persistent connections cause
  it to stop responding.
- unit_id is set per-client (pyModbusTCP requirement), so we create a new
  ModbusClient instance whenever the slave address changes.
- 0.1 s sleep between reads matches the conext-api pattern.
- All calls are synchronous (pyModbusTCP is blocking I/O) and wrapped in
  asyncio.to_thread() for Home Assistant compatibility.
"""

from __future__ import annotations

import asyncio
import logging
import struct
import time
from typing import Any

from pyModbusTCP.client import ModbusClient

from .registers import DataType, ModbusRegisterDefinition, RegisterType

_LOGGER = logging.getLogger(__name__)

# Delay between consecutive register reads (seconds).
# Matches the proven conext-api project: sleep(0.1) between every read.
_READ_DELAY = 0.1

# Number of retry attempts for failed register reads.
# The Schneider Gateway can drop reads under load (many registers,
# multiple devices).  Retrying with a small back-off recovers most
# transient failures.
_MAX_RETRIES = 3
_RETRY_DELAY = 0.15


class SchneiderModbusClient:
    """Manages Modbus TCP communication with a Schneider Conext Gateway."""

    def __init__(
        self,
        host: str,
        port: int,
        timeout: int = 30,
        delay: int = 2,
    ) -> None:
        """Initialize the Modbus client."""
        self._host = host
        self._port = port
        self._timeout = timeout
        self._delay = delay

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
        """With auto_open/auto_close there is no persistent connection."""
        return True

    async def connect(self) -> bool:
        """Test TCP connectivity to the gateway."""
        def _test_connect() -> bool:
            client = ModbusClient(
                host=self._host, port=self._port, timeout=self._timeout,
            )
            ok = client.open()
            if ok:
                client.close()
                _LOGGER.info(
                    "Connectivity OK to Schneider Gateway at %s:%s",
                    self._host, self._port,
                )
            else:
                _LOGGER.warning(
                    "Cannot reach Schneider Gateway at %s:%s",
                    self._host, self._port,
                )
            return ok
        return await asyncio.to_thread(_test_connect)

    async def disconnect(self) -> None:
        """No-op -- auto_close handles disconnection."""

    async def read_register(
        self,
        register: ModbusRegisterDefinition,
        slave_id: int,
    ) -> Any:
        """Read a single register value from a device."""
        def _read() -> Any:
            client = ModbusClient(
                host=self._host, port=self._port,
                auto_open=True, auto_close=True,
                unit_id=slave_id, timeout=self._timeout,
            )
            if register.register_type == RegisterType.INPUT:
                regs = client.read_input_registers(register.address, register.count)
            else:
                regs = client.read_holding_registers(register.address, register.count)

            if regs is None:
                _LOGGER.debug(
                    "read_register: no response for %s (addr=0x%04X) from slave %d",
                    register.key, register.address, slave_id,
                )
                return None

            try:
                return self._decode_value(register, regs)
            except Exception:
                _LOGGER.debug(
                    "read_register: decode error for %s from slave %d",
                    register.key, slave_id, exc_info=True,
                )
                return None

        return await asyncio.to_thread(_read)

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

        def _write() -> bool:
            client = ModbusClient(
                host=self._host, port=self._port,
                auto_open=True, auto_close=True,
                unit_id=slave_id, timeout=self._timeout,
            )
            encoded = self._encode_value(register, value)

            if register.count == 1:
                ok = client.write_single_register(register.address, encoded[0])
            else:
                ok = client.write_multiple_registers(register.address, encoded)

            if not ok:
                _LOGGER.error(
                    "Error writing register %s (addr=0x%04X) on slave %d",
                    register.key, register.address, slave_id,
                )
            else:
                _LOGGER.debug(
                    "Successfully wrote %s=%s to slave %d",
                    register.key, value, slave_id,
                )
            return bool(ok)

        return await asyncio.to_thread(_write)

    async def read_all_registers(
        self,
        registers: list[ModbusRegisterDefinition],
        slave_id: int,
    ) -> dict[str, Any]:
        """Read all registers for a device (alias for read_all_registers_fresh)."""
        return await self.read_all_registers_fresh(registers, slave_id)

    async def read_all_registers_fresh(
        self,
        registers: list[ModbusRegisterDefinition],
        slave_id: int,
    ) -> dict[str, Any]:
        """Read all registers using efficient block reads.

        Groups consecutive registers into blocks and reads each block in a
        single Modbus request.  This dramatically reduces TCP connections
        (from 100+ to ~10) which is critical for the Schneider Gateway's
        embedded TCP stack.  Falls back to individual register reads if a
        block read fails.
        """
        def _read_all() -> dict[str, Any]:
            data: dict[str, Any] = {}
            blocks = self._group_into_blocks(registers)

            _LOGGER.warning(
                "read_all_registers_fresh: reading %d registers in %d "
                "block(s) from slave %d",
                len(registers), len(blocks), slave_id,
            )

            for start_addr, total_count, block_regs in blocks:
                client = ModbusClient(
                    host=self._host, port=self._port,
                    auto_open=True, auto_close=True,
                    unit_id=slave_id, timeout=self._timeout,
                )

                # --- Try block read first ---
                raw_block = None
                for attempt in range(_MAX_RETRIES):
                    if block_regs[0].register_type == RegisterType.INPUT:
                        raw_block = client.read_input_registers(
                            start_addr, total_count,
                        )
                    else:
                        raw_block = client.read_holding_registers(
                            start_addr, total_count,
                        )
                    if raw_block is not None:
                        break
                    if attempt < _MAX_RETRIES - 1:
                        _LOGGER.warning(
                            "Block read retry %d for 0x%04X..0x%04X "
                            "from slave %d (last_error=%s, last_except=%s)",
                            attempt + 1, start_addr,
                            start_addr + total_count - 1, slave_id,
                            client.last_error, client.last_except,
                        )
                        time.sleep(_RETRY_DELAY)

                if raw_block is not None and len(raw_block) >= total_count:
                    # Block read succeeded — extract individual values
                    for register in block_regs:
                        offset = register.address - start_addr
                        reg_raw = raw_block[offset : offset + register.count]
                        self._store_decoded(data, register, reg_raw)
                else:
                    # Block read failed — fall back to individual reads
                    _LOGGER.warning(
                        "Block read FAILED for 0x%04X..0x%04X (%d regs) from "
                        "slave %d after %d retries (last_error=%s, "
                        "last_except=%s); falling back to individual reads",
                        start_addr, start_addr + total_count - 1,
                        total_count, slave_id, _MAX_RETRIES,
                        client.last_error, client.last_except,
                    )
                    self._read_individually(
                        data, block_regs, slave_id,
                    )

                # Delay between blocks
                time.sleep(_READ_DELAY)

            if len(data) < len(registers):
                missing = set(r.key for r in registers) - set(data.keys())
                # Filter out _raw keys from missing count
                missing = {k for k in missing if not k.endswith("_raw")}
                _LOGGER.warning(
                    "read_all_registers_fresh: got %d/%d values from "
                    "slave %d — MISSING: %s",
                    len(data), len(registers), slave_id,
                    ", ".join(sorted(missing)[:20]),
                )
            else:
                _LOGGER.warning(
                    "read_all_registers_fresh: got %d/%d values from slave %d",
                    len(data), len(registers), slave_id,
                )
            return data

        return await asyncio.to_thread(_read_all)

    # ------------------------------------------------------------------
    # Block-read helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _group_into_blocks(
        registers: list[ModbusRegisterDefinition],
        max_gap: int = 10,
        max_block_size: int = 50,
    ) -> list[tuple[int, int, list[ModbusRegisterDefinition]]]:
        """Group registers into contiguous blocks for efficient reads.

        Returns ``(start_address, total_register_count, register_list)``
        tuples.  Adjacent registers (with gaps up to *max_gap* unused
        positions) are merged into a single block.  Each block reads at
        most *max_block_size* Modbus registers.  Only registers of the
        same type (INPUT / HOLDING) are grouped together.
        """
        if not registers:
            return []

        by_type: dict[RegisterType, list[ModbusRegisterDefinition]] = {}
        for reg in registers:
            by_type.setdefault(reg.register_type, []).append(reg)

        blocks: list[tuple[int, int, list[ModbusRegisterDefinition]]] = []

        for _rtype, regs in by_type.items():
            sorted_regs = sorted(regs, key=lambda r: r.address)
            current: list[ModbusRegisterDefinition] = [sorted_regs[0]]

            for reg in sorted_regs[1:]:
                cur_end = max(r.address + r.count for r in current)
                gap = reg.address - cur_end
                new_size = (reg.address + reg.count) - current[0].address

                if gap <= max_gap and new_size <= max_block_size:
                    current.append(reg)
                else:
                    start = current[0].address
                    end = max(r.address + r.count for r in current)
                    blocks.append((start, end - start, current))
                    current = [reg]

            start = current[0].address
            end = max(r.address + r.count for r in current)
            blocks.append((start, end - start, current))

        blocks.sort(key=lambda b: b[0])
        return blocks

    def _store_decoded(
        self,
        data: dict[str, Any],
        register: ModbusRegisterDefinition,
        raw_registers: list[int],
    ) -> None:
        """Decode a register value and store it in *data*."""
        try:
            value = self._decode_value(register, raw_registers)
        except Exception:
            _LOGGER.debug(
                "Decode error for %s", register.key, exc_info=True,
            )
            return

        if value is not None:
            if register.options and isinstance(value, (int, float)):
                int_val = int(value)
                data[register.key] = register.options.get(
                    int_val, str(int_val),
                )
                data[f"{register.key}_raw"] = int_val
            else:
                data[register.key] = value

    def _read_individually(
        self,
        data: dict[str, Any],
        registers: list[ModbusRegisterDefinition],
        slave_id: int,
    ) -> None:
        """Fall-back: read each register one-at-a-time with retries."""
        for register in registers:
            client = ModbusClient(
                host=self._host, port=self._port,
                auto_open=True, auto_close=True,
                unit_id=slave_id, timeout=self._timeout,
            )
            regs = None
            for attempt in range(_MAX_RETRIES):
                if register.register_type == RegisterType.INPUT:
                    regs = client.read_input_registers(
                        register.address, register.count,
                    )
                else:
                    regs = client.read_holding_registers(
                        register.address, register.count,
                    )
                if regs is not None:
                    break
                if attempt < _MAX_RETRIES - 1:
                    _LOGGER.debug(
                        "Individual retry %d for %s (0x%04X) slave %d",
                        attempt + 1, register.key,
                        register.address, slave_id,
                    )
                    time.sleep(_RETRY_DELAY)

            if regs is not None:
                self._store_decoded(data, register, regs)
            else:
                _LOGGER.warning(
                    "Individual read FAILED for %s (0x%04X) slave %d "
                    "(last_error=%s, last_except=%s)",
                    register.key, register.address, slave_id,
                    client.last_error, client.last_except,
                )

            time.sleep(_READ_DELAY)

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
        # Special handling: temperature registers with offset -273.0 use
        # centi-Kelvin encoding.  A raw value of 0 means "no sensor
        # connected" (the Schneider web GUI shows "N/A").  We return None
        # so Home Assistant marks the entity as unavailable instead of
        # showing -459.4 °F.
        if register.offset != 0.0 and value == 0:
            return None

        if register.scale != 1.0:
            value = value * register.scale
        if register.offset != 0.0:
            value = value + register.offset
        if register.scale != 1.0 or register.offset != 0.0:
            value = round(value, register.precision)

        return value

    async def probe_slave(self, slave_id: int) -> str | None:
        """Probe a slave address by reading its Device Name register.

        Device Name (addr 0, str16, 8 registers) is common to ALL
        Schneider Conext device types per the official Modbus 503 specs.
        """
        return await self.probe_slave_fresh(
            self._host, self._port, slave_id, timeout=self._timeout,
        )

    @staticmethod
    async def probe_slave_fresh(
        host: str, port: int, slave_id: int, timeout: int = 10,
    ) -> str | None:
        """Probe a slave using pyModbusTCP (open -> read -> close).

        Uses the same library and pattern as the proven conext-api project.
        Creates a ModbusClient with auto_open/auto_close, reads Device Name
        at register 0 (8 regs = 16 chars), then the client auto-closes.
        """
        def _probe() -> str | None:
            client = ModbusClient(
                host=host, port=port,
                auto_open=True, auto_close=True,
                unit_id=slave_id, timeout=timeout,
            )

            _LOGGER.debug(
                "probe_slave_fresh(%d): reading Device Name (reg 0, 8 regs)",
                slave_id,
            )

            regs = client.read_holding_registers(0, 8)

            if regs is None:
                _LOGGER.debug(
                    "probe_slave_fresh(%d): no response from %s:%s",
                    slave_id, host, port,
                )
                return None

            # Decode 8 x uint16 -> 16-char string
            chars: list[str] = []
            for reg in regs:
                chars.append(chr((reg >> 8) & 0xFF))
                chars.append(chr(reg & 0xFF))
            name = "".join(chars).strip("\x00").strip()

            _LOGGER.debug("probe_slave_fresh(%d): got name=%r", slave_id, name)
            return name if name else None

        return await asyncio.to_thread(_probe)

    async def read_device_name(self, slave_id: int) -> str | None:
        """Read the Device Name string register from a device.

        Alias for probe_slave().
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
