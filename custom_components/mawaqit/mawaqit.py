"""Python Wrapper to access the MAWAQIT API."""

from __future__ import annotations
import json
from datetime import date, datetime, timedelta
from types import TracebackType
from typing import Any, Dict, List, Union

import backoff

import aiohttp
from aiohttp import ClientSession

JSON = Union[Dict[str, Any], List[Dict[str, Any]]]

API_URL_BASE = "https://mawaqit.net/api/2.0"
LOGIN_URL = f"{API_URL_BASE}/me"
SEARCH_MOSQUES_URL = f"{API_URL_BASE}/mosque/search"


def prayer_times_url(mosque_id: int) -> str:
    return f"{API_URL_BASE}/mosque/{mosque_id}/prayer-times"


MAX_LOGIN_RETRIES = 20


class NotAuthenticatedException(Exception):
    pass


class BadCredentialsException(Exception):
    pass


class NoMosqueAround(Exception):
    pass


class MissingCredentials(Exception):
    pass


async def relogin(invocation: dict[str, Any]) -> None:
    await invocation["args"][0].login()


class MawaqitClient:
    """Interface class for the MAWAQIT official API."""
    def __init__(
            self,
            latitude: float = None,
            longitude: float = None,
            mosque: str = None,
            username: str = None,
            password: str = None,
            token: str = None,
            session: ClientSession = None,
    ) -> None:
        
        self.username = username
        self.password = password
        self.latitude = latitude
        self.longitude = longitude
        self.mosque = mosque
        self.token = token
        self.session = session if session else ClientSession()

    async def __aenter__(self) -> MawaqitClient:
        return self

    async def __aexit__(
            self,
            exc_type: type[BaseException] | None,
            exc_value: BaseException | None,
            traceback: TracebackType | None,
    ) -> None:
        await self.close()

    async def close(self) -> None:
        """Close the session."""
        await self.session.close()

    @backoff.on_exception(
        backoff.expo,
        NotAuthenticatedException,
        max_tries=MAX_LOGIN_RETRIES,
        on_backoff=relogin
    )
    async def get_api_token(self) -> str:
        """Get the MAWAQIT API token."""

        if self.token is None:
            await self.login()

        return self.token

    async def all_mosques_neighborhood(self):
        """Get the five nearest mosques from the Client coordinates.
        Returns a list of dicts with info on the mosques."""
        
        if (self.latitude is None) or (self.longitude is None):
            raise MissingCredentials("Please provide a latitude and a longitude in your MawaqitClient object.")

        payload = {
            "lat": self.latitude,
            "lon": self.longitude
            }
        headers = {
            'Authorization': self.token,
            'Content-Type': 'application/json',
            }

        endpoint_url = SEARCH_MOSQUES_URL

        async with self.session.get(endpoint_url, params=payload, data=None, headers=headers) as response:
            if response.status != 200:
                raise NotAuthenticatedException("Authentication failed. Please check your MAWAQIT credentials.")
            data = await response.json()
            
        if len(data) == 0:
            raise NoMosqueAround("No mosque found around your location. Please check your coordinates.")

        return data

    async def fetch_prayer_times(self) -> dict:
        """Fetch the prayer times calendar for self.mosque,
        Returns a dict with info on the mosque and the year-calendar prayer times."""

        if self.mosque is None:
            mosque_id = await self.all_mosques_neighborhood()
            mosque_id = mosque_id[0]["uuid"]
        else:
            mosque_id = self.mosque

        headers = {'Content-Type': 'application/json',
                   'Api-Access-Token': format(self.token)}

        endpoint_url = prayer_times_url(mosque_id)

        async with self.session.get(endpoint_url, data=None, headers=headers) as response:
            if response.status != 200:
                raise NotAuthenticatedException("Authentication failed. Please retry. Response.status : " + str(response.status))
            data = await response.json()

        return data

    async def login(self) -> None:
        """Log into the MAWAQIT website."""
        
        if (self.username is None) or (self.password is None):
            raise MissingCredentials("Please provide a MAWAQIT login and password.")
        
        auth = aiohttp.BasicAuth(self.username, self.password)

        endpoint_url = LOGIN_URL

        async with await self.session.post(endpoint_url, auth=auth) as response:
            if response.status == 401:
                raise BadCredentialsException("Authentication failed. Please check your MAWAQIT credentials.")
            elif response.status != 200:
                raise NotAuthenticatedException("Authentication failed. Please retry.")

            data = await response.text()

            self.token = json.loads(data)["apiAccessToken"]

        
