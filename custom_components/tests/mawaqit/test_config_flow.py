from unittest.mock import patch, Mock, MagicMock, mock_open
import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.components.mawaqit import DOMAIN
from homeassistant.components.mawaqit import config_flow
from homeassistant.components.mawaqit.const import CONF_CALC_METHOD
from homeassistant.const import CONF_USERNAME, CONF_PASSWORD, CONF_UUID
from mawaqit.consts import NoMosqueAround
import json
import os
import aiohttp
from tests.common import MockConfigEntry


@pytest.mark.asyncio
async def test_step_user_one_instance_allowed(hass: HomeAssistant):
    # test if if the data folder is doesn't contain specific config file we abort
    flow = config_flow.MawaqitPrayerFlowHandler()
    flow.hass = hass
    with patch(
        "homeassistant.components.mawaqit.config_flow.is_another_instance",
        return_value=True,
    ):
        result = await flow.async_step_user(None)

        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "one_instance_allowed"


@pytest.mark.asyncio
async def test_show_form_user_no_input_reopens_form(hass: HomeAssistant):
    """Test that the form is served with no input."""
    # Initialize the flow handler with the HomeAssistant instance
    flow = config_flow.MawaqitPrayerFlowHandler()
    flow.hass = hass

    with patch(
        "homeassistant.components.mawaqit.config_flow.is_another_instance",
        return_value=False,
    ):
        # Invoke the initial step of the flow without user input
        result = await flow.async_step_user(user_input=None)

        # Validate that the form is returned to the user
        assert result["type"] == data_entry_flow.FlowResultType.FORM
        assert result["step_id"] == "user"


@pytest.mark.asyncio
async def test_async_step_user_connection_error(hass: HomeAssistant):
    """Test the user step handles connection errors correctly."""
    flow = config_flow.MawaqitPrayerFlowHandler()
    flow.hass = hass

    # Create an instance of ClientConnectorError with mock arguments
    mock_conn_key = MagicMock()
    mock_os_error = MagicMock()
    connection_error_instance = aiohttp.client_exceptions.ClientConnectorError(
        mock_conn_key, mock_os_error
    )

    # Patching the methods used in the flow to simulate external interactions
    with (
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper._test_credentials",
            side_effect=connection_error_instance,
        ),
        patch(
            "homeassistant.components.mawaqit.config_flow.is_another_instance",
            return_value=False,
        ),
    ):
        # Simulate user input to trigger the flow's logic
        result = await flow.async_step_user(
            {CONF_USERNAME: "testuser", CONF_PASSWORD: "testpass"}
        )

        # Check that the flow returns a form with an error message due to the connection error
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "user"
        assert "base" in result["errors"]
        assert result["errors"]["base"] == "cannot_connect_to_server"


@pytest.mark.asyncio
async def test_async_step_user_invalid_credentials(hass: HomeAssistant):
    """Test the user step with invalid credentials."""
    flow = config_flow.MawaqitPrayerFlowHandler()
    flow.hass = hass

    # Patch the credentials test to simulate a login failure
    with (
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper._test_credentials",
            return_value=False,
        ),
        patch(
            "homeassistant.components.mawaqit.config_flow.is_another_instance",
            return_value=False,
        ),
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
async def test_async_step_user_valid_credentials(hass: HomeAssistant):
    """Test the user step with invalid credentials."""
    flow = config_flow.MawaqitPrayerFlowHandler()
    flow.hass = hass

    # Patch the credentials test to simulate a login failure
    with (
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper._test_credentials",
            return_value=True,
        ),
        patch(
            "homeassistant.components.mawaqit.config_flow.is_another_instance",
            return_value=False,
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.get_mawaqit_api_token",
            return_value="MAWAQIT_API_TOKEN",
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.all_mosques_neighborhood",
            return_value={},
        ),
    ):
        # Simulate user input with incorrect credentials
        result = await flow.async_step_user(
            {CONF_USERNAME: "wronguser", CONF_PASSWORD: "wrongpass"}
        )

        # Validate that the error is correctly handled and reported
        assert result["type"] == data_entry_flow.RESULT_TYPE_FORM
        assert result["step_id"] == "mosques"


