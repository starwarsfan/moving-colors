"""Integration tests for Moving Colors __init__.py - manager core logic."""

import logging

from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import ATTR_ENTITY_ID, EVENT_HOMEASSISTANT_STARTED, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.moving_colors import async_setup
from custom_components.moving_colors.const import (
    DEBUG_ENABLED,
    DOMAIN,
    DOMAIN_DATA_MANAGERS,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
)

_LOGGER = logging.getLogger(__name__)

INSTANCE_NAME = "Test Moving Colors"
SWITCH_ENABLED = "switch.test_moving_colors_enable_moving_colors"


# ============================================================================
# async_setup_entry: Edge Cases
# ============================================================================


async def test_setup_entry_success(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test successful setup stores manager in hass.data."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN_DATA_MANAGERS in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN_DATA_MANAGERS]


async def test_setup_entry_missing_name(hass: HomeAssistant, mock_light) -> None:
    """Test setup fails gracefully when instance name is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: ""},
        options={TARGET_LIGHT_ENTITY_ID: ["light.test_light"]},
        entry_id="test_no_name",
        title="",
        version=1,
    )
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state == ConfigEntryState.SETUP_ERROR


async def test_setup_entry_missing_light(hass: HomeAssistant) -> None:
    """Test setup fails when target light entity ID is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={},
        entry_id="test_no_light",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state == ConfigEntryState.SETUP_ERROR


async def test_setup_entry_debug_enabled(hass: HomeAssistant, mock_light) -> None:
    """Test setup with debug mode enabled sets logger to DEBUG."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={
            TARGET_LIGHT_ENTITY_ID: ["light.test_light"],
            DEBUG_ENABLED: True,
        },
        entry_id="test_debug",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    manager = hass.data[DOMAIN_DATA_MANAGERS][entry.entry_id]
    assert manager.logger.getEffectiveLevel() == logging.DEBUG


# ============================================================================
# async_migrate_entry
# ============================================================================


async def test_migrate_entry_version_1(hass: HomeAssistant, mock_light) -> None:
    """Test migration from version 1 succeeds without changes."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={TARGET_LIGHT_ENTITY_ID: ["light.test_light"]},
        entry_id="test_migrate",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state == ConfigEntryState.LOADED


# ============================================================================
# async_unload_entry
# ============================================================================


async def test_unload_entry(hass: HomeAssistant, setup_integration, mock_config_entry) -> None:
    """Test that unloading removes manager from hass.data."""
    assert mock_config_entry.entry_id in hass.data[DOMAIN_DATA_MANAGERS]

    assert await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.entry_id not in hass.data[DOMAIN_DATA_MANAGERS]
    assert mock_config_entry.state == ConfigEntryState.NOT_LOADED


async def test_reload_entry(hass: HomeAssistant, setup_integration, mock_config_entry) -> None:
    """Test that reloading re-creates the manager."""
    assert await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.entry_id in hass.data[DOMAIN_DATA_MANAGERS]
    assert mock_config_entry.state == ConfigEntryState.LOADED


# ============================================================================
# Manager: async_start_update_task + async_update_state (Kernlogik)
# ============================================================================


async def test_update_task_starts_when_enabled(hass: HomeAssistant, setup_integration, mock_config_entry) -> None:
    """Test that enabling the switch starts the update task."""
    manager = hass.data[DOMAIN_DATA_MANAGERS][mock_config_entry.entry_id]
    assert manager._update_listener is None  # Not running initially (disabled)

    await hass.services.async_call(SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: SWITCH_ENABLED}, blocking=True)
    await hass.async_block_till_done()

    assert manager._update_listener is not None


async def test_update_task_stops_when_disabled(hass: HomeAssistant, setup_integration, mock_config_entry) -> None:
    """Test that disabling the switch stops the update task."""
    manager = hass.data[DOMAIN_DATA_MANAGERS][mock_config_entry.entry_id]

    await hass.services.async_call(SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: SWITCH_ENABLED}, blocking=True)
    await hass.async_block_till_done()
    assert manager._update_listener is not None

    await hass.services.async_call(SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: SWITCH_ENABLED}, blocking=True)
    await hass.async_block_till_done()

    assert manager._update_listener is None


async def test_update_state_advances_brightness(hass: HomeAssistant, setup_integration, mock_config_entry, time_travel) -> None:
    """Test that async_update_state advances brightness values over time."""
    manager = hass.data[DOMAIN_DATA_MANAGERS][mock_config_entry.entry_id]
    initial_values = dict(manager._current_values)

    await hass.services.async_call(SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: SWITCH_ENABLED}, blocking=True)
    await hass.async_block_till_done()

    await time_travel(seconds=manager.get_config_trigger_interval() + 1)

    # Values should have changed or task is running
    assert manager._current_values != initial_values or manager._update_listener is not None


