"""Integration with Conversation Entity."""

import logging
from typing import Literal, override

from homeassistant.components.conversation import ChatLog, ConversationEntity
from homeassistant.components.conversation.models import (
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.intent import IntentResponse

_LOGGER = logging.getLogger(__name__)


class LLMAgent(ConversationEntity):
    """LLM conversation agent."""

    def __init__(self):
        """Init Agent."""
        self._attr_name: str | None = "Custom Agent"

    @property
    @override
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return ["*"]

    @override
    async def _async_handle_message(
        self, user_input: ConversationInput, chat_log: ChatLog
    ) -> ConversationResult:
        print(user_input)
        print(chat_log)
        response = IntentResponse(language="en")
        response.async_set_speech("copy")
        return ConversationResult(response)


async def async_setup_entry(
    _hass: HomeAssistant,
    _entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Entry point for our Conversation Entity."""
    _LOGGER.error("Adding Entity")
    async_add_entities([LLMAgent()])