@pytest.mark.asyncio
async def test_async_step_user_no_neighborhood(hass: HomeAssistant):
    """Test the user step when no mosque is found in the neighborhood."""
    flow = config_flow.MawaqitPrayerFlowHandler()
    flow.hass = hass

    # Patching the methods used in the flow to simulate external interactions
    with (
        patch(
            "homeassistant.components.mawaqit.config_flow.is_another_instance",
            return_value=False,
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper._test_credentials",
            return_value=True,
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.get_mawaqit_api_token",
            return_value="MAWAQIT_API_TOKEN",
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.all_mosques_neighborhood",
            side_effect=NoMosqueAround,
        ),
    ):
        # Simulate user input to trigger the flow's logic
        result = await flow.async_step_user(
            {CONF_USERNAME: "testuser", CONF_PASSWORD: "testpass"}
        )

        # Check that the flow is aborted due to the lack of mosques nearby
        assert result["type"] == data_entry_flow.RESULT_TYPE_ABORT
        assert result["reason"] == "no_mosque"


@pytest.fixture
async def mock_mosques_test_data():
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
            "label": "Mosque1-label",
            "localisation": "aaaaa bbbbb cccccc",
        },
        {
            "uuid": "bbbbb-cccccc-ddddd-0000",
            "name": "Mosque2-label",
            "type": "MOSQUE",
            "slug": "2-mosque",
            "latitude": 47,
            "longitude": 1,
            "jumua": None,
            "proximity": 20000,
            "label": "Mosque2-label",
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
            "label": "Mosque3-label",
            "localisation": "bbbbb cccccc ddddd",
        },
    ]

    mocked_mosques_data = (
        [
            "Mosque1-label (1.74km)",
            "Mosque2-label (20.0km)",
            "Mosque3-label (20.0km)",
        ],  # name_servers
        [
            "aaaaa-bbbbb-cccccc-0000",
            "bbbbb-cccccc-ddddd-0000",
            "bbbbb-cccccc-ddddd-0001",
        ],  # uuid_servers
        ["Mosque1-label", "Mosque2-label", "Mosque3-label"],  # CALC_METHODS
    )

    return mock_mosques, mocked_mosques_data


@pytest.mark.asyncio
async def test_async_step_mosques(hass, mock_mosques_test_data):
    mock_mosques, mocked_mosques_data = mock_mosques_test_data

    # Mock external dependencies
    with (
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.get_mawaqit_token_from_env",
            return_value="TOKEN",
        ),
        patch(
            "homeassistant.components.mawaqit.config_flow.read_all_mosques_NN_file",
            return_value=mocked_mosques_data,
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.all_mosques_neighborhood",
            return_value=mock_mosques,
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.fetch_prayer_times",
            return_value={},
        ),
    ):  # empty data
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
        mosque_uuid_label = mocked_mosques_data[0][
            0
        ]  # Assuming the user selects the first mosque
        mosque_uuid = mocked_mosques_data[1][0]  # uuid of the first mosque

        result = await flow.async_step_mosques({CONF_UUID: mosque_uuid_label})

        # Verify the flow processes the selection correctly
        assert result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        assert result["data"][CONF_UUID] == mosque_uuid


@pytest.fixture
def mock_config_entry_setup():
    """Create a mock ConfigEntry."""
    entry = MagicMock(spec=config_entries.ConfigEntry)
    # Set up any necessary properties of the entry here
    # For example: entry.entry_id = "test_entry"
    return entry


