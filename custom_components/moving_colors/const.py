"""Constants for the Moving Colors integration."""

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

MC_ENABLED_STATIC = "mc_enabled_static"
MC_ENABLED_ENTITY = "mc_enabled_entity"
MC_START_VALUE_STATIC = "mc_start_value_static"
MC_START_VALUE_ENTITY = "mc_start_value_entity"
MC_MIN_VALUE_STATIC = "mc_min_value_static"
MC_MIN_VALUE_ENTITY = "mc_min_value_entity"
MC_MAX_VALUE_STATIC = "mc_max_value_static"
MC_MAX_VALUE_ENTITY = "mc_max_value_entity"
MC_STEP_VALUE_STATIC = "mc_step_value_static"
MC_STEP_VALUE_ENTITY = "mc_step_value_entity"
MC_RANDOM_LIMITS_STATIC = "mc_random_limits_static"
MC_RANDOM_LIMITS_ENTITY = "mc_random_limits_entity"
MC_DEFAULT_VALUE_STATIC = "mc_default_value_static"
MC_DEFAULT_VALUE_ENTITY = "mc_default_value_entity"
MC_DEFAULT_MODE_ENABLED_STATIC = "mc_default_mode_enabled_static"
MC_DEFAULT_MODE_ENABLED_ENTITY = "mc_default_mode_enabled_entity"
MC_STEPS_TO_DEFAULT_STATIC = "mc_steps_to_default_static"
MC_STEPS_TO_DEFAULT_ENTITY = "mc_steps_to_default_entity"


CFG_OPTIONS = vol.Schema(
    {
        vol.Optional(TARGET_LIGHT_ENTITY_ID): selector.EntitySelector(selector.EntitySelectorConfig(domain="light", multiple=True)),
        vol.Optional(MC_ENABLED_STATIC, default=True): selector.BooleanSelector(),
        vol.Optional(MC_ENABLED_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["input_boolean", "binary_sensor"])),
        # Start value
        vol.Optional(MC_START_VALUE_STATIC, default=125): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=256, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(MC_START_VALUE_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Minimal value
        vol.Optional(MC_MIN_VALUE_STATIC, default=0): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=255, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(MC_MIN_VALUE_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Maximal value
        vol.Optional(MC_MAX_VALUE_STATIC, default=255): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=255, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(MC_MAX_VALUE_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Stepping
        vol.Optional(MC_STEP_VALUE_STATIC, default=3): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(MC_STEP_VALUE_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Random limits on/off
        vol.Optional(MC_RANDOM_LIMITS_STATIC, default=True): selector.BooleanSelector(),
        vol.Optional(MC_RANDOM_LIMITS_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["input_boolean", "binary_sensor"])),
        # Default value
        vol.Optional(MC_DEFAULT_VALUE_STATIC, default=125): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=256, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(MC_DEFAULT_VALUE_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Enable default mode
        vol.Optional(MC_DEFAULT_MODE_ENABLED_STATIC, default=True): selector.BooleanSelector(),
        vol.Optional(MC_DEFAULT_MODE_ENABLED_ENTITY): selector.EntitySelector(
            selector.EntitySelectorConfig(domain=["input_boolean", "binary_sensor"])
        ),
        # Steps to default value
        vol.Optional(MC_STEPS_TO_DEFAULT_STATIC, default=5): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(MC_STEPS_TO_DEFAULT_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Enable debug mode
        vol.Optional(DEBUG_ENABLED, default=False): selector.BooleanSelector(),
    }
)
