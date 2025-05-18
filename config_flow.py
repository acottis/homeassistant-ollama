"""Config flow for LLM Integration."""

from typing import Any, final, override

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

DOMAIN = "a_llm"


@final
class LLMConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Integration Config Entry Point."""

    VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Create initialistion form for user."""

        if user_input is not None:
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME): str,
                }
            ),
        )
