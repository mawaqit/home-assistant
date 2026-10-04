# MAWAQIT voor Home Assistant

ٱلسَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ

[English](README.md) | [Français](README.fr.md) | [Deutsch](README.de.md) | **Nederlands**

Deze integratie brengt de gebedstijden van je [MAWAQIT](https://mawaqit.net)-moskee naar Home Assistant: de vijf gebeden, Imsak, Shuruq, de iqama's, het Jumu'a-gebed, de tijden van de nacht en de Hijri-datum, als sensoren en als agenda. Gebruik ze om de adhan af te spelen, een herinnering te krijgen voor de iqama, het huis te verwarmen voor Fajr, de rolluiken te openen bij Shuruq of tijdens de Ramadan wakker te worden voor de suhoor.

- [Vereisten](#vereisten)
- [Installatie](#installatie)
- [Instellen](#instellen)
- [Entiteiten](#entiteiten)
- [Adhans](#adhans)
- [Voorbeeldautomatiseringen](#voorbeeldautomatiseringen)
- [Gegevensupdates](#gegevensupdates)
- [Bekende beperkingen](#bekende-beperkingen)
- [Probleemoplossing](#probleemoplossing)
- [Updaten vanaf versie 3](#updaten-vanaf-versie-3)
- [Verwijderen](#verwijderen)
- [Een bug melden](#een-bug-melden)

## Vereisten

- Een MAWAQIT-account. Het is gratis: maak er een aan op [mawaqit.net](https://mawaqit.net) als je er nog geen hebt.
- Home Assistant **2025.3** of nieuwer.
- [HACS](https://www.hacs.xyz/), tenzij je de integratie handmatig installeert.
- Om tijdens het instellen de moskeeën in je buurt te tonen, de locatie van je huis in [**Instellingen** > **Systeem** > **Algemeen**](https://my.home-assistant.io/redirect/general/). Je kunt je moskee ook op naam zoeken.

## Installatie

### Met HACS

[![Open je Home Assistant-instantie en de MAWAQIT-repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mawaqit&repository=home-assistant&category=integration)

De knop hierboven opent de repository direct in HACS. Anders:

1. Open in Home Assistant **HACS**, dan het menu ⋮ rechtsboven, en kies **Aangepaste repositories**.
2. Vul bij **Repository** `https://github.com/mawaqit/home-assistant` in. Kies bij **Type** **Integratie** en daarna **Toevoegen**.
3. Zoek in HACS naar **MAWAQIT**, open het en kies **Downloaden**.
4. Herstart Home Assistant.

HACS laat je daarna weten wanneer er een nieuwe versie beschikbaar is.

### Handmatig

1. Download **[mawaqit.zip](https://github.com/mawaqit/home-assistant/releases/latest/download/mawaqit.zip)** uit de nieuwste release.
2. Pak het uit in `custom_components/mawaqit` in de configuratiemap van Home Assistant, de map met `configuration.yaml`. Maak de mappen aan als ze niet bestaan.
3. Herstart Home Assistant.

Download niet de repository zelf: de branch `main` bevat nog niet uitgebrachte wijzigingen. Herhaal deze stappen met de nieuwe release om bij te werken.

## Instellen

[![Open je Home Assistant-instantie en begin met het instellen van MAWAQIT.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=mawaqit)

1. Ga naar [**Instellingen** > **Apparaten & diensten**](https://my.home-assistant.io/redirect/integrations/), kies **Integratie toevoegen** en zoek naar **MAWAQIT**.
2. Vul het e-mailadres en wachtwoord van je MAWAQIT-account in.
3. Kies hoe je je moskee wilt vinden:
   - **Moskeeën in de buurt van mijn locatie**: de moskeeën rond de locatie van je huis in Home Assistant. Zijn er geen, dan wordt je in plaats daarvan om een trefwoord gevraagd.
   - **Zoeken op trefwoord**: de naam van de moskee of van haar stad. De resultaten komen per 5: kies **Volgende pagina** of **Vorige pagina** om erdoor te bladeren, of **Nieuwe zoekopdracht** om het trefwoord te wijzigen. Laat het trefwoord leeg om terug te gaan naar de zoekmethoden.
4. Kies je moskee.

Je MAWAQIT-wachtwoord wordt niet opgeslagen: Home Assistant bewaart in plaats daarvan een token van MAWAQIT.

### Meerdere moskeeën volgen

Om ook een andere moskee te volgen, bijvoorbeeld die bij je werk, voeg je de integratie opnieuw toe zoals hierboven beschreven en kies je die moskee. Is er al een andere moskee ingesteld die werkt, dan wordt haar login hergebruikt: je wordt er niet opnieuw om gevraagd. Elke moskee heeft haar eigen apparaat en entiteiten, waarvan de entiteit-ID's met de naam van de moskee beginnen. Dezelfde moskee kan niet twee keer worden ingesteld.

### Van moskee wisselen

Om een andere moskee te volgen in plaats van een moskee die al is ingesteld, ga naar **Instellingen** > **Apparaten & diensten** > **MAWAQIT**, open het menu ⋮ van haar vermelding en kies **Opnieuw configureren**. Haar entiteiten behouden hun entiteit-ID's, dus je automatiseringen en dashboards blijven werken.

### Opnieuw inloggen

Als MAWAQIT je login niet meer accepteert, bijvoorbeeld na een wachtwoordwijziging, vraagt Home Assistant je opnieuw in te loggen: kies in **Instellingen** > **Apparaten & diensten** **Opnieuw configureren** op de MAWAQIT-kaart en vul je e-mailadres en nieuwe wachtwoord in. Je entiteiten en hun instellingen blijven behouden. De andere moskeeën met dezelfde login worden tegelijk opnieuw ingelogd.

## Entiteiten

De integratie voegt een apparaat toe met de naam van je moskee, gekoppeld aan haar MAWAQIT-pagina, met de entiteiten hieronder. Alle sensoren behalve **Naam volgend gebed** en de Hijri-datum zijn tijdstempels: Home Assistant toont ze als een tijd, en je kunt ze direct gebruiken in een tijd-trigger.

| Entiteit                                                                | Beschrijving                                                                                                                                                         |
| ----------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fajr-gebed, Dhuhr-gebed, Asr-gebed, Maghrib-gebed, Isha-gebed           | De adhan van de vijf gebeden van de dag.                                                                                                                             |
| Shuruq                                                                  | Zonsopgang, zoals gepubliceerd door de moskee.                                                                                                                       |
| Imsak                                                                   | Imsak, zoals getoond door je moskee, voor Fajr. Alleen aanwezig als je moskee Imsak op MAWAQIT publiceert.                                                           |
| Fajr Iqama, Dhuhr Iqama, Asr Iqama, Maghrib Iqama, Isha Iqama           | De iqama van de vijf gebeden. Alleen aanwezig als je moskee haar iqama's op MAWAQIT publiceert.                                                                      |
| Jumua-gebed, Tweede Jumua-gebed, Derde Jumua-gebed                      | Het Jumu'a-gebed van de komende vrijdag, of van vandaag op vrijdag. Alleen die van je moskee worden aangemaakt.                                                     |
| Einde eerste derde, Midden van de nacht, Begin laatste derde            | De nacht van Maghrib tot de volgende Fajr: het einde van het eerste derde, het midden en het begin van het laatste derde.                                             |
| Naam volgend gebed                                                      | Het volgende gebed: `fajr`, `shuruq`, `dhuhr`, `asr`, `maghrib` of `isha`. De interface toont het vertaald, maar automatiseringen zien altijd deze waarden. Het Jumu'a-gebed hoort er niet bij: op vrijdag is het `dhuhr`. |
| Tijd volgend gebed                                                      | De tijd van het volgende gebed.                                                                                                                                      |
| Hijri-maand                                                             | De maand van de Hijri-datum van je moskee: `muharram`, `safar`, `rabi_al_awwal`, `rabi_al_thani`, `jumada_al_ula`, `jumada_al_akhirah`, `rajab`, `shaban`, `ramadan`, `shawwal`, `dhu_al_qidah` of `dhu_al_hijjah`. De interface toont de maand vertaald, maar automatiseringen zien altijd deze waarden. |
| Hijri-dag, Hijri-jaar                                                   | De dag, van 1 tot 30, en het jaar van de Hijri-datum van je moskee.                                                                                                  |
| Gebedstijden (agenda)                                                   | Alle gebeden van de huidige en de volgende maand, zie hieronder.                                                                                                     |

### De gebedstijdenagenda

Elk gebed is een afspraak met de naam `Fajr`, `Shuruq`, `Dhuhr`, `Asr`, `Maghrib` of `Isha`, en op vrijdag `Jumua`, `Jumua 2` en `Jumua 3`. Ze begint bij de adhan en eindigt bij de iqama als je moskee die publiceert, anders eindigt ze zodra ze begint. De tijden van de nacht zijn afspraken met de naam `End of the first third`, `Middle of the night` en `Start of the last third`, die eindigen zodra ze beginnen.

Deze namen zijn in het Engels, ongeacht je taal, zodat een automatisering die erop filtert bij iedereen werkt. Gebruik de agenda met een `calendar`-trigger, zoals in het [voorbeeld met een herinnering voor de iqama](#voorbeeldautomatiseringen).

### De Hijri-datum

De Hijri-sensoren tonen de datum die op de schermen van je moskee staat. MAWAQIT berekent die met de islamitische kalender, verschoven met de aanpassing die je moskee na de maanwaarneming instelt, of die MAWAQIT voor alle moskeeën van een land instelt. De datum verandert om middernacht in de tijdzone van de moskee, niet bij Maghrib.

Alleen de datum van vandaag is bekend: de aanpassing wordt van dag tot dag beslist, dus de integratie kan niet vooraf zeggen wanneer de Ramadan begint of eindigt. Gebruik een voorwaarde op **Hijri-maand** om een automatisering tijdens de Ramadan uit te voeren, zoals in het [suhoor-voorbeeld](#voorbeeldautomatiseringen).

### Entiteit-ID's

Entiteit-ID's bestaan uit de naam van de moskee en de naam van de entiteit, **in de taal die Home Assistant had toen je de integratie instelde**. Voor een moskee met de naam "Mijn Moskee":

| Taal       | Fajr                             | Volgend gebed                            | Agenda                                |
| ---------- | -------------------------------- | ---------------------------------------- | ------------------------------------- |
| Nederlands | `sensor.mijn_moskee_fajr_gebed`  | `sensor.mijn_moskee_naam_volgend_gebed`  | `calendar.mijn_moskee_gebedstijden`   |
| Engels     | `sensor.mijn_moskee_fajr_prayer` | `sensor.mijn_moskee_next_salat_name`     | `calendar.mijn_moskee_prayer_times`   |

Een entiteit-ID uit een voorbeeld of van een andere gebruiker bestaat bij jou dus misschien niet. Om de jouwe te vinden, ga naar **Instellingen** > **Apparaten & diensten** > **MAWAQIT** en open het apparaat van je moskee: kies een entiteit en dan het pictogram ⚙️ om haar entiteit-ID te zien. Daar kun je haar ook hernoemen. In de automatiseringseditor kun je de entiteiten ook op naam kiezen in plaats van hun ID te typen.

Als je de taal van Home Assistant later wijzigt, veranderen de entiteit-ID's niet, alleen de namen in de interface.

## Adhans

De adhans van de MAWAQIT-moskeeschermen zijn beschikbaar in de mediabrowser. Beluister ze in **Media** > **MAWAQIT** met **Deze browser** als speler, en speel ze af op een speaker met de actie **Media afspelen**. Ze worden gestreamd vanaf de MAWAQIT-servers, dus je speaker heeft internettoegang nodig.

| Adhan     | Media-ID                               | Fajr-versie                                 |
| --------- | -------------------------------------- | ------------------------------------------- |
| Mekka     | `media-source://mawaqit/adhan-maquah`  | `media-source://mawaqit/adhan-maquah-fajr`  |
| Medina    | `media-source://mawaqit/adhan-madina`  | `media-source://mawaqit/adhan-madina-fajr`  |
| Al-Quds   | `media-source://mawaqit/adhan-quds`    | `media-source://mawaqit/adhan-quds-fajr`    |
| Al-Afassy | `media-source://mawaqit/adhan-afassy`  | `media-source://mawaqit/adhan-afassy-fajr`  |
| Algerije  | `media-source://mawaqit/adhan-algeria` | `media-source://mawaqit/adhan-algeria-fajr` |
| Egypte    | `media-source://mawaqit/adhan-egypt`   | `media-source://mawaqit/adhan-egypt-fajr`   |
| Piep      | `media-source://mawaqit/bip`           |                                             |

## Voorbeeldautomatiseringen

Vervang de entiteit-ID's hieronder door de jouwe, zie [Entiteit-ID's](#entiteit-ids). Om een voorbeeld te gebruiken, maak een automatisering aan, open het menu ⋮, kies **Bewerken in YAML** en plak het.

De adhan uit Mekka afspelen op een speaker bij Isha:

```yaml
alias: Isha-adhan
triggers:
  - trigger: time
    at: sensor.mijn_moskee_isha_gebed
actions:
  - action: media_player.play_media
    target:
      entity_id: media_player.woonkamer
    data:
      media_content_id: media-source://mawaqit/adhan-maquah
      media_content_type: audio/mpeg
```

De verwarming 20 minuten voor Fajr aanzetten, met een verschuiving:

```yaml
alias: Verwarming voor Fajr
triggers:
  - trigger: time
    at:
      entity_id: sensor.mijn_moskee_fajr_gebed
      offset: "-00:20:00"
actions:
  - action: climate.turn_on
    target:
      entity_id: climate.slaapkamer
```

Het licht in de slaapkamer aanzetten bij het begin van het laatste derde van de nacht:

```yaml
alias: Laatste derde van de nacht
triggers:
  - trigger: time
    at: sensor.mijn_moskee_begin_laatste_derde
actions:
  - action: light.turn_on
    target:
      entity_id: light.slaapkamer
```

Een melding krijgen 5 minuten voor elke iqama. Het voorbeeld gebruikt de agenda en filtert op de namen van de afspraken, dus het werkt in elke taal:

```yaml
alias: Herinnering voor de iqama
triggers:
  - trigger: calendar
    event: end # start voor de adhan
    entity_id: calendar.mijn_moskee_gebedstijden
    offset: "-00:05:00"
conditions:
  # Gebeden zonder iqama eindigen zodra ze beginnen.
  - condition: template
    value_template: "{{ trigger.calendar_event.end != trigger.calendar_event.start }}"
actions:
  - action: notify.notify
    data:
      message: "Iqama van {{ trigger.calendar_event.summary }} over 5 minuten"
mode: queued
```

Wakker worden voor de suhoor, 45 minuten voor Fajr, alleen tijdens de Ramadan. De Hijri-datum verandert om middernacht, dus de wekker gaat ook voor de eerste vastendag af, en niet op de ochtend van het Suikerfeest:

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

## Gegevensupdates

- De integratie haalt de gebedstijden van het hele jaar op bij MAWAQIT wanneer ze start, en daarna elke 12 uur. Wijzigingen van je moskee verschijnen binnen 12 uur, of meteen als je de integratie herlaadt: **Instellingen** > **Apparaten & diensten** > **MAWAQIT**, menu ⋮ van de vermelding, **Herladen**. Mislukt een update, dan houden de sensoren de al opgehaalde tijden en probeert de integratie het elke 15 minuten opnieuw.
- De Imsak-, iqama- en Jumu'a-sensoren worden aangemaakt zodra je moskee ze publiceert, dus ook binnen 12 uur. Stopt ze daarmee, dan blijven ze bestaan en worden ze onbekend. Na het herladen of herstarten toont Home Assistant ze als niet meer geleverd, en kun je ze verwijderen.
- De gebeds-, Imsak-, iqama- en Jumu'a-sensoren gaan midden in de nacht naar de volgende dag, niet om middernacht: na Isha tonen ze nog de tijden van de dag die eindigt.
- De tijden van de nacht gaan bij Fajr naar de volgende nacht.
- **Naam volgend gebed** en **Tijd volgend gebed** veranderen op het tijdstip van elk gebed.
- De instellingen van de Hijri-datum van je moskee worden elk uur opgehaald, dus een wijziging na de maanwaarneming verschijnt binnen het uur. De Hijri-sensoren gaan om middernacht naar de volgende dag, in de tijdzone van de moskee. Mislukt een update, dan houden ze de al opgehaalde instellingen en probeert de integratie het elke 15 minuten opnieuw.

De tijden worden door de moskee in haar tijdzone gepubliceerd, en Home Assistant toont ze in de jouwe. Het is hetzelfde moment: een moskee in een andere tijdzone wordt in jouw lokale tijd getoond.

## Bekende beperkingen

- De agenda toont alleen de huidige en de volgende maand: MAWAQIT geeft de tijden van elke dag van het jaar, zonder het jaar.
- Als MAWAQIT een ongeldige tijd heeft, wordt alleen die tijd overgeslagen: de sensor en de agenda-afspraak ervan zijn onbekend, net als wat ervan wordt berekend, zoals de tijden van de nacht bij een ongeldige Maghrib of Fajr. Er wordt een waarschuwing in de logboeken geschreven.
- Voor moskeeën die Sabah en Imsak tonen, wordt Sabah als Fajr gebruikt, zoals in de MAWAQIT-app.

## Probleemoplossing

### MAWAQIT staat niet in de lijst met integraties

Herstart Home Assistant na het installeren van de integratie en vernieuw daarna de pagina in je browser. Controleer bij een handmatige installatie dat de bestanden in `custom_components/mawaqit` staan en niet in een submap, zoals `custom_components/mawaqit/mawaqit`.

### Verkeerde login of wachtwoord

Gebruik het e-mailadres en wachtwoord die je op [mawaqit.net](https://mawaqit.net) gebruikt. Controleer of je daar kunt inloggen. Ben je je wachtwoord vergeten, stel het dan opnieuw in op mawaqit.net.

### Geen moskee gevonden in de buurt van mijn locatie

Controleer de locatie van je huis in **Instellingen** > **Systeem** > **Algemeen**, of zoek je moskee op trefwoord. Alleen moskeeën die op MAWAQIT staan kunnen worden gevonden.

### Kan geen verbinding maken met de server

Home Assistant kon MAWAQIT niet bereiken. Controleer of Home Assistant internettoegang heeft en of [mawaqit.net](https://mawaqit.net) opent in je browser, en probeer het enkele minuten later opnieuw.

### De tijden komen niet overeen met mijn moskee

Vergelijk ze met de pagina van je moskee op [mawaqit.net](https://mawaqit.net). Wijken ze af, herlaad dan de integratie om ze opnieuw op te halen. Is de pagina zelf fout, neem dan contact op met je moskee: de integratie toont wat zij publiceert.

Zijn alle tijden met dezelfde duur verschoven, bijvoorbeeld een uur, controleer dan de tijdzone in **Instellingen** > **Systeem** > **Algemeen**, en de instelling **Tijdzone** in je gebruikersprofiel, die tijden kan tonen in de tijdzone van je browser in plaats van die van de server.

### De sensoren zijn onbeschikbaar of onbekend

Open **Instellingen** > **Systeem** > **Logboeken** en zoek naar `mawaqit`. Onbeschikbare sensoren betekenen meestal dat MAWAQIT niet bereikt kon worden toen de integratie startte: ze komen terug zodra het weer bereikbaar is, of wanneer je de integratie herlaadt.

### Debuglogboeken

Om vast te leggen wat de integratie doet, ga naar **Instellingen** > **Apparaten & diensten** > **MAWAQIT**, open het menu ⋮ van de vermelding en kies **Debuglogboek inschakelen**. Reproduceer het probleem en kies dan **Debuglogboek uitschakelen**: Home Assistant downloadt het logbestand. Voeg het toe aan je bugmelding.

Om vanaf de start van Home Assistant te loggen, voeg dit toe aan `configuration.yaml` en herstart:

```yaml
logger:
  logs:
    custom_components.mawaqit: debug
```

## Updaten vanaf versie 3

Versie 4 is een herschreven versie van de integratie. [Maak een back-up](https://my.home-assistant.io/redirect/backup/) voordat je bijwerkt: teruggaan naar versie 3 is daarna niet mogelijk, omdat de update de gegevens verwijdert die versie 3 had opgeslagen.

Werk bij met HACS en herstart daarna Home Assistant. Je configuratie wordt tijdens het herstarten gemigreerd:

- Bestaande sensoren behouden hun entiteit-ID's, zoals `sensor.fajr_adhan`, dus je automatiseringen en dashboards blijven werken. Nieuwe entiteiten, zoals de tijden van de nacht en de agenda, volgen de naamgeving uit [Entiteit-ID's](#entiteit-ids).
- De sensoren horen bij een apparaat met de naam van je moskee, en hun namen beginnen daarmee, bijvoorbeeld "Mijn Moskee Fajr-gebed".
- `sensor.my_mosque` en `sensor.next_salat_preparation` bestaan niet meer.
- **Naam volgend gebed** gebruikt nu waarden in kleine letters (`fajr`, `dhuhr`, ...) en bevat `shuruq`. Pas automatiseringen en templates aan die het vergelijken met `Fajr`, `Dhuhr`, enz.
- Van moskee wissel je met **Opnieuw configureren** in plaats van via de opties van de integratie.

## Verwijderen

1. Ga naar **Instellingen** > **Apparaten & diensten** > **MAWAQIT**, open het menu ⋮ van de vermelding en kies **Verwijderen**. De entiteiten worden verwijderd. Herhaal dit voor elke moskee.
2. Om de bestanden te verwijderen, open **HACS**, dan **MAWAQIT**, en kies **Verwijderen** in het menu ⋮. Verwijder bij een handmatige installatie de map `custom_components/mawaqit`.
3. Herstart Home Assistant.

Je MAWAQIT-account wordt niet verwijderd. Beheer het op [mawaqit.net](https://mawaqit.net).

## Een bug melden

Open een [issue](https://github.com/mawaqit/home-assistant/issues/new?template=bug_report.yml) en voeg de diagnostische gegevens toe: ga naar **Instellingen** > **Apparaten & diensten** > **MAWAQIT**, open het menu ⋮ van de vermelding en kies **Diagnostische gegevens downloaden**. Het bestand bevat de gebedstijden die van MAWAQIT voor je moskee zijn ontvangen. Je MAWAQIT-token, de locatie van je huis en alles wat je moskee identificeert, worden eruit verwijderd.

## Bijdragen

Bijdragen zijn welkom, zie [CONTRIBUTING.md](CONTRIBUTING.md).
