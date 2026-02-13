"""Integration tests for Moving Colors sensor platform."""

import homeassistant.helpers.entity_registry as er
import pytest
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant, State
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.moving_colors.const import (
    DEBUG_ENABLED,
    DOMAIN,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
    MCConfig,
)

from .conftest import assert_entity_exists

INSTANCE_NAME = "Test Moving Colors"
SENSOR_CURRENT_VALUE = "sensor.test_moving_colors_current_color_value"
SENSOR_MIN_VALUE = "sensor.test_moving_colors_current_minimum_value"
SENSOR_MAX_VALUE = "sensor.test_moving_colors_current_maximum_value"


# ============================================================================
# Basic sensor setup
# ============================================================================


async def test_sensor_setup(hass: HomeAssistant, setup_integration) -> None:
    """Test that all three core sensors are created."""
    assert_entity_exists(hass, SENSOR_CURRENT_VALUE)
    assert_entity_exists(hass, SENSOR_MIN_VALUE)
    assert_entity_exists(hass, SENSOR_MAX_VALUE)


async def test_sensor_initial_states_are_numeric(hass: HomeAssistant, setup_integration) -> None:
    """Test that core sensors have numeric initial states."""
    for entity_id in (SENSOR_CURRENT_VALUE, SENSOR_MIN_VALUE, SENSOR_MAX_VALUE):
        state = hass.states.get(entity_id)
        assert state is not None, f"Entity {entity_id} does not exist"
        if state.state not in ("unknown", "unavailable"):
            float(state.state)  # Raises ValueError if not numeric


async def test_sensor_device_info(hass: HomeAssistant, setup_integration) -> None:
    """Test that sensors are associated with the correct device."""
    registry = er.async_get(hass)
    entity = registry.async_get(SENSOR_CURRENT_VALUE)
    assert entity is not None
    assert entity.platform == DOMAIN


# ============================================================================
# External entity sensor - numeric tracking
# ============================================================================


@pytest.fixture
async def config_entry_with_external_sensor(hass: HomeAssistant, mock_light: str) -> MockConfigEntry:
    """Config entry with an external numeric sensor configured."""
    hass.states.async_set(
        "input_number.mc_start_value",
        "100",
        {"unit_of_measurement": "%", "min": 0, "max": 255},
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            MC_CONF_NAME: INSTANCE_NAME,
            TARGET_LIGHT_ENTITY_ID: mock_light,
            DEBUG_ENABLED: False,
        },
        options={
            TARGET_LIGHT_ENTITY_ID: [mock_light],
            MCConfig.START_VALUE_ENTITY.value: "input_number.mc_start_value",
            DEBUG_ENABLED: False,
        },
        entry_id="test_entry_external",
        unique_id="test_unique_external",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    return entry


async def test_external_sensor_created(
    hass: HomeAssistant,
    config_entry_with_external_sensor: MockConfigEntry,
) -> None:
    """Test that external entity value sensor is created when configured."""
    registry = er.async_get(hass)
    entry_id = config_entry_with_external_sensor.entry_id
    unique_id = f"{entry_id}_{MCConfig.START_VALUE_ENTITY.value}_source_value"
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None, f"External sensor with unique_id {unique_id} not found in registry"


async def test_external_sensor_tracks_state_changes(
    hass: HomeAssistant,
    config_entry_with_external_sensor: MockConfigEntry,
) -> None:
    """Test that external entity value sensor updates when source entity changes."""
    registry = er.async_get(hass)
    entry_id = config_entry_with_external_sensor.entry_id
    unique_id = f"{entry_id}_{MCConfig.START_VALUE_ENTITY.value}_source_value"
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None

    hass.states.async_set(
        "input_number.mc_start_value",
        "200",
        {"unit_of_measurement": "%"},
    )
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    assert float(state.state) == 200.0


async def test_external_sensor_handles_unavailable(
    hass: HomeAssistant,
    config_entry_with_external_sensor: MockConfigEntry,
) -> None:
    """Test that external sensor handles unavailable source state gracefully.

    When the source entity state becomes 'unavailable', _update_from_state
    sets _current_value to None, native_value returns None, and HA reports
    the sensor as 'unavailable'.

    We fire the state_changed event directly to bypass HA's numeric validation
    on the source input_number entity itself.
    """
    registry = er.async_get(hass)
    entry_id = config_entry_with_external_sensor.entry_id
    unique_id = f"{entry_id}_{MCConfig.START_VALUE_ENTITY.value}_source_value"
    entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
    assert entity_id is not None

    # Fire state_changed directly with an unavailable State object.
    # This bypasses HA's numeric validation on the source entity and reaches
    # _handle_state_change → _update_from_state in the external sensor.
    unavailable_state = State("input_number.mc_start_value", "unavailable")
    hass.bus.async_fire(
        "state_changed",
        {
            "entity_id": "input_number.mc_start_value",
            "old_state": hass.states.get("input_number.mc_start_value"),
            "new_state": unavailable_state,
        },
    )
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state is not None
    # native_value returns None when _current_value is None,
    # which HA represents as "unknown" (not "unavailable")
    assert state.state == "unknown"


# ============================================================================
# Sensor without external entity configured (cleanup path)
# ============================================================================


async def test_no_external_sensors_without_config(
    hass: HomeAssistant,
    setup_integration,
    mock_config_entry,
) -> None:
    """Test that no external sensors are created when none are configured."""
    registry = er.async_get(hass)

    for config_key in [e.value for e in MCConfig if e.name.endswith("_ENTITY")]:
        unique_id = f"{mock_config_entry.entry_id}_{config_key}_source_value"
        entity_id = registry.async_get_entity_id("sensor", DOMAIN, unique_id)
        assert entity_id is None, f"Unexpected external sensor found: {entity_id}"
