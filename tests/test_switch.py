"""Test moving_colors switch."""

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED, STATE_OFF, STATE_ON
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
    assert state.state in (STATE_ON, STATE_OFF), f"Switch has invalid state: {state.state}"


async def test_switch_states(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test that all switches are created with valid states."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check all expected switches exist
    expected_switches = [
        "switch.test_moving_colors_debug_mode",
        "switch.test_moving_colors_enable_moving_colors",
        "switch.test_moving_colors_random_limits",
        "switch.test_moving_colors_activate_default_mode",
        "switch.test_moving_colors_star_from_current_color",
    ]

    for entity_id in expected_switches:
        state = hass.states.get(entity_id)
        assert state is not None, f"Switch {entity_id} was not created"
        assert state.state in (STATE_ON, STATE_OFF), f"Switch {entity_id} has invalid state"
