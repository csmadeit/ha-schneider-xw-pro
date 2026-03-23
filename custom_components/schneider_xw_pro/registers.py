"""Modbus register definitions for all Schneider Conext device types.

Based on OFFICIAL Schneider Electric Modbus Interface Specifications (Port 503):
- 990-6268B: Conext XW Inverter/Chargers
- 990-6270A: Conext MPPT 80/100 600 Solar Charge Controllers
- 990-6269A: Conext MPPT 60 Solar Charge Controller
- 990-6274A: Conext Automatic Generator Start (AGS)
- 990-6278A: Conext Battery Monitor
- 990-6271B: Conext Gateway / InsightHome / InsightFacility
- 990-6272A: Conext System Control Panel (SCP)

All register addresses are ZERO-BASED (as transmitted on-the-wire in the Modbus frame).
Register numbers in the PDF are 1-based; register addresses are 0-based.

Temperature registers use scale=0.01 and offset=-273.0 (Kelvin to Celsius).
Voltage/current registers typically use scale=0.001.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from homeassistant.components.sensor import SensorDeviceClass, SensorStateClass
from homeassistant.const import (
    PERCENTAGE,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)


class RegisterType(Enum):
    """Modbus register type."""

    INPUT = "input"
    HOLDING = "holding"


class DataType(Enum):
    """Modbus data type."""

    UINT16 = "uint16"
    INT16 = "int16"
    UINT32 = "uint32"
    INT32 = "int32"
    FLOAT32 = "float32"
    STRING = "string"


@dataclass
class ModbusRegisterDefinition:
    """Definition of a single Modbus register."""

    name: str
    key: str
    address: int
    register_type: RegisterType
    data_type: DataType
    count: int = 1
    scale: float = 1.0
    offset: float = 0.0
    precision: int = 0
    unit: str | None = None
    device_class: str | None = None
    state_class: str | None = None
    writable: bool = False
    min_value: float | None = None
    max_value: float | None = None
    options: dict[int, str] | None = None
    icon: str | None = None
    entity_category: str | None = None


# =============================================================================
# XW PRO INVERTER/CHARGER REGISTERS (slave address range: 10..29)
# Source: 990-6268B "Conext XW Modbus 503 spec"
# =============================================================================

XW_PRO_SENSOR_REGISTERS: list[ModbusRegisterDefinition] = [
    # Reg 31, addr 0x001E = Firmware Version (uint32, r)
    ModbusRegisterDefinition(
        name="Firmware Version",
        key="firmware_version",
        address=0x001E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        icon="mdi:information-outline",
        entity_category="diagnostic",
    ),
    # Reg 65, addr 0x0040 = Device State (uint16, r)
    ModbusRegisterDefinition(
        name="Device State",
        key="device_state",
        address=0x0040,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Hibernate", 1: "Power Save", 2: "Safe Mode", 3: "Operating", 4: "Diagnostic Mode", 5: "Remote Power Off", 255: "Data Not Available"},
        icon="mdi:state-machine",
    ),
    # Reg 66, addr 0x0041 = Device Present (uint16, r)
    ModbusRegisterDefinition(
        name="Device Present",
        key="device_present",
        address=0x0041,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Inactive", 1: "Active"},
        entity_category="diagnostic",
    ),
    # Reg 72, addr 0x0047 = Inverter Enabled Status (uint16, r)
    ModbusRegisterDefinition(
        name="Inverter Enabled Status",
        key="inverter_enabled_status",
        address=0x0047,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:power",
    ),
    # Reg 73, addr 0x0048 = Charger Enabled Status (uint16, r)
    ModbusRegisterDefinition(
        name="Charger Enabled Status",
        key="charger_enabled_status",
        address=0x0048,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:battery-charging",
    ),
    # Reg 76, addr 0x004B = Active Faults (uint16, r)
    ModbusRegisterDefinition(
        name="Active Faults",
        key="active_faults",
        address=0x004B,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "No Faults", 1: "Active Faults"},
        icon="mdi:alert-circle",
        entity_category="diagnostic",
    ),
    # Reg 77, addr 0x004C = Active Warnings (uint16, r)
    ModbusRegisterDefinition(
        name="Active Warnings",
        key="active_warnings",
        address=0x004C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "No Warnings", 1: "Active Warnings"},
        icon="mdi:alert",
        entity_category="diagnostic",
    ),
    # Reg 78, addr 0x004D = Charge Mode Status (uint16, r)
    ModbusRegisterDefinition(
        name="Charge Mode Status",
        key="charge_mode_status",
        address=0x004D,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Stand Alone", 1: "Primary", 2: "Secondary"},
        icon="mdi:battery-charging-wireless",
    ),
    # Reg 81, addr 0x0050 = DC Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="DC Voltage",
        key="dc_voltage",
        address=0x0050,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    # Reg 83, addr 0x0052 = DC Current (sint32, r, A)
    ModbusRegisterDefinition(
        name="DC Current",
        key="dc_current",
        address=0x0052,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        scale=0.001,
        precision=3,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    # Reg 85, addr 0x0054 = DC Power (sint32, r, W)
    ModbusRegisterDefinition(
        name="DC Power",
        key="dc_power",
        address=0x0054,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
    ),
    # Reg 87, addr 0x0056 = Battery Temperature (uint16, r, K)
    ModbusRegisterDefinition(
        name="Battery Temperature",
        key="battery_temperature",
        address=0x0056,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        scale=0.01,
        offset=-273.0,
        precision=1,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    # Reg 89, addr 0x0058 = Invert DC Current (uint32, r, A)
    ModbusRegisterDefinition(
        name="Invert DC Current",
        key="invert_dc_current",
        address=0x0058,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=3,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    # Reg 91, addr 0x005A = Invert DC Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="Invert DC Power",
        key="invert_dc_power",
        address=0x005A,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
    ),
    # Reg 93, addr 0x005C = Charge DC Current (uint32, r, A)
    ModbusRegisterDefinition(
        name="Charge DC Current",
        key="charge_dc_current",
        address=0x005C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=3,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    # Reg 95, addr 0x005E = Charge DC Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="Charge DC Power",
        key="charge_dc_power",
        address=0x005E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
    ),
    # Reg 97, addr 0x0060 = Charge DC Power % (uint16, r)
    ModbusRegisterDefinition(
        name="Charge DC Power Percentage",
        key="charge_dc_power_pct",
        address=0x0060,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        unit=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging-high",
    ),
    # Reg 98, addr 0x0061 = AC1 Frequency (uint16, r, Hz)
    ModbusRegisterDefinition(
        name="AC1 Input Frequency",
        key="ac1_input_frequency",
        address=0x0061,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        scale=0.01,
        precision=2,
        unit=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 99, addr 0x0062 = AC1 Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="AC1 Input Voltage",
        key="ac1_input_voltage",
        address=0x0062,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 101, addr 0x0064 = AC1 Current (sint32, r, A)
    ModbusRegisterDefinition(
        name="AC1 Input Current",
        key="ac1_input_current",
        address=0x0064,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 103, addr 0x0066 = AC1 Power (sint32, r, W)
    ModbusRegisterDefinition(
        name="AC1 Input Power",
        key="ac1_input_power",
        address=0x0066,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
    ),
    # Reg 111, addr 0x006E = AC1 L1 Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="AC1 L1 Voltage",
        key="ac1_l1_voltage",
        address=0x006E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 113, addr 0x0070 = AC1 L2 Current (sint32, r, A)
    ModbusRegisterDefinition(
        name="AC1 L2 Current",
        key="ac1_l2_current",
        address=0x0070,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 115, addr 0x0072 = AC1 L2 Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="AC1 L2 Voltage",
        key="ac1_l2_voltage",
        address=0x0072,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 117, addr 0x0074 = AC1 L1 Current (sint32, r, A)
    ModbusRegisterDefinition(
        name="AC1 L1 Current",
        key="ac1_l1_current",
        address=0x0074,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 124, addr 0x007B = Charger Status (uint16, r)
    ModbusRegisterDefinition(
        name="Charger Status",
        key="charger_status",
        address=0x007B,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Not Charging", 1: "Bulk", 2: "Absorption", 3: "Overcharge", 4: "Equalize", 5: "Float", 6: "No Float", 7: "Constant VI", 8: "Charger Disabled", 9: "Qualifying AC", 10: "Qualifying APS"},
        icon="mdi:battery-charging-wireless",
    ),
    # Reg 127, addr 0x007E = AC1 Output Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="AC1 Output Voltage",
        key="ac1_output_voltage",
        address=0x007E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 129, addr 0x0080 = AC1 Output Current (uint32, r, A)
    ModbusRegisterDefinition(
        name="AC1 Output Current",
        key="ac1_output_current",
        address=0x0080,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 131, addr 0x0082 = AC1 Output Frequency (uint16, r, Hz)
    ModbusRegisterDefinition(
        name="AC1 Output Frequency",
        key="ac1_output_frequency",
        address=0x0082,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        scale=0.01,
        precision=2,
        unit=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 133, addr 0x0084 = AC1 Output Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="AC1 Output Power",
        key="ac1_output_power",
        address=0x0084,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:home-lightning-bolt",
    ),
    # Reg 141, addr 0x008C = AC Load Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="AC Load Voltage",
        key="ac_load_voltage",
        address=0x008C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 151, addr 0x0096 = AC Load Current (sint32, r, A)
    ModbusRegisterDefinition(
        name="AC Load Current",
        key="ac_load_current",
        address=0x0096,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 153, addr 0x0098 = AC Load Frequency (uint16, r, Hz)
    ModbusRegisterDefinition(
        name="AC Load Frequency",
        key="ac_load_frequency",
        address=0x0098,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        scale=0.01,
        precision=2,
        unit=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 155, addr 0x009A = AC Load Power (sint32, r, W)
    ModbusRegisterDefinition(
        name="AC Load Power",
        key="ac_load_power",
        address=0x009A,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
    ),
    # Reg 163, addr 0x00A2 = AC2 Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="AC2 Voltage",
        key="ac2_voltage",
        address=0x00A2,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 167, addr 0x00A6 = AC2 Frequency (uint16, r, Hz)
    ModbusRegisterDefinition(
        name="AC2 Frequency",
        key="ac2_frequency",
        address=0x00A6,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        scale=0.01,
        precision=2,
        unit=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 173, addr 0x00AC = AC2 Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="AC2 Power",
        key="ac2_power",
        address=0x00AC,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:engine",
    ),
    # Reg 193, addr 0x00C0 = Switch Operating State (uint16, r)
    ModbusRegisterDefinition(
        name="Switch Operating State",
        key="switch_operating_state",
        address=0x00C0,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={800: "Inactive", 801: "Input1 Active", 802: "Input2 Active", 803: "Input1 Delay", 804: "Input2 Delay"},
        icon="mdi:toggle-switch",
        entity_category="diagnostic",
    ),
    # Reg 194, addr 0x00C1 = Switch Mode (uint16, r)
    ModbusRegisterDefinition(
        name="Switch Mode",
        key="switch_mode",
        address=0x00C1,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Unknown", 1: "Grid Priority", 2: "Generator Priority"},
        icon="mdi:toggle-switch-variant",
        entity_category="diagnostic",
    ),
    # Reg 229, addr 0x00E4 = Energy From Battery Lifetime (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Energy From Battery Lifetime",
        key="energy_from_battery_lifetime",
        address=0x00E4,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-minus",
    ),
    # Reg 253, addr 0x00FC = Energy To Battery Lifetime (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Energy To Battery Lifetime",
        key="energy_to_battery_lifetime",
        address=0x00FC,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-charging",
    ),
    # Reg 261, addr 0x0104 = Grid Input Energy Today (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Grid Input Energy Today",
        key="grid_input_energy_today",
        address=0x0104,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower-import",
    ),
    # Reg 277, addr 0x0114 = Grid Input Energy Lifetime (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Grid Input Energy Lifetime",
        key="grid_input_energy_lifetime",
        address=0x0114,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower-import",
    ),
    # Reg 285, addr 0x011C = Grid Output Energy Today (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Grid Output Energy Today",
        key="grid_output_energy_today",
        address=0x011C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower-export",
    ),
    # Reg 301, addr 0x012C = Grid Output Energy Lifetime (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Grid Output Energy Lifetime",
        key="grid_output_energy_lifetime",
        address=0x012C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:transmission-tower-export",
    ),
    # Reg 309, addr 0x0134 = Load Output Energy Today (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Load Output Energy Today",
        key="load_output_energy_today",
        address=0x0134,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
    ),
    # Reg 325, addr 0x0144 = Load Output Energy Lifetime (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Load Output Energy Lifetime",
        key="load_output_energy_lifetime",
        address=0x0144,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:lightning-bolt",
    ),
    # Reg 349, addr 0x015C = Generator Input Energy Lifetime (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Generator Input Energy Lifetime",
        key="generator_input_energy_lifetime",
        address=0x015C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:engine",
    ),
]


# --- XW Pro Writable Holding Registers ---
# Source: 990-6268B pages 14-18
XW_PRO_CONTROL_REGISTERS: list[ModbusRegisterDefinition] = [
    # Reg 354, addr 0x0161 = Inverter Enable/Disable (uint16, rw)
    ModbusRegisterDefinition(
        name="Inverter Enable",
        key="inverter_enable",
        address=0x0161,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        min_value=0,
        max_value=1,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:power",
    ),
    # Reg 355, addr 0x0162 = Grid Support Sell Enable (uint16, rw)
    ModbusRegisterDefinition(
        name="Grid Support Sell Enable",
        key="grid_support_sell_enable",
        address=0x0162,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        min_value=0,
        max_value=1,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:transmission-tower",
    ),
    # Reg 356, addr 0x0163 = Force Sell (uint16, rw)
    ModbusRegisterDefinition(
        name="Force Sell",
        key="force_sell",
        address=0x0163,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        min_value=0,
        max_value=1,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:cash",
    ),
    # Reg 357, addr 0x0164 = Charger Enable/Disable (uint16, rw)
    ModbusRegisterDefinition(
        name="Charger Enable",
        key="charger_enable",
        address=0x0164,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        min_value=0,
        max_value=1,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:battery-charging",
    ),
    # Reg 358, addr 0x0165 = Force Charger State (uint16, rw)
    ModbusRegisterDefinition(
        name="Force Charger State",
        key="force_charger_state",
        address=0x0165,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        options={1: "Bulk", 2: "Float", 3: "No Float"},
        icon="mdi:battery-charging-high",
    ),
    # Reg 359, addr 0x0166 = Operating Mode (uint16, rw)
    ModbusRegisterDefinition(
        name="Operating Mode",
        key="operating_mode",
        address=0x0166,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        options={2: "Standby", 3: "Operating"},
        icon="mdi:tune",
    ),
    # Reg 362, addr 0x0169 = Search Mode (uint16, rw)
    ModbusRegisterDefinition(
        name="Search Mode",
        key="search_mode",
        address=0x0169,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        min_value=0,
        max_value=1,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:magnify",
    ),
    # Reg 368, addr 0x016F = Maximum Charge Rate (uint16, rw, %)
    ModbusRegisterDefinition(
        name="Maximum Charge Rate",
        key="max_charge_rate",
        address=0x016F,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        unit=PERCENTAGE,
        writable=True,
        min_value=0,
        max_value=100,
        icon="mdi:current-dc",
    ),
    # Reg 377, addr 0x0178 = Grid Support Voltage (uint32, rw, V)
    ModbusRegisterDefinition(
        name="Grid Support Voltage",
        key="grid_support_voltage",
        address=0x0178,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        writable=True,
        icon="mdi:transmission-tower",
    ),
    # Reg 381, addr 0x017C = Low Battery Cut Out (uint32, rw, V)
    ModbusRegisterDefinition(
        name="Low Battery Cut Out",
        key="low_battery_cut_out",
        address=0x017C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        writable=True,
        icon="mdi:battery-alert",
    ),
    # Reg 392, addr 0x0187 = AC Priority (uint16, rw)
    ModbusRegisterDefinition(
        name="AC Priority",
        key="ac_priority",
        address=0x0187,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        options={0: "Force AC Disqualify", 1: "Grid Priority (AC1)", 2: "Generator Priority (AC2)"},
        icon="mdi:power-plug",
    ),
    # Reg 393, addr 0x0188 = AC1 Breaker Size (uint16, rw, A)
    ModbusRegisterDefinition(
        name="AC1 Breaker Size",
        key="ac1_breaker_size",
        address=0x0188,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        scale=0.01,
        unit=UnitOfElectricCurrent.AMPERE,
        writable=True,
        icon="mdi:current-ac",
    ),
    # Reg 394, addr 0x0189 = AC2 Breaker Size (uint16, rw, A)
    ModbusRegisterDefinition(
        name="AC2 Breaker Size",
        key="ac2_breaker_size",
        address=0x0189,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        scale=0.01,
        unit=UnitOfElectricCurrent.AMPERE,
        writable=True,
        icon="mdi:current-ac",
    ),
]


# =============================================================================
# MPPT 80/100 600 CHARGE CONTROLLER REGISTERS (slave address range: 170..189)
# Source: 990-6270A "Conext MPPT 80/100 600 Modbus 503 spec"
# =============================================================================

MPPT_SENSOR_REGISTERS: list[ModbusRegisterDefinition] = [
    # Reg 31, addr 0x001E = Firmware Version (uint32, r)
    ModbusRegisterDefinition(
        name="Firmware Version",
        key="firmware_version",
        address=0x001E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        icon="mdi:information-outline",
        entity_category="diagnostic",
    ),
    # Reg 65, addr 0x0040 = Device State (uint16, r)
    ModbusRegisterDefinition(
        name="Device State",
        key="device_state",
        address=0x0040,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Hibernate", 1: "Power Save", 2: "Safe Mode", 3: "Operating", 4: "Diagnostic Mode", 5: "Remote Power Off", 255: "Data Not Available"},
        icon="mdi:state-machine",
    ),
    # Reg 67, addr 0x0042 = Device Present (uint16, r)
    ModbusRegisterDefinition(
        name="Device Present",
        key="device_present",
        address=0x0042,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Inactive", 1: "Active"},
        entity_category="diagnostic",
    ),
    # Reg 69, addr 0x0044 = Active Faults (uint16, r)
    ModbusRegisterDefinition(
        name="Active Faults",
        key="active_faults",
        address=0x0044,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "No Faults", 1: "Active Faults"},
        icon="mdi:alert-circle",
        entity_category="diagnostic",
    ),
    # Reg 70, addr 0x0045 = Active Warnings (uint16, r)
    ModbusRegisterDefinition(
        name="Active Warnings",
        key="active_warnings",
        address=0x0045,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "No Warnings", 1: "Active Warnings"},
        icon="mdi:alert",
        entity_category="diagnostic",
    ),
    # Reg 74, addr 0x0049 = Charger Status (uint16, r)
    ModbusRegisterDefinition(
        name="Charger Status",
        key="charger_status",
        address=0x0049,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Not Charging", 1: "Bulk", 2: "Absorption", 3: "Float", 4: "Equalize"},
        icon="mdi:battery-charging-wireless",
    ),
    # Reg 77, addr 0x004C = PV Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="PV Voltage",
        key="pv_voltage",
        address=0x004C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-panel",
    ),
    # Reg 79, addr 0x004E = PV Current (uint32, r, A)
    ModbusRegisterDefinition(
        name="PV Current",
        key="pv_current",
        address=0x004E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-panel",
    ),
    # Reg 81, addr 0x0050 = PV Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="PV Power",
        key="pv_power",
        address=0x0050,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    # Reg 87, addr 0x0056 = Battery Temperature (uint16, r, K)
    ModbusRegisterDefinition(
        name="Battery Temperature",
        key="battery_temperature",
        address=0x0056,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        scale=0.01,
        offset=-273.0,
        precision=1,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    # Reg 89, addr 0x0058 = DC Output Voltage (sint32, r, V)
    ModbusRegisterDefinition(
        name="DC Output Voltage",
        key="dc_output_voltage",
        address=0x0058,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    # Reg 91, addr 0x005A = DC Output Current (sint32, r, A)
    ModbusRegisterDefinition(
        name="DC Output Current",
        key="dc_output_current",
        address=0x005A,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    # Reg 93, addr 0x005C = DC Output Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="DC Output Power",
        key="dc_output_power",
        address=0x005C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
    ),
    # Reg 117, addr 0x0074 = Energy From PV Today (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Energy From PV Today",
        key="energy_from_pv_today",
        address=0x0074,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:white-balance-sunny",
    ),
    # Reg 133, addr 0x0084 = Energy From PV Lifetime (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Energy From PV Lifetime",
        key="energy_from_pv_lifetime",
        address=0x0084,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:solar-power-variant",
    ),
    # Reg 141, addr 0x008C = Energy To Battery Today (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Energy To Battery Today",
        key="energy_to_battery_today",
        address=0x008C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-charging",
    ),
    # Reg 157, addr 0x009C = Energy To Battery Lifetime (uint32, r, kWh)
    ModbusRegisterDefinition(
        name="Energy To Battery Lifetime",
        key="energy_to_battery_lifetime",
        address=0x009C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        icon="mdi:battery-plus",
    ),
]

MPPT_CONTROL_REGISTERS: list[ModbusRegisterDefinition] = [
    # Reg 161, addr 0x00A0 = MPPT Enable (uint16, rw)
    ModbusRegisterDefinition(
        name="MPPT Enable",
        key="mppt_enable",
        address=0x00A0,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        min_value=0,
        max_value=1,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:solar-panel",
    ),
    # Reg 171, addr 0x00AA = Force Charger State (uint16, rw)
    ModbusRegisterDefinition(
        name="Force Charger State",
        key="force_charger_state",
        address=0x00AA,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        options={1: "Bulk", 2: "Float", 3: "No Float"},
        icon="mdi:battery-charging-high",
    ),
    # Reg 173, addr 0x00AC = Operating Mode (uint16, rw)
    ModbusRegisterDefinition(
        name="Operating Mode",
        key="operating_mode",
        address=0x00AC,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        options={2: "Standby", 3: "Operating"},
        icon="mdi:tune",
    ),
    # Reg 177, addr 0x00B0 = Absorb Voltage Set Point (uint32, rw, V)
    ModbusRegisterDefinition(
        name="Absorb Voltage Setpoint",
        key="absorb_voltage_setpoint",
        address=0x00B0,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        writable=True,
        icon="mdi:flash",
    ),
    # Reg 179, addr 0x00B2 = Float Voltage Set Point (uint32, rw, V)
    ModbusRegisterDefinition(
        name="Float Voltage Setpoint",
        key="float_voltage_setpoint",
        address=0x00B2,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        writable=True,
        icon="mdi:flash",
    ),
    # Reg 187, addr 0x00BA = Maximum Charge Rate (uint16, rw, %)
    ModbusRegisterDefinition(
        name="Maximum Charge Rate",
        key="max_charge_rate",
        address=0x00BA,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        unit=PERCENTAGE,
        writable=True,
        min_value=0,
        max_value=100,
        icon="mdi:current-dc",
    ),
]


# =============================================================================
# AGS (AUTOMATIC GENERATOR START) REGISTERS (slave address range: 50..69)
# Source: 990-6274A "Conext AGS Modbus 503 spec"
# =============================================================================

AGS_SENSOR_REGISTERS: list[ModbusRegisterDefinition] = [
    # Reg 31, addr 0x001E = Firmware Version (uint32, r)
    ModbusRegisterDefinition(
        name="Firmware Version",
        key="firmware_version",
        address=0x001E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        icon="mdi:information-outline",
        entity_category="diagnostic",
    ),
    # Reg 65, addr 0x0040 = Device State (uint16, r)
    ModbusRegisterDefinition(
        name="Device State",
        key="device_state",
        address=0x0040,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Hibernate", 1: "Power Save", 2: "Safe Mode", 3: "Operating", 4: "Diagnostic Mode", 5: "Remote Power Off", 255: "Data Not Available"},
        icon="mdi:state-machine",
    ),
    # Reg 66, addr 0x0041 = Device Present (uint16, r)
    ModbusRegisterDefinition(
        name="Device Present",
        key="device_present",
        address=0x0041,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Inactive", 1: "Active"},
        entity_category="diagnostic",
    ),
    # Reg 67, addr 0x0042 = Auto Generator State (uint16, r)
    ModbusRegisterDefinition(
        name="Generator State",
        key="generator_state",
        address=0x0042,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Quiet Time", 1: "Auto On", 2: "Auto Off", 3: "Manual On", 4: "Manual Off", 5: "Gen Shutdown", 6: "Ext Shutdown", 7: "AGS Fault", 8: "Suspend", 9: "Not Operating"},
        icon="mdi:engine",
    ),
    # Reg 68, addr 0x0043 = Auto Generator Action (uint16, r)
    ModbusRegisterDefinition(
        name="Generator Action",
        key="generator_action",
        address=0x0043,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Preheating", 1: "Start Delay", 2: "Cranking", 3: "Starter Cooling", 4: "Warming Up", 5: "Cooling Down", 6: "Spinning Down", 7: "Shutdown Bypass", 8: "Stopping", 9: "Running", 10: "Stopped", 11: "Crank Delay"},
        icon="mdi:engine",
    ),
    # Reg 69, addr 0x0044 = Generator On Reason (uint16, r)
    ModbusRegisterDefinition(
        name="Generator On Reason",
        key="generator_on_reason",
        address=0x0044,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Not On", 1: "DC Voltage Low", 2: "Battery SOC Low", 3: "AC Current High", 4: "Contact Closed", 5: "Manual On", 6: "Exercise", 7: "Non Quiet Time"},
        icon="mdi:engine",
        entity_category="diagnostic",
    ),
    # Reg 71, addr 0x0046 = Active Faults Flag (uint16, r)
    ModbusRegisterDefinition(
        name="Active Faults",
        key="active_faults",
        address=0x0046,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "No Faults", 1: "Active Faults"},
        icon="mdi:alert-circle",
        entity_category="diagnostic",
    ),
    # Reg 72, addr 0x0047 = Active Warnings Flag (uint16, r)
    ModbusRegisterDefinition(
        name="Active Warnings",
        key="active_warnings",
        address=0x0047,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "No Warnings", 1: "Active Warnings"},
        icon="mdi:alert",
        entity_category="diagnostic",
    ),
]

AGS_CONTROL_REGISTERS: list[ModbusRegisterDefinition] = [
    # Reg 77, addr 0x004C = Operating Mode (uint16, rw)
    ModbusRegisterDefinition(
        name="Operating Mode",
        key="operating_mode",
        address=0x004C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        options={2: "Standby", 3: "Operating"},
        icon="mdi:tune",
    ),
    # Reg 78, addr 0x004D = Generator Mode (uint16, rw)
    ModbusRegisterDefinition(
        name="Generator Mode",
        key="generator_mode",
        address=0x004D,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        options={0: "Off", 1: "On", 2: "Automatic", 3: "Force On Auto Off"},
        icon="mdi:engine",
    ),
    # Reg 84, addr 0x0053 = Auto Start On DC V (uint16, rw)
    ModbusRegisterDefinition(
        name="Auto Start On DC Voltage",
        key="auto_start_dc_v",
        address=0x0053,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        min_value=0,
        max_value=1,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:engine",
    ),
    # Reg 107, addr 0x006A = Max Gen Run Time (uint16, rw, hours)
    ModbusRegisterDefinition(
        name="Maximum Generator Run Time",
        key="max_gen_run_time",
        address=0x006A,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        scale=0.016667,
        unit=UnitOfTime.HOURS,
        writable=True,
        min_value=0,
        max_value=24,
        icon="mdi:timer",
    ),
]


# =============================================================================
# BATTERY MONITOR REGISTERS (slave address range: 190..209)
# Source: 990-6278A "Conext Battery Monitor Modbus 503 spec"
# =============================================================================

BATTERY_MONITOR_SENSOR_REGISTERS: list[ModbusRegisterDefinition] = [
    # Reg 31, addr 0x001E = Firmware Version (uint32, r)
    ModbusRegisterDefinition(
        name="Firmware Version",
        key="firmware_version",
        address=0x001E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        icon="mdi:information-outline",
        entity_category="diagnostic",
    ),
    # Reg 65, addr 0x0040 = Device State (uint16, r)
    ModbusRegisterDefinition(
        name="Device State",
        key="device_state",
        address=0x0040,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        icon="mdi:state-machine",
    ),
    # Reg 66, addr 0x0041 = Device Present (uint16, r)
    ModbusRegisterDefinition(
        name="Device Present",
        key="device_present",
        address=0x0041,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Inactive", 1: "Active"},
        entity_category="diagnostic",
    ),
    # Reg 71, addr 0x0046 = Battery Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="Battery Voltage",
        key="battery_voltage",
        address=0x0046,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    # Reg 73, addr 0x0048 = Battery Current (sint32, r, A)
    ModbusRegisterDefinition(
        name="Battery Current",
        key="battery_current",
        address=0x0048,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    # Reg 75, addr 0x004A = Battery Temperature (uint32, r, K)
    ModbusRegisterDefinition(
        name="Battery Temperature",
        key="battery_temperature",
        address=0x004A,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.01,
        offset=-273.0,
        precision=1,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
    # Reg 77, addr 0x004C = Battery SOC (uint32, r, %)
    ModbusRegisterDefinition(
        name="Battery SOC",
        key="battery_soc",
        address=0x004C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-heart-variant",
    ),
    # Reg 79, addr 0x004E = Battery State of Health (uint32, r, %)
    ModbusRegisterDefinition(
        name="Battery State of Health",
        key="battery_soh",
        address=0x004E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=PERCENTAGE,
        icon="mdi:battery-heart",
    ),
    # Reg 89, addr 0x0058 = Battery Capacity Remaining (uint32, r, Ah)
    ModbusRegisterDefinition(
        name="Battery Capacity Remaining",
        key="battery_capacity_remaining",
        address=0x0058,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        icon="mdi:battery",
        entity_category="diagnostic",
    ),
    # Reg 95, addr 0x005E = Battery Time To Full (uint32, r, s)
    ModbusRegisterDefinition(
        name="Battery Time To Full",
        key="battery_time_to_full",
        address=0x005E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfTime.SECONDS,
        icon="mdi:timer-sand",
    ),
    # Reg 97, addr 0x0060 = Battery Time To Discharge (uint32, r, s)
    ModbusRegisterDefinition(
        name="Battery Time To Discharge",
        key="battery_time_to_discharge",
        address=0x0060,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfTime.SECONDS,
        icon="mdi:timer-sand-empty",
    ),
    # Reg 111, addr 0x006E = Number of Charge Cycles (uint16, r)
    ModbusRegisterDefinition(
        name="Charge Cycles",
        key="charge_cycles",
        address=0x006E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        icon="mdi:counter",
        entity_category="diagnostic",
    ),
]

BATTERY_MONITOR_CONTROL_REGISTERS: list[ModbusRegisterDefinition] = []


# =============================================================================
# GATEWAY / INSIGHTHOME / INSIGHTFACILITY REGISTERS (slave address: 1)
# Source: 990-6271B "Conext Gateway Modbus 503 spec"
# =============================================================================

GATEWAY_SENSOR_REGISTERS: list[ModbusRegisterDefinition] = [
    # Reg 31, addr 0x001E = Firmware Version (str20, r)
    ModbusRegisterDefinition(
        name="Firmware Version",
        key="firmware_version",
        address=0x001E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.STRING,
        count=10,
        icon="mdi:information-outline",
        entity_category="diagnostic",
    ),
    # Reg 65, addr 0x0040 = System Status bitmap (uint16, r)
    ModbusRegisterDefinition(
        name="System Status",
        key="system_status",
        address=0x0040,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        icon="mdi:router-wireless",
        entity_category="diagnostic",
    ),
    # Reg 66, addr 0x0041 = System Active Faults Count (uint16, r)
    ModbusRegisterDefinition(
        name="System Active Faults Count",
        key="system_active_faults_count",
        address=0x0041,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        icon="mdi:alert-circle",
        entity_category="diagnostic",
    ),
    # Reg 67, addr 0x0042 = Generator State (uint16, r)
    ModbusRegisterDefinition(
        name="Generator State",
        key="generator_state",
        address=0x0042,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Off", 1: "On"},
        icon="mdi:engine",
    ),
    # Reg 69, addr 0x0044 = PV Harvest Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="PV Harvest Power",
        key="pv_harvest_power",
        address=0x0044,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-power",
    ),
    # Reg 71, addr 0x0046 = DC Charging Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="DC Charging Power",
        key="dc_charging_power",
        address=0x0046,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
    ),
    # Reg 73, addr 0x0048 = DC Charging Current (uint32, r, A)
    ModbusRegisterDefinition(
        name="DC Charging Current",
        key="dc_charging_current",
        address=0x0048,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:current-dc",
    ),
    # Reg 75, addr 0x004A = DC Inverting Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="DC Inverting Power",
        key="dc_inverting_power",
        address=0x004A,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
    ),
    # Reg 77, addr 0x004C = Grid Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="Grid Voltage",
        key="grid_voltage",
        address=0x004C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 79, addr 0x004E = Grid Frequency (uint32, r, Hz)
    ModbusRegisterDefinition(
        name="Grid Frequency",
        key="grid_frequency",
        address=0x004E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.01,
        precision=2,
        unit=UnitOfFrequency.HERTZ,
        device_class=SensorDeviceClass.FREQUENCY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 83, addr 0x0052 = Grid Input Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="Grid Input Power",
        key="grid_input_power",
        address=0x0052,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower-import",
    ),
    # Reg 89, addr 0x0058 = Grid Output Power (uint32, r, W)
    ModbusRegisterDefinition(
        name="Grid Output Power",
        key="grid_output_power",
        address=0x0058,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower-export",
    ),
    # Reg 95, addr 0x005E = Load Power (sint32, r, W)
    ModbusRegisterDefinition(
        name="Load Power",
        key="load_power",
        address=0x005E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        unit=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:flash",
    ),
    # Reg 105, addr 0x0068 = Load Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="Load Voltage",
        key="load_voltage",
        address=0x0068,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=1,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 109, addr 0x006C = Load Current (sint32, r, A)
    ModbusRegisterDefinition(
        name="Load Current",
        key="load_current",
        address=0x006C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.INT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    # Reg 157, addr 0x009C = Battery Voltage (uint32, r, V)
    ModbusRegisterDefinition(
        name="Battery Voltage",
        key="battery_voltage",
        address=0x009C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.001,
        precision=2,
        unit=UnitOfElectricPotential.VOLT,
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery",
    ),
    # Reg 159, addr 0x009E = Battery Temperature (uint32, r, K)
    ModbusRegisterDefinition(
        name="Battery Temperature",
        key="battery_temperature",
        address=0x009E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        scale=0.01,
        offset=-273.0,
        precision=1,
        unit=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:thermometer",
    ),
]

GATEWAY_CONTROL_REGISTERS: list[ModbusRegisterDefinition] = []


# =============================================================================
# SCP (System Control Panel) REGISTERS (slave address range: 70..89)
# Source: 990-6272A "Conext SCP Modbus 503 spec"
# =============================================================================

SCP_SENSOR_REGISTERS: list[ModbusRegisterDefinition] = [
    # Reg 31, addr 0x001E = Firmware Version (uint32, r)
    ModbusRegisterDefinition(
        name="Firmware Version",
        key="firmware_version",
        address=0x001E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT32,
        count=2,
        icon="mdi:information-outline",
        entity_category="diagnostic",
    ),
    # Reg 65, addr 0x0040 = Device State (uint16, r)
    ModbusRegisterDefinition(
        name="Device State",
        key="device_state",
        address=0x0040,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Hibernate", 1: "Power Save", 2: "Safe Mode", 3: "Operating", 4: "Diagnostic Mode", 5: "Remote Power Off", 255: "Data Not Available"},
        icon="mdi:state-machine",
    ),
    # Reg 66, addr 0x0041 = Device Present (uint16, r)
    ModbusRegisterDefinition(
        name="Device Present",
        key="device_present",
        address=0x0041,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "Inactive", 1: "Active"},
        entity_category="diagnostic",
    ),
    # Reg 67, addr 0x0042 = Active Faults Flag (uint16, r)
    ModbusRegisterDefinition(
        name="Active Faults",
        key="active_faults",
        address=0x0042,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "No Faults", 1: "Active Faults"},
        icon="mdi:alert-circle",
        entity_category="diagnostic",
    ),
    # Reg 68, addr 0x0043 = Active Warnings Flag (uint16, r)
    ModbusRegisterDefinition(
        name="Active Warnings",
        key="active_warnings",
        address=0x0043,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        options={0: "No Warnings", 1: "Active Warnings"},
        icon="mdi:alert",
        entity_category="diagnostic",
    ),
]

SCP_CONTROL_REGISTERS: list[ModbusRegisterDefinition] = [
    # Reg 73, addr 0x0049 = Operating Mode (uint16, rw)
    ModbusRegisterDefinition(
        name="Operating Mode",
        key="operating_mode",
        address=0x0049,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        options={2: "Standby", 3: "Operating"},
        icon="mdi:tune",
    ),
    # Reg 75, addr 0x004B = Display Brightness (uint16, rw)
    ModbusRegisterDefinition(
        name="Display Brightness",
        key="display_brightness",
        address=0x004B,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        unit=PERCENTAGE,
        writable=True,
        min_value=0,
        max_value=100,
        icon="mdi:brightness-6",
    ),
    # Reg 76, addr 0x004C = Display Contrast (uint16, rw)
    ModbusRegisterDefinition(
        name="Display Contrast",
        key="display_contrast",
        address=0x004C,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        unit=PERCENTAGE,
        writable=True,
        min_value=0,
        max_value=100,
        icon="mdi:contrast-box",
    ),
    # Reg 78, addr 0x004E = Button Beep (uint16, rw)
    ModbusRegisterDefinition(
        name="Button Beep",
        key="button_beep",
        address=0x004E,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        min_value=0,
        max_value=1,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:volume-high",
    ),
    # Reg 79, addr 0x004F = Fault Alarm (uint16, rw)
    ModbusRegisterDefinition(
        name="Fault Alarm",
        key="fault_alarm",
        address=0x004F,
        register_type=RegisterType.HOLDING,
        data_type=DataType.UINT16,
        writable=True,
        min_value=0,
        max_value=1,
        options={0: "Disabled", 1: "Enabled"},
        icon="mdi:alarm-light",
    ),
]


# =============================================================================
# REGISTER MAPS BY DEVICE TYPE
# =============================================================================

from .const import (  # noqa: E402
    DEVICE_TYPE_AGS,
    DEVICE_TYPE_BATTERY_MONITOR,
    DEVICE_TYPE_GATEWAY,
    DEVICE_TYPE_MPPT,
    DEVICE_TYPE_SCP,
    DEVICE_TYPE_XW_PRO,
)

SENSOR_REGISTERS_BY_DEVICE: dict[str, list[ModbusRegisterDefinition]] = {
    DEVICE_TYPE_XW_PRO: XW_PRO_SENSOR_REGISTERS,
    DEVICE_TYPE_MPPT: MPPT_SENSOR_REGISTERS,
    DEVICE_TYPE_AGS: AGS_SENSOR_REGISTERS,
    DEVICE_TYPE_BATTERY_MONITOR: BATTERY_MONITOR_SENSOR_REGISTERS,
    DEVICE_TYPE_GATEWAY: GATEWAY_SENSOR_REGISTERS,
    DEVICE_TYPE_SCP: SCP_SENSOR_REGISTERS,
}

CONTROL_REGISTERS_BY_DEVICE: dict[str, list[ModbusRegisterDefinition]] = {
    DEVICE_TYPE_XW_PRO: XW_PRO_CONTROL_REGISTERS,
    DEVICE_TYPE_MPPT: MPPT_CONTROL_REGISTERS,
    DEVICE_TYPE_AGS: AGS_CONTROL_REGISTERS,
    DEVICE_TYPE_BATTERY_MONITOR: BATTERY_MONITOR_CONTROL_REGISTERS,
    DEVICE_TYPE_GATEWAY: GATEWAY_CONTROL_REGISTERS,
    DEVICE_TYPE_SCP: SCP_CONTROL_REGISTERS,
}
