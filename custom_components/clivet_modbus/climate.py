"""Encja climate Clivet WSAT-YSi - tryb (rejestr 0) i nastawa (rejestr 1)."""
from __future__ import annotations

from homeassistant.components.climate import (
    ClimateEntity,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_TEMPERATURE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MODE_COOL, MODE_OFF, REG_MODE, REG_SETPOINT
from .coordinator import ClivetCoordinator, to_signed
from .sensor import system_device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: ClivetCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ClivetChiller(coordinator, entry)])


class ClivetChiller(CoordinatorEntity[ClivetCoordinator], ClimateEntity):
    """Agregat jako climate: OFF / COOL + nastawa wody wylotowej."""

    _attr_has_entity_name = True
    _attr_name = "Agregat"
    _attr_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_hvac_modes = [HVACMode.OFF, HVACMode.COOL]
    _attr_supported_features = (
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TURN_ON
        | ClimateEntityFeature.TURN_OFF
    )
    _attr_target_temperature_step = 1
    # Poniżej 5°C wymagany glikol (patrz zakres roboczy w instrukcji);
    # rejestr przyjmuje od -8 (lub Tsafe) do 20°C.
    _attr_min_temp = -8
    _attr_max_temp = 20

    def __init__(self, coordinator, entry) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_climate"
        self._attr_device_info = system_device_info(entry)

    @property
    def hvac_mode(self) -> HVACMode | None:
        v = self.coordinator.data["system"].get(REG_MODE)
        if v is None:
            return None
        return HVACMode.COOL if v == MODE_COOL else HVACMode.OFF

    @property
    def target_temperature(self) -> float | None:
        v = self.coordinator.data["system"].get(REG_SETPOINT)
        return None if v is None else float(to_signed(v))

    @property
    def current_temperature(self) -> float | None:
        # Tw jednostki nadrzędnej (rejestr 246) jako temperatura bieżąca
        master = self.coordinator.data["units"].get(0, {})
        v = master.get(246)
        return None if v is None else float(to_signed(v))

    async def async_set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        value = MODE_COOL if hvac_mode == HVACMode.COOL else MODE_OFF
        await self.coordinator.async_write_register(REG_MODE, value)

    async def async_set_temperature(self, **kwargs) -> None:
        temp = kwargs.get(ATTR_TEMPERATURE)
        if temp is None:
            return
        await self.coordinator.async_write_register(REG_SETPOINT, int(round(temp)))
