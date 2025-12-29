"""Global fixtures for moving_colors tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.moving_colors.const import (
    DEBUG_ENABLED,
    DOMAIN,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
)

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom integrations in all tests."""
    return


@pytest.fixture(name="mock_light")
def mock_light_fixture(hass: HomeAssistant) -> str:
    """Mock a light entity."""
    hass.states.async_set(
        "light.test_light",
        "on",
        {
            "brightness": 128,
            "supported_features": 1,  # SUPPORT_BRIGHTNESS
        },
    )
    return "light.test_light"


@pytest.fixture(name="mock_config_entry")
def mock_config_entry_fixture() -> MockConfigEntry:
    """Return a mock config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        data={
            MC_CONF_NAME: "Test Moving Colors",
            TARGET_LIGHT_ENTITY_ID: "light.test_light",
            DEBUG_ENABLED: False,
        },
        entry_id="test_entry_id",
        unique_id="test_unique_id",
        title="Test Moving Colors",
        version=1,
    )


@pytest.fixture(autouse=True)
def expected_lingering_tasks() -> bool:
    """Allow lingering tasks."""
    return True


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Allow lingering timers."""
    return True


@pytest.fixture(autouse=True)
def mock_async_track_time_interval() -> Generator[MagicMock]:
    """Mock async_track_time_interval to prevent timer issues in tests."""
    with patch("custom_components.moving_colors.async_track_time_interval") as mock:
        mock.return_value = MagicMock()
        yield mock
