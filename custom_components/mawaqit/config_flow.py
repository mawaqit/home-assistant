"""Adds config flow for Mawaqit."""
from homeassistant import config_entries
import voluptuous as vol

from .const import  CONF_CALC_METHOD, DEFAULT_CALC_METHOD, DOMAIN, NAME, CONF_SERVER, USERNAME, PASSWORD
from .mosq_list import CALC_METHODS
from .mawaqit import MawaqitClient, BadCredentialsException


from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_PASSWORD, CONF_USERNAME, CONF_API_KEY, CONF_TOKEN

import asyncio
import aiohttp
import os
import json
import time


class MawaqitPrayerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for mawaqit."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self):
        """Initialize."""
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        lat = self.hass.config.latitude
        longi = self.hass.config.longitude

        if user_input is not None:
            valid = await self._test_credentials(
                user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
            )
            #create data folder if does not exist
            current_dir = os.path.dirname(os.path.realpath(__file__))
            if not os.path.exists('{}/data'.format(current_dir)):
                os.makedirs('{}/data'.format(current_dir))
            # check if user credentials are correct
            if valid==False:
                return self.async_abort(reason="wrong_credential")
                
            if valid:
                # downloas mosques in the neighborhood
                
                
                da = await self.neighborhood(
                    lat, longi, user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                    
                    )
                if len(da)==0:
                    return self.async_abort(reason="no_mosque")
                    
                

                text_file = open('{}/data/all_mosquee_NN.txt'.format(current_dir), "w")
                json.dump(da, text_file)
                text_file.close()

                f = open('{}/data/all_mosquee_NN.txt'.format(current_dir))
                data = json.load(f)
                text_file = open('{}/data/my_mosquee_NN.txt'.format(current_dir), "w")
                json.dump(da[0], text_file)
                text_file.close()
                # the nearest mosque is chosen per default initialy
                db = await self.fetch_prayer_times(
                    lat, longi, da[0]["uuid"], user_input[CONF_USERNAME], user_input[CONF_PASSWORD]
                    )
                text_file = open('{dir}/data/pray_time_{name}.txt'.format(dir=current_dir, name=da[0]["uuid"] ), "w")
                json.dump(db, text_file)
                text_file.close()

                #download prayer time for all mosques in the neighborhood 
                for i in range(len(data)):   
                    db = await self.fetch_prayer_times(        
                            lat, longi, str(data[i]["uuid"]), user_input[CONF_USERNAME], user_input[CONF_PASSWORD],
                            )

                    text_file = open('{dir}/data/pray_time_{name}.txt'.format(dir=current_dir, name=data[i]["uuid"] ), "w")
                    json.dump(db, text_file)
                    text_file.close()
                        
                
                # creation of the list of mosques to be displayed in the options
                name_servers=[]
                uuid_servers=[]
                CALC_METHODS=[]
                with open('{}/data/all_mosquee_NN.txt'.format(current_dir), "r") as f:
                    distros_dict = json.load(f)
                
                for distro in distros_dict:
                    name_servers.extend([distro["label"]])
                    uuid_servers.extend([distro["uuid"]])
                    CALC_METHODS.extend([distro["label"]])
                
                text_file = open('{}/mosq_list.py'.format(current_dir), "w")
                n = text_file.write("CALC_METHODS = " + str(CALC_METHODS))
                text_file.close() 


 
                return self.async_create_entry(
                    title='Mawaqit', data={CONF_USERNAME: user_input[CONF_USERNAME], CONF_PASSWORD: user_input[CONF_PASSWORD],CONF_LATITUDE: lat,CONF_LONGITUDE: longi}
                )
            else:
                return self.async_abort(reason="no_mosque")
                self._errors["base"] = "auth"
                

            return await self._show_config_form(user_input)

        return await self._show_config_form(user_input)



    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_USERNAME, default="mawaqit_login"): str, vol.Required(CONF_PASSWORD): str}
            ),
            errors=self._errors,
        )

    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return MawaqitPrayerOptionsFlowHandler(config_entry)



    async def _test_credentials(self, username, password):
        """Return true if credentials is valid."""
        try:
            client = MawaqitClient('','','',username,password,'')
            await  client.login()
            await client.close()
            return True
        except BadCredentialsException:  # pylint: disable=broad-except
            
            pass
            #return self.async_abort(reason="nomosque")

        return False
        #return self.async_abort(reason="nomosque")

    async def neighborhood(self, lat, long, username, password):
        """Return mosques in the neighborhood if any."""
        try:
            client = MawaqitClient(lat,long,'',username,password,'')
            da = await  client.all_mosques_neighberhood()
            await client.close()
            return da
        except BadCredentialsException:  # pylint: disable=broad-except
            pass
        return da

    async def fetch_prayer_times(self, lat, long, mosquee, username, password):
        """fetch prayer time"""
        try:
            client = MawaqitClient(lat,long,mosquee,username,password,'')
            db = await  client.fetch_prayer_times()
            await client.close()
            return db
        except BadCredentialsException:  # pylint: disable=broad-except
            pass
        return db


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

