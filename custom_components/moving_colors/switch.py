"""Platform for Moving Colors switch."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any  # Import TYPE_CHECKING

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry  # noqa: TC002
from homeassistant.core import HomeAssistant  # noqa: TC002
from homeassistant.helpers.entity_platform import AddEntitiesCallback  # noqa: TC002
from homeassistant.helpers.restore_state import RestoreEntity

# Only import MovingColorsManager for type checking
if TYPE_CHECKING:
    from . import MovingColorsManager

from .const import DOMAIN, DOMAIN_DATA_MANAGERS

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    manager: MovingColorsManager = hass.data[DOMAIN_DATA_MANAGERS][config_entry.entry_id]
    _LOGGER.debug("[%s] Setting up switch platform.", manager.name)
    async_add_entities([MovingColorsManagerSwitch(manager)])


class MovingColorsManagerSwitch(SwitchEntity, RestoreEntity):
    """Defines a Moving Colors switch."""

    _attr_has_entity_name = True
    _attr_name = "Moving Colors"

    def __init__(self, manager: MovingColorsManager) -> None:
        """Initialize the switch."""
        self._manager = manager
        self._attr_unique_id = f"{manager.entry_id}_enabled"
        self._attr_is_on = False  # Assuming it starts not by default
        self._attr_device_info = {
            "identifiers": {(DOMAIN, manager.entry_id)},
            "name": manager.name,
            "manufacturer": "Yves Schumann",
            "model": "Moving Colors",
        }

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()
        state = await self.async_get_last_state()
        if state is not None:
            self._attr_is_on = state.state == "on"

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn on the Moving Colors logic."""
        if not self._attr_is_on:
            self._manager.async_start_update_task()
            self._attr_is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the Moving Colors logic."""
        if self._attr_is_on:
            self._manager.stop_update_task()
            self._attr_is_on = False
            self.async_write_ha_state()
