"""Fixtures für Moving Colors Integration Tests."""

import logging
from datetime import timedelta

import pytest
from colorlog import ColoredFormatter
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry, async_fire_time_changed, async_mock_service

from custom_components.moving_colors.const import (
    DEBUG_ENABLED,
    DOMAIN,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
)

_LOGGER = logging.getLogger(__name__)


# ============================================================================
# Logging Setup
# ============================================================================


class SelectiveColoredFormatter(ColoredFormatter):
    """Formatter, der nur für Test-Files Farben anwendet."""

    def format(self, record):
        if "moving_colors" in record.name:
            neutral_formatter = logging.Formatter(
                fmt="%(levelname)-8s %(filename)30s: %(lineno)4s %(message)s",
                datefmt="%H:%M:%S",
            )
            return neutral_formatter.format(record)
        return super().format(record)


@pytest.fixture(autouse=True, scope="session")
def setup_logging():
    """Setup colored logging for integration tests."""
    color_format = "%(log_color)s%(levelname)-8s%(reset)s %(cyan)s%(filename)30s: %(lineno)4s %(message)s%(reset)s"

    formatter = SelectiveColoredFormatter(
        color_format,
        datefmt="%H:%M:%S",
        reset=True,
        log_colors={
            "DEBUG": "cyan",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "red,bg_white",
        },
    )

    root_logger = logging.getLogger()

    def filter_verbose_ha_logs(record):
        """Filter out verbose HA internal debug logs."""
        return not (record.filename == "common.py" and record.levelno == logging.DEBUG)

    seen_handler_types = {}
    unique_handlers = []

    for handler in root_logger.handlers:
        handler_type = type(handler).__name__
        if handler_type in ("_LiveLoggingStreamHandler", "_FileHandler", "LogCaptureHandler"):
            if handler_type == "LogCaptureHandler" and handler_type in seen_handler_types:
                continue
            seen_handler_types[handler_type] = True
            handler.setFormatter(formatter)
            handler.setLevel(logging.DEBUG)
            handler.addFilter(filter_verbose_ha_logs)
            unique_handlers.append(handler)

    root_logger.handlers = unique_handlers
    root_logger.setLevel(logging.DEBUG)


# ============================================================================
# Echte Timer: mock_async_track_time_interval NICHT aktiv
# ============================================================================


@pytest.fixture(autouse=True)
def use_real_timers():
    """Ensure integration tests use real HA timers, not mocks."""
    return


# ============================================================================
# Core Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def mock_light_services(hass: HomeAssistant):
    """Mock light services to prevent ServiceNotFound when integration calls light services."""
    async_mock_service(hass, "light", "turn_off")
    return async_mock_service(hass, "light", "turn_on")


@pytest.fixture(name="mock_light")
def mock_light_fixture(hass: HomeAssistant) -> str:
    """Mock a light entity in HA state machine."""
    hass.states.async_set(
        "light.test_light",
        "on",
        {
            "brightness": 128,
            "supported_features": 1,
        },
    )
    return "light.test_light"


@pytest.fixture(name="mock_config_entry")
def mock_config_entry_fixture() -> MockConfigEntry:
    """Return a mock config entry with minimal required config."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            MC_CONF_NAME: "Test Moving Colors",
        },
        options={
            TARGET_LIGHT_ENTITY_ID: ["light.test_light"],
            DEBUG_ENABLED: False,
        },
        entry_id="test_entry_id",
        unique_id="test_unique_id",
        title="Test Moving Colors",
        version=1,
    )


# ============================================================================
# Setup Helper
# ============================================================================


@pytest.fixture
async def setup_integration(hass: HomeAssistant, mock_config_entry: MockConfigEntry, mock_light: str):
    """Setup Moving Colors integration and fire HA_STARTED event.

    Returns the config entry after successful setup.
    """
    mock_config_entry.add_to_hass(hass)
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    return mock_config_entry


# ============================================================================
# Time Travel Helper
# ============================================================================


@pytest.fixture
def time_travel(hass: HomeAssistant, freezer):
    """Fixture zum Zeitsprung für Timer-Tests.

    Funktioniert mit async_track_time_interval und async_call_later Timern.
    """

    async def _travel(*, seconds: int = 0, minutes: int = 0, hours: int = 0):
        """Spring in der Zeit vorwärts."""
        delta = timedelta(seconds=seconds, minutes=minutes, hours=hours)
        target_time = dt_util.utcnow() + delta

        freezer.move_to(target_time)
        async_fire_time_changed(hass, target_time)

        await hass.async_block_till_done()
        await hass.async_block_till_done()
        await hass.async_block_till_done()

    return _travel


# ============================================================================
# Assert Helpers
# ============================================================================


def assert_state(hass: HomeAssistant, entity_id: str, expected_state: str) -> None:
    """Assert entity state with readable error message.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to check
        expected_state: Expected state string
    """
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} does not exist"
    assert state.state == expected_state, f"{entity_id}: expected state '{expected_state}', got '{state.state}'"
    _LOGGER.info("✓ %s is '%s'", entity_id, expected_state)


def assert_numeric_state(hass: HomeAssistant, entity_id: str, expected_value: float) -> None:
    """Assert entity state as float with readable error message.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to check
        expected_value: Expected numeric value
    """
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} does not exist"
    actual = float(state.state)
    assert actual == expected_value, f"{entity_id}: expected value {expected_value}, got {actual}"
    _LOGGER.info("✓ %s is %s", entity_id, expected_value)


def assert_entity_exists(hass: HomeAssistant, entity_id: str) -> None:
    """Assert that an entity exists in HA state machine.

    Args:
        hass: Home Assistant instance
        entity_id: Entity ID to check
    """
    state = hass.states.get(entity_id)
    assert state is not None, f"Entity {entity_id} was not created"
    _LOGGER.info("✓ %s exists (state: %s)", entity_id, state.state)
