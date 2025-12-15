"""Platform for Moving Colors sensor."""

import homeassistant.helpers.entity_registry as er
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from . import MovingColorsManager
from .const import DOMAIN, DOMAIN_DATA_MANAGERS, EXTERNAL_SENSOR_DEFINITIONS, SensorEntries


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    # Get the manager and use its logger
    manager: MovingColorsManager | None = hass.data.get(DOMAIN_DATA_MANAGERS, {}).get(config_entry.entry_id)
    instance_logger = manager.logger
    instance_logger.debug("Setting up sensor platform from config entry: %s", config_entry.entry_id)
    config_options = config_entry.options
    config_entry_id = config_entry.entry_id  # Shortcut for entry ID

    if manager is None:
        instance_logger.error("[%s] No Moving Colors manager found for config entry %s. Cannot set up sensors.", DOMAIN, config_entry.entry_id)
        return

    instance_logger.debug("[%s] Creating sensors for manager: %s (from entry %s)", DOMAIN, manager.name, config_entry.entry_id)

    entities_to_add = [
        MovingColorsSensor(manager, config_entry.entry_id, SensorEntries.CURRENT_VALUE),
        MovingColorsSensor(manager, config_entry.entry_id, SensorEntries.CURRENT_MIN_VALUE),
        MovingColorsSensor(manager, config_entry.entry_id, SensorEntries.CURRENT_MAX_VALUE),
    ]

    instance_name = manager.sanitized_name
    config_options = config_entry.options

    # ----------------------------------------------------------------------
    # PART 1: Identify and Create REQUIRED External Sensors
    # ----------------------------------------------------------------------
    required_external_unique_ids = set()

    for definition in EXTERNAL_SENSOR_DEFINITIONS:
        config_key = definition["config_key"]
        external_entity_id = config_options.get(config_key)

        unique_id = f"{config_entry_id}_{config_key}_source_value"

        # Check if an external entity ID is configured and is not an empty/none value
        if external_entity_id and external_entity_id.lower() not in ("none", ""):
            # 1. Entity IS required: track its unique ID
            required_external_unique_ids.add(unique_id)

            # 2. Create the entity instance
            sensor = MovingColorsExternalEntityValueSensor(
                hass,
                manager,
                config_entry_id,
                instance_name,
                definition,
                external_entity_id,
            )
            entities_to_add.append(sensor)

    # ----------------------------------------------------------------------
    # PART 2: Cleanup Unrequired External Sensors from the Registry
    # ----------------------------------------------------------------------
    registry = er.async_get(hass)

    # Iterate over ALL possible external sensor unique IDs
    for definition in EXTERNAL_SENSOR_DEFINITIONS:
        config_key = definition["config_key"]
        unique_id = f"{config_entry_id}_{config_key}_source_value"

        # If this unique ID is NOT in the set of currently required entities...
        if unique_id not in required_external_unique_ids:
            # Look it up in the registry
            entity_id = registry.async_get_entity_id(Platform.SENSOR, DOMAIN, unique_id)

            if entity_id:
                instance_logger.debug("Removing deprecated external sensor entity: %s (unique_id: %s)", entity_id, unique_id)
                # Remove the entity from the registry. This removes it from the UI immediately.
                registry.async_remove(entity_id)

    if entities_to_add:
        async_add_entities(entities_to_add, True)
        instance_logger.info("[%s] Successfully added %s Shadow Control sensor entities for '%s'.", DOMAIN, len(entities_to_add), manager.name)
    else:
        instance_logger.warning("[%s] No sensor entities created for manager '%s'.", DOMAIN, manager.name)


