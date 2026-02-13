"""Scenario-based integration tests for Moving Colors.

These tests verify the actual behavior of the color-changing logic,
not just setup/teardown. Each test describes a real-world scenario.

Default values (from MCInternalDefaults):
    STEPPING         = 3
    TRIGGER_INTERVAL = 2s
    MIN_VALUE        = 0
    MAX_VALUE        = 255
    START_VALUE      = 125

NOTE: _sync_current_values_to_snapshot() is called on every async_start_update_task().
It resets _current_values from the physical light state and always sets _count_up_*=True.
Tests must not pre-set internal state before enable_mc() - it will be overwritten.
Instead, tests control behavior via narrow min/max ranges on the number entities.

Known behavior: After stop+restart, direction always resets to UP (count_up=True).
This may be a bug - tracked in test_direction_resets_after_restart.
"""

import logging

import pytest
from homeassistant.components.number import DOMAIN as NUMBER_DOMAIN
from homeassistant.components.number import SERVICE_SET_VALUE
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.const import ATTR_ENTITY_ID, EVENT_HOMEASSISTANT_STARTED, SERVICE_TURN_OFF, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.moving_colors.const import (
    DOMAIN,
    DOMAIN_DATA_MANAGERS,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
    MCInternalDefaults,
)

_LOGGER = logging.getLogger(__name__)

# ============================================================================
# Test Config & Constants
# ============================================================================

INSTANCE_NAME = "MC Test"
INTERVAL = MCInternalDefaults.TRIGGER_INTERVAL.value  # 2s
STEPPING = MCInternalDefaults.STEPPING.value  # 3
MIN_VALUE = MCInternalDefaults.MIN_VALUE.value  # 0
MAX_VALUE = MCInternalDefaults.MAX_VALUE.value  # 255

# Entity IDs - derived from INSTANCE_NAME "MC Test" → slug "mc_test"
SWITCH_ENABLED = "switch.mc_test_enable_moving_colors"
SWITCH_RANDOM_LIMITS = "switch.mc_test_random_limits"
NUMBER_MIN = "number.mc_test_minimum_value"
NUMBER_MAX = "number.mc_test_maximum_value"
NUMBER_STEPPING = "number.mc_test_step_value"
NUMBER_INTERVAL = "number.mc_test_trigger_interval"


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def mc_entry(hass: HomeAssistant, mock_light: str) -> MockConfigEntry:
    """Setup a Moving Colors instance with a simple brightness light."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={TARGET_LIGHT_ENTITY_ID: [mock_light]},
        entry_id="mc_test_entry",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def mc_entry_rgb(hass: HomeAssistant) -> MockConfigEntry:
    """Setup a Moving Colors instance with an RGB light."""
    hass.states.async_set(
        "light.rgb_light",
        "on",
        {"supported_color_modes": ["rgb"], "rgb_color": [100, 150, 200]},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={TARGET_LIGHT_ENTITY_ID: ["light.rgb_light"]},
        entry_id="mc_test_rgb_entry",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


@pytest.fixture
async def mc_entry_rgbw(hass: HomeAssistant) -> MockConfigEntry:
    """Setup a Moving Colors instance with an RGBW light."""
    hass.states.async_set(
        "light.rgbw_light",
        "on",
        {"supported_color_modes": ["rgbw"], "rgbw_color": [100, 150, 200, 50]},
    )
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={MC_CONF_NAME: INSTANCE_NAME},
        options={TARGET_LIGHT_ENTITY_ID: ["light.rgbw_light"]},
        entry_id="mc_test_rgbw_entry",
        title=INSTANCE_NAME,
        version=1,
    )
    entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


# ============================================================================
# Helpers
# ============================================================================


async def enable_mc(hass: HomeAssistant) -> None:
    """Enable Moving Colors via the enable switch."""
    await hass.services.async_call(SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: SWITCH_ENABLED}, blocking=True)
    await hass.async_block_till_done()


async def disable_mc(hass: HomeAssistant) -> None:
    """Disable Moving Colors via the enable switch."""
    await hass.services.async_call(SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: SWITCH_ENABLED}, blocking=True)
    await hass.async_block_till_done()


async def set_number(hass: HomeAssistant, entity_id: str, value: float) -> None:
    """Set a number entity value."""
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: entity_id, "value": value},
        blocking=True,
    )
    await hass.async_block_till_done()


def get_manager(hass: HomeAssistant, entry: MockConfigEntry):
    """Get the Moving Colors manager for a config entry."""
    return hass.data[DOMAIN_DATA_MANAGERS][entry.entry_id]


# ============================================================================
# Scenario 1: Brightness light - basic movement
# ============================================================================


async def test_brightness_changes_after_enable(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: Dimmable light starts moving after enable.

    Given: A simple brightness light is configured
    When:  Moving Colors is enabled and one interval passes
    Then:  The brightness value has changed
    """
    manager = get_manager(hass, mc_entry)
    await enable_mc(hass)

    value_after_enable = manager._current_values["brightness"]
    await time_travel(seconds=INTERVAL + 1)

    assert manager._current_values["brightness"] != value_after_enable, f"Brightness should have changed after {INTERVAL}s tick"


