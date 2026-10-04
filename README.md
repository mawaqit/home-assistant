# MAWAQIT for Home Assistant

ٱلسَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ

**English** | [Français](README.fr.md) | [Deutsch](README.de.md) | [Nederlands](README.nl.md)

This integration brings the prayer times of your [MAWAQIT](https://mawaqit.net) mosque into Home Assistant: the five prayers, Imsak, Shuruq, the iqamas, Jumu'a, the Eid prayers, the times of the night and the Hijri date, as sensors and as a calendar. Use them to play the adhan, send a reminder before the iqama, warm up the house before Fajr, open the shutters at Shuruq or wake up for suhoor during Ramadan.

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Setup](#setup)
- [Entities](#entities)
- [Dashboards](#dashboards)
- [Adhans](#adhans)
- [Automation examples](#automation-examples)
- [Data updates](#data-updates)
- [Known limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)
- [Upgrading from version 3](#upgrading-from-version-3)
- [Removal](#removal)
- [Reporting a bug](#reporting-a-bug)

## Prerequisites

- A MAWAQIT account. It is free: create one on [mawaqit.net](https://mawaqit.net) if you do not have one.
- Home Assistant **2025.3** or newer.
- [HACS](https://www.hacs.xyz/), unless you install the integration manually.
- To list the mosques around you during setup, the location of your home set in [**Settings** > **System** > **General**](https://my.home-assistant.io/redirect/general/). You can also find your mosque by name instead.

## Installation

### With HACS

[![Open your Home Assistant instance and open the MAWAQIT repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mawaqit&repository=home-assistant&category=integration)

The button above opens the repository in HACS directly. Otherwise:

1. In Home Assistant, open **HACS**, then the ⋮ menu at the top right, and select **Custom repositories**.
2. In **Repository**, enter `https://github.com/mawaqit/home-assistant`. In **Type**, select **Integration**, then select **Add**.
3. Search for **MAWAQIT** in HACS, open it and select **Download**.
4. Restart Home Assistant.

HACS then notifies you when a new version is available.

### Manually

1. Download **[mawaqit.zip](https://github.com/mawaqit/home-assistant/releases/latest/download/mawaqit.zip)** from the latest release.
2. Extract it into `custom_components/mawaqit` in your Home Assistant configuration directory, the one containing `configuration.yaml`. Create the folders if they do not exist.
3. Restart Home Assistant.

Do not download the repository itself: the `main` branch contains unreleased changes. To update, repeat these steps with the new release.

## Setup

[![Open your Home Assistant instance and start setting up MAWAQIT.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=mawaqit)

1. Go to [**Settings** > **Devices & services**](https://my.home-assistant.io/redirect/integrations/), select **Add integration** and search for **MAWAQIT**.
2. Enter the email address and password of your MAWAQIT account.
3. Choose how to find your mosque:
   - **Mosques around my location**: the mosques around the location of your home in Home Assistant. If there are none, you are asked for a keyword instead.
   - **Search by keyword**: the name of the mosque or of its city. Results come 5 at a time: select **Next page** or **Previous page** to browse them, or **New search** to change the keyword. Leave the keyword empty to go back to the search methods.
4. Select your mosque.

Your MAWAQIT password is not stored: Home Assistant keeps a token from MAWAQIT instead.

### Following several mosques

To also follow another mosque, for example the one near your work, add the integration again as described above and choose that mosque. If another mosque is already set up and working, its login is reused: you are not asked for it again. Each mosque has its own device and entities, whose entity IDs start with the name of the mosque. The same mosque cannot be set up twice.

### Changing the mosque

To follow another mosque instead of one already set up, go to **Settings** > **Devices & services** > **MAWAQIT**, open the ⋮ menu of its entry and select **Reconfigure**. Its entities keep their entity IDs, so your automations and dashboards keep working.

### Logging in again

If MAWAQIT no longer accepts your login, for example after a password change, Home Assistant asks you to log in again: in **Settings** > **Devices & services**, select **Reconfigure** on the MAWAQIT card and enter your email address and new password. Your entities and their settings are kept. The other mosques set up with the same login are logged in again at the same time.

## Entities

The integration adds a device named after your mosque, linked to its page on MAWAQIT, with the entities below. All the sensors except **Next Salat Name** and the Hijri date are timestamps: Home Assistant shows them as a time, and you can use them directly in a time trigger.

| Entity                                                           | Description                                                                                                                                         |
| ---------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fajr Prayer, Dhuhr Prayer, Asr Prayer, Maghrib Prayer, Isha Prayer | The adhan of the five prayers of the day.                                                                                                          |
| Shuruq                                                           | Sunrise, as published by the mosque.                                                                                                                |
| Imsak                                                            | Imsak, as shown by your mosque, before Fajr. Only created if your mosque publishes it on MAWAQIT.                                                   |
| Fajr Iqama, Dhuhr Iqama, Asr Iqama, Maghrib Iqama, Isha Iqama    | The iqama of the five prayers. Only created if your mosque publishes its iqamas on MAWAQIT.                                                         |
| Jumua Prayer, Second Jumua Prayer, Third Jumua Prayer            | Jumu'a of the coming Friday, or of today on Fridays. Only the ones your mosque has are created.                                                     |
| End of the First Third, Middle of the Night, Start of the Last Third | The night from Maghrib to the next Fajr: the end of its first third, its middle and the start of its last third.                                |
| Next Salat Name                                                  | The next prayer: `fajr`, `shuruq`, `dhuhr`, `asr`, `maghrib` or `isha`. The UI shows it translated, but automations always see these values. Jumu'a is not included: on Fridays it is `dhuhr`. |
| Next Salat Time                                                  | The time of the next prayer.                                                                                                                        |
| Hijri Month                                                      | The month of the Hijri date of your mosque: `muharram`, `safar`, `rabi_al_awwal`, `rabi_al_thani`, `jumada_al_ula`, `jumada_al_akhirah`, `rajab`, `shaban`, `ramadan`, `shawwal`, `dhu_al_qidah` or `dhu_al_hijjah`. The UI shows it translated, but automations always see these values. |
| Hijri Day, Hijri Year                                            | The day, from 1 to 30, and the year of the Hijri date of your mosque.                                                                               |
| Picture, Logo (images)                                           | The picture and the logo of your mosque on MAWAQIT, to show on a dashboard. Only created if your mosque publishes them. |
| Prayer Times (calendar)                                          | All the prayers of the current and the next month, see below.                                                                                       |

### The prayer times calendar

Each prayer is an event named `Fajr`, `Shuruq`, `Dhuhr`, `Asr`, `Maghrib` or `Isha`, and on Fridays `Jumua`, `Jumua 2` and `Jumua 3`. It starts at the adhan and ends at the iqama if your mosque publishes it, otherwise it ends when it starts. The times of the night are events named `End of the first third`, `Middle of the night` and `Start of the last third`, which end when they start.

The Eid prayers are events named `Eid al-Fitr` or `Eid al-Adha`, then `Eid al-Fitr 2`, `Eid al-Fitr 3`, and so on, if your mosque publishes them. Like on the screens of the mosque, they appear from 23 Ramadan to 1 Shawwal and from 3 to 10 Dhu al-Hijjah, using the [Hijri date](#the-hijri-date) of the mosque. Eid al-Fitr is shown on the day after the 30th of Ramadan: if the moon is seen on the 29th, it moves one day earlier within an hour of your mosque changing its Hijri date. They end when they start.

These names are in English whatever your language, so an automation filtering on them works for everyone. Use the calendar with a `calendar` trigger, as in the [iqama reminder example](#automation-examples).

### The Hijri date

The Hijri sensors show the date displayed on the screens of your mosque. MAWAQIT computes it with the Islamic calendar, shifted by the adjustment your mosque sets after the moon sighting, or that MAWAQIT sets for all the mosques of a country. It changes at midnight in the time zone of the mosque, not at Maghrib.

Only today's date is known: the adjustment is decided day by day, so the integration cannot tell in advance when Ramadan starts or ends. To run an automation during Ramadan, use a condition on **Hijri Month**, as in the [suhoor example](#automation-examples).

To show the whole date on a dashboard, like `22 Rabi' al-Thani 1448`, add a **Markdown** card with this content and [your entity IDs](#entity-ids). `state_translated` shows the month in your language:

```yaml
type: markdown
content: >
  {{ states('sensor.my_mosque_hijri_day') }}
  {{ state_translated('sensor.my_mosque_hijri_month') }}
  {{ states('sensor.my_mosque_hijri_year') }}
```

### Entity IDs

Entity IDs are made of the name of the mosque and the name of the entity, **in the language Home Assistant had when you set up the integration**. For a mosque named "My Mosque":

| Language | Fajr                            | Next prayer                                      | Calendar                               |
| -------- | ------------------------------- | ------------------------------------------------ | -------------------------------------- |
| English  | `sensor.my_mosque_fajr_prayer`  | `sensor.my_mosque_next_salat_name`               | `calendar.my_mosque_prayer_times`      |
| French   | `sensor.my_mosque_priere_fajr`  | `sensor.my_mosque_nom_de_la_prochaine_priere`    | `calendar.my_mosque_horaires_des_prieres` |

So an entity ID copied from an example or from another user may not exist in your installation. To find yours, go to **Settings** > **Devices & services** > **MAWAQIT** and open the device of your mosque: select an entity, then the ⚙️ icon, to see its entity ID. You can rename it there too. In the automation editor, you can also pick the entities by their name instead of typing their ID.

Changing the language of Home Assistant later does not change the entity IDs, only the names shown in the UI.

## Dashboards

Ready-to-paste dashboards are in [Dashboards for MAWAQIT](docs/dashboards.md): a prayer times card with the picture of your mosque, a next prayer card, and a full-screen view like the screens of your mosque.

[<img alt="Mosque display with a large clock, the Hijri date and the six prayer times on the picture of the mosque" src="docs/images/dashboards/mosque-display-tablet.jpg" width="640">](docs/dashboards.md)

## Adhans

The adhans of the MAWAQIT mosque screens are available in the media browser. Listen to them in **Media** > **MAWAQIT**, with **This browser** as the player, and play them on a speaker with the **Play media** action. They are streamed from the MAWAQIT servers, so your speaker needs internet access.

| Adhan                  | Media ID                                      | Fajr version                                       |
| ---------------------- | --------------------------------------------- | -------------------------------------------------- |
| Makkah                 | `media-source://mawaqit/adhan-maquah`         | `media-source://mawaqit/adhan-maquah-fajr`         |
| Madinah                | `media-source://mawaqit/adhan-madina`         | `media-source://mawaqit/adhan-madina-fajr`         |
| Al-Quds                | `media-source://mawaqit/adhan-quds`           | `media-source://mawaqit/adhan-quds-fajr`           |
| Al-Afassy              | `media-source://mawaqit/adhan-afassy`         | `media-source://mawaqit/adhan-afassy-fajr`         |
| Algeria                | `media-source://mawaqit/adhan-algeria`        | `media-source://mawaqit/adhan-algeria-fajr`        |
| Egypt                  | `media-source://mawaqit/adhan-egypt`          | `media-source://mawaqit/adhan-egypt-fajr`          |
| Beep                   | `media-source://mawaqit/bip`                  |                                                    |

## Automation examples

Replace the entity IDs below with yours, see [Entity IDs](#entity-ids). To use an example, create an automation, open its ⋮ menu, select **Edit in YAML** and paste it.

Play the adhan of Makkah on a speaker at Isha:

```yaml
alias: Isha adhan
triggers:
  - trigger: time
    at: sensor.my_mosque_isha_prayer
actions:
  - action: media_player.play_media
    target:
      entity_id: media_player.living_room
    data:
      media_content_id: media-source://mawaqit/adhan-maquah
      media_content_type: audio/mpeg
```

Turn on the heating 20 minutes before Fajr, with an offset:

```yaml
alias: Heating before Fajr
triggers:
  - trigger: time
    at:
      entity_id: sensor.my_mosque_fajr_prayer
      offset: "-00:20:00"
actions:
  - action: climate.turn_on
    target:
      entity_id: climate.bedroom
```

Turn on the bedroom light at the start of the last third of the night:

```yaml
alias: Last third of the night
triggers:
  - trigger: time
    at: sensor.my_mosque_start_of_the_last_third
actions:
  - action: light.turn_on
    target:
      entity_id: light.bedroom
```

Get a notification 5 minutes before each iqama. It uses the calendar and filters on the event names, so it works in every language:

```yaml
alias: Iqama reminder
triggers:
  - trigger: calendar
    event: end # start for the adhan
    entity_id: calendar.my_mosque_prayer_times
    offset: "-00:05:00"
conditions:
  # Prayers without iqama end when they start.
  - condition: template
    value_template: "{{ trigger.calendar_event.end != trigger.calendar_event.start }}"
actions:
  - action: notify.notify
    data:
      message: "Iqama of {{ trigger.calendar_event.summary }} in 5 minutes"
mode: queued
```

Wake up for suhoor 45 minutes before Fajr, during Ramadan only. The Hijri date changes at midnight, so it also rings before the first fast, and not on the morning of Eid:

```yaml
alias: Suhoor
triggers:
  - trigger: time
    at:
      entity_id: sensor.my_mosque_fajr_prayer
      offset: "-00:45:00"
conditions:
  - condition: state
    entity_id: sensor.my_mosque_hijri_month
    state: ramadan
actions:
  - action: light.turn_on
    target:
      entity_id: light.bedroom
```

## Data updates

- The integration fetches the prayer times of the whole year from MAWAQIT when it starts, then every 12 hours. Changes made by your mosque appear within 12 hours, or right away if you reload the integration: **Settings** > **Devices & services** > **MAWAQIT**, ⋮ menu of the entry, **Reload**. If an update fails, the sensors keep the times already fetched and the integration tries again every 15 minutes.
- The Imsak, iqama and Jumu'a sensors are added as soon as your mosque publishes them, so within 12 hours too. If it stops publishing them, they stay and become unknown. After a reload or a restart, Home Assistant shows them as no longer provided, and you can delete them.
- The pictures are added as soon as your mosque publishes them, and change within 12 hours when it changes them. If it stops publishing one, it becomes unavailable.
- The prayer, Imsak, iqama and Jumu'a sensors move to the next day at the middle of the night, not at midnight: after Isha, they still show the times of the day that is ending.
- The times of the night move to the next night at Fajr.
- **Next Salat Name** and **Next Salat Time** change at the time of each prayer.
- The Hijri date settings of your mosque are fetched every hour, so a change after the moon sighting appears within an hour. The Hijri sensors move to the next day at midnight, in the time zone of the mosque. If an update fails, they keep the settings already fetched and the integration tries again every 15 minutes.

Times are published by the mosque in its own time zone, and Home Assistant shows them in yours. They are the same moment: a mosque in another time zone is shown with your local time.

## Known limitations

- The calendar only shows the current and the next month: MAWAQIT gives the times of each day of the year, without the year.
- If MAWAQIT has an invalid time, only that time is skipped: its sensor and its calendar event are unknown, as well as what is computed from it, such as the times of the night for an invalid Maghrib or Fajr. A warning is written in the logs.
- For mosques that display Sabah and Imsak, Sabah is used as Fajr, like in the MAWAQIT app.

## Troubleshooting

### MAWAQIT is not in the list of integrations

Restart Home Assistant after installing the integration, then refresh the page of your browser. With a manual installation, check that the files are in `custom_components/mawaqit` and not in a sub-folder, such as `custom_components/mawaqit/mawaqit`.

### Wrong login or password

Use the email address and password you use on [mawaqit.net](https://mawaqit.net). Check that you can log in there. If you forgot your password, reset it on mawaqit.net.

### No mosque found around my location

Check the location of your home in **Settings** > **System** > **General**, or search your mosque by keyword. Only mosques registered on MAWAQIT can be found.

### Cannot connect to the server

Home Assistant could not reach MAWAQIT. Check that Home Assistant has internet access and that [mawaqit.net](https://mawaqit.net) opens in your browser, then try again a few minutes later.

### The times do not match my mosque

Compare them with the page of your mosque on [mawaqit.net](https://mawaqit.net). If they differ, reload the integration to fetch them again. If the page itself is wrong, contact your mosque: the integration shows what it publishes.

If all the times are shifted by the same amount, for example one hour, check the time zone in **Settings** > **System** > **General**, and in your user profile the **Time zone** setting, which can show times in the time zone of your browser instead of the one of the server.

### The sensors are unavailable or unknown

Open **Settings** > **System** > **Logs** and search for `mawaqit`. Unavailable sensors usually mean that MAWAQIT could not be reached when the integration started: they come back once it can be reached, or when you reload the integration.

### Debug logs

To capture what the integration does, go to **Settings** > **Devices & services** > **MAWAQIT**, open the ⋮ menu of the entry and select **Enable debug logging**. Reproduce the problem, then select **Disable debug logging**: Home Assistant downloads the log file. Attach it to your bug report.

To log from the start of Home Assistant, add this to `configuration.yaml` and restart:

```yaml
logger:
  logs:
    custom_components.mawaqit: debug
```

## Upgrading from version 3

Version 4 is a rewrite of the integration. Before updating, [make a backup](https://my.home-assistant.io/redirect/backup/): going back to version 3 afterwards is not supported, because the update deletes the data version 3 stored.

Update with HACS, then restart Home Assistant. Your configuration is migrated during the restart:

- Existing sensors keep their entity IDs, such as `sensor.fajr_adhan`, so your automations and dashboards keep working. New entities, such as the times of the night and the calendar, use the naming described in [Entity IDs](#entity-ids).
- The sensors belong to a device named after your mosque, and their names start with it, for example "My Mosque Fajr Prayer".
- `sensor.my_mosque` and `sensor.next_salat_preparation` no longer exist.
- **Next Salat Name** now uses lowercase values (`fajr`, `dhuhr`, ...) and includes `shuruq`. Update the automations and templates comparing it to `Fajr`, `Dhuhr`, etc.
- The mosque is changed with **Reconfigure** instead of the options of the integration.

## Removal

1. Go to **Settings** > **Devices & services** > **MAWAQIT**, open the ⋮ menu of the entry and select **Delete**. Its entities are removed. Repeat for each mosque.
2. To remove the files, open **HACS**, then **MAWAQIT**, and select **Remove** in its ⋮ menu. With a manual installation, delete the `custom_components/mawaqit` folder.
3. Restart Home Assistant.

Your MAWAQIT account is not deleted. Manage it on [mawaqit.net](https://mawaqit.net).

## Reporting a bug

Open an [issue](https://github.com/mawaqit/home-assistant/issues/new?template=bug_report.yml) and attach the diagnostics: go to **Settings** > **Devices & services** > **MAWAQIT**, open the ⋮ menu of the entry and select **Download diagnostics**. The file contains the prayer times received from MAWAQIT for your mosque. Your MAWAQIT token, the location of your home and everything identifying your mosque are removed from it.

## Contributing

Contributions are welcome, see [CONTRIBUTING.md](CONTRIBUTING.md).
