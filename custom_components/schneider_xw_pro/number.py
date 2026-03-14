"""Number platform for Schneider Electric Conext XW Pro integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
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
from .registers import ModbusRegisterDefinition

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Schneider XW Pro number entities from a config entry."""
    coordinators: dict[str, SchneiderDeviceCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ][COORDINATOR]

    entities: list[SchneiderNumberEntity] = []

    for coordinator_key, coordinator in coordinators.items():
        for register in coordinator.control_registers:
            # Create number entities for writable registers with min/max and no options
            if (
                register.writable
                and register.min_value is not None
                and register.max_value is not None
                and not register.options
            ):
                entities.append(
                    SchneiderNumberEntity(
                        coordinator=coordinator,
                        register=register,
                        entry=entry,
                    )
                )

    async_add_entities(entities)


class SchneiderNumberEntity(
    CoordinatorEntity[SchneiderDeviceCoordinator], NumberEntity
):
    """Representation of a Schneider Conext number entity."""

    _attr_has_entity_name = True
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        coordinator: SchneiderDeviceCoordinator,
        register: ModbusRegisterDefinition,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the number entity."""
        super().__init__(coordinator)
        self._register = register

        self._attr_unique_id = (
            f"{entry.entry_id}_{coordinator.device_type}"
            f"_{coordinator.slave_id}_{register.key}"
        )

        self._attr_name = f"{coordinator.device_name} {register.name}"

        if register.icon:
            self._attr_icon = register.icon

        if register.unit:
            self._attr_native_unit_of_measurement = register.unit

        self._attr_native_min_value = register.min_value
        self._attr_native_max_value = register.max_value

        if register.scale < 1.0:
            self._attr_native_step = register.scale
        else:
            self._attr_native_step = 1.0

        self._attr_device_info = DeviceInfo(
            identifiers={
                (DOMAIN, f"{entry.entry_id}_{coordinator.device_type}_{coordinator.slave_id}")
            },
            name=coordinator.device_name,
            manufacturer=MANUFACTURER,
            model=DEVICE_TYPE_LABELS.get(coordinator.device_type, coordinator.device_type),
            via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
        )

    @property
    def native_value(self) -> float | None:
        """Return the current value."""
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self._register.key)
        if value is None:
            return None
        return float(value)

    async def async_set_native_value(self, value: float) -> None:
        """Set the value."""
        await self.coordinator.async_write_register(self._register, value)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self.coordinator.last_update_success and self.coordinator.data is not None
