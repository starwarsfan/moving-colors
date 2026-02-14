"""Constants for the Moving Colors integration."""

from enum import Enum

from homeassistant.components.sensor import SensorStateClass

DOMAIN = "moving_colors"
DOMAIN_DATA_MANAGERS = f"{DOMAIN}_managers"  # A good practice for unique keys
DEFAULT_NAME = "Moving Colors"
MC_CONF_COVERS = "lights"  # Constant for 'lights' key within configuration

# Config schema version
VERSION = 1

MC_CONF_NAME = "name"
DEBUG_ENABLED = "debug_enabled"
TARGET_LIGHT_ENTITY_ID = "target_light_entity"


class MCInternal(Enum):
    """Instance specific internal Moving Colors entities."""

    ENABLED_MANUAL = "enabled_manual"
    RANDOM_LIMITS_MANUAL = "random_limits_manual"
    DEFAULT_MODE_ENABLED_MANUAL = "default_mode_enabled_manual"
    START_FROM_CURRENT_POSITION_MANUAL = "start_from_current_position_manual"

    START_VALUE_MANUAL = "start_value_manual"
    MIN_VALUE_MANUAL = "min_value_manual"
    MAX_VALUE_MANUAL = "max_value_manual"
    STEPPING_MANUAL = "stepping_manual"
    TRIGGER_INTERVAL_MANUAL = "trigger_interval_manual"
    DEFAULT_VALUE_MANUAL = "default_value_manual"
    STEPS_TO_DEFAULT_MANUAL = "steps_to_default_manual"

    @property
    def domain(self) -> str:
        """Handle domain for internal entities."""
        if self in (
            MCInternal.ENABLED_MANUAL,
            MCInternal.RANDOM_LIMITS_MANUAL,
            MCInternal.DEFAULT_MODE_ENABLED_MANUAL,
            MCInternal.START_FROM_CURRENT_POSITION_MANUAL,
        ):
            return "switch"
        if self in (
            MCInternal.START_VALUE_MANUAL,
            MCInternal.MIN_VALUE_MANUAL,
            MCInternal.MAX_VALUE_MANUAL,
            MCInternal.STEPPING_MANUAL,
            MCInternal.TRIGGER_INTERVAL_MANUAL,
            MCInternal.DEFAULT_VALUE_MANUAL,
            MCInternal.STEPS_TO_DEFAULT_MANUAL,
        ):
            return "number"
        return "select"  # default/fallback


class MCConfig(Enum):
    """Enum for the Moving Colors configuration options."""

    ENABLED_ENTITY = "enabled_entity"
    START_VALUE_ENTITY = "start_value_entity"
    MIN_VALUE_ENTITY = "min_value_entity"
    MAX_VALUE_ENTITY = "max_value_entity"
    STEPPING_ENTITY = "stepping_entity"
    TRIGGER_INTERVAL_ENTITY = "trigger_interval_entity"
    RANDOM_LIMITS_ENTITY = "random_limits_entity"
    DEFAULT_VALUE_ENTITY = "default_value_entity"
    DEFAULT_MODE_ENABLED_ENTITY = "default_mode_enabled_entity"
    START_FROM_CURRENT_POSITION_ENTITY = "start_from_current_position_entity"
    STEPS_TO_DEFAULT_ENTITY = "steps_to_default_entity"


class MCInternalDefaults(Enum):
    """Enum for the Moving Colors default values."""

    START_VALUE = 125
    MIN_VALUE = 0
    MAX_VALUE = 255
    STEPPING = 3
    TRIGGER_INTERVAL = 2  # in seconds
    DEFAULT_VALUE = 125  # noqa: PIE796
    STEPS_TO_DEFAULT = 5


class SensorEntries(Enum):
    """Enum for the possible sensor entries."""

    # Brightness mode
    CURRENT_VALUE = "current_value"

    # RGB / RGBW mode
    CURRENT_RED = "current_red"
    CURRENT_GREEN = "current_green"
    CURRENT_BLUE = "current_blue"

    # Common (all modes)
    CURRENT_MIN_VALUE = "current_min_value"
    CURRENT_MAX_VALUE = "current_max_value"


INTERNAL_TO_DEFAULTS_MAP = {
    MCInternal.ENABLED_MANUAL: False,
    MCInternal.RANDOM_LIMITS_MANUAL: False,
    MCInternal.DEFAULT_MODE_ENABLED_MANUAL: False,
    MCInternal.START_FROM_CURRENT_POSITION_MANUAL: True,
    MCInternal.START_VALUE_MANUAL: MCInternalDefaults.START_VALUE.value,
    MCInternal.MIN_VALUE_MANUAL: MCInternalDefaults.MIN_VALUE.value,
    MCInternal.MAX_VALUE_MANUAL: MCInternalDefaults.MAX_VALUE.value,
    MCInternal.STEPPING_MANUAL: MCInternalDefaults.STEPPING.value,
    MCInternal.TRIGGER_INTERVAL_MANUAL: MCInternalDefaults.TRIGGER_INTERVAL.value,
    MCInternal.DEFAULT_VALUE_MANUAL: MCInternalDefaults.DEFAULT_VALUE.value,
    MCInternal.STEPS_TO_DEFAULT_MANUAL: MCInternalDefaults.STEPS_TO_DEFAULT.value,
}

