"""Test moving_colors switch."""

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


async def test_switch_setup(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test switch platform setup."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check enable switch exists
    entity_id = "switch.test_moving_colors_enable_moving_colors"
    state = hass.states.get(entity_id)

    assert state is not None, f"Switch {entity_id} was not created"


async def test_switch_turn_on_off(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test turning switch on and off."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "switch.test_moving_colors_enable_moving_colors"

    # Just verify the switch can be controlled, regardless of initial state
    initial_state = hass.states.get(entity_id)
    assert initial_state is not None
    initial_value = initial_state.state

    # Try toggling
    target_service = SERVICE_TURN_OFF if initial_value == STATE_ON else SERVICE_TURN_ON
    target_state = STATE_OFF if initial_value == STATE_ON else STATE_ON

    await hass.services.async_call(
        SWITCH_DOMAIN,
        target_service,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    new_state = hass.states.get(entity_id)
    assert new_state is not None
    assert new_state.state == target_state

    # Toggle back
    target_service = SERVICE_TURN_ON if target_state == STATE_OFF else SERVICE_TURN_OFF
    await hass.services.async_call(
        SWITCH_DOMAIN,
        target_service,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    final_state = hass.states.get(entity_id)
    assert final_state is not None
    assert final_state.state == initial_value
