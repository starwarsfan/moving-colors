"""Integration tests for Moving Colors switch platform."""

import homeassistant.helpers.entity_registry as er
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    EVENT_HOMEASSISTANT_STARTED,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant

from custom_components.moving_colors.const import (
    DEBUG_ENABLED,
    DOMAIN,
)

from .conftest import assert_entity_exists, assert_state

SWITCH_DEBUG = "switch.test_moving_colors_debug_mode"
SWITCH_ENABLED = "switch.test_moving_colors_enable_moving_colors"
SWITCH_RANDOM_LIMITS = "switch.test_moving_colors_random_limits"
SWITCH_DEFAULT_MODE = "switch.test_moving_colors_activate_default_mode"
SWITCH_START_FROM_CURRENT = "switch.test_moving_colors_star_from_current_color"

ALL_SWITCHES = [
    SWITCH_DEBUG,
    SWITCH_ENABLED,
    SWITCH_RANDOM_LIMITS,
    SWITCH_DEFAULT_MODE,
    SWITCH_START_FROM_CURRENT,
]


# ============================================================================
# Basic setup
# ============================================================================


async def test_all_switches_created(hass: HomeAssistant, setup_integration) -> None:
    """Test that all expected switches are created."""
    for entity_id in ALL_SWITCHES:
        assert_entity_exists(hass, entity_id)


async def test_switch_initial_states_are_valid(hass: HomeAssistant, setup_integration) -> None:
    """Test that all switches have valid initial states (on or off)."""
    for entity_id in ALL_SWITCHES:
        state = hass.states.get(entity_id)
        assert state is not None, f"Switch {entity_id} does not exist"
        assert state.state in (STATE_ON, STATE_OFF), f"Switch {entity_id} has invalid state: {state.state}"


async def test_switch_device_info(hass: HomeAssistant, setup_integration) -> None:
    """Test that switches are associated with the correct device."""
    registry = er.async_get(hass)
    entity = registry.async_get(SWITCH_ENABLED)
    assert entity is not None
    assert entity.platform == DOMAIN


# ============================================================================
# MovingColorsSwitch: turn_on / turn_off
# ============================================================================


async def test_switch_turn_on(hass: HomeAssistant, setup_integration) -> None:
    """Test turning a MovingColorsSwitch on."""
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_ENABLED},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert_state(hass, SWITCH_ENABLED, STATE_ON)


async def test_switch_turn_off(hass: HomeAssistant, setup_integration) -> None:
    """Test turning a MovingColorsSwitch off."""
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_ENABLED},
        blocking=True,
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: SWITCH_ENABLED},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert_state(hass, SWITCH_ENABLED, STATE_OFF)


async def test_switch_random_limits_turn_on(hass: HomeAssistant, setup_integration) -> None:
    """Test turning random limits switch on."""
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_RANDOM_LIMITS},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert_state(hass, SWITCH_RANDOM_LIMITS, STATE_ON)


async def test_switch_default_mode_toggle(hass: HomeAssistant, setup_integration) -> None:
    """Test toggling default mode switch."""
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_DEFAULT_MODE},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert_state(hass, SWITCH_DEFAULT_MODE, STATE_ON)

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: SWITCH_DEFAULT_MODE},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert_state(hass, SWITCH_DEFAULT_MODE, STATE_OFF)


# ============================================================================
# MovingColorsConfigSwitch (Debug): turn_on / turn_off updates config entry
# ============================================================================


async def test_config_switch_debug_turn_on(
    hass: HomeAssistant,
    setup_integration,
    mock_config_entry,
) -> None:
    """Test that turning debug switch on updates the config entry options."""
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_DEBUG},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert_state(hass, SWITCH_DEBUG, STATE_ON)
    assert mock_config_entry.options.get(DEBUG_ENABLED) is True


async def test_config_switch_debug_turn_off(
    hass: HomeAssistant,
    setup_integration,
    mock_config_entry,
) -> None:
    """Test that turning debug switch off updates the config entry options."""
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_DEBUG},
        blocking=True,
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: SWITCH_DEBUG},
        blocking=True,
    )
    await hass.async_block_till_done()

    assert_state(hass, SWITCH_DEBUG, STATE_OFF)
    assert mock_config_entry.options.get(DEBUG_ENABLED) is False


# ============================================================================
# State restore after restart
# ============================================================================


async def test_switch_state_restored_after_reload(
    hass: HomeAssistant,
    mock_config_entry,
    mock_light,
) -> None:
    """Test that switch state is restored after integration reload."""
    mock_config_entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: SWITCH_ENABLED},
        blocking=True,
    )
    await hass.async_block_till_done()
    assert_state(hass, SWITCH_ENABLED, STATE_ON)

    assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    state = hass.states.get(SWITCH_ENABLED)
    assert state is not None
    assert state.state in (STATE_ON, STATE_OFF)
