# A MAWAQIT component for Home Assistant
## Smart home, Smart mosque : automate things based on prayer times

ٱلسَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ

Essalāmu ʿalaykum wa rahmatu Allahi wa barakatuh
#
## English

This component allows you to integrate the data of your mawaqit mosque into HomeAssistant. To do this, a Mawaqit account from **https://mawaqit.net** is required.

The component is added to HomeAssistant in the form of an integration. For the installation, you must copy the **[custom_components/mawaqit](custom_components/mawaqit)** folder to the _custom_components_ directory of your HomeAssistant installation (create it if it does not exist).

After restarting HomeAssistant, go to _Settings > Devices & Services > Add Integration_ and search for **"Mawaqit"**. Enter the login and password of your **mawaqit.net** account and click on **Submit**. Based on your GPS coordinates (latitude/longitude) stored in HomeAssistant, the component searches for Mawaqit mosques within a radius of 20km around you and asks you to select your preferred mosque.

Integration allows you to add 14 components of type ```sensor``` : the 5 prayer times, their associate Iqamas, the Shuruq, the Jumu'a time and a sensor ```sensor.my_mosque``` which summarizes all the data of your mosque (address, website, jumua, iqama, etc...)

In the configuration.yaml file, you have an example of code to create automations in HomeAssistant with Mawaqit sensors, in particular to launch the athan at the time of prayer or to launch specific actions (read the Quran, increase the heating 10 minutes before Al-Fajr, open the shutters during shuruq, etc...). The actions are to be adapted according to your HomeAssistant installation.

#


## Automation examples

```/config/configuration.yaml```

```yaml
homeassistant:
sensor:
  platform: time_date
  display_options:
    - 'time'
    - 'date_time'
```    

```/config/automations.yaml```

```yaml
- id: 'fajr_wakeup'
  alias: Turn on bedroom light and Alexa routine, 20 min before Fajr Athan
  trigger:
  - platform: template
    value_template: >
      {% set before = (as_timestamp(states("sensor.fajr_adhan")) - 20 * 60) | timestamp_custom("%H:%M", True) %} 
      {% set time = states("sensor.time") %}
      {{ time == before }}
  action:
  # turn on the light of the bedroom
  - service: switch.turn_on
    entity_id: switch.sonoff_1000814ec9 # the entity id of the sonoff switch, can be an other entity
  # play a routine on Alexa
  - service: media_player.play_media
    entity_id: media_player.zehhaf_s_echo_dot # the entity id of your alexa device
    data:
      media_content_id: bonjour # the routine name configured on Alexa mobile app, it can be a sequence of actions, like flash info, weather ...etc
      media_content_type: routine
  initial_state: true
  mode: single      

# Play adhan on a connected speaker
- id: 'isha_adhan'
  alias: Isha adhan
  trigger:
    platform: template
    value_template: >
      {% set isha_time = as_timestamp(states("sensor.isha_adhan")) | timestamp_custom("%H:%M", True) %} 
      {% set time = states("sensor.time")  %}
      {{ time == isha_time }}
  action:
    - service: mqtt.publish
      data_template:
        topic: 'commande/play/mini'
        payload: 'http://192.168.10.101/mp3/adhan.mp3' # an http url to mp3 file
  initial_state: true
  mode: single
```
#

## Français

Ce composant permet d'intégrer les données de votre mosquée Mawaqit dans HomeAssistant. Pour ce faire, Un compte Mawaqit **https://mawaqit.net** est nécessaire.

Le composant est rajouté à HomeAssistant sous forme d'une intégration. Pour l'installation, il faut copier le dossier **[custom_components/mawaqit](custom_components/mawaqit)** dans le répertoire _custom_components_ de votre installation HomeAssistant (créez le s'il n'existe pas).

Après le redémarrage de HomeAssistant, allez dans _Paramètres > Appareils et Services > Ajouter une intégration_ et cherchez **"Mawaqit"**. Entrez le login et mot de passe de votre compte **mawaqit.net** et cliquez sur **Valider**. En se basant sur vos coordonnées GPS (latitude/longitude) enregistrées dans HomeAssistant, le composant cherche les mosquées Mawaqit dans un rayon de 20 km autour de vous et vous demande de sélectionner votre mosquée préférée.

L'intégration permet de rajouter 14 composants de type ```sensor``` : les 5 horaires des prières, les iqamas associées, le Shuruq, les horaires de Jumu'a et un sensor ```sensor.my_mosque``` qui résume toutes les données de votre mosquée (adresse, site web, jumua, iqama, etc...).

Dans le fichier configuration.yaml, vous avez un exemple de code pour créer des automatismes dans HomeAssistant avec les sensors Mawaqit notamment pour lancer l'athan à l'heure de la prière ou encore pour lancer des actions spécifiques (lire le Coran, augmenter le chauffage 10 minutes avant Al-Fajr, ouvrir les volets lors du Shuruq etc...). Les actions sont à adapter en fonction de vote installation HomeAssistant.