@pytest.mark.asyncio
async def test_async_get_options_flow(mock_config_entry_setup):
    """Test the options flow is correctly instantiated with the config entry."""

    options_flow = config_flow.MawaqitPrayerFlowHandler.async_get_options_flow(
        mock_config_entry_setup
    )

    # Verify that the result is an instance of the expected options flow handler
    assert isinstance(options_flow, config_flow.MawaqitPrayerOptionsFlowHandler)
    # check that the config entry is correctly passed to the handler
    assert options_flow.config_entry == mock_config_entry_setup


@pytest.fixture
async def config_entry_setup(hass: HomeAssistant):
    """Create a mock config entry for tests."""
    entry = MockConfigEntry(
        version=10,
        minor_version=1,
        domain=DOMAIN,
        title="MAWAQIT - Mosque1",
        data={
            "api_key": "TOKEN",
            "uuid": "aaaaa-bbbbb-cccccc-0000",
            "latitude": 32.87336,
            "longitude": -117.22743,
        },
        source=config_entries.SOURCE_USER,
    )

    entry.add_to_hass(hass)  # register the MockConfigEntry to Hass

    return entry


@pytest.mark.asyncio
async def test_options_flow_valid_input(
    hass: HomeAssistant, config_entry_setup, mock_mosques_test_data
):
    mock_mosques, mocked_mosques_data = mock_mosques_test_data

    """Test the options flow."""
    with (
        patch(
            "homeassistant.components.mawaqit.config_flow.read_all_mosques_NN_file",
            return_value=mocked_mosques_data,
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.get_mawaqit_token_from_env",
            return_value="TOKEN",
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.all_mosques_neighborhood",
            return_value=mock_mosques,
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.fetch_prayer_times",
            return_value={},
        ),
    ):  # empty data
        # Initialize the options flow
        flow = config_flow.MawaqitPrayerOptionsFlowHandler(config_entry_setup)
        flow.hass = hass  # Assign HomeAssistant instance

        # Simulate user input in the options flow
        mosque_uuid_label = mocked_mosques_data[0][
            1
        ]  # Assuming the user selects the first mosque
        mosque_uuid = mocked_mosques_data[1][1]  # uuid of the first mosque

        # TODO chage this if we remove the create_entry line 278
        result = await flow.async_step_init(
            user_input={CONF_CALC_METHOD: mosque_uuid_label}
        )
        print(result)
        assert (
            result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
        )  # Assert that an entry is created/updated
        # assert result["data"][CONF_UUID] == mosque_uuid


@pytest.mark.asyncio
async def test_options_flow_error_no_mosques_around(
    hass: HomeAssistant, config_entry_setup, mock_mosques_test_data
):
    _, mocked_mosques_data = mock_mosques_test_data

    """Test the options flow."""
    with (
        patch(
            "homeassistant.components.mawaqit.config_flow.read_all_mosques_NN_file",
            return_value=mocked_mosques_data,
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.get_mawaqit_token_from_env",
            return_value="TOKEN",
        ),
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.all_mosques_neighborhood",
            side_effect=NoMosqueAround,
        ),
    ):
        # Initialize the options flow
        flow = config_flow.MawaqitPrayerOptionsFlowHandler(config_entry_setup)
        flow.hass = hass  # Assign HomeAssistant instance

        # Simulate user input in the options flow
        mosque_uuid_label = mocked_mosques_data[0][
            1
        ]  # Assuming the user selects the first mosque
        mosque_uuid = mocked_mosques_data[1][1]  # uuid of the first mosque

        # Since we expect an exception, let's catch it to assert it happens
        with pytest.raises(NoMosqueAround):
            result = await flow.async_step_init(
                user_input={CONF_CALC_METHOD: mosque_uuid_label}
            )
            # Same tests as in test_options_flow_valid_input :
            # TODO chage this if we remove the create_entry line 278
            result = await flow.async_step_init(
                user_input={CONF_CALC_METHOD: mosque_uuid_label}
            )
            assert (
                result["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
            )  # Assert that an entry is created/updated
            # assert result["data"][CONF_UUID] == mosque_uuid


@pytest.mark.asyncio
async def test_options_flow_no_input_reopens_form(
    hass: HomeAssistant, config_entry_setup, mock_mosques_test_data
):
    # MawaqitPrayerOptionsFlowHandler.
    mock_mosques, mocked_mosques_data = mock_mosques_test_data

    """Test the options flow."""
    with (
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.all_mosques_neighborhood",
            return_value={},
        ),
        patch(
            "homeassistant.components.mawaqit.config_flow.read_all_mosques_NN_file",
            return_value=mocked_mosques_data,
        ),
        patch(
            "homeassistant.components.mawaqit.config_flow.read_my_mosque_NN_file",
            return_value=mock_mosques[0],
        ),
    ):
        # Initialize the options flow
        flow = config_flow.MawaqitPrayerOptionsFlowHandler(config_entry_setup)
        flow.hass = hass  # Assign HomeAssistant instance

        # Simulate the init step
        result = await flow.async_step_init(user_input=None)
        assert (
            result["type"] == data_entry_flow.FlowResultType.FORM
        )  # Assert that a form is shown
        assert result["step_id"] == "init"


