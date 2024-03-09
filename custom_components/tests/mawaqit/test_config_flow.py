# from unittest.async_case import AsyncTestCase
from unittest.mock import patch, Mock, MagicMock
import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.components.mawaqit import DOMAIN
from homeassistant.components.mawaqit import config_flow
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD
from mawaqit.consts import NoMosqueAround
# from tests.common import MockConfigEntry

# pytestmark = pytest.mark.usefixtures("mock_setup_entry")
# pytestmark = pytest.mark.usefixtures("mock_setup_entry")

@pytest.mark.asyncio
async def test_show_form(hass: HomeAssistant):
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
        #data_entry_flow.RESULT_TYPE_ABORT
          # data_entry_flow.RESULT_TYPE_FORM
        print(result)
        assert "base" in result["errors"]
        assert result["errors"]["base"] == "wrong_credential"#
