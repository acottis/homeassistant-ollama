"""Integration with Conversation Entity."""

from collections.abc import Mapping, Sequence
import logging
from typing import Any, Literal, override

from ollama import AsyncClient, Message, RequestError, ResponseError
import voluptuous_openapi

from homeassistant.components.conversation import ChatLog, ConversationEntity
from homeassistant.components.conversation.models import (
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.intent import IntentResponse
from homeassistant.util.ssl import get_default_context

from .const import DOMAIN

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


def add_two_numbers(a: int, b: int) -> int:
    """Add two numbers

    Args:
      a (int): The first number
      b (int): The second number

    Returns:
      int: The sum of the two numbers

    """
    return a + b


class LLMAgent(ConversationEntity):
    """LLM conversation agent."""

    agent: AsyncClient
    prompt: str
    apis: str | list[str] | None
    model: str

    def __init__(self, agent: AsyncClient):
        """Init Agent."""
        self._attr_name: str | None = "Custom Agent"
        self.agent = agent
        self.prompt = "/no_think "
        self.apis = "assist"
        self.model = "qwen3:8b"

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

        tools = await self.add_tools(chat_log, user_input)

        messages: Sequence[Mapping[str, Any] | Message] = [
            {"role": "user", "content": user_input.text}
        ]
        try:
            response = await self.agent.chat(
                model=self.model,
                messages=messages,
                tools=tools,
                stream=False,
            )

            if response.message.tool_calls:
                for tool in response.message.tool_calls:
                    print(response.message.tool_calls)
                    ret = add_two_numbers(**tool.function.arguments)
                    messages.append(
                        {
                            "role": response.message.role,
                            "content": response.message.role,
                        }
                    )
                    messages.append(
                        {
                            "role": "tool",
                            "name": tool.function.name,
                            "content": str(ret),
                        }
                    )
                    tool_response = await self.agent.chat(
                        model=self.model,
                        messages=messages,
                        stream=False,
                    )
                    response = IntentResponse(language="en")
                    response.async_set_speech(tool_response.message.content)
                    return ConversationResult(response)

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

    async def add_tools(
        self,
        chat_log: ChatLog,
        user_input: ConversationInput,
    ) -> list[dict[str, Any]]:
        """Insert tools into conversation."""
        await chat_log.async_update_llm_data(
            DOMAIN,
            user_input,
            self.apis,
            self.prompt,
        )

        if chat_log.llm_api:
            return [ollama_tool(tool) for tool in chat_log.llm_api.tools]
        return []


def ollama_tool(tool: llm.Tool) -> dict[str, Any]:
    """Covert HA tool into an Ollama Tool."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": voluptuous_openapi.convert(tool.parameters),
        },
    }
