"""Integration with Conversation Entity."""

from collections.abc import AsyncGenerator, AsyncIterator, Sequence
import logging
from typing import Any, Literal, override

from httpx import ConnectError
from ollama import AsyncClient, ChatResponse, ResponseError
import voluptuous_openapi

from homeassistant.components.conversation import ChatLog, ConversationEntity
from homeassistant.components.conversation.chat_log import (
    AssistantContent,
    AssistantContentDeltaDict,
    Content,
    SystemContent,
    ToolResultContent,
    UserContent,
)
from homeassistant.components.conversation.models import (
    ConversationInput,
    ConversationResult,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_MODEL, CONF_URL
from homeassistant.core import HomeAssistant
from homeassistant.helpers import llm
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.intent import IntentResponse
from homeassistant.util.ssl import get_default_context

from .const import DOMAIN, MAX_TOOL_ITERATIONS

LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    _hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Entry point for our Conversation Entity."""
    async_add_entities([OllamaAgent(entry)])


class OllamaAgent(ConversationEntity):
    """LLM conversation agent."""

    agent: AsyncClient
    prompt: str
    apis: str | list[str] | None
    model: str

    def __init__(self, entry: ConfigEntry):
        """Init Agent."""
        self._attr_name: str | None = entry.data[CONF_MODEL]
        self._attr_unique_id: str | None = entry.entry_id

        self.prompt = "/no_think "
        self.apis = "assist"
        self.model = entry.data[CONF_MODEL]
        self.agent = AsyncClient(
            host=entry.data[CONF_URL], verify=get_default_context()
        )

    @property
    @override
    def supported_languages(self) -> list[str] | Literal["*"]:
        """Return a list of supported languages."""
        return ["*"]

    @override
    async def _async_handle_message(
        self, user_input: ConversationInput, chat_log: ChatLog
    ) -> ConversationResult:
        await chat_log.async_update_llm_data(
            DOMAIN,
            user_input,
            self.apis,
            self.prompt,
        )

        tools = await self.convert_tools(chat_log)

        messages: Sequence[dict[str, Any]] = [
            ollama_message(content) for content in chat_log.content
        ]

        # Prevent infinite loop bugs
        for _ in range(MAX_TOOL_ITERATIONS)
            response = await self.agent.chat(
                model=self.model,
                messages=messages,
                tools=tools,
                stream=True,
            )

            try:
                deltas = [
                    ollama_message(content)
                    # Run any tool calls...
                    async for content in chat_log.async_add_delta_content_stream(
                        user_input.agent_id,
                        ollama_stream(response),
                    )
                ]
                messages.extend(deltas)
            except ResponseError as e:
                return respond_with_error(e, user_input, chat_log)
            except ConnectError as e:
                return respond_with_error(e, user_input, chat_log)

            if not chat_log.unresponded_tool_results:
                break

        response = IntentResponse(language=user_input.language)
        response.async_set_speech(chat_log.content[-1].content)
        return ConversationResult(
            response,
            conversation_id=chat_log.conversation_id,
            continue_conversation=chat_log.continue_conversation,
        )

    async def convert_tools(
        self,
        chat_log: ChatLog,
    ) -> list[dict[str, Any]]:
        """Convert homeassistant tools to ollama tools."""
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


def ollama_message(content: Content) -> dict[str, Any]:
    """Convert Homeassistant Content to an Ollama Message."""
    match content:
        # The User
        case UserContent():
            return {"role": content.role, "content": content.content}
        # What we tell the LLM about our tool call
        case ToolResultContent():
            return {
                "role": "tool",
                "content": str(content.tool_result),
                "name": content.tool_name,
            }
        # Home assistant
        case AssistantContent():
            return {"role": content.role, "content": content.content}
        # The LLM
        case SystemContent():
            return {"role": content.role, "content": content.content}


async def ollama_stream(
    responses: AsyncIterator[ChatResponse],
) -> AsyncGenerator[AssistantContentDeltaDict]:
    """Transform an Ollama delta stream into HA format."""
    async for response in responses:
        delta = AssistantContentDeltaDict(
            role="assistant",
            content=response.message.content,
        )
        if tool_calls := response.message.tool_calls:
            delta["tool_calls"] = [
                llm.ToolInput(
                    tool_name=tool_call.function.name,
                    tool_args=dict(tool_call.function.arguments),
                )
                for tool_call in tool_calls
            ]
        yield delta


def respond_with_error(
    error: Exception, user_input: ConversationInput, chat_log: ChatLog
) -> ConversationResult:
    """Send error back in conversation."""
    response = IntentResponse(language=user_input.language)
    response.async_set_speech(f"Error: {error!s}")
    return ConversationResult(
        response,
        conversation_id=chat_log.conversation_id,
        continue_conversation=chat_log.continue_conversation,
    )
