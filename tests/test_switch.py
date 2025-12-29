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

from custom_components.moving_colors.const import MCInternal


async def test_switch_setup(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test switch platform setup."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check enabled switch exists
    entity_id = f"switch.test_moving_colors_{MCInternal.ENABLED_MANUAL.value}"
    state = hass.states.get(entity_id)

    assert state is not None, f"Switch {entity_id} was not created"


async def test_switch_turn_on_off(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test turning switch on and off."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = f"switch.test_moving_colors_{MCInternal.ENABLED_MANUAL.value}"

    # Get initial state
    state = hass.states.get(entity_id)
    assert state is not None

    # Turn on
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_ON

    # Turn off
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
