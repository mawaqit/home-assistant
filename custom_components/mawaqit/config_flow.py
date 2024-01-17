"""Adds config flow for Mawaqit."""
import logging
import aiohttp
import os
import json
from typing import Any
import voluptuous as vol

from .const import  CONF_CALC_METHOD, DEFAULT_CALC_METHOD, DOMAIN, NAME, CONF_SERVER, USERNAME, PASSWORD, CONF_UUID
from .mawaqit import MawaqitClient, BadCredentialsException, NoMosqueAround

from homeassistant import config_entries

from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_PASSWORD, CONF_USERNAME, CONF_API_KEY, CONF_TOKEN
import homeassistant.helpers.config_validation as cv
from homeassistant.data_entry_flow import FlowResult


_LOGGER = logging.getLogger(__name__)

CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))


class MawaqitPrayerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for MAWAQIT."""

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
        create_data_folder()

        # if the data folder is empty, we can continue the configuration
        # otherwise, we abort the configuration because that means that the user has already configured an entry.
        if not is_data_folder_empty():
            return self.async_abort(reason="one_instance_allowed")

        if user_input is None:
            return await self._show_config_form(user_input=None)
        
        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        # check if the user credentials are correct (valid = True) :
        try:
            valid = await self._test_credentials(username, password)
        # if we have an error connecting to the server :
        except aiohttp.client_exceptions.ClientConnectorError:
            self._errors["base"] = "cannot_connect_to_server"
            return await self._show_config_form(user_input)

        if valid:
            mawaqit_token = await self.get_mawaqit_api_token(username, password)

            text_file = open('{}/data/api.txt'.format(CURRENT_DIR), "w")
            text_file.write(mawaqit_token)
            text_file.close()

            try:
                nearest_mosques = await self.all_mosques_neighborhood(lat, longi, token=mawaqit_token)
            except NoMosqueAround:
                return self.async_abort(reason="no_mosque")
            
            write_all_mosques_NN_file(nearest_mosques)
            
            # creation of the list of mosques to be displayed in the options
            name_servers, uuid_servers, CALC_METHODS = read_all_mosques_NN_file()
            
            text_file = open('{}/mosq_list.py'.format(CURRENT_DIR), "w")
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

        mawaqit_token = get_mawaqit_token_from_file()

        if user_input is not None:
            
            name_servers, uuid_servers, CALC_METHODS = read_all_mosques_NN_file()
                
            mosque = user_input[CONF_UUID]
            index = name_servers.index(mosque)
            mosque_id = uuid_servers[index]

            nearest_mosques = await self.all_mosques_neighborhood(lat, longi, token=mawaqit_token)                                                

            write_my_mosque_NN_file(nearest_mosques[index])
            
            # the mosque chosen by user
            dict_calendar = await self.fetch_prayer_times(mosque=mosque_id, token=mawaqit_token)
                    
            text_file = open('{dir}/data/pray_time{name}.txt'.format(dir=CURRENT_DIR, name=""), "w")
            json.dump(dict_calendar, text_file)
            text_file.close()

            title = 'MAWAQIT' + ' - ' + nearest_mosques[index]["name"]
            data = {CONF_API_KEY: mawaqit_token, CONF_UUID: mosque_id, CONF_LATITUDE: lat, CONF_LONGITUDE: longi}
            
            return self.async_create_entry(title=title, data=data)
        
        return await self._show_config_form2()
        
        
    async def _show_config_form(self, user_input):

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
        
        
    async def _show_config_form2(self):
        """Show the configuration form to edit location data."""
        lat = self.hass.config.latitude
        longi = self.hass.config.longitude

        mawaqit_token = get_mawaqit_token_from_file()


        nearest_mosques = await self.all_mosques_neighborhood(lat, longi, token=mawaqit_token)

        write_all_mosques_NN_file(nearest_mosques)

        name_servers, uuid_servers, CALC_METHODS = read_all_mosques_NN_file()
        
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
        """Return True if the MAWAQIT credentials is valid."""
        try:
            client = MawaqitClient(username=username, password=password)
            await client.login()
            await client.close()
            return True
        except BadCredentialsException:
            return False
        

    async def get_mawaqit_api_token(self, username, password):
        """Return the MAWAQIT API token."""
        try:
            client = MawaqitClient(username=username, password=password)
            token = await client.get_api_token()
            await client.close()
        except BadCredentialsException:
            pass

        return token


    async def all_mosques_neighborhood(self, latitude, longitude, mosque = None, username = None, password = None, token = None):
        """Return mosques in the neighborhood if any. Returns a list of dicts."""
        try:
            client = MawaqitClient(latitude, longitude, mosque, username, password, token, session=None)
            await client.get_api_token()
            nearest_mosques = await client.all_mosques_neighborhood()
            await client.close()
        except BadCredentialsException as e:
            _LOGGER.error("Error on retrieving mosques: %s", e)

        return nearest_mosques
        

    async def fetch_prayer_times(self, latitude = None, longitude = None, mosque = None, username = None, password = None, token = None):
        """Get prayer times from the MAWAQIT API. Returns a dict."""
        
        try:
            client = MawaqitClient(latitude, longitude, mosque, username, password, token, session=None)
            await client.get_api_token()
            dict_calendar = await client.fetch_prayer_times()
            await client.close()
        except BadCredentialsException:
            pass

        return dict_calendar


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
            
            name_servers, uuid_servers, CALC_METHODS = read_all_mosques_NN_file()
                
            mosque = user_input['calculation_method']
            index = name_servers.index(mosque)
            mosque_id = uuid_servers[index]

            mawaqit_token = get_mawaqit_token_from_file()

            try:
                nearest_mosques = await self.all_mosques_neighborhood(lat, longi, token=mawaqit_token)
            except NoMosqueAround:
                # TODO
                raise NoMosqueAround("No mosque around.")

            write_my_mosque_NN_file(nearest_mosques[index])
            
            # the mosque chosen by user
            dict_calendar = await self.fetch_prayer_times(mosque=mosque_id, token=mawaqit_token)
                    
            text_file = open('{dir}/data/pray_time{name}.txt'.format(dir=CURRENT_DIR, name=""), "w")
            json.dump(dict_calendar, text_file)
            text_file.close()

            title = 'MAWAQIT' + ' - ' + nearest_mosques[index]["name"]

            data = {CONF_API_KEY: mawaqit_token, CONF_UUID: mosque_id, CONF_LATITUDE: lat, CONF_LONGITUDE: longi}

            self.hass.config_entries.async_update_entry(
                self.config_entry,
                title=title,
                data=data
            )

            return self.async_create_entry(title=None, data=None)
        
        lat = self.hass.config.latitude
        longi = self.hass.config.longitude

        mawaqit_token = get_mawaqit_token_from_file()

        nearest_mosques = await self.all_mosques_neighborhood(lat, longi, token=mawaqit_token)
        
        write_all_mosques_NN_file(nearest_mosques)
        
        name_servers, uuid_servers, CALC_METHODS = read_all_mosques_NN_file()
            
        options = {
            vol.Optional(
                CONF_CALC_METHOD,
                default=self.config_entry.options.get(
                    CONF_CALC_METHOD, DEFAULT_CALC_METHOD
                ),
            ): vol.In(name_servers)
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))


    async def all_mosques_neighborhood(self, latitude, longitude, mosque = None, username = None, password = None, token = None):
        """Return mosques in the neighborhood if any. Returns a list of dicts."""
        return await MawaqitPrayerFlowHandler.all_mosques_neighborhood(self, latitude, longitude, mosque, username, password, token)


    async def fetch_prayer_times(self, latitude = None, longitude = None, mosque = None, username = None, password = None, token = None):
        """Get prayer times from the MAWAQIT API. Returns a dict."""
        return await MawaqitPrayerFlowHandler.fetch_prayer_times(self, latitude, longitude, mosque, username, password, token)
    

def read_all_mosques_NN_file():
    name_servers = []
    uuid_servers = []
    CALC_METHODS = []

    with open('{}/data/all_mosques_NN.txt'.format(CURRENT_DIR), "r") as f:
        dict_mosques = json.load(f)
    for mosque in dict_mosques:
        distance = mosque["proximity"]
        distance = distance/1000
        distance = round(distance, 2)
        name_servers.extend([mosque["label"] + ' (' + str(distance) + 'km)'])
        uuid_servers.extend([mosque["uuid"]])
        CALC_METHODS.extend([mosque["label"]])

    return name_servers, uuid_servers, CALC_METHODS

def write_all_mosques_NN_file(mosques):
    with open('{}/data/all_mosques_NN.txt'.format(CURRENT_DIR), "w") as f:
        json.dump(mosques, f)

def write_my_mosque_NN_file(mosque):
    text_file = open('{}/data/my_mosque_NN.txt'.format(CURRENT_DIR), "w")
    json.dump(mosque, text_file)
    text_file.close()

def create_data_folder():
    if not os.path.exists('{}/data'.format(CURRENT_DIR)):
        os.makedirs('{}/data'.format(CURRENT_DIR))

def get_mawaqit_token_from_file():
    f = open('{}/data/api.txt'.format(CURRENT_DIR))
    mawaqit_token = f.read()
    f.close()
    return mawaqit_token

def is_data_folder_empty():
    return not os.listdir('{}/data'.format(CURRENT_DIR))
