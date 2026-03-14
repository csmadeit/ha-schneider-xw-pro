# Schneider Electric Conext XW Pro -- HACS Integration Specification

## Overview

This document specifies the complete design of the Schneider XW Pro HACS integration module for Home Assistant. It covers the data model, Modbus register schema, business logic, API specifications, configuration, and future enhancement roadmap.

---

## 1. Data Schema

### 1.1 Configuration Entry Data

The integration stores its configuration in a Home Assistant config entry with these fields:
- `host` (string): Gateway IP address, e.g. "192.168.1.100"
- `port` (int): Modbus TCP port, default 503
- `scan_interval` (int): Polling interval in seconds, default 30
- `devices` (list): Array of device configurations, each with:
  - `device_type` (string): One of xw_pro, mppt, ags, battery_monitor, gateway, scp
  - `device_name` (string): User-friendly name
  - `slave_id` (int): Modbus slave address

Example with full system (2 inverters, 2 MPPTs, AGS, battery monitor, gateway):

| Device | Type | Slave ID |
|--------|------|----------|
| XW Pro Inverter 1 | xw_pro | 10 |
| XW Pro Inverter 2 | xw_pro | 11 |
| MPPT 80 600 #1 | mppt | 170 |
| MPPT 100 600 #2 | mppt | 171 |
| Auto Generator Start | ags | 20 |
| Battery Monitor | battery_monitor | 30 |
| InsightHome Gateway | gateway | 1 |

### 1.2 Device Types

| Type Key | Label | Default Slave Address |
|----------|-------|-----------------------|
| xw_pro | Conext XW Pro Inverter/Charger | 10 |
| mppt | Conext MPPT Charge Controller | 170 |
| ags | Conext AGS (Auto Generator Start) | 20 |
| battery_monitor | Conext Battery Monitor | 30 |
| gateway | Conext Gateway / InsightHome / InsightFacility | 1 |
| scp | Conext System Control Panel | 40 |

### 1.3 Modbus Register Schema

Each register is defined with:

| Field | Type | Description |
|-------|------|-------------|
| name | string | Human-readable name |
| key | string | Unique entity key |
| address | int | Modbus register address |
| register_type | enum | input (read-only) or holding (read/write) |
| data_type | enum | uint16, int16, uint32, int32, float32, string |
| count | int | Number of registers to read (1 for 16-bit, 2 for 32-bit) |
| scale | float | Multiplier for raw value |
| precision | int | Decimal places for display |
| unit | string | Unit of measurement (V, A, W, kWh, etc.) |
| device_class | string | HA device class |
| state_class | string | HA state class |
| writable | bool | Whether register can be written |
| min_value | float | Minimum writable value |
| max_value | float | Maximum writable value |
| options | dict | Value-to-label mapping for enum registers |
| icon | string | MDI icon |
| entity_category | string | HA entity category (diagnostic, config) |

---

## 2. Business Logic

### 2.1 Connection Lifecycle

1. User adds integration via Config Flow
2. Config flow collects gateway IP, port, devices
3. async_setup_entry creates SchneiderModbusClient (shared TCP connection)
4. For each device: create SchneiderDeviceCoordinator
5. Each coordinator polls device at scan_interval
6. On unload: disconnect client, remove coordinators

### 2.2 Data Flow

- Gateway (Modbus TCP) serves as central hub
- Each slave device (XW Pro, MPPT, AGS, etc.) gets its own Coordinator
- Each Coordinator creates Sensor, Switch, Select, and Number entities
- Single shared TCP client to avoid connection limits

### 2.3 Read Operations

1. Coordinator triggers _async_update_data() every scan_interval seconds
2. For each register in the device's register list: read input/holding registers
3. Decode raw values using data type + scale
4. Map enum values to labels
5. Return merged dict of all register values
6. All entities subscribed to the coordinator update automatically

### 2.4 Write Operations

