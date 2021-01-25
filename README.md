# A Mawaqit component for Home Assistant
## Smart home, Smart mosque : automate things based on prayer times

ٱلسَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ

Essalāmu ʿalaykum

### Français

Ce composant permet d'intégrer les données de votre mosquée mawaqit dans votre installation homeassistant. Pour ce faire, Un compte mawaqit https://mawaqit.net/ est nécessaire.

Le composant est rajouté à homeassistant sous forme d'une integration. Pour l'installation, il faut copier le dossier mawaqit dans le répertoire custom_components de votre installation homeassistant (créez le s'il n'existe pas).

Après le redémarrage de homeassistant, allez dans configuration > intégrations et cherchez "mawaqit". Entrez le login et mot de passe et cliquez sur soumettre. En se basant sur vos coordonnées GPS (latitude/longitude) enregistrées dans homeassistant, le composant cherche les mosquées mawaqit dans un rayon de 20km proche de vous et vous demande de sélectionner votre mosquée préférée.

L'integration permet de rajouter 6 composants de type sensor: les 5 horaires des prières et un sensor sensor.my_mosque qui résume toutes les données de votre mosquée (adresse, site web, jumaa, iqama,...)

Dans le fichier configuration.yaml, vous avez un exemple de code pour créer des automatismes dans homeassistant avec les sensors mawaqit notamment pour lancer l'athan à l'heure de la prière ou encore pour lancer des actions spécifiques (lire le coran, augmenter le chauffage 10 min avant Al-fajr, ouvrer les volets lors du shuruq ...etc)  15 minutes avant l'appel à la prière. Les actions sont à adapter en fonction de vote installation homeassistant.

### English

The component permits to link homeassistant to the nearest mawaqit mosque in your neighborhood.

Data of the mosque and prayer times are added as sensors to home assistant.
For the integration, an account at mawaqit is needed. More information on mawaqit is available at https://mawaqit.net/.

The component is added as an integration to homeassistant. for its installation, you need to copy the mawaqit folder into  the custom_components directory of your homeassistant installation (create it if it does not exist).

After restarting homeassistant, you search for "mawaqit" within the homeassistant integrations. You enter your mawaqit login/password and based on your homeassistant latitude/longitude coordinates, the component searches for the nearest mawaqit mosque. You are then asked to select your preferred mosque in the neighborhood.

6 sensors are added: the 5 prayer times and a my_mosque sensor with comprehensive data on your mosque (address, jumaa, website, phone...)

In the configuration.yaml file, you have an example of needed code and automations to interact with the mawaqit sensors. For instance, you have the athan automation at prayer time or specefic actions to trigger few minutes before the athan call. The actions specified in the automations are to adjust based on your homeassistant installation


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

```yalm
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


![Alt text](/image1.png?raw=true "Optional Title")
![Alt text](/image2.png?raw=true "Optional Title")
