"""Platform to retrieve Mawaqit prayer times information for Home Assistant."""

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import DEVICE_CLASS_TIMESTAMP
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import homeassistant.util.dt as dt_util

from .const import DATA_UPDATED, DOMAIN, PRAYER_TIMES_ICON, SENSOR_TYPES

import json
import os
from datetime import datetime, timedelta
from homeassistant.util import Throttle
TIME_BETWEEN_UPDATES = timedelta(minutes=60)

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Mawaqit prayer times sensor platform."""

    client = hass.data[DOMAIN]

    entities = []
    for sensor_type in SENSOR_TYPES:
        if sensor_type != "Mosque":
            entities.append(MawaqitPrayerTimeSensor(sensor_type, client))

    async_add_entities(entities, True)
    name = 'My Mosque'
    sensor1 = [MyMosqueSensor(name, hass)]
    async_add_entities(sensor1, True)

class MawaqitPrayerTimeSensor(SensorEntity):
    """Representation of an Mawaqit prayer time sensor."""

    def __init__(self, sensor_type, client):
        """Initialize the Mawaqit prayer time sensor."""
        self.sensor_type = sensor_type
        self.client = client

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self.sensor_type} {SENSOR_TYPES[self.sensor_type]}"

    @property
    def unique_id(self):
        """Return the unique id of the entity."""
        return self.sensor_type

    @property
    def icon(self):
        """Icon to display in the front end."""
        return PRAYER_TIMES_ICON

   # @property
   # def state(self):
   #     """Return the state of the sensor."""
   #     return (
   #         self.client.prayer_times_info.get(self.sensor_type)
   #         .astimezone(dt_util.UTC)
   #         .isoformat()
   #     )

    @property
    def state(self):
        """Return the state of the sensor.  .astimezone(dt_util.UTC)"""
        return (
            self.client.prayer_times_info.get(self.sensor_type)
        )
    @property
    def should_poll(self):
        """Disable polling."""
        return False

    @property
    def device_class(self):
        """Return the device class."""
        return DEVICE_CLASS_TIMESTAMP

    async def async_added_to_hass(self):
        """Handle entity which will be added."""
        self.async_on_remove(
            async_dispatcher_connect(self.hass, DATA_UPDATED, self.async_write_ha_state)
        )


class MyMosqueSensor(SensorEntity):
    """Representation of a mosque sensor."""

    def __init__(self, name, hass):
        """Initialize the mosque sensor."""
        self.hass = hass
        self._attributes = {}
        self._name = name
        self._state = None
        latitude = self.hass.config.latitude
        longitude = self.hass.config.longitude
        self._latitude = latitude
        self._longitude = longitude




    @Throttle(TIME_BETWEEN_UPDATES)   # update the mosque data every 60 minutes to check news
    async def async_update(self):
        """Get the latest data from the Mawaqit API."""
        current_dir = os.path.dirname(os.path.realpath(__file__))
        f = open('{}/data/my_mosquee.txt'.format(current_dir))
        data = json.load(f)
        f.close()
        for (k, v) in data.items():
            if str(k) != "uuid" and str(k) != "id" and str(k) != "slug":
                self._attributes[k] = str(v)
                print("Key: " + k)
                print("Value: " + str(v))



    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._attributes['name']

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return 'mdi:plex'



    @property
    def device_state_attributes(self):
        """Return attributes for the sensor."""
        return self._attributes