1. User changes a switch/select/number in HA UI
2. Entity calls coordinator.async_write_register(register, value)
3. Coordinator calls client.write_register(register, slave_id, value)
4. Client encodes value (reverse scale, pack to registers)
5. Client writes via write_register (single) or write_registers (multi)
6. On success, coordinator triggers refresh to read back new state

### 2.5 Error Handling

- **Connection failure:** Logged, entities become unavailable
- **Read failure:** Individual register skipped, others still read
- **Write failure:** Logged, no state change, coordinator does not refresh
- **Decode error:** Register value set to None, entity shows unavailable
- **Gateway restart:** Client auto-reconnects on next poll cycle

---

## 3. Complete Register Specifications

### 3.1 XW Pro Inverter/Charger

**Sensors (Input Registers):**

| Register | Address | Type | Scale | Unit | Description |
|----------|---------|------|-------|------|-------------|
| firmware_version | 0 | uint16 | 1 | - | Firmware version |
| device_status | 50 | uint16 | 1 | - | Operating state (enum) |
| active_faults | 52 | uint32 | 1 | - | Fault bitfield |
| active_warnings | 54 | uint32 | 1 | - | Warning bitfield |
| battery_voltage | 80 | int32 | 0.001 | V | Battery voltage |
| battery_current | 82 | int32 | 0.001 | A | Battery current |
| battery_power | 84 | int32 | 1 | W | Battery power |
| battery_temperature | 86 | int16 | 1 | C | Battery temperature |
| battery_soc | 88 | uint16 | 1 | % | Battery state of charge |
| ac_input_voltage_l1 | 90 | int32 | 0.001 | V | AC input voltage L1 |
| ac_input_voltage_l2 | 92 | int32 | 0.001 | V | AC input voltage L2 |
| ac_input_current | 94 | int32 | 0.001 | A | AC input current |
| ac_input_power | 96 | int32 | 1 | W | AC input power |
| ac_input_frequency | 98 | uint16 | 0.01 | Hz | AC input frequency |
| ac_output_voltage_l1 | 100 | int32 | 0.001 | V | AC output voltage L1 |
| ac_output_voltage_l2 | 102 | int32 | 0.001 | V | AC output voltage L2 |
| ac_output_current | 104 | int32 | 0.001 | A | AC output current |
| ac_output_power | 106 | int32 | 1 | W | AC output power |
| ac_output_frequency | 108 | uint16 | 0.01 | Hz | AC output frequency |
| load_power | 110 | int32 | 1 | W | Total load power |
| total_energy_from_grid | 120 | uint32 | 0.001 | kWh | Lifetime grid import energy |
| total_energy_to_grid | 122 | uint32 | 0.001 | kWh | Lifetime grid export energy |
| total_load_energy | 124 | uint32 | 0.001 | kWh | Lifetime load energy |
| charger_state | 130 | uint16 | 1 | - | Charger state (enum) |
| heatsink_temperature | 140 | int16 | 1 | C | Heatsink temperature |
| transformer_temperature | 142 | int16 | 1 | C | Transformer temperature |

**Controls (Holding Registers):**

| Register | Address | Type | Scale | Range | Description |
|----------|---------|------|-------|-------|-------------|
| inverter_enabled | 150 | uint16 | 1 | 0-1 | Enable/disable inverter |
| charger_enabled | 152 | uint16 | 1 | 0-1 | Enable/disable charger |
| search_mode_enabled | 154 | uint16 | 1 | 0-1 | Enable/disable search mode |
| grid_support_enabled | 156 | uint16 | 1 | 0-1 | Enable/disable grid support |
| force_charge_mode | 160 | uint16 | 1 | 0-2 | Off / Bulk / Float |
| ac_input_mode | 162 | uint16 | 1 | 0-2 | Generator / Grid Support / Grid Tie |
| absorb_voltage_setpoint | 170 | uint16 | 0.1 | 40-64V | Absorption voltage |
| float_voltage_setpoint | 172 | uint16 | 0.1 | 40-64V | Float voltage |
| max_charge_current | 174 | uint16 | 0.1 | 0-100A | Max charge current |
| max_ac_input_current | 176 | uint16 | 0.1 | 0-60A | Max AC input current |
| grid_support_voltage | 178 | uint16 | 0.1 | 40-64V | Grid support trigger voltage |
| low_battery_cut_out | 180 | uint16 | 0.1 | 36-56V | Low battery cut out voltage |
| epc_active_power_setpoint | 200 | int32 | 1 | -6800-6800W | EPC active power |
| epc_mode | 202 | uint16 | 1 | 0-3 | EPC mode (enum) |

