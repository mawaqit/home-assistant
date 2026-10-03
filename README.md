# A MAWAQIT component for Home Assistant

## Smart home, Smart mosque : automate things based on prayer times

ٱلسَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ

Essalāmu ʿalaykum wa rahmatu Allahi wa barakatuh

## English

This component allows you to integrate the data of your mawaqit mosque into Home Assistant. To do this, a Mawaqit account from **https://mawaqit.net** is required.

### Integration installation options

The component is added to Home Assistant in the form of an integration. There are two methods to install the integration as mentioned below.

Home Assistant **2025.3** or newer is required.

#### With [HACS](https://www.hacs.xyz/)

If you have HACS installed on your Home Assistant then you can use it to install Mawaqit integration.

* Go to your HACS dashboard, then open the settings (3 dots at the top right corner) and select **Custom Repositories**.
* Now in **Repository** text field put the URL of this repo: https://github.com/mawaqit/home-assistant
* In the type field select **Integration**
* Click **Add** button to finish the setup

#### Manual installation

Download **[mawaqit.zip](https://github.com/mawaqit/home-assistant/releases/latest/download/mawaqit.zip)** from the latest release and extract it into `custom_components/mawaqit` in your Home Assistant configuration directory (create the folders if they do not exist), then restart Home Assistant.

Do not download the repository itself: the `main` branch contains unreleased changes.

### Setup Mawaqit integration

* Restart Home Assistant installation (e.g. From UI go to _Settings > System > Hardware > Power button at top right_)
* After restarting Home Assistant, go to _Settings > Devices & Services > Add Integration_ and search for **"Mawaqit"**.
* Enter the login and password of your **mawaqit.net** account and click on **Submit**.
* Based on your GPS coordinates (latitude/longitude) stored in Home Assistant, the component searches for the Mawaqit mosques around you and will ask you to select your **preferred** mosque.

Only one mosque can be configured. To change it, remove the integration and add it again.

If your MAWAQIT password changes or your login stops working, Home Assistant asks you to log in again from _Settings > Devices & Services_. Your sensors and their settings are kept.

### Components of Mawaqit Integration

The integration adds the following ```sensor``` entities (all times are timestamps):

| Entity | Description |
| --- | --- |
| `sensor.fajr_prayer`, `sensor.dhuhr_prayer`, `sensor.asr_prayer`, `sensor.maghrib_prayer`, `sensor.isha_prayer` | Today's prayer times |
| `sensor.shuruq` | Today's sunrise (Shuruq) |
| `sensor.fajr_iqama` ... `sensor.isha_iqama` | Iqama of the 5 prayers, only if your mosque publishes them |
| `sensor.jumua_prayer`, `sensor.second_jumua_prayer`, `sensor.third_jumua_prayer` | Next Jumu'a times, only those your mosque has |
| `sensor.next_salat_name` | Next prayer: `fajr`, `shuruq`, `dhuhr`, `asr`, `maghrib` or `isha` |
| `sensor.next_salat_time` | Time of the next prayer |

### Upgrading from version 3.x

Version 4 is a rewrite based on the code submitted to Home Assistant core. Your configuration is migrated automatically when Home Assistant restarts:

* Existing sensors keep their entity IDs (e.g. `sensor.fajr_adhan`), so your automations and dashboards keep working. Only new installations use the names listed above.
* `sensor.my_mosque` and `sensor.next_salat_preparation` no longer exist.
* `sensor.next_salat_name` now uses lowercase values (`fajr`, `dhuhr`, ...) and also includes `shuruq`. Update automations comparing it to `Fajr`, `Dhuhr`, etc.
* The mosque can no longer be changed from the integration options: remove the integration and add it again.

## Automation Examples

Prayer sensors are timestamps, so they can be used directly in a `time` trigger, with an optional offset. Below are examples to launch the athan at the time of prayer or to launch specific actions (read the Quran, increase the heating 10 minutes before Al-Fajr, open the shutters during shuruq, etc...).
**NOTE**: The actions are to be adapted according to your Home Assistant installation.

* ```/config/automations.yaml```

```yaml
- id: 'fajr_wakeup'
  alias: Turn on bedroom light and Alexa routine, 20 min before Fajr Athan
  triggers:
    - trigger: time
      at:
        entity_id: sensor.fajr_prayer
        offset: "-00:20:00"
  actions:
    # turn on the light of the bedroom
    - action: switch.turn_on
      target:
        entity_id: switch.sonoff_1000814ec9 # the entity id of the sonoff switch, can be an other entity
    # play a routine on Alexa
    - action: media_player.play_media
      target:
        entity_id: media_player.zehhaf_s_echo_dot # the entity id of your alexa device
      data:
        media_content_id: bonjour # the routine name configured on Alexa mobile app, it can be a sequence of actions, like flash info, weather ...etc
        media_content_type: routine
  mode: single

# Play adhan on a connected speaker
- id: 'isha_adhan'
  alias: Isha adhan
  triggers:
    - trigger: time
      at: sensor.isha_prayer
  actions:
    - action: mqtt.publish
      data:
        topic: 'commande/play/mini'
        payload: 'http://192.168.10.101/mp3/adhan.mp3' # an http url to mp3 file
  mode: single
```

## Contributing

Contributions are welcome, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Français

Ce composant permet d'intégrer les données de votre mosquée Mawaqit dans Home Assistant. Pour ce faire, Un compte Mawaqit **https://mawaqit.net** est nécessaire.

Le composant est rajouté à Home Assistant (version **2025.3** minimum) sous forme d'une intégration, à installer via [HACS](https://www.hacs.xyz/) en ajoutant ce dépôt comme dépôt personnalisé (catégorie **Intégration**). Pour une installation manuelle, téléchargez **[mawaqit.zip](https://github.com/mawaqit/home-assistant/releases/latest/download/mawaqit.zip)** depuis la dernière release et extrayez-le dans `custom_components/mawaqit` de votre configuration Home Assistant (créez les dossiers s'ils n'existent pas). Ne téléchargez pas le dépôt lui-même : la branche `main` contient des changements pas encore publiés.

Après le redémarrage de Home Assistant, allez dans _Paramètres > Appareils et Services > Ajouter une intégration_ et cherchez **"Mawaqit"**. Entrez le login et mot de passe de votre compte **mawaqit.net** et cliquez sur **Valider**. En se basant sur vos coordonnées GPS (latitude/longitude) enregistrées dans Home Assistant, le composant cherche les mosquées Mawaqit autour de vous et vous demande de sélectionner votre mosquée préférée. Une seule mosquée peut être configurée : pour en changer, supprimez l'intégration puis ajoutez-la à nouveau.

L'intégration ajoute des composants de type ```sensor``` : les 5 horaires des prières, le Shuruq, les iqamas associées (si votre mosquée les publie), les horaires de Jumu'a, ainsi que ```sensor.next_salat_name``` et ```sensor.next_salat_time``` pour la prochaine prière (voir le tableau ci-dessus).

**Mise à jour depuis la version 3.x** : la configuration est migrée automatiquement au redémarrage. Les sensors existants gardent leurs identifiants (par ex. `sensor.fajr_adhan`), donc vos automatisations continuent de fonctionner. `sensor.my_mosque` et `sensor.next_salat_preparation` sont supprimés, et `sensor.next_salat_name` renvoie désormais des valeurs en minuscules (`fajr`, `shuruq`, `dhuhr`, ...).

Dans la section ci-dessus, vous avez des exemples de code pour créer des automatismes dans Home Assistant avec les sensors Mawaqit notamment pour lancer l'athan à l'heure de la prière ou encore pour lancer des actions spécifiques (lire le Coran, augmenter le chauffage 10 minutes avant Al-Fajr, ouvrir les volets lors du Shuruq etc...). Les actions sont à adapter en fonction de vote installation Home Assistant.
