# A Mawaqit component for Home Assistant
## Smart home, Smart mosque : automate things based on prayer times

ٱلسَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ

Essalāmu ʿalaykum

### English

This component allows you to integrate the data of your mawaqit mosque into homeassistant. To do this, a mawaqit account from https://mawaqit.net is required.

The component is added to homeassistant in the form of an integration. For the installation, you must copy the mawaqit folder to the custom_components directory of your homeassistant installation (create it if it does not exist).

After restarting homeassistant, go to configuration > integrations and search for "mawaqit". Enter the login and password of your mawaqit.net account and click on submit. Based on your GPS coordinates (latitude / longitude) stored in homeassistant, the component searches for mawaqit mosques within a radius of 20km around you and asks you to select your preferred mosque.

Integration allows you to add 6 sensor type components: the 5 prayer times and a sensor sensor.my_mosque which summarizes all the data of your mosque (address, website, jumua, iqama, ... etc)

In the configuration.yaml file, you have an example of code to create automations in homeassistant with mawaqit sensors, in particular to launch the athan at the time of prayer or to launch specific actions (read the Quran, increase the heating 10 min before Al-fajr, open the shutters during shuruq ... etc). The actions are to be adapted according to your homeassistant installation.


### Automation examples

/config/configuration.yaml

```yaml
homeassistant:
sensor:
  platform: time_date
  display_options:
    - 'time'
    - 'date_time'
```    

/config/automations.yaml

```yaml
- id: 'fajr_wakeup'
  alias: Turn on bedroom light and alexa routine, 20 min before fajr adhan
  trigger:
  - platform: template
    value_template: >
      {% set before = (as_timestamp(states("sensor.fajr_mawaqit")) - 20 * 60) | timestamp_custom("%H:%M") %} 
      {% set time = states("sensor.date_time").split(" ")[1] | timestamp_custom("%H:%M") %}
      {{ time == before }}
  action:
  # turn on the light of the bedroom
  - service: switch.turn_on
    entity_id: switch.sonoff_1000814ec9 # the entity id of the sonoff switch, can be an other entity
  # play a routine on alexa
  - service: media_player.play_media
    entity_id: media_player.zehhaf_s_echo_dot # the entity id of your alexa device
    data:
      media_content_id: bonjour # the routine name configured on alexa mobile app, it can be a sequence of actions, like flash info, weather ...etc
      media_content_type: routine
  initial_state: true
  mode: single      

# Play adhan on a connected speaker
- id: 'isha_adhan'
  alias: Isha adhan
  trigger:
    platform: template
    value_template: >
      {% set isha_time = as_timestamp(states("sensor.isha_mawaqit")) | timestamp_custom("%H:%M") %} 
      {% set time = states("sensor.date_time").split(" ")[1] | timestamp_custom("%H:%M") %}
      {{ time == isha_time }}
  action:
    - service: mqtt.publish
      data_template:
        topic: 'commande/play/mini'
        payload: 'http://192.168.10.101/mp3/adhan.mp3' # an http url to mp3 file
  initial_state: true
  mode: single
```


### Français

Ce composant permet d'intégrer les données de votre mosquée mawaqit dans homeassistant. Pour ce faire, Un compte mawaqit https://mawaqit.net est nécessaire.

Le composant est rajouté à homeassistant sous forme d'une integration. Pour l'installation, il faut copier le dossier mawaqit dans le répertoire custom_components de votre installation homeassistant (créez le s'il n'existe pas).

Après le redémarrage de homeassistant, allez dans configuration > intégrations et cherchez "mawaqit". Entrez le login et mot de passe de votre compte mawaqit.net et cliquez sur soumettre. En se basant sur vos coordonnées GPS (latitude/longitude) enregistrées dans homeassistant, le composant cherche les mosquées mawaqit dans un rayon de 20km autour de vous et vous demande de sélectionner votre mosquée préférée.

L'integration permet de rajouter 6 composants de type sensor: les 5 horaires des prières et un sensor sensor.my_mosque qui résume toutes les données de votre mosquée (adresse, site web, jumua, iqama,...etc)

Dans le fichier configuration.yaml, vous avez un exemple de code pour créer des automatismes dans homeassistant avec les sensors mawaqit notamment pour lancer l'athan à l'heure de la prière ou encore pour lancer des actions spécifiques (lire le coran, augmenter le chauffage 10 min avant Al-fajr, ouvrir les volets lors du shuruq ...etc). Les actions sont à adapter en fonction de vote installation homeassistant.


![Alt text](/image1.png?raw=true "Optional Title")
![Alt text](/image2.png?raw=true "Optional Title")
