"""Moving Colors ConfigFlow and OptionsFlow implementation."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from voluptuous import Any

from .const import (
    CFG_MINIMAL,
    CFG_MINIMAL_OPTIONS,
    CFG_OPTIONS,
    DOMAIN,
    MC_CONF_NAME,
    TARGET_LIGHT_ENTITY_ID,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)


class MovingColorsConfigFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Moving Colors."""

    # Get the schema version from constants
    VERSION = VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Initialize the config flow."""
        self.config_data = {}

    async def async_step_import(self, import_config: dict[str, Any]) -> FlowResult:
        """Handle a flow initiated by a YAML configuration."""
        # Check if there is already an instance to prevent duplicated entries
        # The name is the key
        instance_name = import_config.get(MC_CONF_NAME)
        if instance_name:
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if entry.data.get(MC_CONF_NAME) == instance_name:
                    _LOGGER.warning("Attempted to import duplicate Moving Colors instance '%s' from YAML. Skipping.", instance_name)
                    return self.async_abort(reason="already_configured")

        _LOGGER.debug("[ConfigFlow] Importing from YAML with config: %s", import_config)

        # Convert yaml configuration into ConfigEntry, 'name' goes to 'data' section,
        # all the rest into 'options'.
        # Must be the same as in __init__.py!
        config_data_for_entry = {
            MC_CONF_NAME: import_config.pop(MC_CONF_NAME),  # Remove name from import_config
        }
        # All the rest into 'options'
        options_data_for_entry = import_config

        # Optional validation against FULL_OPTIONS_SCHEMA to verify the yaml data
        try:
            validated_options = CFG_OPTIONS(options_data_for_entry)
        except vol.Invalid:
            _LOGGER.exception("Validation error during YAML import for '%s'", instance_name)
            return self.async_abort(reason="invalid_yaml_config")

        # Create ConfigEntry with 'title' as the name within the UI
        return self.async_create_entry(
            title=instance_name,
            data=config_data_for_entry,
            options=validated_options,
        )

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        # Initialize data for the form, using user_input if available, else empty for initial display
        # This ensures fields are pre-filled if the form is redisplayed due to errors
        form_data = user_input if user_input is not None else {}

        if user_input is not None:
            _LOGGER.debug("[ConfigFlow] Received user_input: %s", user_input)

            # Manual validation of input fields to provide possible error messages
            # for each field at once and not step by step.
            if not user_input.get(MC_CONF_NAME):
                errors[MC_CONF_NAME] = "name"  # Error code from within strings.json

            if not user_input.get(TARGET_LIGHT_ENTITY_ID):
                errors[TARGET_LIGHT_ENTITY_ID] = "target_light_entity"  # Error code from within strings.json

            # If configuration errors found, show the config form again
            if errors:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self.add_suggested_values_to_schema(CFG_MINIMAL, form_data),
                    errors=errors,
                )

            instance_name = user_input.get(MC_CONF_NAME, "")

            # Check for already existing entries
            for entry in self.hass.config_entries.async_entries(DOMAIN):
                if entry.data.get(MC_CONF_NAME) == instance_name:
                    errors = {"base": "already_configured"}
                    return self.async_show_form(step_id="user", data_schema=CFG_MINIMAL, errors=errors)

            # Immutable configuration data, not available within OptionsFlow
            config_data_for_entry = {
                MC_CONF_NAME: instance_name,
            }

            # Create list of options, which are visible and editable within OptionsFlow
            options_data_for_entry = {
                key: value
                for key, value in user_input.items()
                if key not in {MC_CONF_NAME}  # Remove instance name
            }

            # All fine, now perform voluptuous validation
            try:
                validated_options_initial = CFG_MINIMAL_OPTIONS(options_data_for_entry)
                _LOGGER.debug("Creating entry with data: %s and options: %s", config_data_for_entry, validated_options_initial)
                return self.async_create_entry(
                    title=instance_name,
                    data=config_data_for_entry,
                    options=validated_options_initial,
                )
            except vol.Invalid as exc:
                _LOGGER.exception("Validation error during final config flow step:")
                for error in exc.errors:
                    if error.path:
                        errors[str(error.path[0])] = "invalid_input"
                    else:
                        errors["base"] = "unknown_error"

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(CFG_MINIMAL, self.config_data),
            errors=errors,
        )

    def _clean_number_inputs(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Convert empty string number fields to 0 or their default."""
        cleaned_input = user_input.copy()
        for key, value in cleaned_input.items():
            if isinstance(value, str) and value == "":
                # For selectors, the default should come from the schema itself
                # or be explicitly handled. Setting to 0 here for number fields.
                cleaned_input[key] = 0
                _LOGGER.debug("Cleaned empty string for key '%s' to 0.", key)
        return cleaned_input

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return MovingColorsOptionsFlowHandler()


class MovingColorsOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Moving Colors."""

    def __init__(self) -> None:
        """Initialize options flow."""
        self.options_data = None

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Manage the options."""
        # Initialize options_data from config_entry.options, with all editable options
        self.options_data = dict(self.config_entry.options)

        _LOGGER.info("Initial options_data: %s", self.options_data)

        # Redirect to the first specific options step
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle general data options."""
        _LOGGER.debug("[OptionsFlow] -> async_step_user")
        data_schema = CFG_OPTIONS
        validation_schema = CFG_OPTIONS

        errors: dict[str, str] = {}
        if user_input is not None:
            self.options_data.update(self._clean_number_inputs(user_input))
            _LOGGER.debug("Final options data before update: %s", self.options_data)

            try:
                # Validate the entire options configuration using the combined schema
                validated_options = validation_schema(self.options_data)
                _LOGGER.debug("Validated options data: %s", validated_options)

                self.hass.config_entries.async_update_entry(self.config_entry, data=self.config_entry.data, options=validated_options)

                return self.async_create_entry(title="", data=validated_options)

            except vol.Invalid as exc:
                _LOGGER.exception("Validation error during options flow final step:")
                for error in exc.errors:
                    if error.path:
                        errors[str(error.path[0])] = "invalid_input"
                    else:
                        errors["base"] = "unknown_error"

        return self.async_show_form(
            step_id="dawn_settings",
            data_schema=self.add_suggested_values_to_schema(data_schema, self.options_data),
            errors=errors,
        )

    def _clean_number_inputs(self, user_input: dict[str, Any]) -> dict[str, Any]:
        """Convert empty string number fields to 0 or their default."""
        cleaned_input = user_input.copy()
        for key, value in cleaned_input.items():
            if isinstance(value, str) and value == "":
                cleaned_input[key] = 0
                _LOGGER.debug("Cleaned empty string for key '%s' to 0 in options flow.", key)
        return cleaned_input
