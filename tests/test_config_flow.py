"""Tests for the Mawaqit integration's config flow in Home Assistant."""

from unittest.mock import AsyncMock, MagicMock, patch

from aiohttp.client_exceptions import ClientConnectorError
from mawaqit.exceptions import (
    BadCredentialsException,
    MawaqitException,
    NoMosqueAround,
    NoMosqueFound,
)
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.mawaqit import config_flow
from custom_components.mawaqit.const import (
    CANNOT_CONNECT_TO_SERVER,
    CONF_KEYWORD,
    DOMAIN,
    MOSQUES_PER_PAGE,
    NEW_SEARCH,
    NEXT_PAGE,
    NO_MOSQUE_AROUND,
    NO_MOSQUE_FOUND,
    PREVIOUS_PAGE,
    WRONG_CREDENTIAL,
)
from custom_components.mawaqit.types import MawaqitMosqueData
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import (
    CONF_API_KEY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PASSWORD,
    CONF_USERNAME,
    CONF_UUID,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import MOCK_TOKEN, MOCK_UUID

USER_INPUT = {CONF_USERNAME: "user", CONF_PASSWORD: "pass"}
NEW_TOKEN = "new-api-token"


@pytest.fixture
def mock_client() -> MagicMock:
    """Return a mocked AsyncMawaqitClient with a successful login."""
    client = MagicMock()
    client.token = MOCK_TOKEN
    client.get_api_token = AsyncMock(return_value=MOCK_TOKEN)
    client.all_mosques_neighborhood = AsyncMock(return_value=[])
    client.fetch_mosques_by_keyword = AsyncMock(return_value=[])
    return client


def _flow(hass: HomeAssistant) -> config_flow.MawaqitPrayerFlowHandler:
    """Return a flow handler bound to hass."""
    flow = config_flow.MawaqitPrayerFlowHandler()
    flow.hass = hass
    return flow


def _keyword_mosques(count: int, first: int = 0) -> list[dict]:
    """Return raw keyword search results, without proximity."""
    return [
        {
            "uuid": f"mosque-{index}",
            "name": f"Mosque{index}",
            "label": f"Mosque{index}-label",
            "latitude": 48,
            "longitude": 2,
            "localisation": f"City{index}",
        }
        for index in range(first, first + count)
    ]


def _uuids(mosques: list[dict]) -> list[str]:
    """Return the uuids of raw mosques."""
    return [mosque["uuid"] for mosque in mosques]


def _options(result: data_entry_flow.FlowResult) -> list[str]:
    """Return the values offered by the mosque selector of a form."""
    assert "data_schema" in result and result["data_schema"] is not None
    options = result["data_schema"].schema[CONF_UUID].config["options"]
    return [option["value"] for option in options]


async def _login(hass: HomeAssistant, mock_client: MagicMock) -> str:
    """Start a user flow, log in and return the flow id at the search menu."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.mawaqit.config_flow.AsyncMawaqitClient",
        return_value=mock_client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
    assert result.get("type") == data_entry_flow.FlowResultType.MENU
    return result["flow_id"]


async def _search_keyword(
    hass: HomeAssistant, mock_client: MagicMock, keyword: str = "Paris"
) -> data_entry_flow.FlowResult:
    """Log in, choose the keyword search and submit the keyword."""
    flow_id = await _login(hass, mock_client)
    result = await hass.config_entries.flow.async_configure(
        flow_id, {"next_step_id": "keyword_search"}
    )
    assert result.get("step_id") == "keyword_search"
    return await hass.config_entries.flow.async_configure(
        flow_id, {CONF_KEYWORD: keyword}
    )


# ---------------------------------------------------------------------------
# USER FORM
# ---------------------------------------------------------------------------


async def test_show_form_user_no_input_reopens_form(hass: HomeAssistant) -> None:
    """Test that the form is served with no input."""
    result = await _flow(hass).async_step_user(user_input=None)

    assert result.get("type") == data_entry_flow.FlowResultType.FORM
    assert result.get("step_id") == "user"


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (BadCredentialsException, WRONG_CREDENTIAL),
        (MawaqitException, CANNOT_CONNECT_TO_SERVER),
        (ConnectionError, CANNOT_CONNECT_TO_SERVER),
        (TimeoutError, CANNOT_CONNECT_TO_SERVER),
        (
            ClientConnectorError(MagicMock(), MagicMock()),
            CANNOT_CONNECT_TO_SERVER,
        ),
    ],
    ids=[
        "bad_credentials",
        "mawaqit_error",
        "connection_error",
        "timeout",
        "client_connector_error",
    ],
)
async def test_async_step_user_login_errors(
    hass: HomeAssistant,
    mock_client: MagicMock,
    side_effect: Exception | type[Exception],
    expected_error: str,
) -> None:
    """Test the user step surfaces login failures as form errors."""
    mock_client.get_api_token.side_effect = side_effect

    with patch(
        "custom_components.mawaqit.config_flow.AsyncMawaqitClient",
        return_value=mock_client,
    ):
        result = await _flow(hass).async_step_user(USER_INPUT)

    assert result.get("type") == data_entry_flow.FlowResultType.FORM
    assert result.get("step_id") == "user"
    errors = result.get("errors")
    assert errors is not None and errors["base"] == expected_error


async def test_async_step_user_no_token_returned(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Test the user step when the API returns no token."""
    mock_client.get_api_token.return_value = None

    with patch(
        "custom_components.mawaqit.config_flow.AsyncMawaqitClient",
        return_value=mock_client,
    ):
        result = await _flow(hass).async_step_user(USER_INPUT)

    assert result.get("type") == data_entry_flow.FlowResultType.FORM
    errors = result.get("errors")
    assert errors is not None and errors["base"] == CANNOT_CONNECT_TO_SERVER


async def test_async_step_user_valid_credentials(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Test the user step with valid credentials shows the search menu."""
    with patch(
        "custom_components.mawaqit.config_flow.AsyncMawaqitClient",
        return_value=mock_client,
    ):
        result = await _flow(hass).async_step_user(USER_INPUT)

    assert result.get("type") == data_entry_flow.FlowResultType.MENU
    assert result.get("step_id") == "search_method"
    assert result.get("menu_options") == ["mosques_coordinates", "keyword_search"]
    mock_client.all_mosques_neighborhood.assert_not_awaited()


@pytest.mark.usefixtures("mock_setup_entry")
async def test_search_around_location_creates_entry(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_mosques_search_api_raw: list[dict],
) -> None:
    """Test the location search reuses the login client and creates the entry."""
    mock_client.all_mosques_neighborhood.return_value = mock_mosques_search_api_raw

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.mawaqit.config_flow.AsyncMawaqitClient",
        return_value=mock_client,
    ) as mock_client_class:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"next_step_id": "mosques_coordinates"}
        )
        assert result.get("step_id") == "mosques_coordinates"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_UUID: "aaaaa-bbbbb-cccccc-0000"}
        )

    assert result.get("type") == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result.get("title") == "MAWAQIT - Mosque1-label (1.74 km)"
    mock_client_class.assert_called_once()
    mock_client.get_api_token.assert_awaited_once()
    mock_client.all_mosques_neighborhood.assert_awaited_once()


# ---------------------------------------------------------------------------
# MOSQUES COORDINATES - error paths
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("side_effect", "expected_reason"),
    [
        (BadCredentialsException, "cannot_connect"),
        (ConnectionError, "cannot_connect"),
        (TimeoutError, "cannot_connect"),
        (ClientConnectorError(MagicMock(), MagicMock()), "cannot_connect"),
    ],
    ids=[
        "bad_credentials",
        "connection_error",
        "timeout",
        "client_connector_error",
    ],
)
async def test_async_step_mosques_coordinates_errors_abort(
    hass: HomeAssistant,
    mock_client: MagicMock,
    side_effect: Exception | type[Exception],
    expected_reason: str,
) -> None:
    """Test the mosques step aborts when the search fails."""
    mock_client.all_mosques_neighborhood.side_effect = side_effect

    flow = _flow(hass)
    flow.client = mock_client
    result = await flow.async_step_mosques_coordinates()

    assert result.get("type") == data_entry_flow.FlowResultType.ABORT
    assert result.get("reason") == expected_reason


@pytest.mark.parametrize(
    ("side_effect", "return_value"),
    [(NoMosqueAround, None), (None, [])],
    ids=["no_mosque_around", "empty_result"],
)
async def test_no_mosque_around_redirects_to_keyword_search(
    hass: HomeAssistant,
    mock_client: MagicMock,
    side_effect: type[Exception] | None,
    return_value: list | None,
) -> None:
    """Test the location search falls back to the keyword search form."""
    mock_client.all_mosques_neighborhood.side_effect = side_effect
    mock_client.all_mosques_neighborhood.return_value = return_value
    mock_client.fetch_mosques_by_keyword.return_value = _keyword_mosques(1)

    flow_id = await _login(hass, mock_client)
    result = await hass.config_entries.flow.async_configure(
        flow_id, {"next_step_id": "mosques_coordinates"}
    )

    assert result.get("type") == data_entry_flow.FlowResultType.FORM
    assert result.get("step_id") == "keyword_search"
    assert result.get("errors") == {"base": NO_MOSQUE_AROUND}

    # Back to the menu, without the location search that found nothing.
    result = await hass.config_entries.flow.async_configure(flow_id, {})
    assert result.get("type") == data_entry_flow.FlowResultType.MENU
    assert result.get("menu_options") == ["keyword_search"]

    result = await hass.config_entries.flow.async_configure(
        flow_id, {"next_step_id": "keyword_search"}
    )
    result = await hass.config_entries.flow.async_configure(
        flow_id, {CONF_KEYWORD: "Paris"}
    )
    assert result.get("step_id") == "keyword_results"


# ---------------------------------------------------------------------------
# MOSQUES COORDINATES FORM
# ---------------------------------------------------------------------------


async def test_async_step_mosques_coordinates(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_mosques_search_api_raw: list[dict],
    mock_mosques_search_api_wrapper: list[MawaqitMosqueData],
) -> None:
    """Test the mosques coordinates step shows a form then creates an entry."""
    mock_client.all_mosques_neighborhood.return_value = mock_mosques_search_api_raw

    flow = _flow(hass)
    flow.client = mock_client

    result = await flow.async_step_mosques_coordinates()

    assert result.get("type") == data_entry_flow.FlowResultType.FORM
    assert (
        "data_schema" in result
        and result["data_schema"] is not None
        and CONF_UUID in result["data_schema"].schema
    )

    mosque_uuid = mock_mosques_search_api_wrapper[0].uuid
    result = await flow.async_step_mosques_coordinates({CONF_UUID: mosque_uuid})

    assert result.get("type") == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert "data" in result and result["data"][CONF_UUID] == mosque_uuid


# ---------------------------------------------------------------------------
# KEYWORD SEARCH
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_setup_entry")
async def test_keyword_search_creates_entry(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Test searching a trimmed keyword and picking a mosque creates the entry."""
    mock_client.fetch_mosques_by_keyword.return_value = _keyword_mosques(2)

    result = await _search_keyword(hass, mock_client, "  Paris ")

    assert result.get("type") == data_entry_flow.FlowResultType.FORM
    assert result.get("step_id") == "keyword_results"
    assert result.get("description_placeholders") == {"keyword": "Paris", "page": "1"}
    assert _options(result) == ["mosque-0", "mosque-1", NEW_SEARCH]
    mock_client.fetch_mosques_by_keyword.assert_awaited_once_with(
        "Paris", 1, MOSQUES_PER_PAGE
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UUID: "mosque-1"}
    )

    assert result.get("type") == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result.get("title") == "MAWAQIT - Mosque1-label - City1"
    assert result.get("data") == {
        CONF_API_KEY: MOCK_TOKEN,
        CONF_UUID: "mosque-1",
        CONF_LATITUDE: hass.config.latitude,
        CONF_LONGITUDE: hass.config.longitude,
    }


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (NoMosqueFound, NO_MOSQUE_FOUND),
        (BadCredentialsException, CANNOT_CONNECT_TO_SERVER),
        (MawaqitException, CANNOT_CONNECT_TO_SERVER),
        (ConnectionError, CANNOT_CONNECT_TO_SERVER),
        (TimeoutError, CANNOT_CONNECT_TO_SERVER),
        (
            ClientConnectorError(MagicMock(), MagicMock()),
            CANNOT_CONNECT_TO_SERVER,
        ),
    ],
    ids=[
        "no_mosque_found",
        "bad_credentials",
        "mawaqit_error",
        "connection_error",
        "timeout",
        "client_connector_error",
    ],
)
async def test_keyword_search_errors(
    hass: HomeAssistant,
    mock_client: MagicMock,
    side_effect: Exception | type[Exception],
    expected_error: str,
) -> None:
    """Test search failures are shown on the keyword form, which can be retried."""
    mock_client.fetch_mosques_by_keyword.side_effect = side_effect

    result = await _search_keyword(hass, mock_client)

    assert result.get("type") == data_entry_flow.FlowResultType.FORM
    assert result.get("step_id") == "keyword_search"
    assert result.get("errors") == {"base": expected_error}

    mock_client.fetch_mosques_by_keyword.side_effect = None
    mock_client.fetch_mosques_by_keyword.return_value = _keyword_mosques(1)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_KEYWORD: "Paris"}
    )
    assert result.get("step_id") == "keyword_results"


