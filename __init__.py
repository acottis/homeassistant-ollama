"""LLM Integration for Assist."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.CONVERSATION]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Run on integration load."""
    _LOGGER.error("Loading %s", DOMAIN)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(_hass: HomeAssistant, _entry: ConfigEntry):
    """Run on integration exit."""
    _LOGGER.error("Unloading %s", DOMAIN)
    return True
