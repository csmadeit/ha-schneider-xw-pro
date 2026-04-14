# Smarter.Homes Schneider Conext Solar Integration -- Specification

## Overview

This document specifies the complete design of the Schneider XW Pro HACS integration module for Home Assistant.

All register addresses and device specifications are based on **OFFICIAL Schneider Electric Modbus Interface Specifications (Port 503)**:
- 990-6268B: Conext XW Inverter/Chargers
- 990-6270A: Conext MPPT 80/100 600 Solar Charge Controllers
- 990-6269A: Conext MPPT 60 Solar Charge Controller
- 990-6274A: Conext Automatic Generator Start (AGS)
- 990-6278A: Conext Battery Monitor
- 990-6271B: Conext Gateway / InsightHome / InsightFacility
- 990-6272A: Conext System Control Panel (SCP)

---

## 1. Data Schema

### 1.1 Configuration Entry Data

- `host` (string): Gateway IP address
- `port` (int): Modbus TCP port, default 503
- `scan_interval` (int): Polling interval in seconds, default 30
- `devices` (list): Array of device configurations with device_type, device_name, slave_id

### 1.2 Device Types and Slave Address Ranges

| Type Key | Label | Default Slave | Address Range | Spec |
|----------|-------|---------------|---------------|------|
| xw_pro | Conext XW Pro Inverter/Charger | 10 | 10-29 | 990-6268B |
| mppt | Conext MPPT Charge Controller | 170 | 30-49 (60), 170-189 (80) | 990-6270A |
| ags | Conext AGS | 50 | 50-69 | 990-6274A |
| battery_monitor | Conext Battery Monitor | 190 | 190-209 | 990-6278A |
| gateway | Conext Gateway / InsightHome | 1 | 1 | 990-6271B |
| scp | Conext System Control Panel | 70 | 70-89 | 990-6272A |

### 1.3 Register Schema

| Field | Type | Description |
|-------|------|-------------|
| name | string | Human-readable name |
| key | string | Unique entity key |
| address | int | Zero-based Modbus register address |
| register_type | enum | input or holding |
| data_type | enum | uint16, int16, uint32, int32, float32, string |
| count | int | Registers to read (1=16-bit, 2=32-bit) |
| scale | float | Multiplier for raw value |
| offset | float | Added after scaling (e.g. -273.0 for K to C) |
| precision | int | Decimal places |
| unit | string | V, A, W, kWh, etc. |
| writable | bool | Whether register can be written |
| options | dict | Value-to-label mapping for enums |

**Notes:** Addresses are zero-based (wire protocol). PDF register numbers are 1-based.
Temperature: scale=0.01, offset=-273.0 (centi-Kelvin to Celsius).

---

## 2. Business Logic

### 2.1 Connection Lifecycle

1. User adds integration via Config Flow
2. Config flow collects gateway IP, port, scan interval
3. **Auto-discovery** scans all known Modbus slave address ranges
4. User confirms discovered devices or manually adds devices
5. async_setup_entry creates SchneiderModbusClient (shared TCP connection)
6. For each device: create SchneiderDeviceCoordinator
7. Each coordinator polls at scan_interval
8. On unload: disconnect client, remove coordinators

### 2.2 Device Auto-Discovery

Scans: Gateway(1), XW Pro(10-29), MPPT 60(30-49), AGS(50-69), SCP(70-89), MPPT 80(170-189), Battery Monitor(190-209).
Reads Device Present (0x0041) and Device Name (0x0000) registers.

**NOTE:** Modbus TCP has NO authentication per official protocol spec.

### 2.3 Error Handling

- Connection failure: entities become unavailable
- Read failure: individual register skipped
- Write failure: logged, no state change
- Device init failure: one device failing does not block others
- Gateway restart: client auto-reconnects on next poll

---

## 3. Register Counts by Device Type

| Device Type | Sensor | Control | Total |
|------------|--------|---------|-------|
| XW Pro (990-6268B) | 48 | 13 | 61 |
| MPPT (990-6270A) | 17 | 6 | 23 |
| AGS (990-6274A) | 8 | 4 | 12 |
| Battery Monitor (990-6278A) | 12 | 0 | 12 |
| Gateway (990-6271B) | 17 | 0 | 17 |
| SCP (990-6272A) | 5 | 5 | 10 |
| **Total** | **107** | **28** | **135** |

See registers.py for complete definitions with all addresses, data types, scales, offsets, and options.

---

## 4. API Specifications (Modbus TCP)

| Parameter | Value |
|-----------|-------|
| Protocol | Modbus TCP/IP |
| Authentication | **None** (unauthenticated by design) |
| Default Port (InsightHome) | 503 |
| Default Port (ComBox) | 502 |
| Timeout | 15 seconds |
| Read Function | 0x03 (Read Holding Registers) |
| Write Function | 0x06 / 0x10 |

### Temperature Conversion

Formula: Celsius = raw_value * 0.01 - 273.0

---

## 5. Config Flow Steps

1. **User Step** -- Gateway connection (host, port, scan interval)
2. **Discover Step** -- Auto-scan all slave address ranges
3. **Devices Step** (manual fallback) -- Add device manually
4. **Add Another Step** -- Prompt to add more or finish

---

## 6. Official Documentation References

| Document | Description |
|----------|-------------|
| 990-6268B | Conext XW Inverter/Charger Modbus (Port 503) |
| 990-6270A | Conext MPPT 80/100 600 Modbus |
| 990-6269A | Conext MPPT 60 Modbus |
| 990-6274A | Conext AGS Modbus |
| 990-6278A | Conext Battery Monitor Modbus |
| 990-6271B | Conext Gateway / InsightHome Modbus |
| 990-6272A | Conext SCP Modbus |

---

## 7. Future Enhancements

- Phase 2: Advanced write operations (equalize, battery type, sell-to-grid)
- Phase 3: InsightCloud API integration
- Phase 4: Fault code decoder, diagnostics
- Phase 5: HA Energy Dashboard optimization
- Phase 6: Automation blueprints
- Phase 7: Additional device support (SW, Grid-Tie)
