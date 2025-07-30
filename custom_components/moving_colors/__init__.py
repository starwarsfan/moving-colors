"""Integration for Moving Colors."""

import inspect
import logging
import random
import re
from collections.abc import Callable
from datetime import timedelta
from typing import Any

import homeassistant.util.dt as dt_util
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change, async_track_time_interval
from homeassistant.helpers.typing import ConfigType

from .const import (
    DEBUG_ENABLED,
    DOMAIN,
    DOMAIN_DATA_MANAGERS,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
    VERSION,
    MovingColorsConfig,
)

_GLOBAL_DOMAIN_LOGGER = logging.getLogger(DOMAIN)
_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

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

    # Hand over the combined configuration dictionary to the MovingColorsManager
    manager = MovingColorsManager(hass, config_data, entry.entry_id, instance_specific_logger)

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

    entry_id = entry.entry_id
    instance_name = entry.data.get(MC_CONF_NAME)
    instance_logger = _GLOBAL_DOMAIN_LOGGER.getChild(f"{DOMAIN}.{instance_name or entry_id}")
    instance_logger.debug("[%s] async_unload_entry called.", DOMAIN)

    # Stop the periodic update task
    manager: MovingColorsManager = hass.data[DOMAIN_DATA_MANAGERS].get(entry_id)
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

    def __init__(self, hass: HomeAssistant, config: dict[str, Any], entry_id: str, instance_logger: logging.Logger) -> None:
        """Initialize the MovingColorsManager."""
        self.hass = hass
        self.entry_id = entry_id
        self.logger = instance_logger

        self.name = config.get(MC_CONF_NAME)
        self._target_light_entity_id = config.get(TARGET_LIGHT_ENTITY_ID)

        # Check if critical values are missing, even if this might be done within async_setup_entry
        if not self.name:
            self.logger.warning("Manager init: Manager name is missing in config for entry %s. Using fallback.", entry_id)
            self.name = f"Unnamed Moving Colors ({entry_id})"
        if not self._target_light_entity_id:
            self.logger.error("Manager init: Target light entity ID is missing in config for entry %s. This is critical.", entry_id)
            message = f"Target light entity ID missing for entry {entry_id}"
            raise ValueError(message)

        self._options = config  # Store all config/options

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
        self._debug_enabled_static = self._options.get(DEBUG_ENABLED, False)
        self._start_value_static = self._options.get(MovingColorsConfig.START_VALUE_STATIC.value, 125)
        self._min_value_static = self._options.get(MovingColorsConfig.MIN_VALUE_STATIC.value, 0)
        self._max_value_static = self._options.get(MovingColorsConfig.MAX_VALUE_STATIC.value, 255)
        self._step_value_static = self._options.get(MovingColorsConfig.STEP_VALUE_STATIC.value, 2)
        self._random_limits_static = self._options.get(MovingColorsConfig.RANDOM_LIMITS_STATIC.value, True)
        self._default_value_static = self._options.get(MovingColorsConfig.DEFAULT_VALUE_STATIC.value, 0)
        self._default_mode_enabled_static = self._options.get(MovingColorsConfig.DEFAULT_MODE_ENABLED_STATIC.value, False)
        self._steps_to_default_static = self._options.get(MovingColorsConfig.STEPS_TO_DEFAULT_STATIC.value, 3)

        # Store entity IDs for dynamic values
        self._start_value_entity = self._options.get(MovingColorsConfig.START_VALUE_ENTITY.value)
        self._min_value_entity = self._options.get(MovingColorsConfig.MIN_VALUE_ENTITY.value)
        self._max_value_entity = self._options.get(MovingColorsConfig.MAX_VALUE_ENTITY.value)
        self._step_value_entity = self._options.get(MovingColorsConfig.STEP_VALUE_ENTITY.value)
        self._random_limits_entity = self._options.get(MovingColorsConfig.RANDOM_LIMITS_ENTITY.value)
        self._default_value_entity = self._options.get(MovingColorsConfig.DEFAULT_VALUE_ENTITY.value)
        self._default_mode_enabled_entity = self._options.get(MovingColorsConfig.DEFAULT_MODE_ENABLED_ENTITY.value)
        self._steps_to_default_entity = self._options.get(MovingColorsConfig.STEPS_TO_DEFAULT_ENTITY.value)

        # Initialize internal state based on start value
        self._current_value = self._get_value_from_config_or_entity(
            MovingColorsConfig.START_VALUE_STATIC.value, MovingColorsConfig.START_VALUE_ENTITY.value, default_val=125
        )
        self._count_up = True  # Initial direction
        self._remaining_steps_to_default = self._get_value_from_config_or_entity(
            MovingColorsConfig.STEPS_TO_DEFAULT_STATIC.value, MovingColorsConfig.STEPS_TO_DEFAULT_ENTITY.value, default_val=3
        )
        self._current_lower_boundary = self._get_value_from_config_or_entity(
            MovingColorsConfig.MIN_VALUE_STATIC.value, MovingColorsConfig.MIN_VALUE_ENTITY.value, default_val=0
        )
        self._current_upper_boundary = self._get_value_from_config_or_entity(
            MovingColorsConfig.MAX_VALUE_STATIC.value, MovingColorsConfig.MAX_VALUE_ENTITY.value, default_val=255
        )

        # Callback for sensor updates
        self._current_value_update_callback: Callable[[int], None] | None = None

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
        entity_id = self._options.get(MovingColorsConfig.ENABLED_ENTITY.value)
        if entity_id:
            unsub = async_track_state_change(
                self.hass,
                entity_id,
                self._handle_enabled_state_change,
            )
            self._unsub_callbacks.append(unsub)

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
        if self._options.get(MovingColorsConfig.ENABLED_ENTITY.value):
            entity_id = self._options[MovingColorsConfig.ENABLED_ENTITY.value]
            state = self.hass.states.get(entity_id)
            if state and state.state not in ["unavailable", "unknown"]:
                return state.state.lower() in ["on", "true", "1"]
        # Fallback to the static option
        return self._options.get(MovingColorsConfig.ENABLED_STATIC.value, True)

    def get_current_value(self) -> int:
        """Return the current calculated value."""
        return self._current_value if self._current_value is not None else 0

    def get_current_min_value(self) -> int:
        """Return the current min value."""
        return int(self._get_value_from_config_or_entity(MovingColorsConfig.MIN_VALUE_STATIC.value, MovingColorsConfig.MIN_VALUE_ENTITY.value, 0))

    def get_current_max_value(self) -> int:
        """Return the current max value."""
        return int(self._get_value_from_config_or_entity(MovingColorsConfig.MAX_VALUE_STATIC.value, MovingColorsConfig.MAX_VALUE_ENTITY.value, 255))

    def set_current_value_update_callback(self, callback_func: Callable[[int], None]) -> None:
        """Set the callback function for current value updates."""
        self._current_value_update_callback = callback_func

    def _get_value_from_config_or_entity(self, static_key: str, entity_key: str, default_val: Any) -> Any:
        """Get value from a static or a dynamic config entry."""
        if self._options.get(entity_key):
            entity_id = self._options[entity_key]
            state = self.hass.states.get(entity_id)
            if state and state.state not in ["unavailable", "unknown"]:
                try:
                    # For numerical values, convert state to float/int
                    if static_key in [
                        MovingColorsConfig.START_VALUE_STATIC.value,
                        MovingColorsConfig.MIN_VALUE_STATIC.value,
                        MovingColorsConfig.MAX_VALUE_STATIC.value,
                        MovingColorsConfig.STEP_VALUE_STATIC.value,
                        MovingColorsConfig.DEFAULT_VALUE_STATIC.value,
                        MovingColorsConfig.STEPS_TO_DEFAULT_STATIC.value,
                    ]:
                        return float(state.state)  # Use float for calculations, convert to int at the end
                    # For boolean values
                    if static_key in [
                        MovingColorsConfig.RANDOM_LIMITS_STATIC.value,
                        DEBUG_ENABLED,
                        MovingColorsConfig.DEFAULT_MODE_ENABLED_STATIC.value,
                    ]:
                        return state.state.lower() == "on" or state.state.lower() == "true" or state.state == "1"
                except ValueError:
                    self.logger.warning("Could not convert state '%s' for entity '%s' to required type. Using static value.", state.state, entity_id)
            else:
                self.logger.warning("Entity '%s' state is not available or unknown. Using static value.", entity_id)
        return self._options.get(static_key, default_val)

    def async_start_update_task(self) -> None:  # Made async and renamed
        """Start the periodic update task."""
        # Use 2 seconds as a default for now.
        if hasattr(self, "_update_listener") and self._update_listener:
            # Already running
            return
        interval = timedelta(seconds=2)
        self.logger.debug("Starting periodic update task with interval %s.", interval)
        self._update_listener = async_track_time_interval(self.hass, self._async_update_moving_colors_state, interval)
        self._unsub_callbacks.append(self._update_listener)

    def stop_update_task(self) -> None:
        """Stop the periodic update task."""
        self.logger.debug("Stopping periodic update task.")
        if hasattr(self, "_update_listener") and self._update_listener:
            self._update_listener()
            self._update_listener = None

    @callback
    async def _async_update_moving_colors_state(self, now: dt_util.dt.datetime) -> None:
        """Calculate the next dimming value and update the light entity."""
        self.logger.debug("Moving Colors update triggered at %s.", now)

        if not self.is_enabled():
            self.logger.debug("Moving Colors is disabled, skipping update.")
            return

        old_current_value = self._current_value  # Store old value to check for changes

        # Get current configuration values (refresh if from entity)
        min_value = int(
            self._get_value_from_config_or_entity(MovingColorsConfig.MIN_VALUE_STATIC.value, MovingColorsConfig.MIN_VALUE_ENTITY.value, 0)
        )
        max_value = int(
            self._get_value_from_config_or_entity(MovingColorsConfig.MAX_VALUE_STATIC.value, MovingColorsConfig.MAX_VALUE_ENTITY.value, 255)
        )
        stepping = int(
            self._get_value_from_config_or_entity(MovingColorsConfig.STEP_VALUE_STATIC.value, MovingColorsConfig.STEP_VALUE_ENTITY.value, 2)
        )
        use_random = self._get_value_from_config_or_entity(
            MovingColorsConfig.RANDOM_LIMITS_STATIC.value, MovingColorsConfig.RANDOM_LIMITS_ENTITY.value, True
        )
        default_value = int(
            self._get_value_from_config_or_entity(MovingColorsConfig.DEFAULT_VALUE_STATIC.value, MovingColorsConfig.DEFAULT_VALUE_ENTITY.value, 0)
        )
        default_active = self._get_value_from_config_or_entity(
            MovingColorsConfig.DEFAULT_MODE_ENABLED_STATIC.value, MovingColorsConfig.DEFAULT_MODE_ENABLED_ENTITY.value, False
        )
        steps_to_default = int(
            self._get_value_from_config_or_entity(
                MovingColorsConfig.STEPS_TO_DEFAULT_STATIC.value, MovingColorsConfig.STEPS_TO_DEFAULT_ENTITY.value, 3
            )
        )

        # PHP's validation logic from LB_LBSID_validateInput
        # In Python, Voluptuous handles most of this, but some runtime checks or adjustments are still useful
        # especially for values coming from entities.
        min_value = max(0, min(255, min_value))
        max_value = max(0, min(255, max_value))
        if max_value < min_value:
            min_value, max_value = max_value, min_value  # Swap if min > max
            self.logger.warning("Swapped min (%s) and max (%s) values due to invalid configuration.", min_value, max_value)

        # Ensure stepping is within 1-10
        stepping = max(1, min(10, stepping))

        # Ensure steps_to_default is within 1-100 (assuming 100 as a reasonable upper bound)
        steps_to_default = max(1, min(100, steps_to_default))

        # The PHP code checks E8['refresh'] to reset the remaining steps.
        # In Home Assistant, a change listener on the default_value_entity or option might be used.
        # For simplicity now, we'll re-initialize the remaining steps if the default mode is enabled and it's not set.
        # Or, if the default value entity changes, we could reset this. For now, rely on its initial value.
        # If the user changes the static default_value via options, the integration will reload via async_reload_entry,
        # resetting the manager and its internal state.

        # If default value entity changes, reset remaining steps.
        # This part is more complex as it requires tracking the previous state of the default value entity.
        # For a simple migration, we'll rely on the default logic that resets V5 if defaultActive is False
        # and re-initializes it when defaultActive becomes True.

        # PHP: if ($E[8]['refresh']) { setLogicElementVar($id, 5, $E[10]['value']); }
        # This implies: If the default value *input* itself gets refreshed, reset the remaining steps.
        # In HA, if the `MovingColorsConfig.DEFAULT_VALUE_ENTITY.value` changes state, we'd need to detect that.
        # A simpler approach is that if `default_active` is true and `_remaining_steps_to_default` is None or 0,
        # it gets re-initialized to `steps_to_default`.

        # Check if current_value is initialized. If not, use start value.
        if self._current_value is None:
            self._current_value = self._get_value_from_config_or_entity(
                MovingColorsConfig.START_VALUE_STATIC.value, MovingColorsConfig.START_VALUE_ENTITY.value, 0
            )
            self.logger.debug("Initialized _current_value to %s", self._current_value)

        # Default control is active
        if default_active:
            self.logger.debug("Default mode active. Remaining steps: %s", self._remaining_steps_to_default)

            # remainingSteps had not been initialized? Go for it!
            if self._remaining_steps_to_default is None or self._remaining_steps_to_default == 0:
                self._remaining_steps_to_default = steps_to_default
                self.logger.debug("Resetting remaining steps to default: %s", self._remaining_steps_to_default)

            # are there more steps to compute on our way to output the default value?
            if self._remaining_steps_to_default > 0:
                # Calculate new value
                # (defaultValue - currentValue) / remainingSteps -> ensures smooth transition
                # Ensure integer result
                self._current_value = int(self._current_value + (default_value - self._current_value) / self._remaining_steps_to_default)
                self._remaining_steps_to_default -= 1
                self.logger.debug(
                    "defaultActive: true, currentValue: %s, remainingSteps: %s, defaultValue: %s",
                    self._current_value,
                    self._remaining_steps_to_default,
                    default_value,
                )
            else:
                # If the remaining steps are 0, set to the default value to ensure it hits exactly
                self._current_value = default_value
                self.logger.debug("defaultActive: true, remaining steps 0, setting currentValue to defaultValue: %s", self._current_value)

        else:  # Not in the default mode
            # when not in default mode reset remaining steps variable
            self._remaining_steps_to_default = steps_to_default
            self.logger.debug("Default mode inactive. Resetting remaining steps to default.")

            # Get current dimm direction
            # If not initialized, assume count up
            if self._count_up is None:
                self._count_up = True

            # Get current upper and lower dimm boundary
            # If not initialized, use current min/max values
            if self._current_lower_boundary is None:
                self._current_lower_boundary = min_value
            if self._current_upper_boundary is None:
                self._current_upper_boundary = max_value

            self.logger.debug(
                "min_value: %s, max_value: %s, count_up: %s, lower_boundary: %s, currentValue: %s, upper_boundary: %s",
                min_value,
                max_value,
                self._count_up,
                self._current_lower_boundary,
                self._current_value,
                self._current_upper_boundary,
            )

            # Now go ahead and calculate the next dimm value
            if self._count_up and self._current_value < self._current_upper_boundary:
                # Increase dimm value
                self._current_value += stepping
                # Ensure not exceeding upper boundary
                self._current_value = min(self._current_value, self._current_upper_boundary)
            elif self._count_up and self._current_value >= self._current_upper_boundary:
                # Reached upper boundary, so decrease dimm value, change dimm direction
                # and determine random-based next lower boundary
                self._current_value -= stepping
                self._count_up = False
                # If the random-based boundary was deactivated, skip computation of the next value
                if use_random:
                    # PHP: rand($minValue, $upperBoundary)
                    self._current_lower_boundary = random.randint(min_value, self._current_upper_boundary)
                    self.logger.debug("Reached upper boundary, switching to count down. New random lower boundary: %s", self._current_lower_boundary)
                else:
                    self._current_lower_boundary = min_value  # Use fixed min if random is off
                    self.logger.debug("Reached upper boundary, switching to count down. Fixed lower boundary: %s", self._current_lower_boundary)
            elif not self._count_up and self._current_value > self._current_lower_boundary:
                # Decrease dimm value
                self._current_value -= stepping
                # Ensure not going below the lower boundary
                self._current_value = max(self._current_value, self._current_lower_boundary)
            elif not self._count_up and self._current_value <= self._current_lower_boundary:
                # Reached the lower boundary, so increase dimm value, change dimm direction
                # and determine random-based next upper boundary
                self._current_value += stepping
                self._count_up = True
                # If the random-based boundary was deactivated, skip computation of the next value
                if use_random:
                    # PHP: rand($lowerBoundary, $maxValue)
                    self._current_upper_boundary = random.randint(self._current_lower_boundary, max_value)
                    self.logger.debug("Reached lower boundary, switching to count up. New random upper boundary: %s", self._current_upper_boundary)
                else:
                    self._current_upper_boundary = max_value  # Use fixed max if random is off
                    self.logger.debug("Reached lower boundary, switching to count up. Fixed upper boundary: %s", self._current_upper_boundary)

        # Ensure the final value is within 0-255
        self._current_value = max(0, min(255, self._current_value))

        # Notify sensor of updated value if it exists
        if self._current_value_update_callback and self._current_value != old_current_value:
            if inspect.iscoroutinefunction(self._current_value_update_callback):
                self.hass.async_create_task(self._current_value_update_callback(self._current_value))
            else:
                self._current_value_update_callback(self._current_value)

        for target_entity in self._target_light_entity_id:
            if target_entity:
                self.logger.debug("Set light %s to brightness %s", target_entity, self._current_value)
                # Home Assistant brightness is 0-255 for lights
                # We assume the target entity is a light that supports brightness.
                # You might want to add more robust error handling or check capabilities.
                service_data = {"entity_id": target_entity, "brightness": self._current_value}
                await self.hass.services.async_call("light", "turn_on", service_data)
            else:
                self.logger.error("No target light entity ID configured for Moving Colors instance.")


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
