"""Integration for Moving Colors."""

import logging
import re
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import (
    DEBUG_ENABLED,
    DOMAIN,
    DOMAIN_DATA_MANAGERS,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
    VERSION,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_GLOBAL_DOMAIN_LOGGER = logging.getLogger(DOMAIN)
_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SWITCH]

# Get the schema version from constants
CURRENT_SCHEMA_VERSION = VERSION


# Setup entry point, which is called at every start of Home Assistant.
# Not specific for config entries.
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Moving Colors integration."""
    _LOGGER.debug("[%s] async_setup called.", DOMAIN)

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


# Entry point to unload a ConfigEntry
async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("[%s] Unloading Moving Colors integration for entry: %s", DOMAIN, entry.entry_id)

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


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old config entry."""
    _LOGGER.debug(
        "[%s] Migrating config entry '%s' from version %s to %s", DOMAIN, config_entry.entry_id, config_entry.version, CURRENT_SCHEMA_VERSION
    )

    new_data = config_entry.data.copy()
    # new_options = config_entry.options.copy()

    if config_entry.version == 1:
        # Migrate configuration version 1

        try:
            validated_options = None  # FULL_OPTIONS_SCHEMA(new_options)
            _LOGGER.debug("[%s] Migrated options successfully validated. Result: %s", DOMAIN, validated_options)
            _LOGGER.debug("[%s] Type of validated_options: %s", DOMAIN, type(validated_options))
        except vol.Invalid:
            _LOGGER.exception(
                "[%s] Validation failed after migration to version %s for entry %s", DOMAIN, CURRENT_SCHEMA_VERSION, config_entry.entry_id
            )
            return False

        _LOGGER.debug("[%s] Preparing to call hass.config_entries.async_update_entry with:", DOMAIN)
        _LOGGER.debug("[%s]   Arg 'config_entry' type: %s", DOMAIN, type(config_entry))
        _LOGGER.debug("[%s]   Arg 'data' type: %s, value: %s", DOMAIN, type(new_data), new_data)
        _LOGGER.debug("[%s]   Arg 'options' type: %s, value: %s", DOMAIN, type(validated_options), validated_options)
        _LOGGER.debug("[%s]   Arg 'version' type: %s, value: %s", DOMAIN, type(CURRENT_SCHEMA_VERSION), CURRENT_SCHEMA_VERSION)

        hass.config_entries.async_update_entry(config_entry, data=new_data, options=validated_options, version=CURRENT_SCHEMA_VERSION)
        _LOGGER.info("[%s] Config entry '%s' successfully migrated to version %s.", DOMAIN, config_entry.entry_id, CURRENT_SCHEMA_VERSION)
        return True

    _LOGGER.error("[%s] Unknown config entry version %s for migration. This should not happen.", DOMAIN, config_entry.version)
    return False


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update. Will be called if the user modifies the configuration using the OptionsFlow."""
    _LOGGER.debug("[%s] Options update listener triggered for entry %s.", DOMAIN, entry.entry_id)
    await hass.config_entries.async_reload(entry.entry_id)


class MovingColorsManager:
    """Manages the Moving Colors logic."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any], entry_id: str, instance_logger: logging.Logger) -> None:
        """Initialize all defaults."""
        self.hass = hass
        self._config = config
        self._entry_id = entry_id
        self.logger = instance_logger

        self.name = config[MC_CONF_NAME]
        self._target_light_entity_id = config[TARGET_LIGHT_ENTITY_ID]

        # Check if critical values are missing, even if this might be done within async_setup_entry
        if not self.name:
            self.logger.warning("Manager init: Manager name is missing in config for entry %s. Using fallback.", entry_id)
            self.name = f"Unnamed Moving Colors ({entry_id})"
        if not self._target_light_entity_id:
            self.logger.error("Manager init: Target light entity ID is missing in config for entry %s. This is critical.", entry_id)
            message = f"Target light entity ID missing for entry {entry_id}"
            raise ValueError(message)

        self._options = config

        self._unsub_callbacks: list[Callable[[], None]] = []


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
