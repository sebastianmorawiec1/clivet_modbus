"""Sensory Clivet WSAT-YSi Modbus."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    MANUFACTURER,
    MASTER_ONLY_REGS,
    MODEL,
    REG_ERROR,
    REG_LAST_ERROR,
    SYSTEM_SENSORS,
    UNIT_SENSORS,
    decode_error,
)
from .coordinator import ClivetCoordinator, to_signed

DEVICE_CLASS_MAP = {
    "temperature": SensorDeviceClass.TEMPERATURE,
    "frequency": SensorDeviceClass.FREQUENCY,
    "current": SensorDeviceClass.CURRENT,
    "power": SensorDeviceClass.POWER,
    "pressure": SensorDeviceClass.PRESSURE,
}


def unit_device_info(entry: ConfigEntry, addr: int) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_unit_{addr}")},
        name=f"Clivet WSAT-YSi jednostka {addr}"
        + (" (MASTER)" if addr == 0 else ""),
        manufacturer=MANUFACTURER,
        model=MODEL,
        via_device=(DOMAIN, f"{entry.entry_id}_system"),
    )


def system_device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, f"{entry.entry_id}_system")},
        name="Clivet WSAT-YSi system",
        manufacturer=MANUFACTURER,
        model=MODEL,
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: ClivetCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = []

    for reg, key, name, unit, signed, binary in SYSTEM_SENSORS:
        if binary:
            continue  # binarne trafiają do binary_sensor
        entities.append(ClivetSystemSensor(coordinator, entry, reg, key, name, unit, signed))

    for addr in range(coordinator.units):
        for reg, key, name, unit, dclass, signed, scale, enum in UNIT_SENSORS:
            if reg in MASTER_ONLY_REGS and addr != 0:
                continue
            entities.append(
                ClivetUnitSensor(
                    coordinator, entry, addr, reg, key, name, unit, dclass, signed, scale, enum
                )
            )
        entities.append(ClivetErrorSensor(coordinator, entry, addr, REG_ERROR, "error", "Błąd / zabezpieczenie"))
        entities.append(ClivetErrorSensor(coordinator, entry, addr, REG_LAST_ERROR, "last_error", "Ostatni błąd"))

    async_add_entities(entities)


class ClivetSystemSensor(CoordinatorEntity[ClivetCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry, reg, key, name, unit, signed) -> None:
        super().__init__(coordinator)
        self._reg = reg
        self._signed = signed
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{entry.entry_id}_system_{key}"
        self._attr_device_info = system_device_info(entry)
        if unit == "°C":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        v = self.coordinator.data["system"].get(self._reg)
        if v is None:
            return None
        return to_signed(v) if self._signed else v


class ClivetUnitSensor(CoordinatorEntity[ClivetCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self, coordinator, entry, addr, reg, key, name, unit, dclass, signed, scale, enum
    ) -> None:
        super().__init__(coordinator)
        self._addr = addr
        self._reg = reg
        self._signed = signed
        self._scale = scale
        self._enum = enum
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"{entry.entry_id}_u{addr}_{key}"
        self._attr_device_info = unit_device_info(entry, addr)
        if dclass:
            self._attr_device_class = DEVICE_CLASS_MAP.get(dclass)
            self._attr_state_class = SensorStateClass.MEASUREMENT
        if enum:
            self._attr_device_class = SensorDeviceClass.ENUM
            self._attr_options = list(enum.values()) + ["nieznany"]

    @property
    def native_value(self):
        unit_data = self.coordinator.data["units"].get(self._addr, {})
        v = unit_data.get(self._reg)
        if v is None:
            return None
        if self._enum:
            return self._enum.get(v, "nieznany")
        v = to_signed(v) if self._signed else v
        return v * self._scale if self._scale != 1 else v


class ClivetErrorSensor(CoordinatorEntity[ClivetCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_icon = "mdi:alert-circle-outline"

    def __init__(self, coordinator, entry, addr, reg, key, name) -> None:
        super().__init__(coordinator)
        self._addr = addr
        self._reg = reg
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_u{addr}_{key}"
        self._attr_device_info = unit_device_info(entry, addr)

    @property
    def native_value(self):
        unit_data = self.coordinator.data["units"].get(self._addr, {})
        return decode_error(unit_data.get(self._reg))

    @property
    def extra_state_attributes(self):
        unit_data = self.coordinator.data["units"].get(self._addr, {})
        return {"raw": unit_data.get(self._reg)}
