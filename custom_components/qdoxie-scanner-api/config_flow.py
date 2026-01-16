"""Config flow for QDoxie Scanner API integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
)

from .const import (
    DOMAIN,
    # Doxie
    CONF_DOXIE_HOST,
    CONF_DOXIE_PORT,
    CONF_DOXIE_PASSWORD,
    DEFAULT_DOXIE_PORT,
    # Modes
    CONF_MODE,
    MODE_PAPERLESS,
    MODE_CONSUME_DIR,
    # Paperless
    CONF_PAPERLESS_URL,
    CONF_PAPERLESS_TOKEN,
    CONF_PAPERLESS_USERNAME,
    CONF_PAPERLESS_PASSWORD,
    # Consume
    CONF_CONSUME_DIR,
    # Behaviour
    CONF_INTERVAL_SECONDS,
    CONF_DELETE_ON_SUCCESS,
    CONF_WAIT_FOR_TASK,
    DEFAULT_INTERVAL_SECONDS,
)


class QDoxieConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for QDoxie."""

    VERSION = 1

    def __init__(self) -> None:
        self._base_data: dict = {}

    async def async_step_user(self, user_input=None):
        """Step 1: Doxie connection + mode selection."""
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_DOXIE_HOST): TextSelector(),
                        vol.Optional(
                            CONF_DOXIE_PORT,
                            default=DEFAULT_DOXIE_PORT,
                        ): NumberSelector(
                            NumberSelectorConfig(min=1, max=65535, mode="box")
                        ),
                        vol.Optional(CONF_DOXIE_PASSWORD): TextSelector(),
                        vol.Required(CONF_MODE): SelectSelector(
                            SelectSelectorConfig(
                                options=[MODE_PAPERLESS, MODE_CONSUME_DIR],
                                mode="dropdown",
                            )
                        ),
                    }
                ),
            )

        self._base_data = user_input

        if user_input[CONF_MODE] == MODE_PAPERLESS:
            return await self.async_step_paperless()

        return await self.async_step_consume_dir()

    async def async_step_paperless(self, user_input=None):
        """Step 2a: Paperless configuration."""
        if user_input is None:
            return self.async_show_form(
                step_id="paperless",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_PAPERLESS_URL): TextSelector(),
                        vol.Optional(CONF_PAPERLESS_TOKEN): TextSelector(),
                        vol.Optional(CONF_PAPERLESS_USERNAME): TextSelector(),
                        vol.Optional(CONF_PAPERLESS_PASSWORD): TextSelector(),
                    }
                ),
            )

        data = {**self._base_data, **user_input}

        await self.async_set_unique_id(data[CONF_DOXIE_HOST])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Doxie {data[CONF_DOXIE_HOST]}",
            data=data,
        )

    async def async_step_consume_dir(self, user_input=None):
        """Step 2b: Consume directory configuration."""
        if user_input is None:
            return self.async_show_form(
                step_id="consume_dir",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_CONSUME_DIR): TextSelector(),
                    }
                ),
            )

        data = {**self._base_data, **user_input}

        await self.async_set_unique_id(data[CONF_DOXIE_HOST])
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=f"Doxie {data[CONF_DOXIE_HOST]}",
            data=data,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return QDoxieOptionsFlow(config_entry)


class QDoxieOptionsFlow(config_entries.OptionsFlow):
    """Options flow for QDoxie."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}
        mode = current.get(CONF_MODE, MODE_PAPERLESS)

        schema = {
            vol.Optional(
                CONF_INTERVAL_SECONDS,
                default=int(current.get(CONF_INTERVAL_SECONDS, DEFAULT_INTERVAL_SECONDS)),
            ): NumberSelector(
                NumberSelectorConfig(min=10, max=86400, mode="box")
            ),
            vol.Optional(
                CONF_DELETE_ON_SUCCESS,
                default=bool(current.get(CONF_DELETE_ON_SUCCESS, True)),
            ): BooleanSelector(),
            vol.Optional(
                CONF_WAIT_FOR_TASK,
                default=bool(current.get(CONF_WAIT_FOR_TASK, False)),
            ): BooleanSelector(),
        }

        if mode == MODE_CONSUME_DIR:
            schema[
                vol.Optional(
                    CONF_CONSUME_DIR,
                    default=str(current.get(CONF_CONSUME_DIR, "")),
                )
            ] = TextSelector()
        else:
            schema[
                vol.Optional(
                    CONF_PAPERLESS_URL,
                    default=str(current.get(CONF_PAPERLESS_URL, "")),
                )
            ] = TextSelector()
            schema[
                vol.Optional(
                    CONF_PAPERLESS_TOKEN,
                    default=str(current.get(CONF_PAPERLESS_TOKEN, "")),
                )
            ] = TextSelector()
            schema[
                vol.Optional(
                    CONF_PAPERLESS_USERNAME,
                    default=str(current.get(CONF_PAPERLESS_USERNAME, "")),
                )
            ] = TextSelector()
            schema[
                vol.Optional(
                    CONF_PAPERLESS_PASSWORD,
                    default=str(current.get(CONF_PAPERLESS_PASSWORD, "")),
                )
            ] = TextSelector()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )
