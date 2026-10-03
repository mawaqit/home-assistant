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
* Choose how to find your mosque, then select your **preferred** mosque:
  * **Mosques around my location**: the mosques around the GPS coordinates (latitude/longitude) stored in Home Assistant. If there are none, the component asks for a keyword instead.
  * **Search by keyword**: for example the name of the mosque or its city. Results come 5 at a time, use _Next page_ and _Previous page_ to browse them, or _New search_ to change the keyword. Leave the keyword empty to go back to the search methods.

Only one mosque can be configured. To change it, open _Settings > Devices & Services > MAWAQIT_ and choose **Reconfigure**. Your sensors keep their entity IDs, so your automations keep working.

If your MAWAQIT password changes or your login stops working, Home Assistant asks you to log in again from _Settings > Devices & Services_. Your sensors and their settings are kept.

### Components of Mawaqit Integration

The integration adds a device named after your mosque, linked to its MAWAQIT page, with the following ```sensor``` entities (all times are timestamps). Their entity IDs start with the name of the mosque, shown as `<mosque>` below: for a mosque named "My Mosque", the Fajr sensor is `sensor.my_mosque_fajr_prayer`. They also depend on the language of Home Assistant, e.g. `sensor.<mosque>_priere_fajr` in French.

| Entity | Description |
| --- | --- |
| `sensor.<mosque>_fajr_prayer` ... `sensor.<mosque>_isha_prayer` | Today's prayer times |
| `sensor.<mosque>_shuruq` | Today's sunrise (Shuruq) |
| `sensor.<mosque>_fajr_iqama` ... `sensor.<mosque>_isha_iqama` | Iqama of the 5 prayers, only if your mosque publishes them |
| `sensor.<mosque>_jumua_prayer`, `sensor.<mosque>_second_jumua_prayer`, `sensor.<mosque>_third_jumua_prayer` | Next Jumu'a times, only those your mosque has |
| `sensor.<mosque>_next_salat_name` | Next prayer: `fajr`, `shuruq`, `dhuhr`, `asr`, `maghrib` or `isha`, shown translated in the UI |
| `sensor.<mosque>_next_salat_time` | Time of the next prayer |

It also adds a `calendar.<mosque>_prayer_times` calendar (`calendar.<mosque>_horaires_des_prieres` in French) with the prayers of the current and the next month. Each prayer is an event named `Fajr`, `Shuruq`, `Dhuhr`, `Asr`, `Maghrib` or `Isha` (and `Jumua`, `Jumua 2`, `Jumua 3` on Fridays) whatever your language. It starts at the adhan and ends at the iqama if your mosque publishes it, otherwise when it starts. Use it with a `calendar` trigger, see the examples below.

The adhans of the MAWAQIT mosque screens (Makkah, Madinah, Al-Quds, Al-Afassy, Algeria, Egypt, each with its Fajr version) are available in the media browser. Listen to them in _Media > MAWAQIT_, selecting _This browser_ as the player, then pick one in the **Play media** action of your automation. They are streamed from the MAWAQIT servers.

### Upgrading from version 3.x

Version 4 is a rewrite based on the code submitted to Home Assistant core. Your configuration is migrated automatically when Home Assistant restarts:

* Existing sensors keep their entity IDs (e.g. `sensor.fajr_adhan`), so your automations and dashboards keep working. Only new installations use the names listed above.
* Sensors now belong to a device named after your mosque, and their names start with it (e.g. _My Mosque Fajr Prayer_).
* `sensor.my_mosque` and `sensor.next_salat_preparation` no longer exist.
* `sensor.next_salat_name` now uses lowercase values (`fajr`, `dhuhr`, ...) and also includes `shuruq`. Update automations comparing it to `Fajr`, `Dhuhr`, etc.
* The mosque is changed with **Reconfigure** instead of the integration options.

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
        entity_id: sensor.my_mosque_fajr_prayer # the ID shown in your installation
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

# Play the adhan of Makkah on a speaker
- id: 'isha_adhan'
  alias: Isha adhan
  triggers:
    - trigger: time
      at: sensor.my_mosque_isha_prayer
  actions:
    - action: media_player.play_media
      target:
        entity_id: media_player.living_room
      data:
        media_content_id: media-source://mawaqit/adhan-maquah # adhan-maquah-fajr for Fajr
        media_content_type: audio/mpeg
  mode: single

# Works the same in every language: filter on the event name, not on an entity ID
- id: 'iqama_reminder'
  alias: Notify 5 minutes before each iqama
  triggers:
    - trigger: calendar
      event: end # use start for the adhan
      entity_id: calendar.my_mosque_prayer_times
      offset: "-00:05:00"
  conditions:
    # Prayers without iqama end when they start
    - condition: template
      value_template: "{{ trigger.calendar_event.end != trigger.calendar_event.start }}"
  actions:
    - action: notify.notify
      data:
        message: "Iqama of {{ trigger.calendar_event.summary }} in 5 minutes"
  mode: queued
