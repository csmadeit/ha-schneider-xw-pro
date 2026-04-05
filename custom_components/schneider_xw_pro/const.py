"""Constants for the Schneider Electric Conext XW Pro integration."""

from __future__ import annotations

DOMAIN = "schneider_xw_pro"
MANUFACTURER = "Schneider Electric"

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_DEVICES = "devices"
CONF_SLAVE_ID = "slave_id"
CONF_DEVICE_TYPE = "device_type"
CONF_DEVICE_NAME = "device_name"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_REGISTER_TYPE = "register_type"

# Defaults
DEFAULT_PORT = 503
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_TIMEOUT = 15
DEFAULT_DELAY = 2

# Register type options for sensor reads
REGISTER_TYPE_HOLDING = "holding"
REGISTER_TYPE_INPUT = "input"
DEFAULT_REGISTER_TYPE = REGISTER_TYPE_HOLDING

REGISTER_TYPE_LABELS = {
    REGISTER_TYPE_HOLDING: "Holding Registers (FC 0x03) — Stable",
    REGISTER_TYPE_INPUT: "Input Registers (FC 0x04) — Experimental",
}

# Device types
DEVICE_TYPE_XW_PRO = "xw_pro"
DEVICE_TYPE_MPPT = "mppt"
DEVICE_TYPE_AGS = "ags"
DEVICE_TYPE_BATTERY_MONITOR = "battery_monitor"
DEVICE_TYPE_GATEWAY = "gateway"
DEVICE_TYPE_SCP = "scp"

DEVICE_TYPE_LABELS = {
    DEVICE_TYPE_XW_PRO: "Conext XW Pro Inverter/Charger",
    DEVICE_TYPE_MPPT: "Conext MPPT Charge Controller",
    DEVICE_TYPE_AGS: "Conext AGS (Auto Generator Start)",
    DEVICE_TYPE_BATTERY_MONITOR: "Conext Battery Monitor",
    DEVICE_TYPE_GATEWAY: "Conext Gateway / InsightHome / InsightFacility",
    DEVICE_TYPE_SCP: "Conext System Control Panel",
}

# Default slave addresses (per official Schneider Modbus specs)
DEFAULT_SLAVE_ADDRESSES = {
    DEVICE_TYPE_XW_PRO: 10,
    DEVICE_TYPE_MPPT: 170,
    DEVICE_TYPE_AGS: 50,
    DEVICE_TYPE_BATTERY_MONITOR: 190,
    DEVICE_TYPE_GATEWAY: 1,
    DEVICE_TYPE_SCP: 70,
}

# Slave address ranges for device auto-discovery scanning
# Source: Official Schneider Modbus Interface Specifications
SLAVE_ADDRESS_RANGES = {
    DEVICE_TYPE_GATEWAY: (1, 1),
    DEVICE_TYPE_XW_PRO: (10, 29),
    DEVICE_TYPE_MPPT: (30, 49),        # MPPT 60 range
    # DEVICE_TYPE_MPPT: (170, 189),    # MPPT 80 range (scanned separately)
    DEVICE_TYPE_AGS: (50, 69),
    DEVICE_TYPE_SCP: (70, 89),
    DEVICE_TYPE_BATTERY_MONITOR: (190, 209),
}

# Additional MPPT 80 range (separate from MPPT 60)
MPPT80_SLAVE_ADDRESS_RANGE = (170, 189)

# All scannable address ranges for device discovery
ALL_SCAN_RANGES: list[tuple[str, int, int]] = [
    (DEVICE_TYPE_GATEWAY, 1, 1),
    (DEVICE_TYPE_XW_PRO, 10, 29),
    (DEVICE_TYPE_MPPT, 30, 49),        # MPPT 60
    (DEVICE_TYPE_AGS, 50, 69),
    (DEVICE_TYPE_SCP, 70, 89),
    (DEVICE_TYPE_MPPT, 170, 189),      # MPPT 80
    (DEVICE_TYPE_BATTERY_MONITOR, 190, 209),
]

# Modbus data types
DATA_TYPE_UINT16 = "uint16"
DATA_TYPE_INT16 = "int16"
DATA_TYPE_UINT32 = "uint32"
DATA_TYPE_INT32 = "int32"
DATA_TYPE_FLOAT32 = "float32"
DATA_TYPE_STRING = "string"

# Update coordinator key
COORDINATOR = "coordinator"
