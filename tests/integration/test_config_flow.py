"""Integration tests for Moving Colors config flow."""

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.moving_colors.const import (
    DEBUG_ENABLED,
    DOMAIN,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
)

# ============================================================================
# ConfigFlow: async_step_user
# ============================================================================


async def test_form_initial_display(hass: HomeAssistant) -> None:
    """Test that the initial user form is shown correctly."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_form_missing_name(hass: HomeAssistant, mock_light: str) -> None:
    """Test validation error when name is missing."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            MC_CONF_NAME: "",  # Empty name
            TARGET_LIGHT_ENTITY_ID: [mock_light],
            DEBUG_ENABLED: False,
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert MC_CONF_NAME in result["errors"]
    assert result["errors"][MC_CONF_NAME] == "name_missing"


async def test_form_missing_light_entity(hass: HomeAssistant) -> None:
    """Test validation error when target light entity is missing."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            MC_CONF_NAME: "Test Instance",
            # TARGET_LIGHT_ENTITY_ID missing
            DEBUG_ENABLED: False,
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"
    assert TARGET_LIGHT_ENTITY_ID in result["errors"]
    assert result["errors"][TARGET_LIGHT_ENTITY_ID] == "target_light_entity_missing"


async def test_form_missing_name_and_light(hass: HomeAssistant) -> None:
    """Test that both errors are shown simultaneously when name and light are missing."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            MC_CONF_NAME: "",
            DEBUG_ENABLED: False,
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert MC_CONF_NAME in result["errors"]
    assert TARGET_LIGHT_ENTITY_ID in result["errors"]


async def test_form_successful_submit(hass: HomeAssistant, mock_light: str) -> None:
    """Test successful config entry creation via user form."""
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            MC_CONF_NAME: "My Moving Colors",
            TARGET_LIGHT_ENTITY_ID: [mock_light],
            DEBUG_ENABLED: False,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "My Moving Colors"
    assert result["data"][MC_CONF_NAME] == "My Moving Colors"
    assert TARGET_LIGHT_ENTITY_ID not in result["data"]  # Light goes to options
    assert result["options"][TARGET_LIGHT_ENTITY_ID] == [mock_light]


async def test_form_duplicate_entry(hass: HomeAssistant, mock_light: str, mock_config_entry) -> None:
    """Test that duplicate instance name is rejected."""
    # Setup existing entry
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Try to create another entry with the same name
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": config_entries.SOURCE_USER})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            MC_CONF_NAME: "Test Moving Colors",  # Same as mock_config_entry
            TARGET_LIGHT_ENTITY_ID: [mock_light],
            DEBUG_ENABLED: False,
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"] == {"base": "already_configured"}


# ============================================================================
# ConfigFlow: async_step_import (YAML)
# ============================================================================


async def test_import_yaml_success(hass: HomeAssistant, mock_light: str) -> None:
    """Test successful YAML import."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={
            MC_CONF_NAME: "YAML Instance",
            TARGET_LIGHT_ENTITY_ID: [mock_light],
            DEBUG_ENABLED: False,
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["title"] == "YAML Instance"
    assert result["data"][MC_CONF_NAME] == "YAML Instance"


async def test_import_yaml_duplicate(hass: HomeAssistant, mock_light: str, mock_config_entry) -> None:
    """Test that duplicate YAML import is aborted."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={
            MC_CONF_NAME: "Test Moving Colors",  # Same as mock_config_entry
            TARGET_LIGHT_ENTITY_ID: [mock_light],
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_import_yaml_invalid_config(hass: HomeAssistant) -> None:
    """Test that invalid YAML config is aborted."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_IMPORT},
        data={
            MC_CONF_NAME: "Bad YAML Instance",
            TARGET_LIGHT_ENTITY_ID: "not_a_list_and_invalid_entity",  # Invalid value
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "invalid_yaml_config"


# ============================================================================
# OptionsFlow
# ============================================================================


async def test_options_flow_initial_form(hass: HomeAssistant, mock_light: str, mock_config_entry) -> None:
    """Test that options flow shows the form correctly."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "user"


async def test_options_flow_missing_light(hass: HomeAssistant, mock_light: str, mock_config_entry) -> None:
    """Test options flow validation error when light entity is removed."""
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            # TARGET_LIGHT_ENTITY_ID intentionally missing
            DEBUG_ENABLED: False,
        },
    )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert TARGET_LIGHT_ENTITY_ID in result["errors"]
    assert result["errors"][TARGET_LIGHT_ENTITY_ID] == "target_light_entity_missing"


async def test_options_flow_successful_update(hass: HomeAssistant, mock_light: str, mock_config_entry) -> None:
    """Test successful options update returns CREATE_ENTRY.

    Note: The OptionsFlow validates self.options_data (pre-filled from config_entry.options),
    not the user_input directly. So result["data"] reflects the original entry options.
    """
    mock_config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            TARGET_LIGHT_ENTITY_ID: [mock_light],
            DEBUG_ENABLED: True,  # Changed to True
        },
    )
    await hass.async_block_till_done()

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