```

## Reporting a bug

Open an [issue](https://github.com/mawaqit/home-assistant/issues/new?template=bug_report.yml) and attach the diagnostics file: go to _Settings > Devices & Services > MAWAQIT_, open the ⋮ menu of the entry and select **Download diagnostics**. The file contains the prayer times received from MAWAQIT for your mosque. Your MAWAQIT token, your home location and everything identifying your mosque are removed from it.

## Contributing

Contributions are welcome, see [CONTRIBUTING.md](CONTRIBUTING.md).

## Français

Ce composant permet d'intégrer les données de votre mosquée Mawaqit dans Home Assistant. Pour ce faire, Un compte Mawaqit **https://mawaqit.net** est nécessaire.

Le composant est rajouté à Home Assistant (version **2025.3** minimum) sous forme d'une intégration, à installer via [HACS](https://www.hacs.xyz/) en ajoutant ce dépôt comme dépôt personnalisé (catégorie **Intégration**). Pour une installation manuelle, téléchargez **[mawaqit.zip](https://github.com/mawaqit/home-assistant/releases/latest/download/mawaqit.zip)** depuis la dernière release et extrayez-le dans `custom_components/mawaqit` de votre configuration Home Assistant (créez les dossiers s'ils n'existent pas). Ne téléchargez pas le dépôt lui-même : la branche `main` contient des changements pas encore publiés.

Après le redémarrage de Home Assistant, allez dans _Paramètres > Appareils et Services > Ajouter une intégration_ et cherchez **"Mawaqit"**. Entrez le login et mot de passe de votre compte **mawaqit.net** et cliquez sur **Valider**. Choisissez ensuite comment trouver votre mosquée : autour des coordonnées GPS (latitude/longitude) enregistrées dans Home Assistant, ou par mot-clé (comme le nom de la mosquée ou sa ville, avec 5 résultats par page et une option pour lancer une nouvelle recherche). S'il n'y a aucune mosquée autour de vous, le composant vous propose la recherche par mot-clé. Laissez le mot-clé vide pour revenir au choix de la recherche. Sélectionnez enfin votre mosquée préférée. Une seule mosquée peut être configurée : pour en changer, ouvrez _Paramètres > Appareils et Services > MAWAQIT_ et choisissez **Reconfigurer**. Vos sensors gardent leurs identifiants, donc vos automatisations continuent de fonctionner.

L'intégration ajoute un appareil au nom de votre mosquée, avec un lien vers sa page MAWAQIT, et des composants de type ```sensor``` : les 5 horaires des prières, le Shuruq, les iqamas associées (si votre mosquée les publie), les horaires de Jumu'a, ainsi que le nom et l'heure de la prochaine prière (voir le tableau ci-dessus). Leurs identifiants commencent par le nom de la mosquée et suivent la langue de Home Assistant : pour une mosquée nommée « Ma Mosquée », la prière de Fajr est `sensor.ma_mosquee_priere_fajr` et la prochaine prière `sensor.ma_mosquee_nom_de_la_prochaine_priere`. Le nom de la prochaine prière s'affiche traduit (par ex. « Dhohr »), mais vos automatisations utilisent toujours la valeur `dhuhr`. Un calendrier `calendar.ma_mosquee_horaires_des_prieres` contient aussi les prières du mois en cours et du mois suivant : chaque prière est un événement nommé `Fajr`, `Shuruq`, `Dhuhr`, `Asr`, `Maghrib` ou `Isha` (et `Jumua` le vendredi) quelle que soit la langue, de l'adhan jusqu'à l'iqama si votre mosquée la publie. Utilisez-le avec un déclencheur `calendar`, comme un rappel 5 minutes avant la fin de l'événement, donc avant l'iqama.

Les adhans des écrans MAWAQIT (La Mecque, Médine, Al-Qods, Al-Afassy, Algérie, Égypte, chacun avec sa version Fajr) sont disponibles dans le navigateur de médias. Écoutez-les dans _Médias > MAWAQIT_ en choisissant _Ce navigateur_ comme lecteur, puis choisissez-en un dans l'action **Lire un média** de votre automatisation. Ils sont lus depuis les serveurs MAWAQIT.

**Mise à jour depuis la version 3.x** : la configuration est migrée automatiquement au redémarrage. Les sensors existants gardent leurs identifiants (par ex. `sensor.fajr_adhan`), donc vos automatisations continuent de fonctionner. Ils sont regroupés dans un appareil au nom de votre mosquée, et leurs noms commencent par celui-ci (par ex. « Ma Mosquée Prière Fajr »). `sensor.my_mosque` et `sensor.next_salat_preparation` sont supprimés, et `sensor.next_salat_name` renvoie désormais des valeurs en minuscules (`fajr`, `shuruq`, `dhuhr`, ...).

Dans la section ci-dessus, vous avez des exemples de code pour créer des automatismes dans Home Assistant avec les sensors Mawaqit notamment pour lancer l'athan à l'heure de la prière ou encore pour lancer des actions spécifiques (lire le Coran, augmenter le chauffage 10 minutes avant Al-Fajr, ouvrir les volets lors du Shuruq etc...). Les actions sont à adapter en fonction de vote installation Home Assistant.
