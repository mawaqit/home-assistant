"""Config flow for Mawaqit Prayer Times integration."""
import voluptuous as vol
import os
import requests
from requests import get
import json

from homeassistant import config_entries
from homeassistant.core import callback

# pylint: disable=unused-import
from .const import DOMAIN, NAME, CONF_SERVER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME, CONF_API_KEY, CONF_TOKEN

name_servers = ["connect to choose a mosque"]


class MawaqitPrayerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Mawaqit Prayer config flow."""

    VERSION = 1
    """CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL"""
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL
    
    
    def __init__(self):
        """Initialize."""
        self._errors = {}
        
        


    
    

    def _show_setup_form(self, user_input=None, errors=None):
        """Show the setup form to the user."""

        if user_input is None:
            user_input = {}

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME, default=user_input.get(CONF_USERNAME, "Mawaqit login")
                    ): str,
                    vol.Required(
                        CONF_PASSWORD, default=user_input.get(CONF_PASSWORD, "")
                    ): str,
                    vol.Optional(
                        CONF_SERVER, default="connect to choose mosque"): vol.In(name_servers),
                }
            ),
            errors=errors or {},
        )




    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        global name_servers
        global uuid_servers
        name_servers = ["connect to choose mosque"]
        uuid_servers = ["none"]
        if user_input is None:
            return self._show_setup_form(user_input, None)

        

        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]
        server = user_input[CONF_SERVER]
        
        url = 'https://mawaqit.net/api/2.0/me'
        response = get(url, auth=(username, password))
        
        current_dir = os.path.dirname(os.path.realpath(__file__))
        if not os.path.exists('{}/data'.format(current_dir)):
        	os.makedirs('{}/data'.format(current_dir))
        text_file = open('{}/data/api.txt'.format(current_dir), "w")
        n = text_file.write(response.json()["apiAccessToken"])
        text_file.close()
        
        
        api=response.json()["apiAccessToken"]
        
        api_url_base = "https://mawaqit.net/api/2.0/"
        headers = {'Content-Type': 'application/json',
             'Api-Access-Token': format(api)}	
             
        lat = self.hass.config.latitude
        longi = self.hass.config.longitude


        params = {
            "lat": lat,
            "lon": longi,
        }
        api_url0 = '{0}/mosque/search'.format(api_url_base)
        response0 = requests.get(api_url0, params=params, headers=headers)
        if not bool(response0.json()):
        	return self.async_abort(reason="no_mosque")
        		
        else:
        	all_mosques = response0.text
      
       
        
        
        text_file = open('{}/data/all_mosquee.txt'.format(current_dir), "w")
        n = text_file.write(all_mosques)
        text_file.close()

        if server == "connect to choose mosque":
        	name_servers=[]
        	uuid_servers=[]
        	with open('{}/data/all_mosquee.txt'.format(current_dir), "r") as f:
        		distros_dict = json.load(f)
        	for distro in distros_dict:
        		name_servers.extend([distro['name']])
        		uuid_servers.extend([distro['uuid']])
        	return self._show_setup_form(user_input, None)
        	username = user_input[CONF_USERNAME]
        	password = user_input[CONF_PASSWORD]
        	server = user_input[CONF_SERVER]
        
        
        indexes = [index for index in range(len(name_servers)) if name_servers[index] == server]


        		
        mosque_name=server
        with open('{}/data/all_mosquee.txt'.format(current_dir), "r") as f:
        	distros_dict = json.load(f)
        for entry in distros_dict:
        	if mosque_name == entry ['name']:
        		mosque_id = entry ['uuid']
        		mosque_image = entry ['image']
        my_gen = (item for item in distros_dict if item['name'] == mosque_name)
        for item in my_gen:
        	print(item)
        	with open('{}/data/my_mosquee.txt'.format(current_dir), "w") as outfile:
        		json.dump(item, outfile)
 
        		
        current_dir = os.path.dirname(os.path.realpath(__file__))
        text_file = open('{}/data/mosquee.txt'.format(current_dir), "w")
        n = text_file.write(mosque_id)
        text_file.close()
        
        if "http" in mosque_image:
        	hassioDirectory = os.getcwd()
        	r = requests.get(mosque_image, allow_redirects=True)
        	if not os.path.exists('{}/www/mawaqit'.format(hassioDirectory)):
        		os.makedirs('{}/www/mawaqit'.format(hassioDirectory))
        	open('{}/www/mawaqit/image.jpg'.format(hassioDirectory), 'wb').write(r.content)
        
        


        if not mosque_id:
            return self.async_abort(reason="no_mosque")
              
        
        
        if self._async_current_entries():
            return self.async_abort(reason="one_instance_allowed")

        if user_input is None:
            return self.async_show_form(step_id="user")

        
        return self.async_create_entry(
            title=mosque_name,
            data={
                CONF_USERNAME: username,
                CONF_PASSWORD: password,
                CONF_API_KEY: api,
                CONF_TOKEN: mosque_name,
            },
        )
    

    async def async_step_import(self, import_config):
        """Import from config."""
        return await self.async_step_user(user_input=import_config)