@pytest.mark.asyncio
async def test_options_flow_no_input_error_reopens_form(
    hass: HomeAssistant, config_entry_setup, mock_mosques_test_data
):
    # MawaqitPrayerOptionsFlowHandler.
    _, mocked_mosques_data = mock_mosques_test_data

    """Test the options flow."""
    with (
        patch(
            "homeassistant.components.mawaqit.mawaqit_wrapper.all_mosques_neighborhood",
            return_value={},
        ),
        patch(
            "homeassistant.components.mawaqit.config_flow.read_all_mosques_NN_file",
            return_value=mocked_mosques_data,
        ),
        patch(
            "homeassistant.components.mawaqit.config_flow.read_my_mosque_NN_file",
            return_value={"uuid": "non_existent_uuid"},
        ),
    ):  # , \
        # Initialize the options flow
        flow = config_flow.MawaqitPrayerOptionsFlowHandler(config_entry_setup)
        flow.hass = hass  # Assign HomeAssistant instance

        # Simulate the init step
        result = await flow.async_step_init(user_input=None)
        # Same tests as test_options_flow_no_input_reopens_form :
        assert (
            result["type"] == data_entry_flow.FlowResultType.FORM
        )  # Assert that a form is shown
        assert result["step_id"] == "init"


@pytest.fixture
async def mock_data_folder():
    # Utility fixture to mock os.path.exists and os.makedirs
    with patch("os.path.exists") as mock_exists:
        with patch("os.makedirs") as mock_makedirs:
            yield mock_exists, mock_makedirs


@pytest.fixture
async def mock_file_io():
    # Utility fixture for mocking open
    with patch("builtins.open", mock_open()) as mocked_file:
        yield mocked_file


@pytest.mark.asyncio
async def test_read_all_mosques_NN_file(mock_mosques_test_data):
    sample_data, expected_output = mock_mosques_test_data
    with patch("builtins.open", mock_open(read_data=json.dumps(sample_data))):
        assert config_flow.read_all_mosques_NN_file() == expected_output


@pytest.fixture(scope="function")
def test_folder_setup():
    # Define the folder name
    folder_name = "./test_dir"
    # Create the folder
    os.makedirs(folder_name, exist_ok=True)
    # Pass the folder name to the test
    yield folder_name
    # No deletion here, handled by another fixture


@pytest.fixture(scope="function", autouse=True)
def test_folder_cleanup(request, test_folder_setup):
    # This fixture does not need to do anything before the test,
    # so it yields control immediately
    yield
    # Teardown: Delete the folder after the test runs
    folder_path = test_folder_setup  # Corrected variable name

    def cleanup():
        if os.path.exists(folder_path):
            os.rmdir(folder_path)  # Make sure the folder is empty before calling rmdir

    request.addfinalizer(cleanup)