async def test_brightness_stays_within_default_bounds(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: Brightness always stays between 0 and 255.

    Given: Default min=0, max=255
    When:  Moving Colors runs for many ticks
    Then:  Brightness is always within [0, 255]
    """
    manager = get_manager(hass, mc_entry)
    await enable_mc(hass)

    for _ in range(30):
        await time_travel(seconds=INTERVAL + 1)
        brightness = manager._current_values["brightness"]
        assert MIN_VALUE <= brightness <= MAX_VALUE, f"Brightness {brightness} outside default bounds [{MIN_VALUE}, {MAX_VALUE}]"


async def test_brightness_reverses_direction_at_max(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: Brightness reverses when hitting max boundary.

    Given: Narrow range max=15, min=0 so boundary is hit quickly
    When:  Moving Colors runs from 0 upward
    Then:  After hitting max, count_up becomes False
    """
    manager = get_manager(hass, mc_entry)

    # Set narrow range BEFORE enable - _sync_current_values_to_snapshot
    # picks up abs_min/abs_max from get_config_min/max_value at enable time.
    # mock_light has brightness=128, so sync starts at 128.
    # With max=15 the sync would set brightness=128 but active_max=15,
    # so the first update clamps to max=15 immediately.
    await set_number(hass, NUMBER_MIN, 0)
    await set_number(hass, NUMBER_MAX, 15)
    await enable_mc(hass)

    # Run enough ticks to bounce (15/3 = 5 steps, use 10 for safety)
    for _ in range(10):
        await time_travel(seconds=INTERVAL + 1)

    brightness = manager._current_values["brightness"]
    count_up = manager._count_up_brightness
    assert not count_up, f"After hitting max=15, direction should be DOWN. brightness={brightness}, count_up={count_up}"


async def test_brightness_reverses_direction_at_min(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: Brightness reverses when hitting min boundary.

    Given: Narrow range max=15, min=0, starting near top
    When:  Moving Colors runs down and hits min=0
    Then:  count_up becomes True again
    """
    manager = get_manager(hass, mc_entry)
    await set_number(hass, NUMBER_MIN, 0)
    await set_number(hass, NUMBER_MAX, 15)
    await enable_mc(hass)

    # Run enough ticks to bounce twice (up to 15, then down to 0)
    # Simulation: after enable, first update hits max=15 immediately (count_up=False).
    # Then exactly 5 ticks reach min=0 (15→12→9→6→3→0, count_up→True).
    for _ in range(5):
        await time_travel(seconds=INTERVAL + 1)

    count_up = manager._count_up_brightness
    brightness = manager._current_values["brightness"]
    assert count_up, f"After 5 ticks from max=15 down to min=0, direction should be UP. brightness={brightness}, count_up={count_up}"


async def test_brightness_stops_when_disabled(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: Brightness stops changing after disable.

    Given: Moving Colors is running
    When:  It is disabled
    Then:  Values no longer change after subsequent ticks
    """
    manager = get_manager(hass, mc_entry)
    await enable_mc(hass)
    await time_travel(seconds=INTERVAL + 1)

    await disable_mc(hass)
    value_after_disable = dict(manager._current_values)

    await time_travel(seconds=INTERVAL + 1)
    await time_travel(seconds=INTERVAL + 1)

    assert manager._current_values == value_after_disable, "Values should not change after disable"
    assert manager._update_listener is None


async def test_direction_preserved_after_restart(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: After stop+restart, direction is preserved (not reset).

    When start_from_current_position is disabled (default in test env because
    internal entities are not yet initialized), _sync_current_values_to_snapshot
    is NOT called, so _count_up_brightness keeps its last value.

    Given: Moving Colors runs until it goes DOWN (count_up=False)
    When:  It is disabled and re-enabled
    Then:  count_up is still False (direction preserved)
    """
    manager = get_manager(hass, mc_entry)
    await set_number(hass, NUMBER_MIN, 0)
    await set_number(hass, NUMBER_MAX, 15)
    await enable_mc(hass)

    # After enable: first update hits max=15 → count_up=False.
    # Tick 10 lands at val=15 (count_up=False) per simulation.
    for _ in range(10):
        await time_travel(seconds=INTERVAL + 1)
    assert not manager._count_up_brightness, "Should be going DOWN before restart"

    # Restart
    await disable_mc(hass)
    await enable_mc(hass)

    # Without _sync, direction is preserved from before stop
    assert not manager._count_up_brightness, "Direction should be preserved after restart when start_from_current_position is disabled"


async def test_brightness_restarts_after_reenable(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: Brightness resumes after re-enable.

    Given: Moving Colors was disabled
    When:  It is re-enabled and a tick passes
    Then:  Values change again
    """
    manager = get_manager(hass, mc_entry)
    await enable_mc(hass)
    await time_travel(seconds=INTERVAL + 1)
    await disable_mc(hass)

    # After re-enable, _sync resets brightness to light state (128).
    # We just need to verify the timer is running and a tick produces a change.
    await enable_mc(hass)
    value_after_reenable = dict(manager._current_values)

    await time_travel(seconds=INTERVAL + 1)

    assert manager._current_values != value_after_reenable, "Values should change after re-enable + tick"


# ============================================================================
# Scenario 2: Custom min/max boundaries
# ============================================================================


async def test_custom_min_max_respected(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: Custom min/max limits are respected.

    Given: min=100, max=150
    When:  Moving Colors runs for many ticks
    Then:  Brightness stays within [100, 150]
    """
    manager = get_manager(hass, mc_entry)
    await set_number(hass, NUMBER_MIN, 100)
    await set_number(hass, NUMBER_MAX, 150)
    await enable_mc(hass)

    for _ in range(30):
        await time_travel(seconds=INTERVAL + 1)
        brightness = manager._current_values["brightness"]
        assert 100 <= brightness <= 150, f"Brightness {brightness} outside custom bounds [100, 150]"


async def test_custom_stepping_affects_speed(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: Larger stepping means faster color change per tick.

    Given: stepping=20 (within valid range 0-25)
    When:  Moving Colors runs with narrow range to see exact steps
    Then:  Value changes by ~20 per tick instead of default 3
    """
    manager = get_manager(hass, mc_entry)
    await set_number(hass, NUMBER_STEPPING, 20)
    await set_number(hass, NUMBER_MIN, 0)
    await set_number(hass, NUMBER_MAX, 255)
    await enable_mc(hass)

    # After enable, _sync sets brightness=128 (from mock_light).
    # First tick (already called in async_start_update_task) adds 20 → ~148.
    value_after_start = manager._current_values["brightness"]
    await time_travel(seconds=INTERVAL + 1)
    value_after_tick = manager._current_values["brightness"]

    change = abs(value_after_tick - value_after_start)
    assert change >= 20, f"With stepping=20, value should change by ~20 per tick, got change={change} ({value_after_start} → {value_after_tick})"


# ============================================================================
# Scenario 3: Random limits
# ============================================================================


async def test_random_limits_new_min_after_hitting_max(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: With random limits, a new random min is set after hitting max.

    Given: Random limits enabled, narrow range max=15, min=0
    When:  Moving Colors hits the max boundary
    Then:  _active_min["brightness"] gets a new random value between 0 and 15
    """
    manager = get_manager(hass, mc_entry)

    await hass.services.async_call(SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: SWITCH_RANDOM_LIMITS}, blocking=True)
    await hass.async_block_till_done()

    await set_number(hass, NUMBER_MIN, 0)
    await set_number(hass, NUMBER_MAX, 15)
    await enable_mc(hass)

    # Run enough ticks to hit max (15/3 = 5 steps, use 12 for safety)
    for _ in range(12):
        await time_travel(seconds=INTERVAL + 1)

    # After hitting max, a new random min should have been generated
    new_min = manager._active_min.get("brightness")
    assert new_min is not None
    assert 0 <= new_min <= 15, f"New random min {new_min} should be within [0, 15]"


async def test_without_random_limits_boundaries_stay_fixed(hass: HomeAssistant, mc_entry: MockConfigEntry, time_travel) -> None:
    """Scenario: Without random limits, boundaries stay at configured values.

    Given: Random limits disabled (default), narrow range max=15, min=0
    When:  Moving Colors bounces at max
    Then:  _active_min stays at 0 (not randomized)
    """
    manager = get_manager(hass, mc_entry)
    # Random limits default is False - no need to explicitly disable

    await set_number(hass, NUMBER_MIN, 0)
    await set_number(hass, NUMBER_MAX, 15)
    await enable_mc(hass)

    for _ in range(12):
        await time_travel(seconds=INTERVAL + 1)

    assert manager._active_min.get("brightness") == 0, "Without random limits, active_min should stay at configured min=0"
    assert manager._active_max.get("brightness") == 15, "Without random limits, active_max should stay at configured max=15"


# ============================================================================
# Scenario 4: RGB light - channels move independently
# ============================================================================


async def test_rgb_color_mode_detected(hass: HomeAssistant, mc_entry_rgb: MockConfigEntry) -> None:
    """Scenario: RGB light is correctly identified.

    Given: A light with supported_color_modes=['rgb']
    When:  Integration starts
    Then:  color_mode is 'rgb' with r, g, b channels (no brightness, no w)
    """
    manager = get_manager(hass, mc_entry_rgb)
    assert manager._color_mode == "rgb"
    assert set(manager._current_values.keys()) == {"r", "g", "b"}


async def test_rgb_channels_change_after_tick(hass: HomeAssistant, mc_entry_rgb: MockConfigEntry, time_travel) -> None:
    """Scenario: RGB channels advance after each tick.

    Given: RGB light
    When:  Moving Colors runs one tick
    Then:  At least one channel value has changed
    """
    manager = get_manager(hass, mc_entry_rgb)
    await enable_mc(hass)
    initial_values = dict(manager._current_values)

    await time_travel(seconds=INTERVAL + 1)

    assert manager._current_values != initial_values, "RGB channel values should change after one tick"


async def test_rgb_channels_stay_within_bounds(hass: HomeAssistant, mc_entry_rgb: MockConfigEntry, time_travel) -> None:
    """Scenario: All RGB channels stay within [0, 255].

    Given: RGB light
    When:  Moving Colors runs for many ticks
    Then:  All r, g, b values are always within [0, 255]
    """
    manager = get_manager(hass, mc_entry_rgb)
    await enable_mc(hass)

    for _ in range(30):
        await time_travel(seconds=INTERVAL + 1)
        for channel in ("r", "g", "b"):
            val = manager._current_values[channel]
            assert 0 <= val <= 255, f"RGB channel '{channel}' value {val} outside [0, 255]"


async def test_rgb_channels_move_independently(hass: HomeAssistant, mc_entry_rgb: MockConfigEntry, time_travel) -> None:
    """Scenario: RGB channels have independent direction tracking.

    Given: RGB light where r=100, g=150, b=200 (different start positions)
    When:  Moving Colors runs for many ticks
    Then:  Not all channels always move in the same direction at the same time
    """
    manager = get_manager(hass, mc_entry_rgb)
    await enable_mc(hass)

    directions_differ = False
    for _ in range(30):
        await time_travel(seconds=INTERVAL + 1)
        r_up = getattr(manager, "_count_up_r", True)
        g_up = getattr(manager, "_count_up_g", True)
        b_up = getattr(manager, "_count_up_b", True)
        if not (r_up == g_up == b_up):
            directions_differ = True
            break

    assert directions_differ, "RGB channels starting at different positions should eventually have independent directions"


# ============================================================================
# Scenario 5: RGBW light - white channel is always zeroed
# ============================================================================


async def test_rgbw_color_mode_detected(hass: HomeAssistant, mc_entry_rgbw: MockConfigEntry) -> None:
    """Scenario: RGBW light is correctly identified.

    Given: A light with supported_color_modes=['rgbw']
    When:  Integration starts
    Then:  color_mode is 'rgbw' with r, g, b, w channels
    """
    manager = get_manager(hass, mc_entry_rgbw)
    assert manager._color_mode == "rgbw"
    assert set(manager._current_values.keys()) == {"r", "g", "b", "w"}


async def test_rgbw_white_channel_always_zero(hass: HomeAssistant, mc_entry_rgbw: MockConfigEntry, time_travel) -> None:
    """Scenario: RGBW white channel is always forced to 0 by design.

    Given: RGBW light with w=50 initially
    When:  Moving Colors runs for several ticks
    Then:  The 'w' channel is always 0
    """
    manager = get_manager(hass, mc_entry_rgbw)
    await enable_mc(hass)

    for _ in range(10):
        await time_travel(seconds=INTERVAL + 1)
        assert manager._current_values["w"] == 0, f"White channel should always be 0, got {manager._current_values['w']}"


async def test_rgbw_rgb_channels_change_while_w_stays_zero(hass: HomeAssistant, mc_entry_rgbw: MockConfigEntry, time_travel) -> None:
    """Scenario: RGBW r, g, b channels advance while w stays at 0.

    Given: RGBW light
    When:  Moving Colors runs
    Then:  r, g, b channels change while w stays 0
    """
    manager = get_manager(hass, mc_entry_rgbw)
    await enable_mc(hass)
    initial_rgb = {c: manager._current_values[c] for c in ("r", "g", "b")}

    await time_travel(seconds=INTERVAL + 1)

    current_rgb = {c: manager._current_values[c] for c in ("r", "g", "b")}
    assert current_rgb != initial_rgb, "RGB channels should change in RGBW mode"
    assert manager._current_values["w"] == 0
