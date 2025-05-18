"""Integration with Conversation Entity."""

import logging
from typing import Literal, override

from ollama import AsyncClient, RequestError, ResponseError

from homeassistant.components.conversation import ChatLog, ConversationEntity
from homeassistant.components.conversation.models import (
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.intent import IntentResponse
from homeassistant.util.ssl import get_default_context

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Entry point for our Conversation Entity."""
    _LOGGER.error("Adding Entity")

    agent = AsyncClient(host=entry.data[CONF_URL], verify=get_default_context())
    async_add_entities([LLMAgent(agent)])


class LLMAgent(ConversationEntity):
    """LLM conversation agent."""

    agent: AsyncClient

    def __init__(self, agent: AsyncClient):
        """Init Agent."""
        self._attr_name: str | None = "Custom Agent"
        self.agent = agent

    @property
    @override
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return ["*"]

    @override
    async def _async_handle_message(
        self, user_input: ConversationInput, chat_log: ChatLog
    ) -> ConversationResult:
        _LOGGER.error(user_input)
        _LOGGER.error(chat_log)

        try:
            response = await self.agent.chat(
                model="qwen3:8b",
                messages=[{"role": "user", "content": user_input.text}],
            )
            _LOGGER.error(response)
            message = response.message.content
            if not isinstance(message, str):
                message = "Error: Empty response from agent"
        except ResponseError as e:
            message = str(e)
        except ConnectionError as e:
            message = str(e)
        except RequestError as e:
            # Should not be possible to hit this
            message = f"Bug in this integration: {e!s}"
            raise

        response = IntentResponse(language="en")
        response.async_set_speech(message)
        return ConversationResult(response)