### 3.2 MPPT Charge Controller

**Sensors (Input Registers):**

| Register | Address | Type | Scale | Unit | Description |
|----------|---------|------|-------|------|-------------|
| firmware_version | 0 | uint16 | 1 | - | Firmware version |
| device_status | 50 | uint16 | 1 | - | Operating state (enum) |
| active_faults | 52 | uint32 | 1 | - | Fault bitfield |
| pv_voltage | 60 | int32 | 0.001 | V | PV input voltage |
| pv_current | 62 | int32 | 0.001 | A | PV input current |
| pv_power | 64 | int32 | 1 | W | PV input power |
| battery_voltage | 70 | int32 | 0.001 | V | Battery output voltage |
| battery_current | 72 | int32 | 0.001 | A | Battery charge current |
| charge_power | 74 | int32 | 1 | W | Charge power |
| charge_state | 76 | uint16 | 1 | - | Charge state (enum) |
| total_energy_harvested | 80 | uint32 | 0.001 | kWh | Lifetime PV energy |
| daily_energy_harvested | 82 | uint32 | 0.001 | kWh | Daily PV energy |
| heatsink_temperature | 90 | int16 | 1 | C | Heatsink temperature |

**Controls (Holding Registers):**

| Register | Address | Type | Scale | Range | Description |
|----------|---------|------|-------|-------|-------------|
| mppt_enabled | 150 | uint16 | 1 | 0-1 | Enable/disable MPPT |
| absorb_voltage_setpoint | 160 | uint16 | 0.1 | 40-64V | Absorption voltage |
| float_voltage_setpoint | 162 | uint16 | 0.1 | 40-64V | Float voltage |
| max_charge_current | 164 | uint16 | 0.1 | 0-80A | Max charge current |

### 3.3 AGS (Auto Generator Start)

**Sensors:** firmware_version, ags_status (enum), generator_run_time, generator_start_count

**Controls:** generator_force_on (on/off), ags_enabled (on/off), start_voltage_setpoint, stop_voltage_setpoint, max_gen_run_time

### 3.4 Battery Monitor

**Sensors:** firmware_version, battery_voltage, battery_current, battery_soc, battery_temperature, battery_power, days_since_full_charge, min_battery_voltage, max_battery_voltage

**Controls:** None

### 3.5 Gateway / InsightHome

**Sensors:** firmware_version, system_status, total_system_pv_power, total_system_load_power, total_system_battery_power, total_system_grid_power, system_battery_soc, connected_devices_count, total_system_pv_energy, total_system_grid_import_energy, total_system_grid_export_energy, total_system_load_energy

**Controls:** None

---

## 4. API Specifications (Modbus TCP)

### 4.1 Connection Parameters

| Parameter | Value |
|-----------|-------|
| Protocol | Modbus TCP/IP |
| Default Port (InsightHome) | 503 |
| Default Port (ComBox) | 502 |
| Timeout | 15 seconds |
| Retry Delay | 2 seconds |

### 4.2 Read Request

- Function Code: 0x04 (Read Input Registers) or 0x03 (Read Holding Registers)
- Slave Address: Device-specific (e.g., 10 for XW Pro)
- Starting Address: Register address from table
- Quantity: Register count (1 for 16-bit, 2 for 32-bit)
- Response: Raw register values (big-endian)

### 4.3 Write Request

