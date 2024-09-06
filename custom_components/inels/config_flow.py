"""Config flow for iNELS."""

from __future__ import annotations

from typing import Any

from inelsmqtt import InelsMqtt
from inelsmqtt.const import MQTT_TRANSPORT
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, TITLE

CONNECTION_TIMEOUT = 5


class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle of iNELS config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> InelsOptionsFlowHandler:
        """Get the options flow for this handler."""
        return InelsOptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a flow initiated by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return await self.async_step_setup()

    async def async_step_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            test_connect = await self.hass.async_add_executor_job(
                try_connection,
                self.hass,
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input.get(CONF_USERNAME, ""),
                user_input.get(CONF_PASSWORD, ""),
                user_input[MQTT_TRANSPORT],
            )

            if test_connect is None:
                return self.async_create_entry(
                    title=TITLE,
                    data=user_input,
                )

            errors["base"] = connect_val_to_error(test_connect)

        return self.async_show_form(
            step_id="setup",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=1883): vol.Coerce(int),
                    vol.Optional(CONF_USERNAME): str,
                    vol.Optional(CONF_PASSWORD): str,
                    vol.Required(MQTT_TRANSPORT, default="tcp"): vol.In(
                        ["tcp", "websockets"]
                    ),
                }
            ),
            errors=errors,
            last_step=True,
        )


class InelsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle iNELS options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: None = None) -> ConfigFlowResult:
        """Manage the options."""
        return await self.async_step_setup()

    async def async_step_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the MQTT options."""
        errors = {}
        current_config = self.config_entry.data

        if user_input is not None:
            test_connect = await self.hass.async_add_executor_job(
                try_connection,
                self.hass,
                user_input[CONF_HOST],
                user_input[CONF_PORT],
                user_input.get(CONF_USERNAME, ""),
                user_input.get(CONF_PASSWORD, ""),
                user_input[MQTT_TRANSPORT],
            )

            if test_connect is None:
                return self.async_create_entry(title=TITLE, data=user_input)

            errors["base"] = connect_val_to_error(test_connect)

        return self.async_show_form(
            step_id="setup",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=current_config[CONF_HOST]): str,
                    vol.Required(
                        CONF_PORT, default=current_config[CONF_PORT]
                    ): vol.Coerce(int),
                    vol.Optional(
                        CONF_USERNAME, default=current_config.get(CONF_USERNAME, "")
                    ): str,
                    vol.Optional(
                        CONF_PASSWORD, default=current_config.get(CONF_PASSWORD, "")
                    ): str,
                    vol.Required(
                        MQTT_TRANSPORT, default=current_config[MQTT_TRANSPORT]
                    ): vol.In(["tcp", "websockets"]),
                }
            ),
            errors=errors,
            last_step=True,
        )


def try_connection(
    hass: HomeAssistant,
    host: str,
    port: int,
    username: str,
    password: str,
    transport: str = "tcp",
) -> int | None:
    """Test if we can connect to an MQTT broker."""
    entry_config = {
        CONF_HOST: host,
        CONF_PORT: port,
        CONF_USERNAME: username,
        CONF_PASSWORD: password,
        MQTT_TRANSPORT: transport,
    }
    client = InelsMqtt(entry_config)
    ret = client.test_connection()
    client.disconnect()

    return ret


TEST_CONNECT_ERRORS: dict[int, str] = {
    1: "mqtt_version",
    2: "forbidden_id",  # should never happen
    3: "cannot_connect",
    4: "invalid_auth",
    5: "unauthorized",
}


def connect_val_to_error(test_connect: int | None) -> str:
    """Turn test_connect value into an error string."""
    if test_connect in TEST_CONNECT_ERRORS:
        return TEST_CONNECT_ERRORS[test_connect]
    return "unknown"