@pytest.mark.asyncio
async def test_write_all_mosques_NN_file(mock_file_io, test_folder_setup):
    # test for write_all_mosques_NN_file
    with patch(
        "homeassistant.components.mawaqit.config_flow.CURRENT_DIR", new="./test_dir"
    ):
        mosques = [{"label": "Mosque A", "uuid": "uuid1"}]
        config_flow.write_all_mosques_NN_file(mosques)
        mock_file_io.assert_called_with(
            f"{test_folder_setup}/data/all_mosques_NN.txt", "w"
        )
        assert mock_file_io().write.called, "The file's write method was not called."


@pytest.mark.asyncio
async def test_read_my_mosque_NN_file():
    # test for read_my_mosque_NN_file
    sample_mosque = {"label": "My Mosque", "uuid": "myuuid"}
    with patch("builtins.open", mock_open(read_data=json.dumps(sample_mosque))):
        assert config_flow.read_my_mosque_NN_file() == sample_mosque


@pytest.mark.asyncio
# @patch('path.to.your.config_flow_module.CURRENT_DIR', './test_dir')
async def test_write_my_mosque_NN_file(mock_file_io, test_folder_setup):
    # test for write_my_mosque_NN_file
    with patch(
        "homeassistant.components.mawaqit.config_flow.CURRENT_DIR", new="./test_dir"
    ):
        mosque = {"label": "My Mosque", "uuid": "myuuid"}
        config_flow.write_my_mosque_NN_file(mosque)
        mock_file_io.assert_called_with(
            f"{test_folder_setup}/data/my_mosque_NN.txt", "w"
        )
        assert mock_file_io().write.called, "The file's write method was not called."


@pytest.mark.asyncio
async def test_create_data_folder_already_exists(mock_data_folder):
    # test for create_data_folder
    mock_exists, mock_makedirs = mock_data_folder
    mock_exists.return_value = True
    config_flow.create_data_folder()
    mock_makedirs.assert_not_called()


@pytest.mark.asyncio
async def test_create_data_folder_does_not_exist(mock_data_folder):
    mock_exists, mock_makedirs = mock_data_folder
    mock_exists.return_value = False
    config_flow.create_data_folder()
    mock_makedirs.assert_called_once()


@pytest.mark.usefixtures("test_folder_setup")
@pytest.mark.parametrize(
    "file_exists, expected_result",
    [
        (True, True),  # The file exists, function should return True
        (False, False),  # The file does not exist, function should return False
    ],
)
def test_is_already_configured(file_exists, expected_result, test_folder_setup):
    with (
        patch(
            "homeassistant.components.mawaqit.config_flow.CURRENT_DIR",
            new=test_folder_setup,
        ),
        patch(
            "homeassistant.components.mawaqit.config_flow.os.path.isfile",
            return_value=file_exists,
        ) as mock_isfile,
    ):
        result = config_flow.is_already_configured()
        assert result == expected_result
        mock_isfile.assert_called_once_with(
            f"{test_folder_setup}/data/my_mosque_NN.txt"
        )


@pytest.mark.usefixtures("test_folder_setup")
@pytest.mark.parametrize(
    "configured, expected_result",
    [
        (
            True,
            True,
        ),  # is_already_configured returns True, is_another_instance should also return True
        (
            False,
            False,
        ),  # is_already_configured returns False, is_another_instance should return False
    ],
)
def test_is_another_instance(configured, expected_result, test_folder_setup):
    with (
        patch(
            "homeassistant.components.mawaqit.config_flow.CURRENT_DIR",
            new=test_folder_setup,
        ),
        patch(
            "homeassistant.components.mawaqit.config_flow.is_already_configured",
            return_value=configured,
        ),
    ):
        result = config_flow.is_another_instance()
        assert result == expected_result
