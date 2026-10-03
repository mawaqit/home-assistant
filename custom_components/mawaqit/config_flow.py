"""Config flow for the Mawaqit integration."""

from collections.abc import Mapping
import logging
from typing import Any, override

from aiohttp.client_exceptions import ClientConnectorError
from mawaqit import AsyncMawaqitClient
from mawaqit.exceptions import (
    BadCredentialsException,
    MawaqitException,
    NoMosqueAround,
    NoMosqueFound,
)
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_API_KEY, CONF_PASSWORD, CONF_USERNAME, CONF_UUID
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from . import mawaqit_wrapper, utils
from .const import (
    CANNOT_CONNECT_TO_SERVER,
    CONF_KEYWORD,
    DOMAIN,
    MAWAQIT_URL,
    MOSQUES_PER_PAGE,
    NEW_SEARCH,
    NEXT_PAGE,
    NO_MOSQUE_AROUND,
    NO_MOSQUE_FOUND,
    PREVIOUS_PAGE,
    WRONG_CREDENTIAL,
)
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

KEYWORD_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_KEYWORD): selector.TextSelector(
            selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
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
        self.keyword = ""
        self.page = 1
        self.pages: dict[int, list[MawaqitMosqueData]] = {}
        self.no_mosque_around = False

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
                return await self.async_step_search_method()

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

    async def async_step_search_method(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Let the user search the mosques around their location or by keyword."""
        menu_options = ["keyword_search"]
        if not self.no_mosque_around:
            menu_options.insert(0, "mosques_coordinates")
        return self.async_show_menu(step_id="search_method", menu_options=menu_options)

    async def async_step_mosques_coordinates(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Handle mosques step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            return self._create_mosque_entry(user_input[CONF_UUID])

        # Always fetched: self.mosques may hold keyword results by now.
        try:
            neighborhood_mosques = await mawaqit_wrapper.all_mosques_neighborhood(
                self.client
            )
        except NoMosqueAround:
            neighborhood_mosques = []
        except (
            BadCredentialsException,
            ClientConnectorError,
            ConnectionError,
            TimeoutError,
        ):
            return self.async_abort(reason="cannot_connect")

        if not neighborhood_mosques:
            self.no_mosque_around = True
            return self._show_keyword_search_form({"base": NO_MOSQUE_AROUND})
        self.mosques = {mosque.uuid: mosque for mosque in neighborhood_mosques}

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

    async def async_step_keyword_search(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Ask for a keyword and search the matching mosques."""
        errors: dict[str, str] = {}

        if user_input is not None:
            keyword = user_input.get(CONF_KEYWORD, "").strip()
            if not keyword:
                return await self.async_step_search_method()
            self.keyword = keyword
            self.pages = {}
            errors = await self._async_load_page(1)
            if not errors and not self.pages[1]:
                errors["base"] = NO_MOSQUE_FOUND
            if not errors:
                self.page = 1
                return await self.async_step_keyword_results()

        return self._show_keyword_search_form(errors, user_input)

    async def async_step_keyword_results(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show a page of the keyword results and let the user pick a mosque."""
        errors: dict[str, str] = {}

        if user_input is not None:
            choice = user_input[CONF_UUID]
            # Both pages are cached: they are only offered once loaded.
            if choice == NEXT_PAGE:
                self.page += 1
            elif choice == PREVIOUS_PAGE:
                self.page -= 1
            elif choice == NEW_SEARCH:
                return self._show_keyword_search_form({}, {CONF_KEYWORD: self.keyword})
            else:
                return self._create_mosque_entry(choice)

        self.mosques = {mosque.uuid: mosque for mosque in self.pages[self.page]}
        # The API returns no total: prefetch the next page to offer it only when
        # it has mosques.
        if len(self.mosques) == MOSQUES_PER_PAGE:
            errors = await self._async_load_page(self.page + 1)

        options = [
            selector.SelectOptionDict(value=mosque.uuid, label=mosque.display_name)
            for mosque in self.mosques.values()
        ]
        if self.page > 1:
            options.append(
                selector.SelectOptionDict(value=PREVIOUS_PAGE, label=PREVIOUS_PAGE)
            )
        if self.pages.get(self.page + 1):
            options.append(selector.SelectOptionDict(value=NEXT_PAGE, label=NEXT_PAGE))
        options.append(selector.SelectOptionDict(value=NEW_SEARCH, label=NEW_SEARCH))

        return self.async_show_form(
            step_id="keyword_results",
            data_schema=vol.Schema(
                {
                    # Mosque labels have no translation, so the frontend keeps them.
                    vol.Required(CONF_UUID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=options,
                            mode=selector.SelectSelectorMode.LIST,
                            translation_key="keyword_results",
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={"keyword": self.keyword, "page": str(self.page)},
        )

    async def _async_load_page(self, page: int) -> dict[str, str]:
        """Cache a page of the keyword results and return the form errors."""
        if page in self.pages:
            return {}
        try:
            mosques = await mawaqit_wrapper.fetch_mosques_by_keyword(
                self.client, self.keyword, page
            )
        except NoMosqueFound:
            mosques = []
        except (
            ClientConnectorError,
            ConnectionError,
            TimeoutError,
            MawaqitException,
        ):
            return {"base": CANNOT_CONNECT_TO_SERVER}
        self.pages[page] = mosques
        return {}

    def _show_keyword_search_form(
        self, errors: dict[str, str], user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Show the keyword search form."""
        return self.async_show_form(
            step_id="keyword_search",
            data_schema=self.add_suggested_values_to_schema(KEYWORD_SCHEMA, user_input),
            errors=errors,
        )

    def _create_mosque_entry(self, mosque_uuid: str) -> config_entries.ConfigFlowResult:
        """Create the config entry for the chosen mosque."""
        title, data_entry = utils.save_mosque(
            self.mosques[mosque_uuid].display_name,
            mosque_uuid,
            self.client.token,
            self.hass.config.latitude,
            self.hass.config.longitude,
        )
        return self.async_create_entry(title=title, data=data_entry)
