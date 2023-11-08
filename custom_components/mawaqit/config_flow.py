"""Adds config flow for Mawaqit."""
from homeassistant import config_entries
import voluptuous as vol

from .const import  CONF_CALC_METHOD, DEFAULT_CALC_METHOD, DOMAIN, NAME, CONF_SERVER, USERNAME, PASSWORD, CONF_UUID
from .mosq_list import CALC_METHODS
from .mawaqit import MawaqitClient, BadCredentialsException


from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_PASSWORD, CONF_USERNAME, CONF_API_KEY, CONF_TOKEN

import logging
import asyncio
import aiohttp
import os
import json
import time
import homeassistant.helpers.config_validation as cv
from typing import Any
from homeassistant.data_entry_flow import FlowResult


_LOGGER = logging.getLogger(__name__)


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

        # create data folder if does not exist
        current_dir = os.path.dirname(os.path.realpath(__file__))
        if not os.path.exists('{}/data'.format(current_dir)):
            os.makedirs('{}/data'.format(current_dir))

        if user_input is None:
            return await self._show_config_form(user_input=None)
        
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        # check if user credentials are correct
        try:
            valid = await self._test_credentials(username, password)
        except aiohttp.client_exceptions.ClientConnectorError:
            self._errors["base"] = "cannot_connect_to_server"
            return await self._show_config_form(user_input)

        if valid:
            de = await self.apimawaqit(
                username, password
                )
            
            da = await self.neighborhood(
                lat, longi, username, password, de

                )
            if len(da)==0:
                return self.async_abort(reason="no_mosque")


            # create data folder if does not exist
            current_dir = os.path.dirname(os.path.realpath(__file__))
            if not os.path.exists('{}/data'.format(current_dir)):
                os.makedirs('{}/data'.format(current_dir))
                
            text_file = open('{}/data/api.txt'.format(current_dir), "w")
            text_file.write(de)
            text_file.close()
            
            text_file = open('{}/data/all_mosquee_NN.txt'.format(current_dir), "w")
            json.dump(da, text_file)
            text_file.close()
            
            # creation of the list of mosques to be displayed in the options
            name_servers = []
            uuid_servers = []
            CALC_METHODS = []

            with open('{}/data/all_mosquee_NN.txt'.format(current_dir), "r") as f:
                distros_dict = json.load(f)
            for distro in distros_dict:
                name_servers.extend([distro["label"]])
                uuid_servers.extend([distro["uuid"]])
                CALC_METHODS.extend([distro["label"]])
            
            text_file = open('{}/mosq_list.py'.format(current_dir), "w")
            n = text_file.write("CALC_METHODS = " + str(CALC_METHODS))
            text_file.close()                 

            return await self.async_step_mosques()

        else : # (if not valid)
            self._errors["base"] = "wrong_credential"

            return await self._show_config_form(user_input)


    async def async_step_mosques(self, user_input=None) -> FlowResult:
        """Handle mosques step."""

        self._errors = {}

        lat = self.hass.config.latitude
        longi = self.hass.config.longitude
        current_dir = os.path.dirname(os.path.realpath(__file__))
        f = open('{}/data/api.txt'.format(current_dir))
        api = f.read()
        f.close()


        if user_input is not None:
            da = await self.neighborhood(lat, longi, '', '', api)
            
            name_servers=[]
            uuid_servers=[]
            CALC_METHODS=[]
            with open('{}/data/all_mosquee_NN.txt'.format(current_dir), "r") as f:
                distros_dict = json.load(f)
            for distro in distros_dict:
                name_servers.extend([distro["label"]])
                uuid_servers.extend([distro["uuid"]])
                CALC_METHODS.extend([distro["label"]])
                
            mosquee = user_input[CONF_UUID]
            index = name_servers.index(mosquee)
            mosque_id = uuid_servers[index]
            
            text_file = open('{}/data/my_mosquee_NN.txt'.format(current_dir), "w")
            json.dump(da[index], text_file)
            text_file.close()          
            
            # the mosque chosen by user
            db = await self.fetch_prayer_times(lat, longi, mosque_id, '', '', api)
                    
            text_file = open('{dir}/data/pray_time{name}.txt'.format(dir=current_dir, name=""), "w")
            json.dump(db, text_file)
            text_file.close()

            title = 'MAWAQIT' + ' - ' + da[index]["name"]
            data = {CONF_API_KEY: api, CONF_UUID: mosque_id, CONF_LATITUDE: lat, CONF_LONGITUDE: longi}
            
            return self.async_create_entry(title=title, data=data)
        
        return await self._show_config_form2()
        
        
    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument

        if user_input is None:
            user_input = {}
            user_input[CONF_USERNAME] = ""
            user_input[CONF_PASSWORD] = ""
        
        schema = vol.Schema(
                {vol.Required(CONF_USERNAME, default=user_input[CONF_USERNAME]): str,
                 vol.Required(CONF_PASSWORD, default=user_input[CONF_PASSWORD]): str}
            )

        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=self._errors,
        )
        
        
    async def _show_config_form2(self):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        lat = self.hass.config.latitude
        longi = self.hass.config.longitude
        current_dir = os.path.dirname(os.path.realpath(__file__))
        f = open('{}/data/api.txt'.format(current_dir))
        api = f.read()
        f.close()

        da = await self.neighborhood(lat, longi, '', '', api) 

        name_servers=[]
        uuid_servers=[]
        CALC_METHODS=[]

        with open('{}/data/all_mosquee_NN.txt'.format(current_dir), "r") as f:
            distros_dict = json.load(f)
        for distro in distros_dict:
            name_servers.extend([distro["label"]])
            uuid_servers.extend([distro["uuid"]])
            CALC_METHODS.extend([distro["label"]])
        
        return self.async_show_form(
                step_id="mosques",
                data_schema=vol.Schema(
                    {
                        vol.Required(CONF_UUID): vol.In(name_servers),
                    }
                ),
                errors=self._errors,
            )


    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return MawaqitPrayerOptionsFlowHandler(config_entry)



    async def _test_credentials(self, username, password):
        """Return true if credentials is valid."""
        try:
            client = MawaqitClient('', '', '', username, password, '')
            await client.login()
            await client.close()
            return True
        except BadCredentialsException:  # pylint: disable=broad-except
            return False


    async def neighborhood(self, lat, long, username, password, api):
        """Return mosques in the neighborhood if any."""
        try:
            client = MawaqitClient(lat,long,'',username,password, api, '')
            da = await client.all_mosques_neighborhood()
            await client.close()
            return da
        except BadCredentialsException:  # pylint: disable=broad-except
            pass
        return da


    async def apimawaqit(self, username, password):
        """Return mosques in the neighborhood if any."""
        try:
            client = MawaqitClient('','','',username,password,'')
            da = await client.apimawaqit()
            await client.close()
            return da
        except BadCredentialsException:  # pylint: disable=broad-except
            pass
        return da
        
        

    async def fetch_prayer_times(self, lat, long, mosquee, username, password, api):
        """fetch prayer time"""
        try:
            client = MawaqitClient(lat,long,mosquee,username,password,api,'')
            db = await client.fetch_prayer_times()
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
            lat = self.hass.config.latitude
            longi = self.hass.config.longitude
            current_dir = os.path.dirname(os.path.realpath(__file__))  
            
            f = open('{}/data/api.txt'.format(current_dir))
            api = f.read()
            f.close()
            da = await self.neighborhood(lat, longi, '', '', api)
            
            name_servers=[]
            uuid_servers=[]
            CALC_METHODS=[]

            with open('{}/data/all_mosquee_NN.txt'.format(current_dir), "r") as f:
                distros_dict = json.load(f)
            for distro in distros_dict:
                name_servers.extend([distro["label"]])
                uuid_servers.extend([distro["uuid"]])
                CALC_METHODS.extend([distro["label"]])
                
            mosquee = user_input['calculation_method']
            index = name_servers.index(mosquee)
            mosque_id = uuid_servers[index]
            
            text_file = open('{}/data/my_mosquee_NN.txt'.format(current_dir), "w")
            json.dump(da[index], text_file)
            text_file.close()            
            
            # the mosque chosen by user
            db = await self.fetch_prayer_times(
                    lat, longi, mosque_id, '', '', api
                    )
                    
            text_file = open('{dir}/data/pray_time{name}.txt'.format(dir=current_dir, name=""), "w")
            json.dump(db, text_file)
            text_file.close()

            title = 'MAWAQIT' + ' - ' + da[index]["name"]

            data = {CONF_API_KEY: api, CONF_UUID: mosque_id, CONF_LATITUDE: lat, CONF_LONGITUDE: longi}

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                title=title,
                data=data
            )

            return self.async_create_entry(title=None, data=None)
        
        lat = self.hass.config.latitude
        longi = self.hass.config.longitude
        current_dir = os.path.dirname(os.path.realpath(__file__))
        f = open('{}/data/api.txt'.format(current_dir))
        api = f.read()
        f.close()
        da = await self.neighborhood(lat, longi, '', '', api)
        
        text_file = open('{}/data/all_mosquee_NN.txt'.format(current_dir), "w")
        json.dump(da, text_file)
        text_file.close()
        
        name_servers=[]
        uuid_servers=[]
        CALC_METHODS=[]

        with open('{}/data/all_mosquee_NN.txt'.format(current_dir), "r") as f:
            distros_dict = json.load(f)
        for distro in distros_dict:
            name_servers.extend([distro["label"]])
            uuid_servers.extend([distro["uuid"]])
            CALC_METHODS.extend([distro["label"]])
            
        options = {
            vol.Optional(
                CONF_CALC_METHOD,
                default=self.config_entry.options.get(
                    CONF_CALC_METHOD, DEFAULT_CALC_METHOD
                ),
            ): vol.In(name_servers)
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))


    async def neighborhood(self, lat, long, username, password, api):
        """Return mosques in the neighborhood if any."""
        try:
            client = MawaqitClient(lat,long,'',username,password, api, '')
            da = await  client.all_mosques_neighborhood()
            await client.close()
            return da
        except BadCredentialsException:  # pylint: disable=broad-except
            pass
        return da


    async def fetch_prayer_times(self, lat, long, mosquee, username, password, api):
        """fetch prayer time"""
        try:
            client = MawaqitClient(lat,long,mosquee,username,password,api,'')
            db = await  client.fetch_prayer_times()
            await client.close()
            return db
        except BadCredentialsException:  # pylint: disable=broad-except
            pass
        return db
