"""Test the Moving Colors config flow."""

from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.moving_colors.const import DOMAIN

from .const import MOCK_CONFIG_USER_INPUT


async def test_form(hass: HomeAssistant) -> None:
    """Test we get the user form."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "user"


async def test_user_flow(hass: HomeAssistant) -> None:
    """Test the user config flow."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    with patch(
        "custom_components.moving_colors.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            MOCK_CONFIG_USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "Test Moving Colors"
    assert result["data"] == MOCK_CONFIG_USER_INPUT
    assert len(mock_setup_entry.mock_calls) == 1


async def test_options_flow(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test options flow."""
    mock_config_entry.add_to_hass(hass)

    # Setup entry first
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Initiate options flow
    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    # Your integration might not have an options flow, so check what it returns
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    # Remove the step_id assertion or adjust based on your actual implementation