class MovingColorsSensor(SensorEntity):
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
        self._attr_unique_id = f"{self._entry_id}_{self._sensor_entry_type.value}"

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
        """Run when this entity has been added to Home Assistant."""
        # Register a Dispatcher listener here to receive updates.
        # The manager must then send this signal when its data is updated.
        # The signal name must exactly match what the manager sends.
        # Use the manager's name (which is unique for each config entry) to create a unique signal.
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_update_{self._manager.name.lower().replace(' ', '_')}",  # Unique signal for this manager
                self.async_write_ha_state,  # Calls this sensor's method to update its state in HA
            )
        )

    @property
    def native_value(self):  # noqa: ANN201
        """Return the state of the sensor."""
        value = None
        if self._sensor_entry_type == SensorEntries.CURRENT_VALUE:
            value = self._manager.get_current_value()
        if self._sensor_entry_type == SensorEntries.CURRENT_MIN_VALUE:
            value = self._manager.get_current_min_value()
        if self._sensor_entry_type == SensorEntries.CURRENT_MAX_VALUE:
            value = self._manager.get_current_max_value()

        if value is None:
            return None

            # 2. Apply the rounding logic for clean UI display
        if isinstance(value, (float, int)):
            # Round and cast to int to ensure the final output is a whole number,
            # which removes the trailing decimals in the HA frontend.
            return int(round(value))  # noqa: RUF046

            # Return all other types (strings, etc.) as is
        return value


class MovingColorsExternalEntityValueSensor(SensorEntity):
    """Sensor that mirrors the state of a configured external entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        manager: MovingColorsManager,
        config_entry_id: str,
        instance_name: str,
        definition: dict,
        external_entity_id: str,
    ) -> None:
        """Initialize the sensor."""
        self.hass = hass
        self._manager = manager
        self._external_entity_id = external_entity_id
        self._attr_translation_key = definition["translation_key"]
        self._attr_has_entity_name = True

        # Unique ID based on the config key to ensure one per external entity type
        self._attr_unique_id = f"{config_entry_id}_{definition['config_key']}_source_value"

        # Attributes
        self._attr_native_unit_of_measurement = definition.get("unit")
        self._attr_state_class = definition.get("state_class")
        self._attr_device_class = definition.get("device_class")
        self._attr_icon = definition.get("icon")

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry_id)},
            name=manager.name,
            model="Moving Colors",
            manufacturer="Yves Schumann",
        )

        self._current_value = None

    @property
    def native_value(self) -> float | str | None:
        """Return the state of the sensor, mirroring the external entity's state."""
        value = self._current_value

        if value is None:
            return None

        # Check if the value is a float OR an int. This handles all numeric states.
        if isinstance(value, (float, int)):
            # This is done to ensure the final output is a Python 'int',
            # which prevents the HA frontend from displaying trailing decimals (.0 or ,0).
            # We must use int() because round() can return a float (e.g., 50000.0).
            return int(round(value))  # noqa: RUF046

        # Return all other types (strings like 'on'/'off' or 'unavailable') as is.
        return value

    async def async_added_to_hass(self) -> None:
        """Register callbacks and start state tracking."""
        await super().async_added_to_hass()

        # Get initial state
        state = self.hass.states.get(self._external_entity_id)
        if state:
            self._update_from_state(state)

        # Start tracking state changes of the external entity
        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                [self._external_entity_id],
                self._handle_state_change,
            )
        )

    @callback
    def _handle_state_change(self, event: Event) -> None:
        """Handle state changes of the tracked entity."""
        new_state = event.data.get("new_state")
        if new_state is not None:
            self._update_from_state(new_state)
            self.async_write_ha_state()

    @callback
    def _update_from_state(self, state: State) -> None:
        """Parse the state object and update the sensor value."""
        # Try to convert to float if a unit is defined (assuming it's a number sensor)
        if self.native_unit_of_measurement:
            try:
                self._current_value = float(state.state)
            except (ValueError, TypeError):
                # Fallback for 'unavailable', 'unknown', or invalid string values
                self._current_value = state.state
        else:
            # For non-numeric sensors (e.g., switches, selects), just use the state string
            self._current_value = state.state
