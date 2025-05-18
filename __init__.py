"""LLM Integration for Assist."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

_LOGGER.error("global start")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Run on integration load."""
    _LOGGER.error("LOAD")

    platforms = [Platform.CONVERSATION]
    await hass.config_entries.async_forward_entry_setups(entry, platforms)
    return True


async def async_unload_entry(_: HomeAssistant, entry: ConfigEntry):
    """Run on integration exit."""
    _LOGGER.error("UNLOAD")
    # Tear down integration
    return True
