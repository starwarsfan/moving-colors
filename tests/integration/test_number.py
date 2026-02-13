"""Test moving_colors number."""

from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.components.number import SERVICE_SET_VALUE
from homeassistant.const import ATTR_ENTITY_ID, EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant


async def test_number_setup(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test number platform setup."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that number entities exist
    entity_id = "number.test_moving_colors_start_value"
    state = hass.states.get(entity_id)

    assert state is not None, f"Number entity {entity_id} was not created"


async def test_number_default_values(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test number entities have correct default values."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check start value (default: 125)
    state = hass.states.get("number.test_moving_colors_start_value")
    assert state is not None
    assert float(state.state) == 125.0

    # Check min value (default: 0)
    state = hass.states.get("number.test_moving_colors_minimum_value")
    assert state is not None
    assert float(state.state) == 0.0

    # Check max value (default: 255)
    state = hass.states.get("number.test_moving_colors_maximum_value")
    assert state is not None
    assert float(state.state) == 255.0


async def test_number_set_value(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test setting number value."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    entity_id = "number.test_moving_colors_start_value"

    # Set value
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: entity_id,
            "value": 200,
        },
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 200.0
