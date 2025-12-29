"""Constants for moving_colors tests."""

from custom_components.moving_colors.const import (
    DEBUG_ENABLED,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
)

MOCK_CONFIG_DATA = {
    MC_CONF_NAME: "Test Moving Colors",
    TARGET_LIGHT_ENTITY_ID: "light.test_light",
    DEBUG_ENABLED: False,
}

MOCK_CONFIG_USER_INPUT = {
    MC_CONF_NAME: "Test Moving Colors",
    TARGET_LIGHT_ENTITY_ID: "light.test_light",  # <-- Das fehlte!
    DEBUG_ENABLED: False,
}
