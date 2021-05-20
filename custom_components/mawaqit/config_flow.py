"""Config flow for Mawaqit Prayer Times integration."""
import voluptuous as vol
import os
from homeassistant import config_entries
from homeassistant.core import callback

from .const import  CONF_CALC_METHOD, DEFAULT_CALC_METHOD, DOMAIN, NAME, CONF_SERVER, USERNAME, PASSWORD

from .mosq_list import CALC_METHODS

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_PASSWORD, CONF_USERNAME, CONF_API_KEY, CONF_TOKEN

import homeassistant.helpers.config_validation as cv

from mawaqit_times_calculator import MawaqitTimesCalculator
name_servers = ["Connect to choose a mosque"]


class MawaqitPrayerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Mawaqit Prayer config flow."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return MawaqitPrayerOptionsFlowHandler(config_entry)

    def _show_setup_form(self, user_input=None, errors=None):
        """Show the setup form to the user."""

        if user_input is None:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME, default=user_input.get(CONF_USERNAME, "mawaqit login")
                    ): str,
                    vol.Required(
                        CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
                    ): str,
                    vol.Optional(
                        CONF_LATITUDE, default=self.hass.config.latitude
                    ): cv.latitude,
                    vol.Optional(
                        CONF_LONGITUDE, default=self.hass.config.longitude
                    ): cv.longitude,
#                    vol.Optional(
#                        CONF_SERVER, default="Nearest Mosque will be configured. Once installed, you can change your Mosque preference in the addon configuration"): vol.In(name_servers),
                }
            ),
            errors=errors or {},
        )
    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")



        global name_servers
        global uuid_servers
        global username
        global password
        global lat
        global longi
        name_servers = ["Connect to choose mosque"]
        uuid_servers = ["none"]
        if user_input is None:
            return self._show_setup_form(user_input, None)

        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        lat = user_input[CONF_LATITUDE]
        longi = user_input[CONF_LONGITUDE]
        #server = user_input[CONF_SERVER]



        #try: 
        #    prayer_times = await self.hass.async_add_executor_job(
        #        self.test_location())


       # if location_point_valid:
       #     return self.async_abort(reason="single_instance_allowed")




        return self.async_create_entry(
            title="Mawaqit",
            data={
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_LATITUDE: user_input[CONF_LATITUDE],
                CONF_LONGITUDE: user_input[CONF_LONGITUDE],
            },
        )
  





   

    async def async_step_import(self, import_config):
        """Import from config."""
        return await self.async_step_user(user_input=import_config)

     


class MawaqitPrayerOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Mawaqit Prayer client options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Manage options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_CALC_METHOD,
                default=self.config_entry.options.get(
                    CONF_CALC_METHOD, DEFAULT_CALC_METHOD
                ),
            ): vol.In(CALC_METHODS)
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))
