"""Provides a wrapper for interacting with the MAWAQIT API.

It includes functions for testing credentials, retrieving API tokens,
fetching prayer times, and finding mosques in the neighborhood.
"""

import logging

import aiohttp
from mawaqit import AsyncMawaqitClient
from mawaqit.consts import BadCredentialsException, NotAuthenticatedException

_LOGGER = logging.getLogger(__name__)

MAWAQIT_API_BASE = "https://mawaqit.net/api/2.0"


async def _create_authenticated_client(
    latitude=None, longitude=None, mosque=None, username=None, password=None, token=None
):
    """Create and authenticate an AsyncMawaqitClient.

    When credentials (username + password) are available, creates a client
    WITHOUT the old token so that get_api_token() is forced to call login()
    and obtain a fresh token. The library skips login() when a token is
    already set in the constructor.

    When only a token is available (no credentials), creates a client with
    the token as-is.

    Returns the authenticated client (caller must close it).
    """
    if username and password:
        _LOGGER.debug("Creating client with credentials, will perform fresh login")
        client = AsyncMawaqitClient(
            latitude=latitude,
            longitude=longitude,
            mosque=mosque,
            username=username,
            password=password,
        )
        try:
            await client.get_api_token()  # token is None → calls login() → gets fresh token
            _LOGGER.debug("Fresh login succeeded, token obtained")
        except Exception:
            await client.close()
            raise
    else:
        _LOGGER.debug("Creating client with existing token only (no credentials)")
        client = AsyncMawaqitClient(
            latitude=latitude,
            longitude=longitude,
            mosque=mosque,
            token=token,
        )
    return client


async def test_credentials(username, password):
    """Return True if the MAWAQIT credentials is valid."""
    client = None
    try:
        client = AsyncMawaqitClient(username=username, password=password)
        await client.login()
    except (BadCredentialsException, NotAuthenticatedException):
        _LOGGER.error("Error : Bad Credentials")
        return False
    except (ConnectionError, TimeoutError) as e:
        _LOGGER.error("Network-related error: %s", e)
        return False
    finally:
        if client is not None:
            await client.close()

    return True


async def get_mawaqit_api_token(username, password):
    """Return the MAWAQIT API token."""
    client = None
    token = None
    try:
        client = AsyncMawaqitClient(username=username, password=password)
        token = await client.get_api_token()
    except (BadCredentialsException, NotAuthenticatedException) as e:
        _LOGGER.error("Error on retrieving API Token: %s", e)
    except (ConnectionError, TimeoutError) as e:
        _LOGGER.error("Network-related error: %s", e)
    finally:
        if client is not None:
            await client.close()
    return token


async def all_mosques_neighborhood(
    latitude, longitude, mosque=None, username=None, password=None, token=None
):
    """Return mosques in the neighborhood if any. Returns a list of dicts."""
    client = None
    nearest_mosques = []
    try:
        client = await _create_authenticated_client(
            latitude=latitude,
            longitude=longitude,
            mosque=mosque,
            username=username,
            password=password,
            token=token,
        )
        nearest_mosques = await client.all_mosques_neighborhood()
    except (BadCredentialsException, NotAuthenticatedException) as e:
        _LOGGER.error("Error on retrieving mosques: %s", e)
    except (ConnectionError, TimeoutError) as e:
        _LOGGER.error("Network-related error: %s", e)
    finally:
        if client is not None:
            await client.close()

    return nearest_mosques


async def all_mosques_by_keyword(
    search_keyword, username=None, password=None, token=None
):
    """Return mosques in the neighborhood if any. Returns a list of dicts."""
    client = None
    search_mosques = []
    try:
        client = await _create_authenticated_client(
            username=username,
            password=password,
            token=token,
        )

        if search_keyword is not None:
            search_mosques = await client.fetch_mosques_by_keyword(search_keyword)

    except (BadCredentialsException, NotAuthenticatedException) as e:
        _LOGGER.error("Error on retrieving mosques: %s", e)
    except (ConnectionError, TimeoutError) as e:
        _LOGGER.error("Network-related error: %s", e)
    finally:
        if client is not None:
            await client.close()

    return search_mosques


async def _fetch_prayer_times_direct(mosque_id, token):
    """Fetch prayer times directly via HTTP using the Authorization header.

    The mawaqit library v1.0.0 uses 'Api-Access-Token' header for this
    endpoint, but the MAWAQIT API now requires the 'Authorization' header
    (the same format used for mosque search). This function bypasses the
    library and makes the request directly.
    """
    url = f"{MAWAQIT_API_BASE}/mosque/{mosque_id}/prayer-times"
    headers = {
        "Authorization": f"{token}",
        "Content-Type": "application/json",
    }
    timeout = aiohttp.ClientTimeout(total=30)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    _LOGGER.error(
                        "Direct prayer times fetch failed: status=%s for mosque %s",
                        response.status,
                        mosque_id,
                    )
                    return None
                return await response.json()
    except aiohttp.ClientError as err:
        _LOGGER.error(
            "Direct prayer times fetch failed for mosque %s: %s", mosque_id, err
        )
        return None


async def fetch_prayer_times(
    latitude=None, longitude=None, mosque=None, username=None, password=None, token=None
):
    """Get prayer times from the MAWAQIT API. Returns a dict."""
    client = None
    dict_calendar = None
    try:
        client = await _create_authenticated_client(
            latitude=latitude,
            longitude=longitude,
            mosque=mosque,
            username=username,
            password=password,
            token=token,
        )

        # First try the library's fetch_prayer_times
        try:
            dict_calendar = await client.fetch_prayer_times()
        except NotAuthenticatedException:
            # The library uses 'Api-Access-Token' header which the API may
            # no longer accept. Fall back to direct HTTP with 'Authorization'.
            mosque_id = mosque if mosque else client.mosque
            _LOGGER.warning(
                "Library fetch_prayer_times failed with 401, "
                "retrying with Authorization header for mosque %s",
                mosque_id,
            )
            dict_calendar = await _fetch_prayer_times_direct(mosque_id, client.token)

    except (BadCredentialsException, NotAuthenticatedException) as e:
        _LOGGER.error("Error on retrieving prayer times: %s", e)
    except (ConnectionError, TimeoutError) as e:
        _LOGGER.error("Network-related error: %s", e)
    finally:
        if client is not None:
            await client.close()

    return dict_calendar