- Function Code: 0x06 (Write Single Register) or 0x10 (Write Multiple Registers)
- Slave Address: Device-specific
- Starting Address: Register address from table
- Value: Encoded value (reverse-scaled, big-endian packed)
- Response: Echo of written address and value

### 4.4 Data Type Encoding

| Type | Registers | Encoding |
|------|-----------|----------|
| uint16 | 1 | Raw unsigned 16-bit |
| int16 | 1 | Two's complement 16-bit |
| uint32 | 2 | High word first (big-endian) |
| int32 | 2 | Two's complement, high word first |
| float32 | 2 | IEEE 754, high word first |
| string | N | 2 chars per register |

---

## 5. Permissions and Settings

### 5.1 Config Flow Steps

1. **User Step** -- Gateway connection (host, port, scan interval)
2. **Devices Step** -- Add device (type, name, slave address) -- repeatable
3. **Add Another Step** -- Prompt to add more devices or finish

### 5.2 Options Flow

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| scan_interval | int | 30 | Polling interval in seconds |

### 5.3 Entity Categories

| Category | Entities |
|----------|---------|
| Default | All power, voltage, current, energy, SOC sensors; all controls |
| Diagnostic | Firmware version, fault codes, warning codes, temperatures |

---

## 6. Modbus Documentation References

| Document | Description |
|----------|-------------|
| 503-0246-01-01_RevA.4 | XW/XW+ inverter Modbus map |
| 503-0252-01-01_RevA.4 | MPPT 80 charge controller Modbus map |
| 503-0248-01-01_RevA.4 | MPPT 60 charge controller Modbus map |
| 503-0247-01-01_RevA.4 | AGS Modbus map |
| 503-0261-01-01_RevA.4 | Battery Monitor Modbus map |
| 503-0244-01-01_RevA.4 | Conext SW device Modbus map |
| 503-0253-01-01_RevA.4 | ComBox/Gateway converter Modbus map |
| IH-IF-Gateway_Modbus-Maps | Gateway/InsightHome/InsightFacility maps |

### Key URLs

- Schneider Electric InsightHome Modbus Maps: https://www.se.com/us/en/download/document/IH-IF-Gateway_Modbus-Maps/
- DIY Solar Forum Full Modbus Maps + HA Thread: https://diysolarforum.com/threads/all-modbus-maps-and-schneider-xw-6848-pro-integration-into-home-assistant-via-modbus-tcp.62707/
- DIY Solar Forum XW Pro Modbus: https://diysolarforum.com/threads/schneider-xw-pro-modbus.94314/
- DIY Solar Forum EPC Commands: https://diysolarforum.com/threads/schneider-xw-external-power-control-epc-commands.98154/
- XW Pro Operation Guide: https://solar.se.com/us/wp-content/uploads/sites/7/2023/02/990-91227F-01.pdf

---

## 7. Future Enhancements Roadmap

### Phase 2 -- Advanced Write Operations
- Equalize charge command
- Battery type configuration
- AC frequency setpoints
- Sell-to-grid configuration
- Time-of-use scheduling integration

### Phase 3 -- InsightCloud API
- REST API integration for cloud monitoring data
- Historical data retrieval
- System firmware version tracking
- Remote configuration sync

### Phase 4 -- Diagnostics and Monitoring
- Fault code decoder with human-readable descriptions
- Warning history tracking
- Device uptime monitoring
- Communication quality metrics

### Phase 5 -- Energy Dashboard Optimization
- Proper energy flow sensors for HA Energy Dashboard
- Solar production, grid import/export, battery charge/discharge
- Self-consumption ratio calculation
- Cost tracking integration

### Phase 6 -- Automation Helpers
- Blueprint templates for common automations (time-of-use optimization, storm mode, generator auto-start based on SOC, load shedding)
- Custom services for advanced control

### Phase 7 -- Additional Device Support
- Conext SW inverter/charger
- Grid-Tie inverter
- Additional MPPT models (MPPT 60)
- Third-party Xanbus devices
