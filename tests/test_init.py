"""Test moving_colors setup process."""

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.moving_colors.const import DOMAIN, DOMAIN_DATA_MANAGERS, MC_CONF_NAME


async def test_setup_entry(hass: HomeAssistant, mock_config_entry, mock_light) -> None:
    """Test setup of a config entry."""
    mock_config_entry.add_to_hass(hass)

    hass.bus.async_fire(EVENT_HOMEASSISTANT_STARTED)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert mock_config_entry.state == ConfigEntryState.LOADED
    assert DOMAIN_DATA_MANAGERS in hass.data
    assert mock_config_entry.entry_id in hass.data[DOMAIN_DATA_MANAGERS]


async def test_setup_entry_missing_target_light(hass: HomeAssistant) -> None:
    """Test setup fails when target light is missing."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            MC_CONF_NAME: "Test",
            # TARGET_LIGHT_ENTITY_ID missing
        },
        entry_id="test_no_light",
    )
    entry.add_to_hass(hass)

    assert not await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state == ConfigEntryState.SETUP_ERROR
