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
    STATE_ON,
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
    INTERNAL_TO_DEFAULTS_MAP,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
    VERSION,
    MCConfig,
    MCInternal,
    MCInternalDefaults,
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
        instance_specific_logger.debug("Debug log for instance '%s' disabled.", instance_name)
        instance_specific_logger.setLevel(logging.INFO)

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
    manager = MovingColorsManager(hass, entry, instance_specific_logger)

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

        # 2. NEW: Initialize empty internal entities with MCIntDefaults
        for internal_member in MCInternal:
            entity_id = manager.get_internal_entity_id(internal_member)

            if not entity_id:
                _LOGGER.debug("Entity ID for %s not found, skipping initialization", internal_member.name)
                continue

            state = hass.states.get(entity_id)

            # If the entity exists but has no value, push the default from const.py
            if state is None or state.state in ["unavailable", "unknown"]:
                default_val = INTERNAL_TO_DEFAULTS_MAP.get(internal_member)

                if default_val is not None:
                    domain = internal_member.domain
                    if domain == "number":
                        await hass.services.async_call("number", "set_value", {"entity_id": entity_id, "value": default_val})
                    elif domain == "switch":
                        service = "turn_on" if default_val else "turn_off"
                        await hass.services.async_call("switch", service, {"entity_id": entity_id})

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, set_internal_entities_when_ready)
    # End of setting internal entities
    # =================================================================

    # Store manager within 'hass.data' to let sensors and other components access it.
    if DOMAIN_DATA_MANAGERS not in hass.data:
        hass.data[DOMAIN_DATA_MANAGERS] = {}
    hass.data[DOMAIN_DATA_MANAGERS][entry.entry_id] = manager
    _LOGGER.debug("[%s] Moving Colors manager stored for entry %s in %s.", manager_name, entry.entry_id, DOMAIN_DATA_MANAGERS)

    # Only start immediately if HA is already fully started.
    # If HA is still booting, the EVENT_HOMEASSISTANT_STARTED listener
    # inside the manager will trigger the start automatically.
    if hass.is_running:
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

        _LOGGER.info("[%s] Moving Colors integration for entry %s successfully unloaded.", DOMAIN, entry.entry_id)
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
        self._config_entry = config_entry
        self._entry_id = config_entry.entry_id
        self._config = {**config_entry.data, **config_entry.options}
        self.logger = instance_logger

        self.name = self._config.get(MC_CONF_NAME)
        self._target_light_entity_id = self._config.get(TARGET_LIGHT_ENTITY_ID)

        # Sanitize instance name
        # 1. Replace spaces with underscores
        # 2. All lowercase
        # 3. Remove all characters that are not alphanumeric or underscores
        sanitized_instance_name = re.sub(r"\s+", "_", self.name).lower()
        sanitized_instance_name = re.sub(r"[^a-z0-9_]", "", sanitized_instance_name)
        self.sanitized_name = sanitized_instance_name
        self.logger.debug("Sanitized instance name from %s to %s", self.name, self.sanitized_name)

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

        # 1. Structural Config Helper (fixes repetitive code and ANN202)
        def get_conf(key: str, default: Any = None) -> Any:
            """Fetch structural config from options or fallback to data."""
            return config_entry.options.get(key, config_entry.data.get(key, default))

        # 2. Structural Config (Things that usually don't change without a reload)
        self._target_light_entity_id = get_conf(TARGET_LIGHT_ENTITY_ID)
        self._debug_enabled = get_conf(DEBUG_ENABLED, False)

        # 3. Runtime State (Tracking variables used by the logic loop)
        self._current_value: int | None = None
        self._current_direction: int = 1  # 1 for up, -1 for down
        self._update_listener: Callable[[], None] | None = None

        # Initialize the state trackers for the logic
        self._active_min: dict[str, int] = {}
        self._active_max: dict[str, int] = {}
        self._current_values: dict[str, int] = {}
        self._color_mode = None

        # Boundaries and Mode Tracking
        self._steps_since_last_change: int = 0
        self._is_in_default_mode: bool = False

        # Callback for sensor updates
        self._current_value_update_callback: Callable[[int], None] | None = None

        # Detect color mode and initialize values based on the target light entity's state
        self._detect_color_mode_and_init_values()

        self.logger.debug("[%s] Manager initialized for target: %s", self.name, self._target_light_entity_id)

    async def async_start(self) -> None:
        """Start the Moving Colors manager's operations."""
        if not self.is_enabled():
            self.logger.info("Moving Colors '%s' is disabled. Waiting for activation.", self.name)
            return

        self.logger.debug("Starting Moving Colors instance loop.")
        await self.async_update_state()

    async def async_stop(self) -> None:
        """Stop the Moving Colors manager's operations."""
        self.logger.debug("Stopping manager lifecycle...")
        await self.stop_update_task()
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

    def get_current_value(self) -> int:
        """Return the current calculated value."""
        if self._color_mode == "rgbw":
            rgbw = [self._current_values[c] for c in "rgbw"]
            self.logger.warning("Current value requested for rgbw mode: %s. Returning 0 as placeholder.", rgbw)
            current_value = rgbw[0]
        elif self._color_mode == "rgb":
            rgb = [self._current_values[c] for c in "rgb"]
            self.logger.warning("Current value requested for rgb mode: %s. Returning 0 as placeholder.", rgb)
            current_value = rgb[0]
        else:
            current_value = self._current_values["brightness"]

        return current_value

    def set_current_value_update_callback(self, callback_func: Callable[[int], None]) -> None:
        """Set the callback function for current value updates."""
        self._current_value_update_callback = callback_func

    async def async_start_update_task(self) -> None:
        """Start the periodic update task."""
        # 1. Check if already running
        if hasattr(self, "_update_listener") and self._update_listener:
            # Already running
            return

        # 2. Capture initial state
        # This must happen before we start the timer
        await self._capture_initial_state()

        # 3. (Optional) Sync current loop values to the snapshot
        # so the first step isn't a huge jump
        if self.is_start_from_current_position_enabled():
            # You'll need to implement this to pull RGBW from the snapshot
            self._sync_current_values_to_snapshot()

        interval = timedelta(seconds=self.get_config_trigger_interval())
        self.logger.debug("Starting periodic update task with interval %s.", interval)

        # 4. Start the timer
        self._update_listener = async_track_time_interval(self.hass, self.async_update_state, interval)
        self._unsub_callbacks.append(self._update_listener)

        # Manually trigger the first step AFTER the listener is set
        await self.async_update_state()

    async def stop_update_task(self) -> None:
        """Stop the periodic update task."""
        self.logger.debug("Stopping periodic update task.")
        if hasattr(self, "_update_listener") and self._update_listener:
            self._update_listener()  # Stop the timer
            # Remove it from the list so we don't try to call it again later
            if self._update_listener in self._unsub_callbacks:
                self._unsub_callbacks.remove(self._update_listener)
            self._update_listener = None

        await self._restore_initial_state()

    def _sync_current_values_to_snapshot(self) -> None:
        """Align internal loop values with the physical light state (RGBW or Brightness)."""
        if not self._initial_state:
            return

        abs_min = self.get_config_min_value()
        abs_max = self.get_config_max_value()

        # Case 1: RGBW Lights
        if self._color_mode == "rgbw" and self._initial_state.get("rgbw_color"):
            for i, channel in enumerate(["r", "g", "b", "w"]):
                val = self._initial_state["rgbw_color"][i]
                self._current_values[channel] = val

                # PRIME THE LOGIC: Set boundaries and direction for each channel
                self._active_min[channel] = abs_min
                self._active_max[channel] = abs_max
                setattr(self, f"_count_up_{channel}", True)

            self.logger.debug("Sync: RGBW values aligned and logic primed: %s", self._current_values)

        # Case 2: RGB Lights
        elif self._color_mode == "rgb" and self._initial_state.get("rgb_color"):
            for i, channel in enumerate(["r", "g", "b"]):
                val = self._initial_state["rgb_color"][i]
                self._current_values[channel] = val

                # PRIME THE LOGIC: Set boundaries and direction for each channel
                self._active_min[channel] = abs_min
                self._active_max[channel] = abs_max
                setattr(self, f"_count_up_{channel}", True)

            self.logger.debug("Sync: RGB values aligned to %s", self._current_values)

        # Case 3: Simple Brightness Lights
        elif self._initial_state.get("brightness") is not None:
            val = self._initial_state["brightness"]
            self._current_values["brightness"] = val

            # PRIME THE LOGIC for brightness
            self._active_min["brightness"] = abs_min
            self._active_max["brightness"] = abs_max
            setattr(self, "_count_up_brightness", True)

            self.logger.debug("Sync: Brightness aligned to %s", self._current_values["brightness"])

    def _detect_color_mode_and_init_values(self) -> None:
        """Detect color mode and initialize current values for the target light entity."""
        entity_id = self._target_light_entity_id[0]
        state = self.hass.states.get(entity_id)

        # 1. Try to get capabilities from the Entity Registry first (more reliable)
        registry = entity_registry.async_get(self.hass)
        entry = registry.async_get(entity_id)

        # Extract capabilities from registry entry if available
        supported_features = []
        if entry and entry.capabilities:
            supported_features = entry.capabilities.get("supported_color_modes", [])

        # 2. Fallback to current state attributes if registry is sparse
        if not supported_features and state:
            supported_features = state.attributes.get("supported_color_modes", [])

        self.logger.debug("Supported features for %s: %s", entity_id, supported_features)

        # 3. Logic-based detection
        if "rgbw" in supported_features:
            self._color_mode = "rgbw"
            rgbw = state.attributes.get("rgbw_color") if state else None
            if not isinstance(rgbw, (list, tuple)):
                rgbw = [0, 0, 0, 0]
            self._current_values = {"r": rgbw[0], "g": rgbw[1], "b": rgbw[2], "w": rgbw[3]}

        elif "rgb" in supported_features or "xy" in supported_features:
            self._color_mode = "rgb"
            rgb = state.attributes.get("rgb_color") if state else None
            if not isinstance(rgb, (list, tuple)):
                rgb = [0, 0, 0]
            self._current_values = {"r": rgb[0], "g": rgb[1], "b": rgb[2]}

        else:
            self._color_mode = "brightness"
            brightness = state.attributes.get("brightness", 0) if state else 0
            self._current_values = {"brightness": brightness}

        self.logger.debug("Final detected color mode: %s", self._color_mode)

    async def _capture_initial_state(self) -> None:
        """Capture current light state before the loop starts."""
        # We take the first target entity as the reference
        entity_id = self._target_light_entity_id[0]
        state = self.hass.states.get(entity_id)

        if state:
            self._initial_state = {
                "state": state.state,  # Store 'on' or 'off'
                "rgbw_color": state.attributes.get("rgbw_color"),
                "rgb_color": state.attributes.get("rgb_color"),
                "brightness": state.attributes.get("brightness"),
            }
            self.logger.debug("Snapshot captured for %s: %s", entity_id, self._initial_state)

            # Sync internal values to current state to prevent a "jump" on the first tick
            if self._color_mode == "rgbw" and self._initial_state["rgbw_color"]:
                for i, char in enumerate("rgbw"):
                    self._current_values[char] = self._initial_state["rgbw_color"][i]

    async def async_update_state(self, now: dt_util.dt.datetime | None = None) -> None:
        """Calculate the next dimming value(s) and update the light entity."""
        if not self.is_enabled():
            self.logger.debug("Moving Colors is disabled, skipping update.")
            self.stop_update_task()
            return

        # if now is None:
        #     now = dt_util.utcnow()
        # self.logger.debug("Moving Colors update triggered at %s.", now)

        # Configured absolute limits
        abs_min = self.get_config_min_value()
        abs_max = self.get_config_max_value()
        stepping = self.get_config_stepping()
        use_random = self.is_random_limits_enabled()

        new_values = self._current_values.copy()

        for channel in self._current_values:
            if channel == "w":
                # Skip white channel entirely by setting it to 0
                new_values[channel] = max(0, min(255, 0))
                continue

            val = self._current_values[channel]

            # 1. Initialize per-channel state if needed
            if channel not in self._active_min:
                self._active_min[channel] = abs_min
                self._active_max[channel] = abs_max
                setattr(self, f"_count_up_{channel}", True)

            count_up = getattr(self, f"_count_up_{channel}")

            # 2. Logic for moving UP
            if count_up:
                val += stepping
                # Check if we hit the CURRENT active max for this channel
                if val >= self._active_max[channel]:
                    val = self._active_max[channel]
                    setattr(self, f"_count_up_{channel}", False)

                    # We hit the top, generate new RANDOM MIN for the trip down
                    if use_random:
                        # New min is between absolute min and current position
                        self._active_min[channel] = random.randint(abs_min, int(val))
                        self.logger.debug("Channel %s: Hit max (%s). New random min border: %s", channel, val, self._active_min[channel])
                    else:
                        self._active_min[channel] = abs_min
                        self.logger.debug("Channel %s: Hit max (%s).", channel, val)

            # 3. Logic for moving DOWN
            else:
                val -= stepping
                # Check if we hit the CURRENT active min for this channel
                if val <= self._active_min[channel]:
                    val = self._active_min[channel]
                    setattr(self, f"_count_up_{channel}", True)

                    # We hit the bottom, generate new RANDOM MAX for the trip up
                    if use_random:
                        # New max is between current position and absolute max
                        self._active_max[channel] = random.randint(int(val), abs_max)
                        self.logger.debug("Channel %s: Hit min (%s). New random max border: %s", channel, val, self._active_max[channel])
                    else:
                        self._active_max[channel] = abs_max
                        self.logger.debug("Channel %s: Hit min (%s).", channel, val)

            new_values[channel] = max(0, min(255, val))

        self._current_values = new_values

        # val_str = ", ".join([f"{k}: {v:.1f}" if isinstance(v, float) else f"{k}: {v}" for k, v in new_values.items()])
        # self.logger.debug("Values: %s", val_str)

        # Prepare service data based on color mode
        for target_entity in self._target_light_entity_id:
            if target_entity:
                if self.is_debug_enabled():
                    if self._color_mode in ["rgb", "rgbw"]:
                        # 1. Determine which channels to look up
                        channels = list(self._color_mode)  # results in ['r', 'g', 'b'] or ['r', 'g', 'b', 'w']

                        # 2. Build strings for current values and active ranges
                        vals_str = "/".join([str(int(self._current_values.get(c, 0))) for c in channels])
                        ranges_str = " | ".join([f"{c}:{self._active_min.get(c)}-{self._active_max.get(c)}" for c in channels])

                        self.logger.debug(
                            "Update %s [%s]: Values=%s (Active Ranges: %s)", target_entity, self._color_mode.upper(), vals_str, ranges_str
                        )
                    else:
                        # 3. Fallback for simple Brightness mode
                        brightness = int(self._current_values.get("brightness", 0))
                        b_min = self._active_min.get("brightness")
                        b_max = self._active_max.get("brightness")

                        self.logger.debug("Update %s: Brightness=%s (Range: %s-%s)", target_entity, brightness, b_min, b_max)

                if self._color_mode == "rgbw":
                    rgbw = [self._current_values[c] for c in "rgbw"]
                    service_data = {"entity_id": target_entity, "brightness_pct": 100, "rgbw_color": rgbw}
                elif self._color_mode == "rgb":
                    rgb = [self._current_values[c] for c in "rgb"]
                    service_data = {"entity_id": target_entity, "brightness_pct": 100, "rgb_color": rgb}
                else:
                    brightness = self._current_values["brightness"]
                    service_data = {"entity_id": target_entity, "brightness": brightness}
                await self.hass.services.async_call("light", "turn_on", service_data)
            else:
                self.logger.error("No target light entity ID configured for Moving Colors instance.")

    async def _restore_initial_state(self) -> None:
        """Restore the light to its pre-loop state."""
        if not self._initial_state:
            return

        for target_entity in self._target_light_entity_id:
            # If the light was originally off, turn it back off
            if self._initial_state["state"] == "off":
                await self.hass.services.async_call("light", "turn_off", {"entity_id": target_entity})
                continue

            # Otherwise, restore the values
            data = {"entity_id": target_entity}
            if self._initial_state["rgbw_color"]:
                data["rgbw_color"] = self._initial_state["rgbw_color"]
            elif self._initial_state["rgb_color"]:
                data["rgb_color"] = self._initial_state["rgb_color"]

            if self._initial_state["brightness"]:
                data["brightness"] = self._initial_state["brightness"]

            self.logger.debug("Restoring %s to initial state.", target_entity)
            await self.hass.services.async_call("light", "turn_on", data)

        # Clear the snapshot so we don't restore it twice
        self._initial_state = None

    async def async_refresh(self) -> None:
        """Handle a state change from the switches."""
        # Check if we need to start or stop the periodic task
        if self.is_enabled():
            if not self._update_listener:
                await self.async_start_update_task()
            await self.async_update_state()
        else:
            await self.stop_update_task()

    def is_debug_enabled(self) -> bool:
        """Check if the debug switch for this instance is ON."""
        return self.logger.getEffectiveLevel() == logging.DEBUG

    ### =========================================================
    ### Helpers for sensors
    def get_current_lower_boundary(self) -> int | None:
        """Return the current lower boundary."""
        return -1

    def get_current_upper_boundary(self) -> int | None:
        """Return the current upper boundary."""
        return 256

    ### =========================================================
    ### Getters for all configuration values
    ###
    ### Boolean getters
    def is_enabled(self) -> bool:
        """Return if the instance is enabled."""
        return self._get_composed_config_value(MCConfig.ENABLED_ENTITY, MCInternal.ENABLED_MANUAL, False, bool)

    def is_random_limits_enabled(self) -> bool:
        """Return the current stepping value."""
        return self._get_composed_config_value(MCConfig.RANDOM_LIMITS_ENTITY, MCInternal.RANDOM_LIMITS_MANUAL, True, bool)

    def is_default_mode_enabled(self) -> bool:
        """Return the current stepping value."""
        return self._get_composed_config_value(MCConfig.DEFAULT_MODE_ENABLED_ENTITY, MCInternal.DEFAULT_MODE_ENABLED_MANUAL, False, bool)

    def is_start_from_current_position_enabled(self) -> bool:
        """Return the current stepping value."""
        return self._get_composed_config_value(MCConfig.START_FROM_CURRENT_POSITION_ENTITY, MCInternal.START_FROM_CURRENT_POSITION_MANUAL, True, bool)

    ### Integer getters
    def get_config_start_value(self) -> int:
        """Return the current start value."""
        return self._get_composed_config_value(MCConfig.START_VALUE_ENTITY, MCInternal.START_VALUE_MANUAL, MCInternalDefaults.START_VALUE.value, int)

    def get_config_min_value(self) -> int:
        """Return the current min value."""
        return self._get_composed_config_value(MCConfig.MIN_VALUE_ENTITY, MCInternal.MIN_VALUE_MANUAL, MCInternalDefaults.MIN_VALUE.value, int)

    def get_config_max_value(self) -> int:
        """Return the current max value."""
        return self._get_composed_config_value(MCConfig.MAX_VALUE_ENTITY, MCInternal.MAX_VALUE_MANUAL, MCInternalDefaults.MAX_VALUE.value, int)

    def get_config_stepping(self) -> int:
        """Return the current stepping value."""
        return self._get_composed_config_value(MCConfig.STEPPING_ENTITY, MCInternal.STEPPING_MANUAL, MCInternalDefaults.STEPPING.value, int)

    def get_config_trigger_interval(self) -> int:
        """Return the current trigger interval."""
        return self._get_composed_config_value(
            MCConfig.TRIGGER_INTERVAL_ENTITY, MCInternal.TRIGGER_INTERVAL_MANUAL, MCInternalDefaults.TRIGGER_INTERVAL.value, int
        )

    def get_config_default_value(self) -> int:
        """Return the current stepping value."""
        return self._get_composed_config_value(
            MCConfig.DEFAULT_VALUE_ENTITY, MCInternal.DEFAULT_VALUE_MANUAL, MCInternalDefaults.DEFAULT_VALUE.value, int
        )

    def get_config_steps_to_default(self) -> int:
        """Return the current stepping value."""
        return self._get_composed_config_value(
            MCConfig.STEPS_TO_DEFAULT_ENTITY, MCInternal.STEPS_TO_DEFAULT_MANUAL, MCInternalDefaults.STEPS_TO_DEFAULT.value, int
        )

    ### =========================================================
    ### Helper methods for getters
    def _get_composed_config_value(
        self,
        config_enum: MCConfig,
        internal_enum: MCInternal,
        default_value: Any,
        value_type: type,
    ) -> Any:
        """Get a configuration value using the tiered fallback logic."""
        """
        Tier 1: Configured External Entity (via MCConfig)
        Tier 2: Internal Manual Entity (via MCInternal)
        Tier 3: Hardcoded Default
        """
        # Step 1: Get the state of the internal manual entity
        internal_id = self.get_internal_entity_id(internal_enum)
        internal_state = self._get_internal_entity_state_value(internal_id, default_value, value_type) if internal_id else default_value

        # Step 2: Use internal state as fallback for the external entity lookup
        # We access .value here so the caller doesn't have to
        final_value = self._get_entity_state_value(config_enum.value, internal_state, value_type)

        return value_type(final_value)

    def get_internal_entity_id(self, internal_enum: MCInternal) -> str:
        """Get the internal entity_id for this instance."""
        registry = entity_registry.async_get(self.hass)
        unique_id = f"{self._entry_id}_{internal_enum.value}"
        entity_id = registry.async_get_entity_id(internal_enum.domain, "moving_colors", unique_id)
        # self.logger.debug("Looking up internal entity_id for unique_id: %s -> %s", unique_id, entity_id)
        return entity_id  # noqa: RET504

    def _get_internal_entity_state_value(self, entity_id: str, default: Any, expected_type: type, log_warning: bool = True) -> Any:
        """Extract dynamic value from an entity state."""
        return self._get_state_value(entity_id=entity_id, default=default, expected_type=expected_type, log_warning=log_warning)

    def _get_state_value(self, entity_id: str, default: Any, expected_type: type, log_warning: bool = True) -> Any:
        """Extract dynamic value from an entity state."""
        if entity_id in [None, "none"]:
            # Directly return the default value for None or "none" without logging warnings
            return default

        if not isinstance(entity_id, str):
            if log_warning:
                self.logger.warning("Invalid entity_id: %s. Using default: %s", entity_id, default)
            return default

        state = self.hass.states.get(entity_id)

        if state is None or state.state in ["unavailable", "unknown"]:
            if log_warning:
                self.logger.debug("Entity '%s' is unavailable or unknown. Using default: %s", entity_id, default)
            return default

        try:
            if expected_type is bool:
                return state.state == STATE_ON
            if expected_type is int:
                return int(float(state.state))  # Handle cases where state might be "10.0"
            if expected_type is float:
                return float(state.state)
            return expected_type(state.state)
        except (ValueError, TypeError):
            if log_warning:
                self.logger.warning(
                    "Failed to convert state '%s' of entity '%s' to type %s. Using default: %s",
                    state.state,
                    entity_id,
                    expected_type.__name__,
                    default,
                )
            return default

    def _get_entity_state_value(self, key: str, default: Any, expected_type: type, log_warning: bool = True) -> Any:
        """Extract dynamic value from an entity state."""
        # Type conversion and default will be handled
        entity_id = self._config.get(key)  # This will be the string entity_id or None
        return self._get_state_value(entity_id=entity_id, default=default, expected_type=expected_type, log_warning=log_warning)


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
