# homeassistant-mawaqit
English and Arabic versions below
Al Salam Aleikom,

ce composent homeassistant permet d'intégrer une mosquée mawaqit avec son installation domotique. Un compte mawaqit est nécessaire


The component permits to link homeassistant with the nearest mawaqit mosque in your neighborhood. Data of the mosque and prayer times are added as sensors to home assistant.
For the integration, an account on mawaqit is needed. more information on mawaqit is available at https://mawaqit.net/.

The component is added as an integration to homeassistant. for its installation, you need to copy the mawaqit folder into  the custom_components directory of your homeassistant installation (create it if it does not exist).

After restarting homeassistant, you search for "mawaqit" in homeassistant integrations. You enter your mawaqit login/password. Based on your homeassistant latitude/longitude coordinates, the component searches for the nearest mawaqit mosque. You are then asked to select your preferred mosque in the neighborhood.

6 sensors are added: the 5 prayer times and a my_mosque sensor with comprehensive data on your mosque (address, jumaa, website, phone...)

in the configuration.yaml file, you have needed code and automations to hava athan iqama at prayer time.
