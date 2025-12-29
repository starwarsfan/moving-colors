"""Test sensors."""
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component  # <-- Das fehlte!


async def test_sensor_setup(hass: HomeAssistant):
    """Test sensor platform setup."""

    # Setup der Integration mit Konfiguration
    config = {
        "sensor": {
            "platform": "moving_colors",  # <-- Dein echter Domain-Name
            "name": "Test Sensor",
        }
    }

    assert await async_setup_component(hass, SENSOR_DOMAIN, config)
    await hass.async_block_till_done()

    # Prüfe, ob der Sensor existiert
    state = hass.states.get("sensor.test_sensor")
    assert state is not None
    assert state.state != STATE_UNKNOWN


async def test_sensor_update(hass: HomeAssistant):
    """Test sensor updates."""

    config = {
        "sensor": {
            "platform": "moving_colors",  # <-- Dein echter Domain-Name
            "name": "Test Sensor",
        }
    }

    await async_setup_component(hass, SENSOR_DOMAIN, config)
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sensor")

    # Simuliere ein Update
    await hass.services.async_call(
        "homeassistant",
        "update_entity",
        {"entity_id": "sensor.test_sensor"},
        blocking=True,
    )

    new_state = hass.states.get("sensor.test_sensor")
    assert new_state is not None