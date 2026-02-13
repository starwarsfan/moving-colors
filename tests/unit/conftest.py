"""Fixtures für Moving Colors Unit Tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture(autouse=True)
def mock_async_track_time_interval() -> Generator[MagicMock]:
    """Mock async_track_time_interval to prevent real timers in unit tests."""
    with patch("custom_components.moving_colors.async_track_time_interval") as mock:
        mock.return_value = MagicMock()
        yield mock
