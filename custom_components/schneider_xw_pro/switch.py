"""Switch platform for Schneider Electric Conext XW Pro integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up Schneider XW Pro switches from a config entry."""
    coordinators: dict[str, SchneiderDeviceCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ][COORDINATOR]

    entities: list[SchneiderSwitchEntity] = []

    for coordinator_key, coordinator in coordinators.items():
        for register in coordinator.control_registers:
            # Only create switches for binary (0/1) writable registers
            if (
                register.writable
                and register.options
                and set(register.options.keys()) == {0, 1}
            ):
                entities.append(
                    SchneiderSwitchEntity(
                        coordinator=coordinator,
                        register=register,
                        entry=entry,
                    )
                )

    async_add_entities(entities)


class SchneiderSwitchEntity(
    CoordinatorEntity[SchneiderDeviceCoordinator], SwitchEntity
):
    """Representation of a Schneider Conext switch."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SchneiderDeviceCoordinator,
        register: ModbusRegisterDefinition,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._register = register

        self._attr_unique_id = (
            f"{entry.entry_id}_{coordinator.device_type}"
            f"_{coordinator.slave_id}_{register.key}"
        )

        self._attr_name = f"{coordinator.device_name} {register.name}"

        if register.icon:
            self._attr_icon = register.icon

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
            via_device=(DOMAIN, f"{entry.entry_id}_gateway"),
        )

    @property
    def is_on(self) -> bool | None:
        """Return True if the switch is on."""
        if self.coordinator.data is None:
            return None
        raw_key = f"{self._register.key}_raw"
        value = self.coordinator.data.get(raw_key)
        if value is None:
            value = self.coordinator.data.get(self._register.key)
        if value is None:
            return None
        return bool(int(value))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.coordinator.async_write_register(self._register, 1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.coordinator.async_write_register(self._register, 0)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )
