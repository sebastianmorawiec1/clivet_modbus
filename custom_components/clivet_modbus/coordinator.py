"""Koordynator danych Clivet WSAT-YSi Modbus."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta

from pymodbus.client import AsyncModbusTcpClient

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    SYSTEM_BLOCK_COUNT,
    SYSTEM_BLOCK_START,
    UNIT_BLOCK_COUNT,
    UNIT_BLOCK_START,
)

_LOGGER = logging.getLogger(__name__)


def to_signed(value: int) -> int:
    """Konwersja 16-bit unsigned -> signed (temperatury mogą być ujemne)."""
    return value - 0x10000 if value >= 0x8000 else value


class ClivetCoordinator(DataUpdateCoordinator[dict]):
    """Odpytuje agregat Clivet po Modbus TCP (bramka RS485<->TCP)."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str,
        port: int,
        slave: int,
        units: int,
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.host = host
        self.port = port
        self.slave = slave
        self.units = max(1, min(16, units))
        self._client = AsyncModbusTcpClient(host, port=port)
        self._lock = asyncio.Lock()

    async def _ensure_connected(self) -> None:
        if not self._client.connected:
            await self._client.connect()
        if not self._client.connected:
            raise UpdateFailed(f"Brak połączenia z {self.host}:{self.port}")

    async def _read_block(self, address: int, count: int) -> list[int]:
        """Odczyt bloku rejestrów z obsługą różnych wersji pymodbus."""
        try:
            rr = await self._client.read_holding_registers(
                address, count=count, device_id=self.slave
            )
        except TypeError:
            rr = await self._client.read_holding_registers(
                address, count=count, slave=self.slave
            )
        if rr.isError():
            raise UpdateFailed(f"Błąd odczytu rejestrów {address}..{address + count - 1}: {rr}")
        return list(rr.registers)

    async def async_write_register(self, address: int, value: int) -> None:
        """Zapis pojedynczego rejestru (FC06)."""
        if value < 0:
            value &= 0xFFFF
        async with self._lock:
            await self._ensure_connected()
            try:
                rq = await self._client.write_register(
                    address, value, device_id=self.slave
                )
            except TypeError:
                rq = await self._client.write_register(
                    address, value, slave=self.slave
                )
            if rq.isError():
                raise UpdateFailed(f"Błąd zapisu rejestru {address}={value}: {rq}")
        await self.async_request_refresh()

    async def _async_update_data(self) -> dict:
        async with self._lock:
            try:
                await self._ensure_connected()

                data: dict = {"system": {}, "units": {}}

                # Rejestry 0-2: tryb, nastawy
                regs = await self._read_block(0, 3)
                for i, v in enumerate(regs):
                    data["system"][i] = v

                # Rejestry 101-109
                regs = await self._read_block(SYSTEM_BLOCK_START, SYSTEM_BLOCK_COUNT)
                for i, v in enumerate(regs):
                    data["system"][SYSTEM_BLOCK_START + i] = v

                # Bloki jednostek: 240..293 + adres*100
                for addr in range(self.units):
                    start = UNIT_BLOCK_START + addr * 100
                    regs = await self._read_block(start, UNIT_BLOCK_COUNT)
                    data["units"][addr] = {
                        UNIT_BLOCK_START + i: v for i, v in enumerate(regs)
                    }

                return data
            except UpdateFailed:
                self._client.close()
                raise
            except Exception as err:  # noqa: BLE001
                self._client.close()
                raise UpdateFailed(f"Błąd komunikacji Modbus: {err}") from err

    async def async_close(self) -> None:
        self._client.close()
