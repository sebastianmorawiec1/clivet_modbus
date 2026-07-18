"""Binarne sensory Clivet WSAT-YSi Modbus (zawory, pompa, grzałki)."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SYSTEM_SENSORS, UNIT_BINARY_SENSORS
from .coordinator import ClivetCoordinator
from .sensor import system_device_info, unit_device_info

DEVICE_CLASS_MAP = {
    "running": BinarySensorDeviceClass.RUNNING,
    "heat": BinarySensorDeviceClass.HEAT,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: ClivetCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[BinarySensorEntity] = []

    for reg, key, name, unit, signed, binary in SYSTEM_SENSORS:
        if binary:
            entities.append(ClivetSystemBinary(coordinator, entry, reg, key, name))

    for addr in range(coordinator.units):
        for reg, key, name, dclass in UNIT_BINARY_SENSORS:
            entities.append(
                ClivetUnitBinary(coordinator, entry, addr, reg, key, name, dclass)
            )

    async_add_entities(entities)


class ClivetSystemBinary(CoordinatorEntity[ClivetCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, reg, key, name) -> None:
        super().__init__(coordinator)
        self._reg = reg
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_system_{key}"
        self._attr_device_info = system_device_info(entry)

    @property
    def is_on(self):
        v = self.coordinator.data["system"].get(self._reg)
        return None if v is None else bool(v)


class ClivetUnitBinary(CoordinatorEntity[ClivetCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, addr, reg, key, name, dclass) -> None:
        super().__init__(coordinator)
        self._addr = addr
        self._reg = reg
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_u{addr}_{key}"
        self._attr_device_info = unit_device_info(entry, addr)
        if dclass:
            self._attr_device_class = DEVICE_CLASS_MAP.get(dclass)

    @property
    def is_on(self):
        unit_data = self.coordinator.data["units"].get(self._addr, {})
        v = unit_data.get(self._reg)
        return None if v is None else bool(v)
