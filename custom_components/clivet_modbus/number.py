"""Encja number Clivet WSAT-YSi - nastawa temperatury B (rejestr 2)."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, REG_SETPOINT_B
from .coordinator import ClivetCoordinator, to_signed
from .sensor import system_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: ClivetCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ClivetSetpointB(coordinator, entry)])


class ClivetSetpointB(CoordinatorEntity[ClivetCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_name = "Nastawa temperatury B"
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = -8
    _attr_native_max_value = 20
    _attr_native_step = 1

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_setpoint_b"
        self._attr_device_info = system_device_info(entry)

    @property
    def native_value(self) -> float | None:
        v = self.coordinator.data["system"].get(REG_SETPOINT_B)
        return None if v is None else float(to_signed(v))

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_write_register(REG_SETPOINT_B, int(round(value)))
