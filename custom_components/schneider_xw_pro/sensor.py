"""Sensor platform for Schneider Electric Conext XW Pro integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    COORDINATOR,
    DEVICE_TYPE_LABELS,
    DOMAIN,
    MANUFACTURER,
)
from .coordinator import SchneiderDeviceCoordinator
from .registers import DataType, ModbusRegisterDefinition

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Schneider XW Pro sensors from a config entry."""
    coordinators: dict[str, SchneiderDeviceCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ][COORDINATOR]

    entities: list[SchneiderSensorEntity] = []

    for coordinator_key, coordinator in coordinators.items():
        for register in coordinator.sensor_registers:
            entities.append(
                SchneiderSensorEntity(
                    coordinator=coordinator,
                    register=register,
                    entry=entry,
                )
            )

    async_add_entities(entities)


class SchneiderSensorEntity(
    CoordinatorEntity[SchneiderDeviceCoordinator], SensorEntity
):
    """Representation of a Schneider Conext sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SchneiderDeviceCoordinator,
        register: ModbusRegisterDefinition,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._register = register

        # Unique ID: entry_id + device_type + slave_id + register_key
        self._attr_unique_id = (
            f"{entry.entry_id}_{coordinator.device_type}"
            f"_{coordinator.slave_id}_{register.key}"
        )

        self._attr_name = register.name

        # Status / enum sensors: registers with an options map return
        # string values.  HA 2023.x+ requires SensorDeviceClass.ENUM
        # and an explicit list of valid option strings for such sensors.
        if register.options and not register.device_class:
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = list(register.options.values())
        elif register.device_class:
            self._attr_device_class = register.device_class

        if register.unit:
            self._attr_native_unit_of_measurement = register.unit
        if register.state_class:
            self._attr_state_class = register.state_class
        if register.icon:
            self._attr_icon = register.icon
        if register.entity_category:
            self._attr_entity_category = register.entity_category

        # Only set display precision for numeric sensors (not STRING/ENUM)
        if register.data_type != DataType.STRING and not register.options:
            self._attr_suggested_display_precision = register.precision

        # Device info for device registry
        self._attr_device_info = DeviceInfo(
            identifiers={
                (
                    DOMAIN,
                    f"{entry.entry_id}_{coordinator.device_type}_{coordinator.slave_id}",
                )
            },
            name=coordinator.device_name,
            manufacturer=MANUFACTURER,
            model=DEVICE_TYPE_LABELS.get(
                coordinator.device_type, coordinator.device_type
            ),
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @property
    def native_value(self) -> Any:
        """Return the sensor value."""
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self._register.key)
        # For ENUM sensors, only return values that are in the declared
        # options list.  Unmapped Modbus values (stored as str(int)) would
        # violate HA's ENUM validation; return None so the entity shows
        # "unknown" instead of failing.
        if (
            value is not None
            and self._register.options
            and isinstance(value, str)
            and hasattr(self, "_attr_options")
            and value not in self._attr_options
        ):
            _LOGGER.debug(
                "Unmapped enum value %r for %s — returning unknown",
                value,
                self._register.key,
            )
            return None
        return value

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self._register.key in self.coordinator.data
        )
