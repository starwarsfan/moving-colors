"""Test moving_colors sensor."""

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant

from custom_components.moving_colors.const import SensorEntries


async def test_sensor_setup(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test sensor platform setup."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that sensors exist (they might be created with a slight delay)
    # Use slugified name: "Test Moving Colors" -> "test_moving_colors"
    sensor_prefix = "sensor.test_moving_colors"

    # At least one sensor should exist
    states = [
        hass.states.get(f"{sensor_prefix}_{SensorEntries.CURRENT_VALUE.value}"),
        hass.states.get(f"{sensor_prefix}_{SensorEntries.CURRENT_MIN_VALUE.value}"),
        hass.states.get(f"{sensor_prefix}_{SensorEntries.CURRENT_MAX_VALUE.value}"),
    ]

    # Check at least one sensor was created
    assert any(state is not None for state in states), "No sensors were created"
