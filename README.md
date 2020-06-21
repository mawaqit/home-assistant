# homeassistant-mawaqit
The component permits to link homeassistant with the nearest mawaqit mosque in your neighborhood. Data of the mosque and prayer times are added as sensors to home assistant.
For the integration, an account on mawaqit is needed. You can sign up in https://mawaqit.net/.

The component is added as in integration to homeassistant. for its installation, you need to copy the mawaqit folder into  the custom_components folder of your homeassistant installation. After the restart homeassistant, you search for "mawaqit" in homeassistant integrations. You enter your mawaqit login/password and then select your preferred mosque in the neighborhood.

6 sensors are added: 5 prayer times and a my_mosque sensor with comprehnsive data on your mosque (address, jumaa, website, phone...)
