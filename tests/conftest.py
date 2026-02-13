"""Root conftest für alle Moving Colors Tests."""

import logging

import pytest

# Reduziere verbose HA-Logs
logging.getLogger("homeassistant").setLevel(logging.WARNING)
logging.getLogger("homeassistant.core").setLevel(logging.ERROR)
logging.getLogger("homeassistant.helpers").setLevel(logging.ERROR)
logging.getLogger("homeassistant.loader").setLevel(logging.ERROR)
logging.getLogger("homeassistant.setup").setLevel(logging.WARNING)
logging.getLogger("homeassistant.components").setLevel(logging.ERROR)
logging.getLogger("asyncio").setLevel(logging.ERROR)

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: None) -> None:
    """Enable loading custom integrations in all tests."""
    return


@pytest.fixture(autouse=True)
def expected_lingering_tasks() -> bool:
    """Allow lingering tasks in tests."""
    return True


@pytest.fixture(autouse=True)
def expected_lingering_timers() -> bool:
    """Allow lingering timers in tests."""
    return True


@pytest.fixture(autouse=True)
def configure_test_logging(caplog):
    """Configure logging for tests."""
    caplog.set_level(logging.DEBUG, logger="custom_components.moving_colors")
    caplog.set_level(logging.INFO, logger="tests")
    caplog.set_level(logging.WARNING, logger="homeassistant")
