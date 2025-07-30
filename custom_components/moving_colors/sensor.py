"""Platform for Moving Colors sensor."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry  # noqa: TC002
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback  # noqa: TC002
from homeassistant.helpers.restore_state import RestoreEntity

# Only import MovingColorsManager for type checking
if TYPE_CHECKING:
    from . import MovingColorsManager

from .const import DOMAIN, DOMAIN_DATA_MANAGERS, SensorEntries

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    _LOGGER.debug("[%s] Setting up sensor platform from config entry: %s", DOMAIN, config_entry.entry_id)

    manager: MovingColorsManager | None = hass.data.get(DOMAIN_DATA_MANAGERS, {}).get(config_entry.entry_id)

    if manager is None:
        _LOGGER.error("[%s] No Moving Colors manager found for config entry %s. Cannot set up sensors.", DOMAIN, config_entry.entry_id)
        return

    _LOGGER.debug("[%s] Creating sensors for manager: %s (from entry %s)", DOMAIN, manager.name, config_entry.entry_id)

    entities_to_add = [
        MovingColorsSensor(manager, config_entry.entry_id, SensorEntries.CURRENT_VALUE),
        MovingColorsSensor(manager, config_entry.entry_id, SensorEntries.CURRENT_MIN_VALUE),
        MovingColorsSensor(manager, config_entry.entry_id, SensorEntries.CURRENT_MAX_VALUE),
    ]

    if entities_to_add:
        async_add_entities(entities_to_add, True)
        _LOGGER.info("[%s] Successfully added %s Shadow Control sensor entities for '%s'.", DOMAIN, len(entities_to_add), manager.name)
    else:
        _LOGGER.warning("[%s] No sensor entities created for manager '%s'.", DOMAIN, manager.name)


class MovingColorsSensor(SensorEntity, RestoreEntity):
    """Defines a Moving Colors sensor."""

    _attr_has_entity_name = True

    def __init__(self, manager: MovingColorsManager, entry_id: str, sensor_entry_type: SensorEntries) -> None:
        """Initialize the sensor."""
        self._manager = manager
        self._entry_id = entry_id

        # Store the enum itself, not only the string representation
        self._sensor_entry_type = sensor_entry_type

        # Set _attr_has_entity_name true for naming convention
        self._attr_has_entity_name = True

        # Use stable unique_id based on entry_id and the sensor type
        self._attr_unique_id = f"mc_{self._entry_id}_{self._sensor_entry_type.value}"

        # Define key used within translation files based on enum values e.g. "target_height".
        self._attr_translation_key = f"{self._sensor_entry_type.value}"

        self._attr_state_class = "measurement"
        self._attr_native_unit_of_measurement = "%"

        # Connect with the device (important for UI)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._entry_id)},
            name=manager.name,
            model="Shadow Control",
            manufacturer="Yves Schumann",
        )

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
    def native_value(self):  # noqa: ANN201
        """Return the state of the sensor."""
        if self._sensor_entry_type == SensorEntries.CURRENT_VALUE:
            return self._manager.get_current_value()
        if self._sensor_entry_type == SensorEntries.CURRENT_MIN_VALUE:
            return self._manager.get_current_min_value()
        if self._sensor_entry_type == SensorEntries.CURRENT_MAX_VALUE:
            return self._manager.get_current_max_value()

        return None
