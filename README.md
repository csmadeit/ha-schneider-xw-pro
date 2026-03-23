# Schneider Electric Conext XW Pro -- Home Assistant Integration

A full HACS-compatible custom integration for the Schneider Electric Conext XW Pro solar inverter/charger ecosystem. Supports **read and write** Modbus TCP operations through the Conext Gateway / InsightHome / InsightFacility.

**Status:** Register addresses verified against official Schneider Modbus specs. Device auto-discovery implemented. Ready for hardware testing.

---

## Session Details

- **Created by:** Chris S (@csmadeit) via Devin AI
- **Session:** [Devin Session](https://app.devin.ai/sessions/4503fa9209474d858e2a17c069e0e1ef)
- **Repository:** [gitlab.cmhtransfer.com/independent/ha-schneider-xw-pro](https://gitlab.cmhtransfer.com/independent/ha-schneider-xw-pro)
- **Date:** 2026-03-14 (initial), 2026-03-22 (register rewrite + auto-discovery)

---

## Supported Devices

| Device | Type | Slave Address Range | Spec Document |
|--------|------|-------------------|---------------|
| Conext XW Pro Inverter/Charger | xw_pro | 10-29 | 990-6268B |
| Conext MPPT 60 Charge Controller | mppt | 30-49 | 990-6269A |
| Conext MPPT 80/100 600 Charge Controller | mppt | 170-189 | 990-6270A |
| Conext AGS (Auto Generator Start) | ags | 50-69 | 990-6274A |
| Conext Battery Monitor | battery_monitor | 190-209 | 990-6278A |
| Conext Gateway / InsightHome | gateway | 1 | 990-6271B |
| Conext System Control Panel (SCP) | scp | 70-89 | 990-6272A |

---

## Features

### Device Auto-Discovery
The integration automatically scans all known Modbus slave address ranges to find connected devices. No need to manually enter slave addresses.

### Read Sensors (107 registers)
- DC voltage, current, power (battery side)
- AC input/output voltage, current, power, frequency
- PV voltage, current, power (MPPT)
- Battery SOC, temperature
- System totals (PV, load, grid, battery)
- Device state, faults, warnings
- Energy counters (daily and lifetime)

### Write Controls (28 registers)
- Inverter/charger/MPPT enable/disable
- Force charge mode (off/bulk/float)
- Voltage setpoints (absorb, float, equalize, LBCO, grid support)
- Current limits (max charge, max AC input)
- Operating mode, AC input mode
- SCP display brightness, contrast, beep, alarm

### No Authentication Required
Modbus TCP is unauthenticated by design per the official protocol spec. The integration connects directly to the gateway's Modbus port (default 503).

---

## Files

### Integration Core

| File | Purpose |
|------|---------|
| `__init__.py` | Integration setup, config entry handling, multi-device coordinator init |
| `const.py` | Constants: domain, device types, slave addresses, scan ranges |
| `manifest.json` | HACS manifest with metadata and pymodbus dependency |
| `config_flow.py` | Config flow with auto-discovery + manual fallback |
| `coordinator.py` | DataUpdateCoordinator per device -- polls Modbus registers |
| `modbus_client.py` | pymodbus async TCP client with read/write/probe/discovery |
| `registers.py` | Complete Modbus register definitions (135 registers, 6 device types) |

### Entity Platforms

| File | Purpose |
|------|---------|
| `sensor.py` | Read-only sensor entities |
| `switch.py` | On/off switches for binary controls |
| `select.py` | Select entities for mode controls |
| `number.py` | Number entities for setpoints |

---

## Module Structure

```
ha-schneider-xw-pro/
+-- README.md
+-- SPECIFICATION.md
+-- hacs.json
+-- custom_components/
    +-- schneider_xw_pro/
        +-- __init__.py
        +-- const.py
        +-- manifest.json
        +-- config_flow.py
        +-- coordinator.py
        +-- modbus_client.py
        +-- registers.py
        +-- sensor.py
        +-- switch.py
        +-- select.py
        +-- number.py
        +-- strings.json
        +-- translations/
            +-- en.json
```

---

## Installation

### HACS (Recommended)
1. Open HACS in Home Assistant
2. Go to **Integrations** -> **Custom Repositories**
3. Add this repository URL
4. Install **Schneider Electric Conext XW Pro**
5. Restart Home Assistant

### Manual
1. Copy `custom_components/schneider_xw_pro/` to your HA `custom_components/` directory
2. Restart Home Assistant

### Configuration
1. Go to **Settings** -> **Devices & Services** -> **Add Integration**
2. Search for "Schneider Electric Conext XW Pro"
3. Enter your Gateway/InsightHome IP and port (default: 503)
4. The integration will auto-discover connected devices
5. Confirm the discovered devices or manually add them

---

## Audit Log

### Audit 1 -- 2026-03-14
- Added asyncio.Lock on shared Modbus client
- Fixed double disconnect in config_flow
- Fixed select.py filter for 2-option non-binary registers
- Removed unused imports
- Fixed hacs.json zip_release flag
- Added graceful device init failure handling

### Audit 2 -- 2026-03-22 (Register Rewrite + Auto-Discovery)
- **registers.py**: Complete rewrite with correct addresses from official Schneider Modbus 503 specs. 107 sensor + 28 control registers across 6 device types.
- **const.py**: Fixed critical slave address errors (AGS: 20->50, Battery Monitor: 30->190, SCP: 40->70). Added slave address ranges for discovery.
- **modbus_client.py**: Added offset support for temperature conversion (Kelvin to Celsius). Added probe_slave() and read_device_name() for discovery.
- **config_flow.py**: Added device auto-discovery via Modbus slave address scanning. Added connection validation. Documented that Modbus TCP has no authentication.
- **SCP device type**: Expanded from 1 register to 10 (5 sensor + 5 control).
