"""Config flow for LLM Integration."""

import logging
from typing import Any, final, override

from voluptuous import Required, Schema

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_MODEL, CONF_URL
from homeassistant.helpers.selector import (
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

AGENT_SCHEMA = Schema(
    {
        Required(
            CONF_MODEL,
            description={"suggested_value": "qwen3:8b"},
        ): TextSelector(TextSelectorConfig(type=TextSelectorType.URL)),
        Required(
            CONF_URL, description={"suggested_value": "http://localhost:11434"}
        ): str,
    }
)


@final
class LLMConfigFlow(ConfigFlow, domain=DOMAIN):
    """Integration Config Entry Point."""

    VERSION = 0
    MINTOR_VERSION = 1

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create initialistion form for user.

        This is called in a loop until we return a config.
        """

        errors: dict[str, str] = {}

        if user_input is not None:
            return self.async_create_entry(
                title=user_input[CONF_MODEL],
                data=user_input,
            )

        return self.async_show_form(data_schema=AGENT_SCHEMA, errors=errors)
