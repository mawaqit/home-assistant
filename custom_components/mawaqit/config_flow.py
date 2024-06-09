"""Adds config flow for Mawaqit."""

import logging
import aiohttp
import os
import json
from typing import Any
import voluptuous as vol

from .const import (
    CONF_CALC_METHOD,
    DEFAULT_CALC_METHOD,
    DOMAIN,
    NAME,
    CONF_SERVER,
    USERNAME,
    PASSWORD,
    CONF_UUID,
)

from mawaqit.consts import BadCredentialsException, NoMosqueAround

from homeassistant import config_entries
from . import mawaqit_wrapper

from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_API_KEY,
    CONF_TOKEN,
)
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
        if is_another_instance():
            return self.async_abort(reason="one_instance_allowed")

        if user_input is None:
            return await self._show_config_form(user_input=None)

        username = user_input[CONF_USERNAME]
        password = user_input[CONF_PASSWORD]

        # check if the user credentials are correct (valid = True) :
        try:
            valid = await mawaqit_wrapper._test_credentials(username, password)
        # if we have an error connecting to the server :
        except aiohttp.client_exceptions.ClientConnectorError:
            self._errors["base"] = "cannot_connect_to_server"
            return await self._show_config_form(user_input)

        if valid:
            mawaqit_token = await mawaqit_wrapper.get_mawaqit_api_token(
                username, password
            )

            text_file = open("{}/data/api.txt".format(CURRENT_DIR), "w")
            text_file.write(mawaqit_token)
            text_file.close()

            try:
                nearest_mosques = await mawaqit_wrapper.all_mosques_neighborhood(
                    lat, longi, token=mawaqit_token
                )
            except NoMosqueAround:
                return self.async_abort(reason="no_mosque")

            write_all_mosques_NN_file(nearest_mosques)

            # creation of the list of mosques to be displayed in the options
            name_servers, uuid_servers, CALC_METHODS = read_all_mosques_NN_file()

            file_path = f"{CURRENT_DIR}/data/mosq_list_data"
            with open(file_path, "w+") as text_file:
                json.dump({"CALC_METHODS": CALC_METHODS}, text_file)

            return await self.async_step_mosques()

        else:  # (if not valid)
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

            nearest_mosques = await mawaqit_wrapper.all_mosques_neighborhood(
                lat, longi, token=mawaqit_token
            )

            write_my_mosque_NN_file(nearest_mosques[index])

            # the mosque chosen by user
            dict_calendar = await mawaqit_wrapper.fetch_prayer_times(
                mosque=mosque_id, token=mawaqit_token
            )

            text_file = open(
                "{dir}/data/pray_time{name}.txt".format(dir=CURRENT_DIR, name=""), "w"
            )
            json.dump(dict_calendar, text_file)
            text_file.close()

            title = "MAWAQIT" + " - " + nearest_mosques[index]["name"]
            data = {
                CONF_API_KEY: mawaqit_token,
                CONF_UUID: mosque_id,
                CONF_LATITUDE: lat,
                CONF_LONGITUDE: longi,
            }

            return self.async_create_entry(title=title, data=data)

        return await self._show_config_form2()

    async def _show_config_form(self, user_input):
        if user_input is None:
            user_input = {}
            user_input[CONF_USERNAME] = ""
            user_input[CONF_PASSWORD] = ""

        schema = vol.Schema(
            {
                vol.Required(CONF_USERNAME, default=user_input[CONF_USERNAME]): str,
                vol.Required(CONF_PASSWORD, default=user_input[CONF_PASSWORD]): str,
            }
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

        nearest_mosques = await mawaqit_wrapper.all_mosques_neighborhood(
            lat, longi, token=mawaqit_token
        )

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

            mosque = user_input[CONF_CALC_METHOD]
            index = name_servers.index(mosque)
            mosque_id = uuid_servers[index]

            mawaqit_token = get_mawaqit_token_from_file()

            try:
                nearest_mosques = await mawaqit_wrapper.all_mosques_neighborhood(
                    lat, longi, token=mawaqit_token
                )
            except NoMosqueAround:
                raise NoMosqueAround("No mosque around.")

            write_my_mosque_NN_file(nearest_mosques[index])

            # the mosque chosen by user
            dict_calendar = await mawaqit_wrapper.fetch_prayer_times(
                mosque=mosque_id, token=mawaqit_token
            )

            text_file = open(
                "{dir}/data/pray_time{name}.txt".format(dir=CURRENT_DIR, name=""), "w"
            )
            json.dump(dict_calendar, text_file)
            text_file.close()

            title = "MAWAQIT" + " - " + nearest_mosques[index]["name"]

            data = {
                CONF_API_KEY: mawaqit_token,
                CONF_UUID: mosque_id,
                CONF_LATITUDE: lat,
                CONF_LONGITUDE: longi,
            }

            self.hass.config_entries.async_update_entry(
                self.config_entry, title=title, data=data
            )
            return self.config_entry

        lat = self.hass.config.latitude
        longi = self.hass.config.longitude

        mawaqit_token = get_mawaqit_token_from_file()

        nearest_mosques = await mawaqit_wrapper.all_mosques_neighborhood(
            lat, longi, token=mawaqit_token
        )

        write_all_mosques_NN_file(nearest_mosques)

        name_servers, uuid_servers, CALC_METHODS = read_all_mosques_NN_file()

        current_mosque = read_my_mosque_NN_file()["uuid"]

        try:
            index = uuid_servers.index(current_mosque)
            default_name = name_servers[index]
        except ValueError:
            default_name = "None"

        options = {
            vol.Required(
                CONF_CALC_METHOD,
                default=default_name,
            ): vol.In(name_servers)
        }

        return self.async_show_form(step_id="init", data_schema=vol.Schema(options))


def read_all_mosques_NN_file():
    name_servers = []
    uuid_servers = []
    CALC_METHODS = []

    with open("{}/data/all_mosques_NN.txt".format(CURRENT_DIR), "r") as f:
        dict_mosques = json.load(f)
    for mosque in dict_mosques:
        distance = mosque["proximity"]
        distance = distance / 1000
        distance = round(distance, 2)
        name_servers.extend([mosque["label"] + " (" + str(distance) + "km)"])
        uuid_servers.extend([mosque["uuid"]])
        CALC_METHODS.extend([mosque["label"]])

    return name_servers, uuid_servers, CALC_METHODS


def write_all_mosques_NN_file(mosques):
    with open("{}/data/all_mosques_NN.txt".format(CURRENT_DIR), "w") as f:
        json.dump(mosques, f)


def read_my_mosque_NN_file():
    with open("{}/data/my_mosque_NN.txt".format(CURRENT_DIR), "r") as f:
        mosque = json.load(f)
    return mosque


def write_my_mosque_NN_file(mosque):
    text_file = open("{}/data/my_mosque_NN.txt".format(CURRENT_DIR), "w")
    json.dump(mosque, text_file)
    text_file.close()


def create_data_folder():
    if not os.path.exists("{}/data".format(CURRENT_DIR)):
        os.makedirs("{}/data".format(CURRENT_DIR))


def get_mawaqit_token_from_file():
    f = open("{}/data/api.txt".format(CURRENT_DIR))
    mawaqit_token = f.read()
    f.close()
    return mawaqit_token


def is_data_folder_empty():
    return not os.listdir("{}/data".format(CURRENT_DIR))


def is_another_instance() -> bool:
    if is_data_folder_empty():
        return False
    files_in_directory = os.listdir(f"{CURRENT_DIR}/data")
    # Check if the data folder contains only one file named api.txt and no other files
    if len(files_in_directory) == 1 and files_in_directory[0] == "api.txt":
        return False
    return True