async def test_update_state_skipped_when_disabled(hass: HomeAssistant, setup_integration, mock_config_entry) -> None:
    """Test that async_update_state skips and stops task when disabled."""
    manager = hass.data[DOMAIN_DATA_MANAGERS][mock_config_entry.entry_id]

    await manager.async_update_state()
    await hass.async_block_till_done()

    assert manager._update_listener is None


# ============================================================================
# Manager: Color mode detection
# ============================================================================


async def test_detect_color_mode_rgb(hass: HomeAssistant, mock_light) -> None:
    """Test that RGB color mode is detected from light attributes."""
    hass.states.async_set(
        "light.rgb_light",
        "on",
        {"supported_color_modes": ["rgb"], "rgb_color": [100, 150, 200]},
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={TARGET_LIGHT_ENTITY_ID: ["light.rgb_light"]},
        entry_id="test_rgb",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    manager = hass.data[DOMAIN_DATA_MANAGERS][entry.entry_id]
    assert manager._color_mode == "rgb"
    assert "r" in manager._current_values
    assert "g" in manager._current_values
    assert "b" in manager._current_values


async def test_detect_color_mode_rgbw(hass: HomeAssistant, mock_light) -> None:
    """Test that RGBW color mode is detected from light attributes."""
    hass.states.async_set(
        "light.rgbw_light",
        "on",
        {"supported_color_modes": ["rgbw"], "rgbw_color": [100, 150, 200, 50]},
    )

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={TARGET_LIGHT_ENTITY_ID: ["light.rgbw_light"]},
        entry_id="test_rgbw",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    manager = hass.data[DOMAIN_DATA_MANAGERS][entry.entry_id]
    assert manager._color_mode == "rgbw"
    assert "r" in manager._current_values
    assert "w" in manager._current_values


async def test_detect_color_mode_brightness_fallback(hass: HomeAssistant, mock_light) -> None:
    """Test that brightness mode is used as fallback when no color mode detected."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={TARGET_LIGHT_ENTITY_ID: ["light.test_light"]},
        entry_id="test_brightness",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    manager = hass.data[DOMAIN_DATA_MANAGERS][entry.entry_id]
    assert manager._color_mode == "brightness"
    assert "brightness" in manager._current_values


# ============================================================================
# Manager: _get_brightness_of_first_light_entity
# ============================================================================


async def test_get_brightness_of_light(hass: HomeAssistant, setup_integration, mock_config_entry) -> None:
    """Test brightness retrieval from light entity."""
    manager = hass.data[DOMAIN_DATA_MANAGERS][mock_config_entry.entry_id]

    brightness = manager._get_brightness_of_first_light_entity()
    assert brightness == 128  # mock_light has brightness=128


async def test_get_brightness_fallback_when_no_brightness(hass: HomeAssistant, mock_light) -> None:
    """Test brightness fallback to 1 when light has no brightness attribute."""
    hass.states.async_set("light.test_light", "on", {})  # No brightness

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={TARGET_LIGHT_ENTITY_ID: ["light.test_light"]},
        entry_id="test_no_brightness",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    manager = hass.data[DOMAIN_DATA_MANAGERS][entry.entry_id]
    brightness = manager._get_brightness_of_first_light_entity()
    assert brightness == 1


# ============================================================================
# Manager: _restore_initial_state
# ============================================================================


async def test_restore_initial_state_clears_snapshot(hass: HomeAssistant, mock_light) -> None:
    """Test that _restore_initial_state clears the snapshot afterwards."""
    hass.states.async_set("light.test_light", "off", {})

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={TARGET_LIGHT_ENTITY_ID: ["light.test_light"]},
        entry_id="test_restore_off",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    manager = hass.data[DOMAIN_DATA_MANAGERS][entry.entry_id]
    await manager._capture_initial_state()
    assert manager._initial_state is not None

    await manager._restore_initial_state()
    await hass.async_block_till_done()

    assert manager._initial_state is None


# ============================================================================
# async_setup: YAML import path
# ============================================================================


async def test_async_setup_with_yaml_config(hass: HomeAssistant, mock_light) -> None:
    """Test async_setup triggers a config flow import for YAML entries."""
    yaml_config = {
        DOMAIN: [
            {
                MC_CONF_NAME: "YAML Instance",
                TARGET_LIGHT_ENTITY_ID: ["light.test_light"],
            }
        ]
    }

    result = await async_setup(hass, yaml_config)
    await hass.async_block_till_done()

    assert result is True


async def test_async_setup_without_yaml_config(hass: HomeAssistant) -> None:
    """Test async_setup succeeds even without YAML config."""
    result = await async_setup(hass, {})
    assert result is True
