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
- Edge case handling (device offline, gateway restart, communication errors)
- InsightCloud API integration (Phase 4 — API docs not publicly available)
- Additional device types if discovered during testing

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