NUMBER_INTERNAL_TO_EXTERNAL_MAP = {
    MCInternal.START_VALUE_MANUAL.value: MCConfig.START_VALUE_ENTITY.value,
    MCInternal.MIN_VALUE_MANUAL.value: MCConfig.MIN_VALUE_ENTITY.value,
    MCInternal.MAX_VALUE_MANUAL.value: MCConfig.MAX_VALUE_ENTITY.value,
    MCInternal.STEPPING_MANUAL.value: MCConfig.STEPPING_ENTITY.value,
    MCInternal.TRIGGER_INTERVAL_MANUAL.value: MCConfig.TRIGGER_INTERVAL_ENTITY.value,
    MCInternal.DEFAULT_VALUE_MANUAL.value: MCConfig.DEFAULT_VALUE_ENTITY.value,
    MCInternal.STEPS_TO_DEFAULT_MANUAL.value: MCConfig.STEPS_TO_DEFAULT_ENTITY.value,
}

SWITCH_INTERNAL_TO_EXTERNAL_MAP = {
    MCInternal.ENABLED_MANUAL.value: MCConfig.ENABLED_ENTITY.value,
    MCInternal.RANDOM_LIMITS_MANUAL.value: MCConfig.RANDOM_LIMITS_ENTITY.value,
    MCInternal.DEFAULT_MODE_ENABLED_MANUAL.value: MCConfig.DEFAULT_MODE_ENABLED_ENTITY.value,
    MCInternal.START_FROM_CURRENT_POSITION_MANUAL.value: MCConfig.START_FROM_CURRENT_POSITION_ENTITY.value,
}

EXTERNAL_SENSOR_DEFINITIONS = [
    # Lock control and position values
    {
        "config_key": MCConfig.ENABLED_ENTITY.value,
        "translation_key": MCConfig.ENABLED_ENTITY.value,
        "unit": None,
        "state_class": None,
        "icon": "mdi:toggle-switch",
    },
    {
        "config_key": MCConfig.START_VALUE_ENTITY.value,
        "translation_key": MCConfig.START_VALUE_ENTITY.value,
        "unit": None,
        "state_class": SensorStateClass.MEASUREMENT.value,
        "icon": "mdi:chevron-right-circle-outline",
    },
    {
        "config_key": MCConfig.MIN_VALUE_ENTITY.value,
        "translation_key": MCConfig.MIN_VALUE_ENTITY.value,
        "unit": None,
        "state_class": SensorStateClass.MEASUREMENT.value,
        "icon": "mdi:arrow-collapse-left",
    },
    {
        "config_key": MCConfig.MAX_VALUE_ENTITY.value,
        "translation_key": MCConfig.MAX_VALUE_ENTITY.value,
        "unit": None,
        "state_class": SensorStateClass.MEASUREMENT.value,
        "icon": "mdi:arrow-collapse-right",
    },
    {
        "config_key": MCConfig.STEPPING_ENTITY.value,
        "translation_key": MCConfig.STEPPING_ENTITY.value,
        "unit": None,
        "state_class": SensorStateClass.MEASUREMENT.value,
        "icon": "mdi:chevron-double-right",
    },
    {
        "config_key": MCConfig.TRIGGER_INTERVAL_ENTITY.value,
        "translation_key": MCConfig.TRIGGER_INTERVAL_ENTITY.value,
        "unit": None,
        "state_class": SensorStateClass.MEASUREMENT.value,
        "icon": "mdi:animation-play-outline",
    },
    {
        "config_key": MCConfig.RANDOM_LIMITS_ENTITY.value,
        "translation_key": MCConfig.RANDOM_LIMITS_ENTITY.value,
        "unit": None,
        "state_class": None,
        "icon": "mdi:toggle-switch",
    },
    {
        "config_key": MCConfig.DEFAULT_VALUE_ENTITY.value,
        "translation_key": MCConfig.DEFAULT_VALUE_ENTITY.value,
        "unit": None,
        "state_class": SensorStateClass.MEASUREMENT.value,
        "icon": "mdi:pan-vertical",
    },
    {
        "config_key": MCConfig.DEFAULT_MODE_ENABLED_ENTITY.value,
        "translation_key": MCConfig.DEFAULT_MODE_ENABLED_ENTITY.value,
        "unit": None,
        "state_class": None,
        "icon": "mdi:toggle-switch",
    },
    {
        "config_key": MCConfig.START_FROM_CURRENT_POSITION_ENTITY.value,
        "translation_key": MCConfig.START_FROM_CURRENT_POSITION_ENTITY.value,
        "unit": None,
        "state_class": None,
        "icon": "mdi:toggle-switch",
    },
    {
        "config_key": MCConfig.STEPS_TO_DEFAULT_ENTITY.value,
        "translation_key": MCConfig.STEPS_TO_DEFAULT_ENTITY.value,
        "unit": None,
        "state_class": SensorStateClass.MEASUREMENT.value,
        "icon": "mdi:chevron-double-right",
    },
]
