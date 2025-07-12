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

# [e#3            =Startwert              #init=0   ]
START_VALUE_STATIC = "start_value_static"
START_VALUE_ENTITY = "start_value_entity"
# [e#4            =Min                    #init=0   ]
MIN_VALUE_STATIC = "min_value_static"
MIN_VALUE_ENTITY = "min_value_entity"
# [e#5            =Max                    #init=255 ]
MAX_VALUE_STATIC = "max_value_static"
MAX_VALUE_ENTITY = "max_value_entity"
# [e#6            =Stepping               #init=2   ]
STEP_VALUE_STATIC = "step_value_static"
STEP_VALUE_ENTITY = "step_value_entity"
# [e#7            =Zufallsgrenzen         #init=1   ]
RANDOM_LIMITS_STATIC = "random_limits_static"
RANDOM_LIMITS_ENTITY = "random_limits_entity"
# [e#8 OPTION     =Default-Wert                     ]
DEFAULT_VALUE_STATIC = "default_value_static"
DEFAULT_VALUE_ENTITY = "default_value_entity"
# [e#9 OPTION     =Default-Mode aktiv     #init=0   ]
DEFAULT_MODE_ENABLED_STATIC = "default_mode_enabled_static"
DEFAULT_MODE_ENABLED_ENTITY = "default_mode_enabled_entity"
# [e#10           =Schritte bis default   #init=3   ]
STEPS_TO_DEFAULT_STATIC = "steps_to_default_static"
STEPS_TO_DEFAULT_ENTITY = "steps_to_default_entity"


CFG_OPTIONS = vol.Schema(
    {
        # Start value
        vol.Optional(START_VALUE_STATIC, default=True): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=256, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(START_VALUE_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Minimal value
        vol.Optional(MIN_VALUE_STATIC, default=True): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=255, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(MIN_VALUE_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Maximal value
        vol.Optional(MAX_VALUE_STATIC, default=True): selector.NumberSelector(
            selector.NumberSelectorConfig(min=1, max=256, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(MAX_VALUE_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Stepping
        vol.Optional(STEP_VALUE_STATIC, default=True): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(STEP_VALUE_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Random limits on/off
        vol.Optional(RANDOM_LIMITS_STATIC, default=True): selector.BooleanSelector(),
        vol.Optional(RANDOM_LIMITS_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["input_boolean", "binary_sensor"])),
        # Default value
        vol.Optional(DEFAULT_VALUE_STATIC, default=True): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=256, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(DEFAULT_VALUE_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Enable default mode
        vol.Optional(DEFAULT_MODE_ENABLED_STATIC, default=True): selector.BooleanSelector(),
        vol.Optional(DEFAULT_MODE_ENABLED_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["input_boolean", "binary_sensor"])),
        # Steps to default value
        vol.Optional(STEPS_TO_DEFAULT_STATIC, default=True): selector.NumberSelector(
            selector.NumberSelectorConfig(min=0, max=100, step=1, mode=selector.NumberSelectorMode.BOX)
        ),
        vol.Optional(STEPS_TO_DEFAULT_ENTITY): selector.EntitySelector(selector.EntitySelectorConfig(domain=["sensor", "input_number"])),
        # Enable debug mode
        vol.Optional(DEBUG_ENABLED, default=False): selector.BooleanSelector(),
    }
)
