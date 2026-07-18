"""Config flow dla Clivet WSAT-YSi Modbus."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from pymodbus.client import AsyncModbusTcpClient

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import (
    CONF_SCAN_INTERVAL,
    CONF_SLAVE,
    CONF_UNITS,
    DEFAULT_PORT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SLAVE,
    DEFAULT_UNITS,
    DOMAIN,
)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.Coerce(int),
        vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=247)
        ),
        vol.Required(CONF_UNITS, default=DEFAULT_UNITS): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=16)
        ),
        vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
            vol.Coerce(int), vol.Range(min=5, max=300)
        ),
    }
)


async def _test_connection(host: str, port: int, slave: int) -> bool:
    client = AsyncModbusTcpClient(host, port=port)
    try:
        await client.connect()
        if not client.connected:
            return False
        try:
            rr = await client.read_holding_registers(0, count=3, device_id=slave)
        except TypeError:
            rr = await client.read_holding_registers(0, count=3, slave=slave)
        return not rr.isError()
    except Exception:  # noqa: BLE001
        return False
    finally:
        client.close()


class ClivetConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Konfiguracja przez UI."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}:{user_input[CONF_SLAVE]}"
            )
            self._abort_if_unique_id_configured()

            ok = await _test_connection(
                user_input[CONF_HOST], user_input[CONF_PORT], user_input[CONF_SLAVE]
            )
            if ok:
                return self.async_create_entry(
                    title=f"Clivet WSAT-YSi ({user_input[CONF_HOST]})",
                    data=user_input,
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )
