"""Test component setup."""
from homeassistant.setup import async_setup_component


async def test_async_setup(hass):
    """Test the component gets setup."""
    assert await async_setup_component(hass, "moving_colors", {}) is not False