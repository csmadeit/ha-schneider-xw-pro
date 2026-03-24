"""Select platform for Schneider Electric Conext XW Pro integration."""

from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
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
    """Set up Schneider XW Pro selects from a config entry."""
    coordinators: dict[str, SchneiderDeviceCoordinator] = hass.data[DOMAIN][
        entry.entry_id
    ][COORDINATOR]

    entities: list[SchneiderSelectEntity] = []

    for coordinator_key, coordinator in coordinators.items():
        for register in coordinator.control_registers:
            # Create selects for writable registers with options that aren't
            # simple binary {0, 1} switches
            if (
                register.writable
                and register.options
                and not (set(register.options.keys()) == {0, 1})
            ):
                entities.append(
                    SchneiderSelectEntity(
                        coordinator=coordinator,
                        register=register,
                        entry=entry,
                    )
                )

    async_add_entities(entities)


class SchneiderSelectEntity(
    CoordinatorEntity[SchneiderDeviceCoordinator], SelectEntity
):
    """Representation of a Schneider Conext select."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: SchneiderDeviceCoordinator,
        register: ModbusRegisterDefinition,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the select."""
        super().__init__(coordinator)
        self._register = register

        self._attr_unique_id = (
            f"{entry.entry_id}_{coordinator.device_type}"
            f"_{coordinator.slave_id}_{register.key}"
        )

        self._attr_name = register.name

        if register.icon:
            self._attr_icon = register.icon

        # Build options list from register options
        self._options_map = register.options or {}
        self._reverse_map = {v: k for k, v in self._options_map.items()}
        self._attr_options = list(self._options_map.values())

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

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if self.coordinator.data is None:
            return None
        value = self.coordinator.data.get(self._register.key)
        if value is None:
            return None
        # If value is already a string label from options resolution
        if isinstance(value, str) and value in self._attr_options:
            return value
        # If value is a raw int, resolve it
        if isinstance(value, (int, float)):
            return self._options_map.get(int(value))
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        raw_value = self._reverse_map.get(option)
        if raw_value is not None:
            await self.coordinator.async_write_register(self._register, raw_value)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )
