"""Constants for the Moving Colors integration."""

from enum import Enum

import voluptuous as vol
from homeassistant.helpers import selector

DOMAIN = "moving_colors"
DOMAIN_DATA_MANAGERS = f"{DOMAIN}_managers"  # A good practice for unique keys
DEFAULT_NAME = "Moving Colors"
MC_CONF_COVERS = "lights"  # Constant for 'lights' key within configuration

# Config schema version
VERSION = 1

MC_CONF_NAME = "name"
DEBUG_ENABLED = "debug_enabled"
TARGET_LIGHT_ENTITY_ID = "target_light_entity"

# =================================================================================================
# Voluptuous schemas for minimal configuration
# They are used the initial configuration of a new instance, as the instance name is the one and
# only configuration value, which is immutable. So it must be stored within `data`. All
# other options will be stored as `options`.

# Wrapper for minimal configuration, which will be stored within `data`
CFG_MINIMAL_REQUIRED = vol.Schema(
    {
        vol.Optional(MC_CONF_NAME, default=""): selector.TextSelector(selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)),
    }
)

# Wrapper for minimal options, which will be used and validated within ConfigFlow and OptionFlow
CFG_MINIMAL_OPTIONS = vol.Schema(
    {
        vol.Optional(TARGET_LIGHT_ENTITY_ID): selector.EntitySelector(selector.EntitySelectorConfig(domain="light", multiple=True)),
    }
)

# Wrapper for minimal configuration, which is used to show initial ConfigFlow
CFG_MINIMAL = vol.Schema(CFG_MINIMAL_REQUIRED.schema | CFG_MINIMAL_OPTIONS.schema)
# End of minimal configuration schema
# =================================================================================================


class MovingColorsConfig(Enum):
    """Enum for the Moving Colors configuration options."""

    ENABLED_STATIC = "enabled_static"
    ENABLED_ENTITY = "enabled_entity"
    START_FROM_CURRENT_POSITION = "start_from_current_position"
    START_VALUE_STATIC = "start_value_static"
    START_VALUE_ENTITY = "start_value_entity"
    MIN_VALUE_STATIC = "min_value_static"
    MIN_VALUE_ENTITY = "min_value_entity"
    MAX_VALUE_STATIC = "max_value_static"
    MAX_VALUE_ENTITY = "max_value_entity"
    STEPPING_STATIC = "stepping_static"
    STEPPING_ENTITY = "stepping_entity"
    TRIGGER_INTERVAL_STATIC = "trigger_interval_static"
    TRIGGER_INTERVAL_ENTITY = "trigger_interval_entity"
    RANDOM_LIMITS_STATIC = "random_limits_static"
    RANDOM_LIMITS_ENTITY = "random_limits_entity"
    DEFAULT_VALUE_STATIC = "default_value_static"
    DEFAULT_VALUE_ENTITY = "default_value_entity"
    DEFAULT_MODE_ENABLED_STATIC = "default_mode_enabled_static"
    DEFAULT_MODE_ENABLED_ENTITY = "default_mode_enabled_entity"
    STEPS_TO_DEFAULT_STATIC = "steps_to_default_static"
    STEPS_TO_DEFAULT_ENTITY = "steps_to_default_entity"


class MovingColorsIntDefaults(Enum):
    """Enum for the Moving Colors default values."""

    START = 125
    MIN = 0
    MAX = 255
    STEPPING = 3
    TRIGGER_INTERVAL = 2  # in seconds
    DEFAULT_END = 125  # noqa: PIE796
    STEPS_TO_DEFAULT_END = 5


CFG_OPTIONS = vol.Schema(
    {
        # Target light entity or entities
        vol.Optional(TARGET_LIGHT_ENTITY_ID): selector.EntitySelector(selector.EntitySelectorConfig(domain="light", multiple=True)),
        # Enable Moving Colors
        vol.Optional(MovingColorsConfig.ENABLED_STATIC.value, default=False): selector.BooleanSelector(),
        vol.Optional(MovingColorsConfig.ENABLED_ENTITY.value): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["input_boolean", "binary_sensor"])
        ),
        # Start from current position
        vol.Optional(MovingColorsConfig.START_FROM_CURRENT_POSITION.value, default=True): selector.BooleanSelector(),
        # Start value
        vol.Optional(MovingColorsConfig.START_VALUE_ENTITY.value): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "input_number"])
        ),
        vol.Optional(MovingColorsConfig.START_VALUE_STATIC.value, default=125): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=255, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        # Minimal value
        vol.Optional(MovingColorsConfig.MIN_VALUE_ENTITY.value): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "input_number"])
        ),
        vol.Optional(MovingColorsConfig.MIN_VALUE_STATIC.value, default=0): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=255, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        # Maximal value
        vol.Optional(MovingColorsConfig.MAX_VALUE_ENTITY.value): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "input_number"])
        ),
        vol.Optional(MovingColorsConfig.MAX_VALUE_STATIC.value, default=255): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=255, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        # Stepping
        vol.Optional(MovingColorsConfig.STEPPING_ENTITY.value): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "input_number"])
        ),
        vol.Optional(MovingColorsConfig.STEPPING_STATIC.value, default=3): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        # Trigger interval
        vol.Optional(MovingColorsConfig.TRIGGER_INTERVAL_ENTITY.value): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "input_number"])
        ),
        vol.Optional(MovingColorsConfig.TRIGGER_INTERVAL_STATIC.value, default=2): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=3600, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        # Random limits on/off
        vol.Optional(MovingColorsConfig.RANDOM_LIMITS_STATIC.value, default=True): selector.BooleanSelector(),
        vol.Optional(MovingColorsConfig.RANDOM_LIMITS_ENTITY.value): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["input_boolean", "binary_sensor"])
        ),
        # Default value
        vol.Optional(MovingColorsConfig.DEFAULT_VALUE_ENTITY.value): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "input_number"])
        ),
        vol.Optional(MovingColorsConfig.DEFAULT_VALUE_STATIC.value, default=125): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=256, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        # Enable default mode
        vol.Optional(MovingColorsConfig.DEFAULT_MODE_ENABLED_ENTITY.value): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["input_boolean", "binary_sensor"])
        ),
        vol.Optional(MovingColorsConfig.DEFAULT_MODE_ENABLED_STATIC.value, default=True): selector.BooleanSelector(),
        # Steps to default value
        vol.Optional(MovingColorsConfig.STEPS_TO_DEFAULT_ENTITY.value): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["sensor", "input_number"])
        ),
        vol.Optional(MovingColorsConfig.STEPS_TO_DEFAULT_STATIC.value, default=5): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        # Enable debug mode
        vol.Optional(DEBUG_ENABLED, default=False): selector.BooleanSelector(),
    }
)


class SensorEntries(Enum):
    """Enum for the possible sensor entries."""

    CURRENT_VALUE = "current_value"
    CURRENT_MIN_VALUE = "current_min_value"
    CURRENT_MAX_VALUE = "current_max_value"