@pytest.mark.parametrize(
    "user_input", [{CONF_KEYWORD: "   "}, {}], ids=["blank", "missing"]
)
async def test_keyword_search_empty_keyword_goes_back(
    hass: HomeAssistant, mock_client: MagicMock, user_input: dict
) -> None:
    """Test an empty keyword goes back to the search menu without calling the API."""
    flow_id = await _login(hass, mock_client)
    await hass.config_entries.flow.async_configure(
        flow_id, {"next_step_id": "keyword_search"}
    )

    result = await hass.config_entries.flow.async_configure(flow_id, user_input)

    assert result.get("type") == data_entry_flow.FlowResultType.MENU
    assert result.get("menu_options") == ["mosques_coordinates", "keyword_search"]
    mock_client.fetch_mosques_by_keyword.assert_not_awaited()


async def test_location_search_after_keyword_search(
    hass: HomeAssistant,
    mock_client: MagicMock,
    mock_mosques_search_api_raw: list[dict],
) -> None:
    """Test the location search lists nearby mosques, not the keyword results."""
    mock_client.fetch_mosques_by_keyword.return_value = _keyword_mosques(1)
    mock_client.all_mosques_neighborhood.return_value = mock_mosques_search_api_raw

    result = await _search_keyword(hass, mock_client)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UUID: NEW_SEARCH}
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "mosques_coordinates"}
    )

    assert result.get("step_id") == "mosques_coordinates"
    assert "data_schema" in result and result["data_schema"] is not None
    assert list(result["data_schema"].schema[CONF_UUID].container) == [
        mosque["uuid"] for mosque in mock_mosques_search_api_raw
    ]


