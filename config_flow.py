"""Config flow for LLM Integration."""

import logging
from typing import Any, final, override

from voluptuous import Required, Schema

from const import DOMAIN
from homeassistant import config_entries
from homeassistant.const import CONF_MODEL, CONF_NAME, CONF_URL

_LOGGER = logging.getLogger(__name__)


@final
class LLMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Integration Config Entry Point."""

    VERSION = 0
    MINTOR_VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Create initialistion form for user.

        This is called in a loop until we return a config.
        """

        # Exit when we have what we need
        if user_input is not None:
            _LOGGER.error(user_input)
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            data_schema=Schema(
                {
                    Required(CONF_NAME): str,
                    Required(CONF_URL): str,
                    Required(CONF_MODEL): str,
                }
            ),
        )
