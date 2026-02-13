"""Test moving_colors sensor."""

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant


async def test_sensor_setup(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test sensor platform setup."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that sensors exist
    sensor_ids = [
        "sensor.test_moving_colors_current_color_value",
        "sensor.test_moving_colors_current_minimum_value",
        "sensor.test_moving_colors_current_maximum_value",
    ]

    states = [hass.states.get(sensor_id) for sensor_id in sensor_ids]

    # Check all sensors were created
    assert all(state is not None for state in states), f"Not all sensors were created. Found: {[s.entity_id if s else None for s in states]}"