async def test_keyword_results_pagination(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Test the next page is prefetched and visited pages are not fetched again."""
    page_1 = _keyword_mosques(MOSQUES_PER_PAGE)
    page_2 = _keyword_mosques(3, first=MOSQUES_PER_PAGE)
    mock_client.fetch_mosques_by_keyword.side_effect = [page_1, page_2]

    result = await _search_keyword(hass, mock_client)
    assert result.get("errors") == {}
    assert _options(result) == [*_uuids(page_1), NEXT_PAGE, NEW_SEARCH]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UUID: NEXT_PAGE}
    )
    assert result.get("description_placeholders") == {"keyword": "Paris", "page": "2"}
    assert _options(result) == [*_uuids(page_2), PREVIOUS_PAGE, NEW_SEARCH]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UUID: PREVIOUS_PAGE}
    )
    assert result.get("description_placeholders") == {"keyword": "Paris", "page": "1"}
    assert _options(result) == [*_uuids(page_1), NEXT_PAGE, NEW_SEARCH]
    assert [
        call.args for call in mock_client.fetch_mosques_by_keyword.await_args_list
    ] == [("Paris", 1, MOSQUES_PER_PAGE), ("Paris", 2, MOSQUES_PER_PAGE)]


async def test_keyword_results_full_last_page(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Test the next page is not offered when it has no mosques."""
    page_1 = _keyword_mosques(MOSQUES_PER_PAGE)
    mock_client.fetch_mosques_by_keyword.side_effect = [page_1, NoMosqueFound]

    result = await _search_keyword(hass, mock_client)

    assert result.get("errors") == {}
    assert _options(result) == [*_uuids(page_1), NEW_SEARCH]
    assert mock_client.fetch_mosques_by_keyword.await_count == 2


async def test_keyword_results_prefetch_error(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Test a failed prefetch hides the next page until the page is shown again."""
    page_1 = _keyword_mosques(MOSQUES_PER_PAGE)
    page_2 = _keyword_mosques(MOSQUES_PER_PAGE, first=MOSQUES_PER_PAGE)
    page_3 = _keyword_mosques(1, first=2 * MOSQUES_PER_PAGE)
    mock_client.fetch_mosques_by_keyword.side_effect = [
        page_1,
        page_2,
        ConnectionError,
        page_3,
    ]

    result = await _search_keyword(hass, mock_client)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UUID: NEXT_PAGE}
    )
    assert result.get("errors") == {"base": CANNOT_CONNECT_TO_SERVER}
    assert _options(result) == [*_uuids(page_2), PREVIOUS_PAGE, NEW_SEARCH]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UUID: PREVIOUS_PAGE}
    )
    assert result.get("errors") == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UUID: NEXT_PAGE}
    )
    assert result.get("errors") == {}
    assert _options(result) == [*_uuids(page_2), PREVIOUS_PAGE, NEXT_PAGE, NEW_SEARCH]
    mock_client.fetch_mosques_by_keyword.assert_awaited_with(
        "Paris", 3, MOSQUES_PER_PAGE
    )


async def test_keyword_results_new_search(
    hass: HomeAssistant, mock_client: MagicMock
) -> None:
    """Test a new search starts from the first page of the new keyword."""
    page_1 = _keyword_mosques(MOSQUES_PER_PAGE)
    mock_client.fetch_mosques_by_keyword.side_effect = [
        page_1,
        NoMosqueFound,
        page_1,
        _keyword_mosques(1, first=MOSQUES_PER_PAGE),
    ]

    result = await _search_keyword(hass, mock_client)
    assert NEXT_PAGE not in _options(result)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UUID: NEW_SEARCH}
    )
    assert result.get("step_id") == "keyword_search"
    assert result.get("errors") == {}
    assert "data_schema" in result and result["data_schema"] is not None
    keyword_key = next(iter(result["data_schema"].schema))
    assert keyword_key.description == {"suggested_value": "Paris"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_KEYWORD: "Lyon"}
    )
    assert result.get("description_placeholders") == {"keyword": "Lyon", "page": "1"}
    assert NEXT_PAGE in _options(result)
    mock_client.fetch_mosques_by_keyword.assert_awaited_with(
        "Lyon", 2, MOSQUES_PER_PAGE
    )


# ---------------------------------------------------------------------------
# REAUTH
# ---------------------------------------------------------------------------


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reauth_flow(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test reauthentication stores the new token and keeps the mosque."""
    mock_config_entry.add_to_hass(hass)
    mock_client.token = NEW_TOKEN
    mock_client.get_api_token.return_value = NEW_TOKEN

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result.get("type") == data_entry_flow.FlowResultType.FORM
    assert result.get("step_id") == "reauth_confirm"

    with patch(
        "custom_components.mawaqit.config_flow.AsyncMawaqitClient",
        return_value=mock_client,
    ) as mock_client_class:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()

    assert result.get("type") == data_entry_flow.FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"
    assert mock_client_class.call_args.kwargs[CONF_USERNAME] == "user"
    assert mock_client_class.call_args.kwargs[CONF_PASSWORD] == "pass"
    assert mock_config_entry.data[CONF_API_KEY] == NEW_TOKEN
    assert mock_config_entry.data[CONF_UUID] == MOCK_UUID


@pytest.mark.parametrize(
    ("side_effect", "expected_error"),
    [
        (BadCredentialsException, WRONG_CREDENTIAL),
        (MawaqitException, CANNOT_CONNECT_TO_SERVER),
    ],
    ids=["bad_credentials", "mawaqit_error"],
)
@pytest.mark.usefixtures("mock_setup_entry")
async def test_reauth_flow_errors_then_recovers(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
    side_effect: type[Exception],
    expected_error: str,
) -> None:
    """Test the reauth form shows login errors and lets the user retry."""
    mock_config_entry.add_to_hass(hass)
    mock_client.get_api_token.side_effect = side_effect

    result = await mock_config_entry.start_reauth_flow(hass)

    with patch(
        "custom_components.mawaqit.config_flow.AsyncMawaqitClient",
        return_value=mock_client,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        assert result.get("type") == data_entry_flow.FlowResultType.FORM
        assert result.get("step_id") == "reauth_confirm"
        assert result.get("errors") == {"base": expected_error}

        mock_client.get_api_token.side_effect = None
        mock_client.token = NEW_TOKEN
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()

    assert result.get("type") == data_entry_flow.FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"
    assert mock_config_entry.data[CONF_API_KEY] == NEW_TOKEN


# ---------------------------------------------------------------------------
# RECONFIGURE
# ---------------------------------------------------------------------------

NEW_MOSQUE_UUID = "bbbbb-cccccc-ddddd-0000"


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reconfigure_changes_mosque_and_keeps_entities(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
    mock_mosques_search_api_raw: list[dict],
) -> None:
    """Test reconfiguring moves the entities to the new mosque, without a login."""
    mock_config_entry.add_to_hass(hass)
    # Otherwise the reload runs the legacy migration, which drops unknown entities.
    hass.config_entries.async_update_entry(mock_config_entry, minor_version=2)
    mock_client.all_mosques_neighborhood.return_value = mock_mosques_search_api_raw
    ent_reg = er.async_get(hass)
    fajr = ent_reg.async_get_or_create(
        "sensor",
        DOMAIN,
        f"{MOCK_UUID}_prayer_fajr",
        config_entry=mock_config_entry,
        suggested_object_id="fajr_prayer",
    )
    other = ent_reg.async_get_or_create(
        "sensor", DOMAIN, "other", config_entry=mock_config_entry
    )
    stale = ent_reg.async_get_or_create(
        "sensor", DOMAIN, f"{NEW_MOSQUE_UUID}_prayer_fajr"
    )

    with patch(
        "custom_components.mawaqit.config_flow.AsyncMawaqitClient",
        return_value=mock_client,
    ) as mock_client_class:
        result = await mock_config_entry.start_reconfigure_flow(hass)

    assert result.get("type") == data_entry_flow.FlowResultType.MENU
    assert result.get("step_id") == "search_method"
    assert mock_client_class.call_args.kwargs["token"] == MOCK_TOKEN

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "mosques_coordinates"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UUID: NEW_MOSQUE_UUID}
    )
    await hass.async_block_till_done()

    assert result.get("type") == data_entry_flow.FlowResultType.ABORT
    assert result.get("reason") == "reconfigure_successful"
    assert mock_config_entry.title == "MAWAQIT - Mosque2-label (20.00 km)"
    assert mock_config_entry.data[CONF_UUID] == NEW_MOSQUE_UUID
    assert mock_config_entry.data[CONF_API_KEY] == MOCK_TOKEN
    mock_client.get_api_token.assert_not_awaited()

    moved = ent_reg.async_get(fajr.entity_id)
    assert moved is not None
    assert moved.entity_id == "sensor.fajr_prayer"
    assert moved.unique_id == f"{NEW_MOSQUE_UUID}_prayer_fajr"
    assert ent_reg.async_get(other.entity_id) is not None
    assert ent_reg.async_get(stale.entity_id) is None


@pytest.mark.usefixtures("mock_setup_entry")
async def test_reconfigure_with_keyword_search(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test the keyword search can pick the new mosque when reconfiguring."""
    mock_config_entry.add_to_hass(hass)
    mock_client.fetch_mosques_by_keyword.return_value = _keyword_mosques(1)

    with patch(
        "custom_components.mawaqit.config_flow.AsyncMawaqitClient",
        return_value=mock_client,
    ):
        result = await mock_config_entry.start_reconfigure_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "keyword_search"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_KEYWORD: "Paris"}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_UUID: "mosque-0"}
    )
    await hass.async_block_till_done()

    assert result.get("reason") == "reconfigure_successful"
    assert mock_config_entry.title == "MAWAQIT - Mosque0-label - City0"
    assert mock_config_entry.data[CONF_UUID] == "mosque-0"
