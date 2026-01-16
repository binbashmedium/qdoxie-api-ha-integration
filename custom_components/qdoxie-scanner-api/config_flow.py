"""Config flow for qdoxie-scanner-api integration."""

from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.helpers.selector import (
    BooleanSelector,
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
)

from .const import (
    CONF_CONSUME_DIR,
    CONF_DELETE_ON_SUCCESS,
    CONF_DOXIE_HOST,
    CONF_DOXIE_PASSWORD,
    CONF_DOXIE_PORT,
    CONF_INTERVAL_SECONDS,
    CONF_MODE,
    CONF_PAPERLESS_PASSWORD,
    CONF_PAPERLESS_TOKEN,
    CONF_PAPERLESS_URL,
    CONF_PAPERLESS_USERNAME,
    CONF_WAIT_FOR_TASK,
    DEFAULT_DOXIE_PORT,
    DEFAULT_INTERVAL_SECONDS,
    DOMAIN,
    MODE_CONSUME_DIR,
    MODE_PAPERLESS,
)


class DoxiePaperlessConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_DOXIE_HOST): TextSelector(),
                        vol.Optional(CONF_DOXIE_PORT, default=DEFAULT_DOXIE_PORT): NumberSelector(
                            NumberSelectorConfig(min=1, max=65535, mode="box")
                        ),
                        vol.Optional(CONF_DOXIE_PASSWORD): TextSelector(),
                        vol.Optional(CONF_PAPERLESS_URL): TextSelector(),
                        vol.Optional(CONF_PAPERLESS_TOKEN): TextSelector(),
                        vol.Optional(CONF_PAPERLESS_USERNAME): TextSelector(),
                        vol.Optional(CONF_PAPERLESS_PASSWORD): TextSelector(),
                    }
                ),
            )

        await self.async_set_unique_id(user_input[CONF_DOXIE_HOST])
        self._abort_if_unique_id_configured()

        title = f"Doxie {user_input[CONF_DOXIE_HOST]}"
        return self.async_create_entry(title=title, data=user_input)

    async def async_step_options(self, user_input=None):
        return await DoxiePaperlessOptionsFlowHandler(self).async_step_init(user_input)


class DoxiePaperlessOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is None:
            current = {**self.config_entry.data, **self.config_entry.options}

            return self.async_show_form(
                step_id="init",
                data_schema=vol.Schema(
                    {
                        vol.Optional(
                            CONF_INTERVAL_SECONDS,
                            default=int(current.get(CONF_INTERVAL_SECONDS, DEFAULT_INTERVAL_SECONDS)),
                        ): NumberSelector(NumberSelectorConfig(min=10, max=86400, mode="box")),
                        vol.Optional(
                            CONF_MODE,
                            default=str(current.get(CONF_MODE, MODE_PAPERLESS)),
                        ): SelectSelector(
                            SelectSelectorConfig(
                                options=[MODE_PAPERLESS, MODE_CONSUME_DIR],
                                mode="dropdown",
                            )
                        ),
                        vol.Optional(
                            CONF_CONSUME_DIR,
                            default=str(current.get(CONF_CONSUME_DIR, "")),
                        ): TextSelector(),
                        vol.Optional(
                            CONF_DELETE_ON_SUCCESS,
                            default=bool(current.get(CONF_DELETE_ON_SUCCESS, True)),
                        ): BooleanSelector(),
                        vol.Optional(
                            CONF_WAIT_FOR_TASK,
                            default=bool(current.get(CONF_WAIT_FOR_TASK, False)),
                        ): BooleanSelector(),
                    }
                ),
            )

        return self.async_create_entry(title="", data=user_input)
