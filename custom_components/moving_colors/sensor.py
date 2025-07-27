"""Platform for Moving Colors sensor."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry  # noqa: TC002
from homeassistant.core import HomeAssistant, callback
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
    """Set up the sensor platform."""
    manager: MovingColorsManager = hass.data[DOMAIN_DATA_MANAGERS][config_entry.entry_id]
    _LOGGER.debug("[%s] Setting up sensor platform.", manager.name)
    async_add_entities([MovingColorsCurrentValueSensor(manager)])


class MovingColorsCurrentValueSensor(SensorEntity, RestoreEntity):
    """Defines a Moving Colors sensor."""

    _attr_has_entity_name = True
    _attr_name = "Current Value"

    def __init__(self, manager: MovingColorsManager) -> None:
        """Initialize the sensor."""
        self._manager = manager
        self._attr_unique_id = f"{manager.entry_id}_current_value"
        self._attr_native_value = manager.get_current_value()
        self._attr_state_class = "measurement"
        self._attr_unit_of_measurement = "brightness"
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
        if state is not None and state.state is not None:
            try:
                self._attr_native_value = int(float(state.state))
            except ValueError:
                _LOGGER.warning("Could not restore sensor state from '%s'", state.state)

        @callback
        def async_update_callback(new_value: int) -> None:
            """Update the sensor's state."""
            self._attr_native_value = new_value
            self.async_write_ha_state()

        self._manager.set_current_value_update_callback(async_update_callback)

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        # Use the public getter method
        return self._manager.get_current_value()
