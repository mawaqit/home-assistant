"""Constants for the Islamic Prayer component."""
DOMAIN = "mawaqit_prayer_times"
NAME = "Mawaqit Prayer Times"
PRAYER_TIMES_ICON = "mdi:calendar-clock"

SENSOR_TYPES = {
    "Fajr": "mawaqit",
    "Shurouq": "mawaqit",
    "Sunrise": "time",
    "Dhuhr": "mawaqit",
    "Asr": "mawaqit",
    "Maghrib": "mawaqit",
    "Isha": "mawaqit",
    "next_mawaqit": "time",
    "Fajr_Iqama": "mawaqit",  
    "Dhuhr_Iqama": "mawaqit",   
    "Asr_Iqama": "mawaqit",    
    "Maghrib_Iqama": "mawaqit",  
    "Isha_Iqama": "mawaqit",                  
}

CONF_CALC_METHOD = "calculation_method"

CALC_METHODS = ["nearest", "farest"]
DEFAULT_CALC_METHOD = "nearest"

DATA_UPDATED = "Mawaqit_prayer_data_updated"

CONF_SERVER = "server"


USERNAME = "user"

PASSWORD = "password"

API = "api"
