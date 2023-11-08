""" Python wrapper for the mawaqit  API """
from __future__ import annotations
import json
from datetime import date, datetime, timedelta
from types import TracebackType
from typing import Any, Dict, List, Union

import backoff
from aiohttp import ClientSession
import aiohttp

JSON = Union[Dict[str, Any], List[Dict[str, Any]]]


LOGIN_URL = f"https://mawaqit.net/api/2.0/me"


async def relogin(invocation: dict[str, Any]) -> None:
    await invocation["args"][0].login()


class NotAuthenticatedException(Exception):
    pass


class BadCredentialsException(Exception):
    pass

class NoMosqueAround(Exception):
    pass


class MawaqitClient:
    """Interface class for the mawaqit unofficial API"""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        mosquee: str,
        username: str,
        password: str,        
        token: str,
        session: ClientSession = None,
    ) -> None:
        """
        Constructor
        :param username: the username for eau-services.com
        :param password: the password for eau-services.com
        :param session: optional ClientSession
        """

        self.username = username
        self.password = password
        self.latitude = latitude
        self.longitude = longitude
        self.mosquee = mosquee
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
        max_tries=20,
        on_backoff=relogin,
    )

    async def apimawaqit(self) -> str:
        if self.token == '': 
          auth=aiohttp.BasicAuth(self.username, self.password)
          async with self.session.get(LOGIN_URL, auth=auth) as response:
            if response.status != 200:
                raise NotAuthenticatedException
            data = await response.text()

          return json.loads(data)["apiAccessToken"]
        else:
            return self.token  

    async def all_mosques_neighborhood(self):
        if self.token == '': 
            api = await self.apimawaqit()
        else: api = self.token
        #api = await self.apimawaqit()
        if len(str(api))>1:
            payload = {
                "lat": self.latitude,
                "lon": self.longitude
                }
            headers = {
                'Authorization': api,
                'Content-Type': 'application/json',
                }
            api_url0 = 'https://mawaqit.net/api/2.0/mosque/search'
    
            async with self.session.get(api_url0, params=payload, data=None, headers=headers) as response:
                if response.status != 200:
                    raise NotAuthenticatedException
                #if len(response.text()) == 0:
                #    raise NoMosqueAround
               
                data = await response.json()

                #if len(data) == 0:
                #    raise NoMosqueAround
            return data #json.loads(data)

    async def fetch_prayer_times(self) -> dict:
      if self.mosquee == '': # and len(self.all_mosques_neighborhood())>0: 
            mosque_id =   await (self.all_mosques_neighborhood())
            mosque_id = mosque_id[0]["uuid"]
      else: 
          mosque_id= self.mosquee 

      if self.token == '': 
          api_token = await self.apimawaqit()
      else: api_token = self.token

      headers = {'Content-Type': 'application/json',
             'Api-Access-Token': format(api_token)}	
      api_url_base = 'https://mawaqit.net/api/2.0/'
      api_url = api_url_base + 'mosque/' + mosque_id + '/prayer-times'
      
      async with self.session.get(api_url, data=None, headers=headers) as response:
                if response.status != 200:
                    raise NotAuthenticatedException
                data = await response.json()

      return data

    async def login(self) -> None:
        """Log into the mawaqit website."""
        auth = aiohttp.BasicAuth(self.username, self.password)
        async with await self.session.post(
            LOGIN_URL, auth = auth
        ) as response:
            if response.status != 200:
                raise BadCredentialsException
