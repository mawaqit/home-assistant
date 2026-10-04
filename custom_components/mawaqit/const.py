"""Constants for the Mawaqit Integration."""

# GENERAL

MAWAQIT_URL = "https://mawaqit.net/"

# INTEGRATION
DOMAIN = "mawaqit"

CONF_KEYWORD = "keyword"
MOSQUES_PER_PAGE = 5
NEW_SEARCH = "new_search"
NEXT_PAGE = "next_page"
PREVIOUS_PAGE = "previous_page"


# Error messages

CANNOT_CONNECT_TO_SERVER = "cannot_connect_to_server"
NO_MOSQUE_AROUND = "no_mosque_around"
NO_MOSQUE_FOUND = "no_mosque_found"
WRONG_CREDENTIAL = "wrong_credential"

PRAYER_NAMES = ["fajr", "shuruq", "dhuhr", "asr", "maghrib", "isha"]
PRAYER_NAMES_IQAMA = ["fajr", "dhuhr", "asr", "maghrib", "isha"]

# The Imsak of each day of mosques displaying Sabah and Imsak, added to the API
# data by the coordinator. In snake case, so it cannot clash with an API field.
IMSAK_CALENDAR = "imsak_calendar"

# Times of the night, as fractions of the night from Maghrib to the next Fajr.
NIGHT_TIMES = {
    "first_third_end": (1, 3),
    "middle_of_the_night": (1, 2),
    "last_third_start": (2, 3),
}
