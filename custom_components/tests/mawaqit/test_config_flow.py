# from unittest.async_case import AsyncTestCase
from unittest.mock import patch, Mock, MagicMock
import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.components.mawaqit import DOMAIN
from homeassistant.components.mawaqit import config_flow
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_UUID
from mawaqit.consts import NoMosqueAround
# from tests.common import MockConfigEntry

# pytestmark = pytest.mark.usefixtures("mock_setup_entry")
# pytestmark = pytest.mark.usefixtures("mock_setup_entry")


@pytest.mark.asyncio
async def test_show_form_user(hass: HomeAssistant):
    """Test that the form is served with no input."""
    # Initialize the flow handler with the HomeAssistant instance
    flow = config_flow.MawaqitPrayerFlowHandler()
    flow.hass = hass

    with patch(
        "homeassistant.components.mawaqit.config_flow.is_data_folder_empty",
        return_value=True,
    ):
        # Invoke the initial step of the flow without user input
        result = await flow.async_step_user(user_input=None)

        # Validate that the form is returned to the user
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_async_step_user_no_neighborhood(hass: HomeAssistant):
    """Test the user step when no mosque is found in the neighborhood."""
    flow = config_flow.MawaqitPrayerFlowHandler()
    flow.hass = hass

    # Patching the methods used in the flow to simulate external interactions
    with patch(
        "homeassistant.components.mawaqit.config_flow.MawaqitPrayerFlowHandler._test_credentials",
        return_value=True,
    ), patch(
        "homeassistant.components.mawaqit.config_flow.MawaqitPrayerFlowHandler.get_mawaqit_api_token",
        return_value="MAWAQIT_API_TOKEN",
    ), patch(
        "homeassistant.components.mawaqit.config_flow.MawaqitPrayerFlowHandler.all_mosques_neighborhood",
        side_effect=NoMosqueAround,
    ), patch(
        "homeassistant.components.mawaqit.config_flow.is_data_folder_empty",
        return_value=True,
    ):
        # Simulate user input to trigger the flow's logic
        result = await flow.async_step_user(
            {CONF_USERNAME: "testuser", CONF_PASSWORD: "testpass"}
        )

        # Check that the flow is aborted due to the lack of mosques nearby
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "no_mosque"


@pytest.mark.asyncio
async def test_async_step_user_invalid_credentials(hass: HomeAssistant):
    """Test the user step with invalid credentials."""
    flow = config_flow.MawaqitPrayerFlowHandler()
    flow.hass = hass

    # Patch the credentials test to simulate a login failure
    with patch(
        "homeassistant.components.mawaqit.config_flow.MawaqitPrayerFlowHandler._test_credentials",
        return_value=False,
    ), patch(
        "homeassistant.components.mawaqit.config_flow.is_data_folder_empty",
        return_value=True,
    ):
        # Simulate user input with incorrect credentials
        result = await flow.async_step_user(
            {CONF_USERNAME: "wronguser", CONF_PASSWORD: "wrongpass"}
        )

        # Validate that the error is correctly handled and reported
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert "base" in result["errors"]
        assert result["errors"]["base"] == "wrong_credential"


@pytest.mark.asyncio
async def test_async_step_mosques(hass):
    mock_mosques = [
        {
            "uuid": "aaaaa-bbbbb-cccccc-0000",
            "name": "Mosque1",
            "type": "MOSQUE",
            "slug": "1-mosque",
            "latitude": 48,
            "longitude": 1,
            "jumua": None,
            "proximity": 1744,
            "label": "Mosque1",
            "localisation": "aaaaa bbbbb cccccc",
        },
        {
            "uuid": "bbbbb-cccccc-ddddd-0000",
            "name": "Mosque2",
            "type": "MOSQUE",
            "slug": "2-mosque",
            "latitude": 47,
            "longitude": 1,
            "jumua": None,
            "proximity": 20000,
            "label": "Mosque1",
            "localisation": "bbbbb cccccc ddddd",
        },
        {
            "uuid": "bbbbb-cccccc-ddddd-0001",
            "name": "Mosque3",
            "type": "MOSQUE",
            "slug": "2-mosque",
            "latitude": 47,
            "longitude": 1,
            "jumua": None,
            "proximity": 20000,
            "label": "Mosque1",
            "localisation": "bbbbb cccccc ddddd",
        },
    ]

    mocked_mosques_data = (
        ["Mosque1 (1.74km)", "Mosque2 (20.0km)", "Mosque2 (20.0km)"],  # name_servers
        [
            "aaaaa-bbbbb-cccccc-0000",
            "bbbbb-cccccc-ddddd-0000",
            "bbbbb-cccccc-ddddd-0001",
        ],  # uuid_servers
        ["Mosque1", "Mosque2", "Mosque3"],  # CALC_METHODS
    )

    # Mock external dependencies
    with patch(
        "homeassistant.components.mawaqit.config_flow.get_mawaqit_token_from_file",
        return_value="TOKEN",
    ), patch(
        "homeassistant.components.mawaqit.config_flow.read_all_mosques_NN_file",
        return_value=mocked_mosques_data,
    ), patch(
        "homeassistant.components.mawaqit.config_flow.MawaqitPrayerFlowHandler.all_mosques_neighborhood",
        return_value=mock_mosques,
    ), patch(
        "homeassistant.components.mawaqit.config_flow.MawaqitPrayerFlowHandler.fetch_prayer_times",
        return_value={},
    ):
        # Initialize the flow
        flow = config_flow.MawaqitPrayerFlowHandler()
        flow.hass = hass

        # # Pre-fill the token and mosques list as if the user step has been completed
        flow.context = {}

        # Call the mosques step
        result = await flow.async_step_mosques()

        # Verify the form is displayed with correct mosques options
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        # print(result["data_schema"].schema)
        assert CONF_UUID in result["data_schema"].schema

        # Now simulate the user selecting a mosque and submitting the form
        mosque_uuid_label = "Mosque1 (1.74km)"  # Assuming the user selects the first mosque
        mosque_uuid = "aaaaa-bbbbb-cccccc-0000"  # uuid of the first mosque
        
        result = await flow.async_step_mosques({CONF_UUID: mosque_uuid_label})

        # Verify the flow processes the selection correctly
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["data"][CONF_UUID] == mosque_uuid
