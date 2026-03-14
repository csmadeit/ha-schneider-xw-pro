# Home Assistant Modules

Third-party Home Assistant custom integration modules maintained by MadeIT.

## Modules

### Schneider Electric Conext XW Pro (`schneider_xw_pro`)

A full HACS-compatible custom integration for the Schneider Electric Conext XW Pro solar inverter/charger ecosystem. Supports **read and write** Modbus TCP operations through the Conext Gateway / InsightHome / InsightFacility.

**Status:** Initial implementation complete — ready for hardware testing.

---

## Session Details

- **Created by:** Chris S (@csmadeit) via Devin AI
- **Session:** [Devin Session](https://app.devin.ai/sessions/4503fa9209474d858e2a17c069e0e1ef)
- **Repository:** [gitlab.cmhtransfer.com/ai-test/homeassistant-modules](https://gitlab.cmhtransfer.com/ai-test/homeassistant-modules)
- **Date:** 2026-03-14

---

## Schneider XW Pro Integration — Files Created

### Backend (Integration Core)

| File | Purpose |
|------|---------|
| `custom_components/schneider_xw_pro/__init__.py` | Integration setup, config entry handling, multi-device coordinator init |
| `custom_components/schneider_xw_pro/const.py` | Constants: domain, device types, default slave addresses, config keys |
| `custom_components/schneider_xw_pro/manifest.json` | HACS manifest with metadata and pymodbus dependency |
| `custom_components/schneider_xw_pro/config_flow.py` | UI config flow for gateway connection + multi-device setup |
| `custom_components/schneider_xw_pro/coordinator.py` | DataUpdateCoordinator per device — polls Modbus registers |
| `custom_components/schneider_xw_pro/modbus_client.py` | pymodbus async TCP client wrapper with read/write/encode/decode |
| `custom_components/schneider_xw_pro/registers.py` | Complete Modbus register definitions for all device types |

### Entity Platforms (UI)

| File | Purpose |
|------|---------|
| `custom_components/schneider_xw_pro/sensor.py` | Read-only sensor entities (voltage, current, power, SOC, energy, etc.) |
| `custom_components/schneider_xw_pro/switch.py` | On/off switches (inverter enable, charger enable, search mode, etc.) |
| `custom_components/schneider_xw_pro/select.py` | Select entities for mode controls (charge mode, AC input mode, EPC mode) |
| `custom_components/schneider_xw_pro/number.py` | Number entities for setpoints (voltage, current limits) |

### Configuration & Translations

| File | Purpose |
|------|---------|
| `custom_components/schneider_xw_pro/strings.json` | Config flow strings |
| `custom_components/schneider_xw_pro/translations/en.json` | English translations |
| `hacs.json` | HACS repository metadata |

---

## Module Structure

```
homeassistant-modules/
├── README.md                          # This file
├── SPECIFICATION.md                   # Full module specification
├── hacs.json                          # HACS repo config
└── custom_components/
    └── schneider_xw_pro/
        ├── __init__.py                # Integration setup
        ├── const.py                   # Constants & defaults
        ├── manifest.json              # HA manifest
        ├── config_flow.py             # UI config flow
        ├── coordinator.py             # Data update coordinator
        ├── modbus_client.py           # Modbus TCP client
        ├── registers.py               # Register definitions (all devices)
        ├── sensor.py                  # Sensor entities
        ├── switch.py                  # Switch entities
        ├── select.py                  # Select entities
        ├── number.py                  # Number entities
        ├── strings.json               # UI strings
        └── translations/
            └── en.json                # English translations
```

---

## What's Ready vs What Needs Implementation

### Ready (Implemented)
- Full HACS-compatible integration structure
- Config flow with multi-device support (gateway IP, port, slave addresses)
- Modbus TCP client with async read/write support (pymodbus)
- Register definitions for XW Pro, MPPT, AGS, Battery Monitor, Gateway, SCP
- Sensor entities for all input registers (voltage, current, power, SOC, energy, temperature, status)
- Switch entities for binary controls (inverter/charger/search mode/grid support enable/disable)
- Select entities for mode controls (charge mode, AC input mode, EPC mode)
- Number entities for setpoints (absorb/float voltage, max charge current, grid support voltage, LBCO, EPC power)
- Device registry integration (each device appears separately in HA)
- Energy dashboard compatible sensors (state_class: total_increasing)
- Options flow for scan interval adjustment

### Needs Testing / Refinement
- Hardware testing with actual Conext Gateway/InsightHome
- Verification of exact Modbus register addresses against physical hardware
- Fine-tuning of register scales, offsets, and data types based on actual device responses
- InsightCloud API integration (Phase 4 — API docs not publicly available)
- Additional device types if discovered during testing

---

## Audit Log

### Audit 1 — 2026-03-14

**Findings & Fixes:**

| # | Severity | Issue | Fix |
|---|----------|-------|-----|
| 1 | CRITICAL | No asyncio.Lock on shared Modbus client — concurrent coordinator polls could corrupt TCP stream | Added `asyncio.Lock` around all `read_register` and `write_register` calls |
| 2 | BUG | Double `disconnect()` in config_flow on success path (called explicitly then again in `finally`) | Removed redundant early `disconnect()`, rely on `finally` block only |
| 3 | BUG | `select.py` missed 2-option non-binary registers (e.g. keys {0, 2}) — fell through both switch and select filters | Changed filter to "writable + has options + NOT binary {0,1}" instead of "> 2 options" |
| 4 | CODE | Unused `from typing import Any` in `__init__.py` | Removed |
| 5 | CODE | Unused `callback` import in `select.py` and `number.py` | Removed |
| 6 | CODE | Unused `NumberDeviceClass` import in `registers.py` | Removed |
| 7 | CODE | `registers.py` bottom-of-file import not annotated | Added `# noqa: E402` and explanatory comment, sorted alphabetically |
| 8 | IMPROVEMENT | `hacs.json` had `zip_release: true` with no CI to produce zips | Removed `zip_release` and `filename` fields |
| 9 | IMPROVEMENT | If any device fails initial Modbus poll, entire integration setup fails | Wrapped `async_config_entry_first_refresh()` in try/except — logs warning, retries on next poll |

**No security issues found.** No hardcoded secrets, no credential exposure, proper input validation via voluptuous schemas.

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
4. Add each device (inverter, MPPT, AGS, etc.) with its Modbus slave address
