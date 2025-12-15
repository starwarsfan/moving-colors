"""Integration for Moving Colors."""

import logging
import random
import re
from collections.abc import Callable
from datetime import timedelta
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED,
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry
from homeassistant.helpers.event import async_track_state_change, async_track_time_interval
from homeassistant.helpers.typing import ConfigType

from .const import (
    DEBUG_ENABLED,
    DOMAIN,
    DOMAIN_DATA_MANAGERS,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
    VERSION,
    MCConfig,
    MCIntDefaults,
    MCInternal,
)

_GLOBAL_DOMAIN_LOGGER = logging.getLogger(DOMAIN)
_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.NUMBER, Platform.SENSOR, Platform.SWITCH]

CURRENT_SCHEMA_VERSION = VERSION


# Setup entry point, which is called at every start of Home Assistant.
# Not specific for config entries.
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Moving Colors integration."""
    _LOGGER.debug("[%s] Integration 'Moving Colors' base setup (async_setup) started.", DOMAIN)

    # Placeholder for all data of this integration within 'hass.data'.
    # Will be used to store things like the MovingColorsManager instances.
    # hass.data[DOMAIN_DATA_MANAGERS] will be a dictionary to map ConfigEntry
    # IDs to manager instances.
    hass.data.setdefault(DOMAIN_DATA_MANAGERS, {})

    if DOMAIN in config:
        for entry_config in config[DOMAIN]:
            # Import YAML configuration into ConfigEntry, separated the same way than
            # on the ConfigFlow: Name in 'data', rest in 'options'

            # Remove name from YAML configuration
            instance_name = entry_config.pop(MC_CONF_NAME)

            hass.async_create_task(
                hass.config_entries.flow.async_init(
                    DOMAIN,
                    context={"source": "import"},
                    data={
                        MC_CONF_NAME: instance_name,  # Name into the 'data' section
                        # Pass the dictionary which contains the options for the
                        # ConfigEntry. YAML content without a name will be options
                        **entry_config,
                    },
                )
            )

    _LOGGER.info("[%s] Integration 'Moving Colors' base setup complete.", DOMAIN)
    return True


# Entry point for setup using ConfigEntry (via ConfigFlow)
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Moving Colors from a config entry."""
    _LOGGER.debug("[%s] Setting up Moving Colors from config entry: %s: data=%s, options=%s", DOMAIN, entry.entry_id, entry.data, entry.options)

    # Most reliable way to store the 'name',
    # as it will be set as 'title' during the creation of an entry.
    manager_name = entry.title

    # Combined entry-data and entry.options for the configuration of the manager.
    # 'Options' overwrite 'data', if their key is identical.
    config_data = {**entry.data, **entry.options}

    instance_name = config_data[MC_CONF_NAME]
    if not instance_name:
        _LOGGER.error("Instance name not found within configuration data.")
        return False

    # Sanitize logger instance name
    # 1. Replace spaces with underscores
    # 2. All lowercase
    # 3. Remove all characters that are not alphanumeric or underscores
    sanitized_instance_name = re.sub(r"\s+", "_", instance_name).lower()
    sanitized_instance_name = re.sub(r"[^a-z0-9_]", "", sanitized_instance_name)

    # Prevent empty name if there were only special characters used
    if not sanitized_instance_name:
        _LOGGER.warning("Sanitized logger instance name would be empty, using entry_id as fallback for: '%s'", instance_name)
        sanitized_instance_name = entry.entry_id

    instance_logger_name = f"{DOMAIN}.{sanitized_instance_name}"
    instance_specific_logger = logging.getLogger(instance_logger_name)

    if entry.options.get(DEBUG_ENABLED, False):
        instance_specific_logger.setLevel(logging.DEBUG)
        instance_specific_logger.debug("Debug log for instance '%s' activated.", instance_name)
    else:
        instance_specific_logger.setLevel(logging.INFO)
        instance_specific_logger.debug("Debug log for instance '%s' disabled.", instance_name)

    # The manager can't work without a configuration.
    if not config_data:
        _LOGGER.error(
            "[%s] Config data (entry.data + entry.options) is empty for entry %s during setup/reload. This means no configuration could be loaded.",
            manager_name,
            entry.entry_id,
        )
        return False

    # The light to handle with this integration
    target_light_entity_id = config_data.get(TARGET_LIGHT_ENTITY_ID)

    if not manager_name:
        _LOGGER.error(
            "[%s] No manager name found (entry.title was empty) for entry %s. This should not happen and indicates a deeper problem.",
            DOMAIN,
            entry.entry_id,
        )
        return False

    if not target_light_entity_id:
        _LOGGER.error("[%s] No target light entity ID found in config for entry %s.", manager_name, entry.entry_id)
        return False

    # =================================================================
    # Get SCInternal config options from yaml import and remove them
    # from entry.options and entry.data afterward.
    mc_internal_values = config_data.get("mc_internal_values", {})

    config_data.pop("mc_internal_values", None)

    # Remove from options
    if "mc_internal_values" in entry.options:
        new_options = dict(entry.options)
        new_options.pop("mc_internal_values")
        hass.config_entries.async_update_entry(entry, options=new_options)

    # Remove from data
    if "mc_internal_values" in entry.data:
        new_data = dict(entry.data)
        new_data.pop("mc_internal_values")
        hass.config_entries.async_update_entry(entry, data=new_data)
    # End of SCInternal handling
    # =================================================================

    # Hand over the combined configuration dictionary to the MovingColorsManager
    manager = MovingColorsManager(hass, config_data, entry.entry_id, instance_specific_logger)

    # =================================================================
    # After HA was started, the new internal entities exist.
    # Now set internal (manual) entities with configured values from yaml import
    async def set_internal_entities_when_ready(event=None) -> None:
        for internal_enum_name, value in mc_internal_values.items():
            _LOGGER.info("Configuring internal entity %s with %s", internal_enum_name, value)
            internal_enum = next((member for member in MCInternal if member.value == internal_enum_name), None)

            if internal_enum is None:
                _LOGGER.warning("Could not find SCInternal member for configuration key: %s. Skipping entity setup.", internal_enum_name)
                continue

            entity_id = manager.get_internal_entity_id(internal_enum)
            if entity_id:
                domain = internal_enum.domain
                if domain == "number":
                    _LOGGER.debug("Setting value of number %s to %s", entity_id, value)
                    await hass.services.async_call("number", "set_value", {"entity_id": entity_id, "value": value}, blocking=True)
                elif domain == "switch":
                    _LOGGER.debug("Setting value of switch %s to %s", entity_id, value)
                    service = "turn_on" if value else "turn_off"
                    await hass.services.async_call("switch", service, {"entity_id": entity_id}, blocking=True)
                elif domain == "select":
                    _LOGGER.debug("Setting value of select %s to %s", entity_id, value)
                    if hass.services.has_service("select", "select_option"):
                        await hass.services.async_call("select", "select_option", {"entity_id": entity_id, "option": value}, blocking=True)
                    else:
                        _LOGGER.warning("Service select.select_option not found for entity %s", entity_id)
                else:
                    _LOGGER.warning("Unsupported domain %s for internal entity %s", domain, entity_id)
            else:
                _LOGGER.warning("Could not find entity ID for internal entity %s", internal_enum_name)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, set_internal_entities_when_ready)
    # End of setting internal entities
    # =================================================================

    # Store manager within 'hass.data' to let sensors and other components access it.
    if DOMAIN_DATA_MANAGERS not in hass.data:
        hass.data[DOMAIN_DATA_MANAGERS] = {}
    hass.data[DOMAIN_DATA_MANAGERS][entry.entry_id] = manager
    _LOGGER.debug("[%s] Moving Colors manager stored for entry %s in %s.", manager_name, entry.entry_id, DOMAIN_DATA_MANAGERS)

    # Initial start of the manager
    await manager.async_start()

    # Load platforms (like sensors)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Add listeners for update of input values and integration trigger
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    _LOGGER.info("[%s] Integration '%s' successfully set up from config entry.", DOMAIN, manager_name)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("[%s] Unloading Moving Colors integration for entry: %s", DOMAIN, entry.entry_id)

    # Stop the periodic update task
    manager: MovingColorsManager = hass.data[DOMAIN_DATA_MANAGERS].get(entry.entry_id)
    if manager:
        manager.stop_update_task()

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        # Stop manager instance
        manager: MovingColorsManager = hass.data[DOMAIN_DATA_MANAGERS].pop(entry.entry_id, None)
        if manager:
            await manager.async_stop()

        _LOGGER.info("[%s] Shadow Control integration for entry %s successfully unloaded.", DOMAIN, entry.entry_id)
    else:
        _LOGGER.error("[%s] Failed to unload platforms for entry %s.", DOMAIN, entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug("[%s] Migrating from version %s", DOMAIN, config_entry.version)

    if config_entry.version == 1:
        # Example migration for version 1 to 2 if needed in the future
        # config_entry.version = 2
        # config_entry.data = {**config_entry.data, "new_key": "new_value"}
        _LOGGER.info("Data migration to version 1 successful (no changes needed yet).")
        return True

    _LOGGER.error("[%s] Unknown config entry version %s for migration. This should not happen.", DOMAIN, config_entry.version)
    return False


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update. Will be called if the user modifies the configuration using the OptionsFlow."""
    _LOGGER.debug("[%s] Options update listener triggered for entry %s.", DOMAIN, entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


class MovingColorsManager:
    """Manages the Moving Colors logic and state."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, instance_logger: logging.Logger) -> None:
        """Initialize the MovingColorsManager."""
        self.hass = hass
        self.config_entry = config_entry
        self._entry_id = config_entry.entry_id
        self._config = {**config_entry.data, **config_entry.options}
        self.logger = instance_logger

        self.name = self._config.get(MC_CONF_NAME)
        self._target_light_entity_id = self._config.get(TARGET_LIGHT_ENTITY_ID)

        # Check if critical values are missing, even if this might be done within async_setup_entry
        if not self.name:
            self.logger.warning("Manager init: Manager name is missing in config for entry %s. Using fallback.", self._entry_id)
            self.name = f"Unnamed Moving Colors ({self._entry_id})"
        if not self._target_light_entity_id:
            self.logger.error("Manager init: Target light entity ID is missing in config for entry %s. This is critical.", self._entry_id)
            message = f"Target light entity ID missing for entry {self._entry_id}"
            raise ValueError(message)

        self._unsub_callbacks: list[Callable[[], None]] = []
        self._update_listener: Callable[[], None] | None = None  # To store the interval task unlistener

        # Initialize internal state variables, equivalent to PHP's V#
        # V1: current lower boundary
        self._current_lower_boundary: int | None = None
        # V2: current upper boundary
        self._current_upper_boundary: int | None = None
        # V3: current value
        self._current_value: int | None = None
        # V4: current direction (True for count up, False for count down)
        self._count_up: bool | None = None
        # V5: remaining steps to default
        self._remaining_steps_to_default: int | None = None

        # Pre-fetch initial static values from config
        self._debug_enabled_static = self._config.get(DEBUG_ENABLED, False)
        self._start_from_current_position = self._config.get(MCConfig.START_FROM_CURRENT_POSITION_ENTITY.value, True)
        self._start_value = self._config.get(MCInternal.START_VALUE_MANUAL.value, MCIntDefaults.START.value)
        self._min_value = self._config.get(MCInternal.MIN_VALUE_MANUAL.value, MCIntDefaults.MIN.value)
        self._max_value = self._config.get(MCInternal.MAX_VALUE_MANUAL.value, MCIntDefaults.MAX.value)
        self._random_limits = self._config.get(MCInternal.RANDOM_LIMITS_MANUAL.value, True)
        self._default_value = self._config.get(MCInternal.DEFAULT_VALUE_MANUAL.value, MCIntDefaults.DEFAULT_END.value)
        self._default_mode_enabled = self._config.get(MCInternal.DEFAULT_MODE_ENABLED_MANUAL.value, False)
        self._steps_to_default = self._config.get(MCInternal.STEPS_TO_DEFAULT_MANUAL.value, MCIntDefaults.STEPS_TO_DEFAULT_END.value)

        # Store entity IDs for dynamic values
        self._start_value_entity = self._config.get(MCConfig.START_VALUE_ENTITY.value)
        self._min_value_entity = self._config.get(MCConfig.MIN_VALUE_ENTITY.value)
        self._max_value_entity = self._config.get(MCConfig.MAX_VALUE_ENTITY.value)
        self._random_limits_entity = self._config.get(MCConfig.RANDOM_LIMITS_ENTITY.value)
        self._default_value_entity = self._config.get(MCConfig.DEFAULT_VALUE_ENTITY.value)
        self._default_mode_enabled_entity = self._config.get(MCConfig.DEFAULT_MODE_ENABLED_ENTITY.value)
        self._steps_to_default_entity = self._config.get(MCConfig.STEPS_TO_DEFAULT_ENTITY.value)

        # Initialize internal state based on start value
        self._current_value = self._get_value_from_config_or_entity(
            MCInternal.START_VALUE_MANUAL.value, MCConfig.START_VALUE_ENTITY.value, default_val=MCIntDefaults.START.value
        )
        if self._start_from_current_position:
            self._current_value = self._get_brightness_of_first_light_entity()

        self._count_up = True  # Initial direction
        self._remaining_steps_to_default = self._get_value_from_config_or_entity(
            MCInternal.STEPS_TO_DEFAULT_MANUAL.value,
            MCConfig.STEPS_TO_DEFAULT_ENTITY.value,
            default_val=MCIntDefaults.STEPS_TO_DEFAULT_END.value,
        )
        self._current_lower_boundary = self._get_value_from_config_or_entity(
            MCInternal.MIN_VALUE_MANUAL.value, MCConfig.MIN_VALUE_ENTITY.value, default_val=MCIntDefaults.MIN.value
        )
        self._current_upper_boundary = self._get_value_from_config_or_entity(
            MCInternal.MAX_VALUE_MANUAL.value, MCConfig.MAX_VALUE_ENTITY.value, default_val=MCIntDefaults.MAX.value
        )

        # Get stepping and trigger interval values
        self._stepping = int(
            self._get_value_from_config_or_entity(MCInternal.STEPPING_MANUAL.value, MCConfig.STEPPING_ENTITY.value, MCIntDefaults.STEPPING.value)
        )
        self._trigger_interval = int(
            self._get_value_from_config_or_entity(
                MCInternal.TRIGGER_INTERVAL_MANUAL.value,
                MCConfig.TRIGGER_INTERVAL_ENTITY.value,
                MCIntDefaults.TRIGGER_INTERVAL.value,
            )
        )

        # Callback for sensor updates
        self._current_value_update_callback: Callable[[int], None] | None = None

        # Color mode and current values initialization
        self._color_mode = None
        self._current_values = {}

        # Detect color mode and initialize values based on the target light entity's state
        self._detect_color_mode_and_init_values()

    async def async_start(self) -> None:
        """Start the Moving Colors manager's operations."""
        self.logger.debug("Calling async_start for MovingColorsManager.")
        self._setup_enabled_listener()
        if self.is_enabled():
            self.async_start_update_task()

    async def async_stop(self) -> None:
        """Stop the Moving Colors manager's operations."""
        self.logger.debug("Stopping manager lifecycle...")
        self.stop_update_task()
        for unsub_callback in self._unsub_callbacks:
            unsub_callback()
        self._unsub_callbacks.clear()
        self.logger.debug("Listeners unregistered.")
        self.logger.debug("Manager lifecycle stopped.")

    def _setup_enabled_listener(self) -> None:
        """Set up listeners for enable/disable changes."""
        # Listen for entity state changes
        entity_id = self._config.get(MCConfig.ENABLED_ENTITY.value)
        if entity_id:
            unsub = async_track_state_change(self.hass, entity_id, self._handle_enabled_state_change)
            self._unsub_callbacks.append(unsub)

    def _get_brightness_of_first_light_entity(self) -> int:
        """Get the current brightness of the first configured light entity."""
        if not self._target_light_entity_id:
            self.logger.warning("No target light entity configured for START_FROM_CURRENT_POSITION.")
            return self._current_value  # fallback

        first_entity = self._target_light_entity_id[0]
        state = self.hass.states.get(first_entity)
        brightness = state.attributes.get("brightness") if state and hasattr(state, "attributes") else None

        if brightness is not None:
            try:
                return int(brightness)
            except (ValueError, TypeError):
                self.logger.warning(
                    "Brightness attribute for %s is not a valid integer: %s. Using current value %s as fallback.",
                    first_entity,
                    brightness,
                    self._current_value,
                )
        else:
            self.logger.debug("Could not get valid brightness from %s (state: %s). Starting at 1%%.", first_entity, state.state if state else "None")
            return 1  # Start at 1% if no valid brightness found

        return self._current_value  # fallback

    @callback
    def _handle_enabled_state_change(self, entity_id, old_state, new_state) -> None:
        """Handle changes to the enabled entity."""
        if self.is_enabled():
            self.logger.debug("Enabled state changed to ON, starting update task.")
            self.async_start_update_task()
        else:
            self.logger.debug("Enabled state changed to OFF, stopping update task.")
            self.stop_update_task()

    def is_enabled(self) -> bool:
        """Return True if Moving Colors should be active."""
        # Prefer entity if set
        if self._config.get(MCConfig.ENABLED_ENTITY.value):
            entity_id = self._config[MCConfig.ENABLED_ENTITY.value]
            state = self.hass.states.get(entity_id)
            if state and state.state not in ["unavailable", "unknown"]:
                return state.state.lower() in ["on", "true", "1"]
        # Fallback to the static option
        return self._config.get(MCInternal.ENABLED_MANUAL.value, True)

    def get_current_value(self) -> int:
        """Return the current calculated value."""
        return self._current_value if self._current_value is not None else 0

    def get_current_min_value(self) -> int:
        """Return the current min value."""
        return int(self._get_value_from_config_or_entity(MCInternal.MIN_VALUE_MANUAL.value, MCConfig.MIN_VALUE_ENTITY.value, MCIntDefaults.MIN.value))

    def get_current_max_value(self) -> int:
        """Return the current max value."""
        return int(self._get_value_from_config_or_entity(MCInternal.MAX_VALUE_MANUAL.value, MCConfig.MAX_VALUE_ENTITY.value, MCIntDefaults.MAX.value))

    def set_current_value_update_callback(self, callback_func: Callable[[int], None]) -> None:
        """Set the callback function for current value updates."""
        self._current_value_update_callback = callback_func

    def _get_value_from_config_or_entity(self, static_key: str, entity_key: str, default_val: Any) -> Any:
        """Get value from a static or a dynamic config entry."""
        if self._config.get(entity_key):
            entity_id = self._config[entity_key]
            state = self.hass.states.get(entity_id)
            if state and state.state not in ["unavailable", "unknown"]:
                try:
                    # For numerical values, convert state to float/int
                    if static_key in [
                        MCInternal.START_VALUE_MANUAL.value,
                        MCInternal.MIN_VALUE_MANUAL.value,
                        MCInternal.MAX_VALUE_MANUAL.value,
                        MCInternal.STEPPING_MANUAL.value,
                        MCInternal.DEFAULT_VALUE_MANUAL.value,
                        MCInternal.STEPS_TO_DEFAULT_MANUAL.value,
                    ]:
                        return float(state.state)  # Use float for calculations, convert to int at the end
                    # For boolean values
                    if static_key in [
                        MCInternal.RANDOM_LIMITS_MANUAL.value,
                        DEBUG_ENABLED,
                        MCInternal.DEFAULT_MODE_ENABLED_MANUAL.value,
                    ]:
                        return state.state.lower() == "on" or state.state.lower() == "true" or state.state == "1"
                except ValueError:
                    self.logger.warning("Could not convert state '%s' for entity '%s' to required type. Using static value.", state.state, entity_id)
            else:
                self.logger.warning("Entity '%s' state is not available or unknown. Using static value.", entity_id)
        return self._config.get(static_key, default_val)

    def async_start_update_task(self) -> None:  # Made async and renamed
        """Start the periodic update task."""
        if self._start_from_current_position:
            self._current_value = self._get_brightness_of_first_light_entity()

        if hasattr(self, "_update_listener") and self._update_listener:
            # Already running
            return
        interval = timedelta(seconds=self._trigger_interval)
        self.logger.debug("Starting periodic update task with interval %s.", interval)
        self._update_listener = async_track_time_interval(self.hass, self._async_update_moving_colors_state, interval)
        self._unsub_callbacks.append(self._update_listener)

    def stop_update_task(self) -> None:
        """Stop the periodic update task."""
        self.logger.debug("Stopping periodic update task.")
        if hasattr(self, "_update_listener") and self._update_listener:
            self._update_listener()
            self._update_listener = None

    def _detect_color_mode_and_init_values(self) -> None:
        """Detect color mode and initialize current values for the target light entity."""
        entity_id = self._target_light_entity_id[0]
        state = self.hass.states.get(entity_id)
        self.logger.debug("State for %s: %s", entity_id, state)
        if state:
            self.logger.debug("Attributes for %s: %s", entity_id, state.attributes)
        supported = state.attributes.get("supported_color_modes", []) if state else []
        color_mode = state.attributes.get("color_mode") if state else None
        # Default to brightness
        if "rgbw" in supported or color_mode == "rgbw":
            self._color_mode = "rgbw"
            rgbw = state.attributes.get("rgbw_color", [0, 0, 0, 0]) if state else [0, 0, 0, 0]
            self._current_values = {"r": rgbw[0], "g": rgbw[1], "b": rgbw[2], "w": rgbw[3]}
        elif "rgb" in supported or color_mode == "rgb":
            self._color_mode = "rgb"
            rgb = state.attributes.get("rgb_color", [0, 0, 0]) if state else [0, 0, 0]
            self._current_values = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}
        elif state and "rgb_color" in state.attributes:
            # Fallback: if rgb_color attribute exists, treat as rgb
            self._color_mode = "rgb"
            rgb = state.attributes.get("rgb_color", [0, 0, 0])
            self._current_values = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}
        else:
            self._color_mode = "brightness"
            brightness = state.attributes.get("brightness", 0) if state else 0
            self._current_values = {"brightness": brightness}
        self.logger.debug("Detected color mode: %s, initial values: %s", self._color_mode, self._current_values)

    @callback
    async def _async_update_moving_colors_state(self, now: dt_util.dt.datetime) -> None:
        """Calculate the next dimming value(s) and update the light entity."""
        self.logger.debug("Moving Colors update triggered at %s.", now)

        if not self.is_enabled():
            self.logger.debug("Moving Colors is disabled, skipping update.")
            return

        # Get current configuration values (refresh if from entity)
        min_value = int(
            self._get_value_from_config_or_entity(MCInternal.MIN_VALUE_MANUAL.value, MCConfig.MIN_VALUE_ENTITY.value, MCIntDefaults.MIN.value)
        )
        max_value = int(
            self._get_value_from_config_or_entity(MCInternal.MAX_VALUE_MANUAL.value, MCConfig.MAX_VALUE_ENTITY.value, MCIntDefaults.MAX.value)
        )
        stepping = int(
            self._get_value_from_config_or_entity(MCInternal.STEPPING_MANUAL.value, MCConfig.STEPPING_ENTITY.value, MCIntDefaults.STEPPING.value)
        )
        use_random = self._get_value_from_config_or_entity(MCInternal.RANDOM_LIMITS_MANUAL.value, MCConfig.RANDOM_LIMITS_ENTITY.value, True)

        # For each channel, cycle independently
        new_values = self._current_values.copy()
        for channel in self._current_values:
            val = self._current_values[channel]
            # Simple up/down cycling for each channel
            if not hasattr(self, f"_count_up_{channel}"):
                setattr(self, f"_count_up_{channel}", True)
            count_up = getattr(self, f"_count_up_{channel}")
            if count_up and val < max_value:
                val += stepping
                val = min(val, max_value)
            elif count_up and val >= max_value:
                val -= stepping
                setattr(self, f"_count_up_{channel}", False)
                if use_random:
                    min_rand = random.randint(min_value, val)
                    self.logger.debug("Channel %s: Reached upper boundary, switching to count down. New random lower boundary: %s", channel, min_rand)
                else:
                    min_rand = min_value
                # Not used further, but could be stored per channel
            elif not count_up and val > min_value:
                val -= stepping
                val = max(val, min_value)
            elif not count_up and val <= min_value:
                val += stepping
                setattr(self, f"_count_up_{channel}", True)
                if use_random:
                    max_rand = random.randint(val, max_value)
                    self.logger.debug("Channel %s: Reached lower boundary, switching to count up. New random upper boundary: %s", channel, max_rand)
                else:
                    max_rand = max_value
                # Not used further, but could be stored per channel
            new_values[channel] = max(0, min(255, val))
        self._current_values = new_values

        # Prepare service data based on color mode
        for target_entity in self._target_light_entity_id:
            if target_entity:
                if self._color_mode == "rgbw":
                    rgbw = [self._current_values[c] for c in "rgbw"]
                    service_data = {"entity_id": target_entity, "rgbw_color": rgbw}
                    self.logger.debug(
                        "Set light %s to rgbw_color %s (lower boundary: %s, upper boundary: %s)",
                        target_entity,
                        rgbw,
                        self._current_lower_boundary,
                        self._current_upper_boundary,
                    )
                elif self._color_mode == "rgb":
                    rgb = [self._current_values[c] for c in "rgb"]
                    service_data = {"entity_id": target_entity, "rgb_color": rgb}
                    self.logger.debug(
                        "Set light %s to rgb_color %s (lower boundary: %s, upper boundary: %s)",
                        target_entity,
                        rgb,
                        self._current_lower_boundary,
                        self._current_upper_boundary,
                    )
                else:
                    brightness = self._current_values["brightness"]
                    service_data = {"entity_id": target_entity, "brightness": brightness}
                    self.logger.debug(
                        "Set light %s to brightness %s (lower boundary: %s, upper boundary: %s)",
                        target_entity,
                        brightness,
                        self._current_lower_boundary,
                        self._current_upper_boundary,
                    )
                await self.hass.services.async_call("light", "turn_on", service_data)
            else:
                self.logger.error("No target light entity ID configured for Moving Colors instance.")

    def get_internal_entity_id(self, internal_enum: MCInternal) -> str:
        """Get the internal entity_id for this instance."""
        registry = entity_registry.async_get(self.hass)
        unique_id = f"{self._entry_id}_{internal_enum.value.lower()}"
        entity_id = registry.async_get_entity_id(internal_enum.domain, "shadow_control", unique_id)
        self.logger.debug("Looking up internal entity_id for unique_id: %s -> %s", unique_id, entity_id)
        return entity_id


# Helper for dynamic log output
def _format_config_object_for_logging(obj, prefix: str = "") -> str:
    """Format the public attributes of a given configuration object into one string."""
    if not obj:
        return f"{prefix}None"

    parts = []
    # `vars(obj)` returns a dictionary of __dict__ attributes of a given object
    for attr, value in vars(obj).items():
        # Skip 'private' attributes, which start with an underscore
        if not attr.startswith("_"):
            parts.append(f"{attr}={value}")

    if not parts:
        return f"{prefix}No attributes to log found."

    return f"{prefix}{', '.join(parts)}"
