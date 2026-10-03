"""Config flow for the Mawaqit integration."""

from collections.abc import Mapping
import logging
from typing import Any, override

from aiohttp.client_exceptions import ClientConnectorError
from mawaqit import AsyncMawaqitClient
from mawaqit.exceptions import BadCredentialsException, MawaqitException, NoMosqueAround
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME, CONF_UUID
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import mawaqit_wrapper, utils
from .const import CANNOT_CONNECT_TO_SERVER, DOMAIN, MAWAQIT_URL, WRONG_CREDENTIAL
from .types import MawaqitMosqueData

_LOGGER = logging.getLogger(__name__)

CREDENTIALS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
        ),
        vol.Required(CONF_PASSWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
        ),
    }
)


class MawaqitPrayerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for MAWAQIT."""

    VERSION = 1
    # Bumped for the legacy custom integration migration; keep VERSION at 1 so
    # entries stay loadable by the core integration.
    MINOR_VERSION = 2

    client: AsyncMawaqitClient

    def __init__(self) -> None:
        """Initialize."""
        self.mosques: dict[str, MawaqitMosqueData] = {}

    @override
    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = AsyncMawaqitClient(
                latitude=self.hass.config.latitude,
                longitude=self.hass.config.longitude,
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                session=async_get_clientsession(self.hass),
            )
            if not (errors := await self._async_login(client)):
                self.client = client
                return await self.async_step_mosques_coordinates()

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(
                CREDENTIALS_SCHEMA, user_input
            ),
            errors=errors,
            description_placeholders={"mawaqit_url": MAWAQIT_URL},
        )

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Handle a reauthentication request when the API token is rejected."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Ask for the credentials again and store the new API token."""
        errors: dict[str, str] = {}

        if user_input is not None:
            client = AsyncMawaqitClient(
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                session=async_get_clientsession(self.hass),
            )
            if not (errors := await self._async_login(client)):
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates={CONF_API_KEY: client.token},
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                CREDENTIALS_SCHEMA, user_input
            ),
            errors=errors,
        )

    async def _async_login(self, client: AsyncMawaqitClient) -> dict[str, str]:
        """Log in to MAWAQIT and return the form errors, empty on success."""
        try:
            token = await client.get_api_token()
        except BadCredentialsException:
            return {"base": WRONG_CREDENTIAL}
        except (
            ClientConnectorError,
            ConnectionError,
            TimeoutError,
            MawaqitException,
        ):
            return {"base": CANNOT_CONNECT_TO_SERVER}
        if not token:
            return {"base": CANNOT_CONNECT_TO_SERVER}
        return {}

    async def async_step_mosques_coordinates(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle mosques step."""

        errors: dict[str, str] = {}

        lat = self.hass.config.latitude
        longi = self.hass.config.longitude

        if user_input is not None:
            mosque_uuid = user_input[CONF_UUID]
            title, data_entry = utils.save_mosque(
                self.mosques[mosque_uuid].display_name,
                mosque_uuid,
                self.client.token,
                lat,
                longi,
            )
            return self.async_create_entry(title=title, data=data_entry)

        if not self.mosques:
            try:
                neighborhood_mosques = await mawaqit_wrapper.all_mosques_neighborhood(
                    self.client
                )
                if neighborhood_mosques:
                    self.mosques = {
                        mosque.uuid: mosque for mosque in neighborhood_mosques
                    }
            except NoMosqueAround:
                return self.async_abort(reason="no_mosque")
            except (
                BadCredentialsException,
                ClientConnectorError,
                ConnectionError,
                TimeoutError,
            ):
                return self.async_abort(reason="cannot_connect")

        if len(self.mosques) == 0:
            return self.async_abort(reason="no_mosque")

        return self.async_show_form(
            step_id="mosques_coordinates",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_UUID): vol.In(
                        {
                            mosque.uuid: mosque.display_name
                            for mosque in self.mosques.values()
                        }
                    ),
                }
            ),
            errors=errors,
        )
