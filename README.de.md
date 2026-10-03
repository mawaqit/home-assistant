# MAWAQIT für Home Assistant

ٱلسَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ

[English](README.md) | [Français](README.fr.md) | **Deutsch** | [Nederlands](README.nl.md)

Diese Integration bringt die Gebetszeiten deiner [MAWAQIT](https://mawaqit.net)-Moschee in Home Assistant: die fünf Gebete, Shuruq, die Iqamas, das Jumu'a-Gebet und die Zeiten der Nacht, als Sensoren und als Kalender. Nutze sie, um den Adhan abzuspielen, vor der Iqama erinnert zu werden, das Haus vor Fajr zu heizen oder die Rollläden bei Shuruq zu öffnen.

- [Voraussetzungen](#voraussetzungen)
- [Installation](#installation)
- [Einrichtung](#einrichtung)
- [Entitäten](#entitäten)
- [Adhans](#adhans)
- [Beispiel-Automationen](#beispiel-automationen)
- [Datenaktualisierung](#datenaktualisierung)
- [Bekannte Einschränkungen](#bekannte-einschränkungen)
- [Fehlerbehebung](#fehlerbehebung)
- [Update von Version 3](#update-von-version-3)
- [Entfernen](#entfernen)
- [Einen Fehler melden](#einen-fehler-melden)

## Voraussetzungen

- Ein MAWAQIT-Konto. Es ist kostenlos: Erstelle eines auf [mawaqit.net](https://mawaqit.net), falls du noch keines hast.
- Home Assistant **2025.3** oder neuer.
- [HACS](https://www.hacs.xyz/), außer du installierst die Integration manuell.
- Um während der Einrichtung die Moscheen in deiner Nähe aufzulisten, den Standort deines Zuhauses unter [**Einstellungen** > **System** > **Allgemein**](https://my.home-assistant.io/redirect/general/). Du kannst deine Moschee auch über ihren Namen suchen.

## Installation

### Mit HACS

[![Öffne deine Home Assistant-Instanz und das MAWAQIT-Repository in HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mawaqit&repository=home-assistant&category=integration)

Die Schaltfläche oben öffnet das Repository direkt in HACS. Andernfalls:

1. Öffne in Home Assistant **HACS**, dann das Menü ⋮ oben rechts, und wähle **Benutzerdefinierte Repositories**.
2. Gib unter **Repository** `https://github.com/mawaqit/home-assistant` ein. Wähle unter **Typ** **Integration** und dann **Hinzufügen**.
3. Suche in HACS nach **MAWAQIT**, öffne es und wähle **Herunterladen**.
4. Starte Home Assistant neu.

HACS benachrichtigt dich dann, wenn eine neue Version verfügbar ist.

### Manuell

1. Lade **[mawaqit.zip](https://github.com/mawaqit/home-assistant/releases/latest/download/mawaqit.zip)** aus dem neuesten Release herunter.
2. Entpacke es nach `custom_components/mawaqit` im Konfigurationsverzeichnis von Home Assistant, dem Ordner mit der `configuration.yaml`. Lege die Ordner an, falls sie nicht existieren.
3. Starte Home Assistant neu.

Lade nicht das Repository selbst herunter: Der Branch `main` enthält unveröffentlichte Änderungen. Wiederhole diese Schritte mit dem neuen Release, um zu aktualisieren.

## Einrichtung

[![Öffne deine Home Assistant-Instanz und starte die Einrichtung von MAWAQIT.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=mawaqit)

1. Gehe zu [**Einstellungen** > **Geräte & Dienste**](https://my.home-assistant.io/redirect/integrations/), wähle **Integration hinzufügen** und suche nach **MAWAQIT**.
2. Gib die E-Mail-Adresse und das Passwort deines MAWAQIT-Kontos ein.
3. Wähle, wie du deine Moschee finden möchtest:
   - **Moscheen in meiner Nähe**: die Moscheen rund um den Standort deines Zuhauses in Home Assistant. Gibt es keine, wirst du stattdessen nach einem Stichwort gefragt.
   - **Per Stichwort suchen**: der Name der Moschee oder ihrer Stadt. Die Ergebnisse kommen zu je 5: Wähle **Nächste Seite** oder **Vorherige Seite**, um sie durchzublättern, oder **Neue Suche**, um das Stichwort zu ändern. Lass das Stichwort leer, um zu den Suchmethoden zurückzukehren.
4. Wähle deine Moschee.

Dein MAWAQIT-Passwort wird nicht gespeichert: Home Assistant speichert stattdessen ein Token von MAWAQIT.

### Die Moschee wechseln

Es kann nur eine Moschee eingerichtet werden. Um einer anderen zu folgen, gehe zu **Einstellungen** > **Geräte & Dienste** > **MAWAQIT**, öffne das Menü ⋮ des Eintrags und wähle **Neu konfigurieren**. Deine Entitäten behalten ihre Entitäts-IDs, sodass deine Automationen und Dashboards weiter funktionieren.

### Erneut anmelden

Wenn MAWAQIT deine Anmeldung nicht mehr akzeptiert, zum Beispiel nach einer Passwortänderung, bittet dich Home Assistant, dich erneut anzumelden: Wähle unter **Einstellungen** > **Geräte & Dienste** **Neu konfigurieren** auf der MAWAQIT-Karte und gib deine E-Mail-Adresse und dein neues Passwort ein. Deine Entitäten und ihre Einstellungen bleiben erhalten.

## Entitäten

Die Integration fügt ein Gerät mit dem Namen deiner Moschee hinzu, verlinkt mit ihrer MAWAQIT-Seite, mit den unten aufgeführten Entitäten. Alle Sensoren außer **Name des nächsten Gebets** sind Zeitstempel: Home Assistant zeigt sie als Uhrzeit an, und du kannst sie direkt in einem Zeit-Auslöser verwenden.

| Entität                                                                    | Beschreibung                                                                                                                                                          |
| -------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Fajr-Gebet, Dhuhr-Gebet, Asr-Gebet, Maghrib-Gebet, Isha-Gebet              | Der Adhan der fünf Gebete des Tages.                                                                                                                                  |
| Shuruq                                                                     | Sonnenaufgang, wie von der Moschee veröffentlicht.                                                                                                                    |
| Fajr Iqama, Dhuhr Iqama, Asr Iqama, Maghrib Iqama, Isha Iqama              | Die Iqama der fünf Gebete. Nur vorhanden, wenn deine Moschee ihre Iqamas auf MAWAQIT veröffentlicht.                                                                 |
| Jumua-Gebet, Zweites Jumua-Gebet, Drittes Jumua-Gebet                      | Das Jumu'a-Gebet des kommenden Freitags, freitags des heutigen Tages. Nur die, die deine Moschee hat, werden angelegt.                                               |
| Ende des ersten Drittels, Mitte der Nacht, Beginn des letzten Drittels     | Die Nacht von Maghrib bis zum nächsten Fajr: das Ende ihres ersten Drittels, ihre Mitte und der Beginn ihres letzten Drittels.                                        |
| Name des nächsten Gebets                                                   | Das nächste Gebet: `fajr`, `shuruq`, `dhuhr`, `asr`, `maghrib` oder `isha`. Die Oberfläche zeigt es übersetzt an, Automationen sehen aber immer diese Werte. Das Jumu'a-Gebet gehört nicht dazu: Freitags ist es `dhuhr`. |
| Zeit des nächsten Gebets                                                   | Die Uhrzeit des nächsten Gebets.                                                                                                                                      |
| Gebetszeiten (Kalender)                                                    | Alle Gebete des aktuellen und des nächsten Monats, siehe unten.                                                                                                       |

### Der Gebetszeiten-Kalender

Jedes Gebet ist ein Ereignis namens `Fajr`, `Shuruq`, `Dhuhr`, `Asr`, `Maghrib` oder `Isha`, freitags außerdem `Jumua`, `Jumua 2` und `Jumua 3`. Es beginnt mit dem Adhan und endet mit der Iqama, wenn deine Moschee sie veröffentlicht, sonst endet es, sobald es beginnt. Die Zeiten der Nacht sind Ereignisse namens `End of the first third`, `Middle of the night` und `Start of the last third`, die enden, sobald sie beginnen.

Diese Namen sind unabhängig von deiner Sprache auf Englisch, damit eine Automation, die nach ihnen filtert, bei allen funktioniert. Verwende den Kalender mit einem `calendar`-Auslöser, wie im [Beispiel zur Erinnerung vor der Iqama](#beispiel-automationen).

### Entitäts-IDs

Entitäts-IDs bestehen aus dem Namen der Moschee und dem Namen der Entität, **in der Sprache, die Home Assistant bei der Einrichtung der Integration hatte**. Für eine Moschee namens „Meine Moschee":

| Sprache  | Fajr                              | Nächstes Gebet                                    | Kalender                               |
| -------- | --------------------------------- | ------------------------------------------------- | -------------------------------------- |
| Deutsch  | `sensor.meine_moschee_fajr_gebet` | `sensor.meine_moschee_name_des_nachsten_gebets`   | `calendar.meine_moschee_gebetszeiten`  |
| Englisch | `sensor.meine_moschee_fajr_prayer`| `sensor.meine_moschee_next_salat_name`            | `calendar.meine_moschee_prayer_times`  |

Eine Entitäts-ID aus einem Beispiel oder von einem anderen Benutzer existiert bei dir also möglicherweise nicht. Um deine zu finden, gehe zu **Einstellungen** > **Geräte & Dienste** > **MAWAQIT** und öffne das Gerät deiner Moschee: Wähle eine Entität und dann das Symbol ⚙️, um ihre Entitäts-ID zu sehen. Dort kannst du sie auch umbenennen. Im Automationseditor kannst du die Entitäten auch über ihren Namen auswählen, statt ihre ID einzutippen.

Wenn du die Sprache von Home Assistant später änderst, ändern sich die Entitäts-IDs nicht, nur die in der Oberfläche angezeigten Namen.

## Adhans

Die Adhans der MAWAQIT-Moscheebildschirme sind im Medienbrowser verfügbar. Höre sie unter **Medien** > **MAWAQIT** mit **Dieser Browser** als Player an und spiele sie mit der Aktion **Medien abspielen** auf einem Lautsprecher ab. Sie werden von den MAWAQIT-Servern gestreamt, dein Lautsprecher braucht also Internetzugang.

| Adhan     | Medien-ID                              | Fajr-Version                                |
| --------- | -------------------------------------- | ------------------------------------------- |
| Mekka     | `media-source://mawaqit/adhan-maquah`  | `media-source://mawaqit/adhan-maquah-fajr`  |
| Medina    | `media-source://mawaqit/adhan-madina`  | `media-source://mawaqit/adhan-madina-fajr`  |
| Al-Quds   | `media-source://mawaqit/adhan-quds`    | `media-source://mawaqit/adhan-quds-fajr`    |
| Al-Afassy | `media-source://mawaqit/adhan-afassy`  | `media-source://mawaqit/adhan-afassy-fajr`  |
| Algerien  | `media-source://mawaqit/adhan-algeria` | `media-source://mawaqit/adhan-algeria-fajr` |
| Ägypten   | `media-source://mawaqit/adhan-egypt`   | `media-source://mawaqit/adhan-egypt-fajr`   |
| Signalton | `media-source://mawaqit/bip`           |                                             |

## Beispiel-Automationen

Ersetze die Entitäts-IDs unten durch deine, siehe [Entitäts-IDs](#entitäts-ids). Um ein Beispiel zu verwenden, erstelle eine Automation, öffne ihr Menü ⋮, wähle **In YAML bearbeiten** und füge es ein.

Den Adhan aus Mekka zu Isha auf einem Lautsprecher abspielen:

```yaml
alias: Isha-Adhan
triggers:
  - trigger: time
    at: sensor.meine_moschee_isha_gebet
actions:
  - action: media_player.play_media
    target:
      entity_id: media_player.wohnzimmer
    data:
      media_content_id: media-source://mawaqit/adhan-maquah
      media_content_type: audio/mpeg
```

Die Heizung 20 Minuten vor Fajr einschalten, mit einem Versatz:

```yaml
alias: Heizung vor Fajr
triggers:
  - trigger: time
    at:
      entity_id: sensor.meine_moschee_fajr_gebet
      offset: "-00:20:00"
actions:
  - action: climate.turn_on
    target:
      entity_id: climate.schlafzimmer
```

Das Licht im Schlafzimmer zu Beginn des letzten Drittels der Nacht einschalten:

```yaml
alias: Letztes Drittel der Nacht
triggers:
  - trigger: time
    at: sensor.meine_moschee_beginn_des_letzten_drittels
actions:
  - action: light.turn_on
    target:
      entity_id: light.schlafzimmer
```

5 Minuten vor jeder Iqama eine Benachrichtigung erhalten. Das Beispiel nutzt den Kalender und filtert nach den Namen seiner Ereignisse, es funktioniert also in jeder Sprache:

```yaml
alias: Erinnerung vor der Iqama
triggers:
  - trigger: calendar
    event: end # start für den Adhan
    entity_id: calendar.meine_moschee_gebetszeiten
    offset: "-00:05:00"
conditions:
  # Gebete ohne Iqama enden, sobald sie beginnen.
  - condition: template
    value_template: "{{ trigger.calendar_event.end != trigger.calendar_event.start }}"
actions:
  - action: notify.notify
    data:
      message: "Iqama von {{ trigger.calendar_event.summary }} in 5 Minuten"
mode: queued
```

## Datenaktualisierung

- Die Integration ruft die Gebetszeiten des ganzen Jahres beim Start von MAWAQIT ab, danach alle 12 Stunden. Änderungen deiner Moschee erscheinen innerhalb von 12 Stunden, oder sofort, wenn du die Integration neu lädst: **Einstellungen** > **Geräte & Dienste** > **MAWAQIT**, Menü ⋮ des Eintrags, **Neu laden**.
- Die Gebets-, Iqama- und Jumu'a-Sensoren wechseln in der Mitte der Nacht auf den nächsten Tag, nicht um Mitternacht: Nach Isha zeigen sie noch die Zeiten des zu Ende gehenden Tages.
- Die Zeiten der Nacht wechseln bei Fajr auf die nächste Nacht.
- **Name des nächsten Gebets** und **Zeit des nächsten Gebets** ändern sich zur Zeit jedes Gebets.

Die Zeiten werden von der Moschee in ihrer Zeitzone veröffentlicht, und Home Assistant zeigt sie in deiner an. Es ist derselbe Zeitpunkt: Eine Moschee in einer anderen Zeitzone wird in deiner Ortszeit angezeigt.

## Bekannte Einschränkungen

- Nur eine Moschee pro Home Assistant-Instanz ([#143](https://github.com/mawaqit/home-assistant/issues/143)).
- Die Iqama- und Jumu'a-Sensoren werden beim Start der Integration angelegt, je nachdem, was deine Moschee zu diesem Zeitpunkt veröffentlicht. Fügt deine Moschee sie später hinzu, lade die Integration neu ([#144](https://github.com/mawaqit/home-assistant/issues/144)).
- Der Kalender zeigt nur den aktuellen und den nächsten Monat: MAWAQIT liefert die Zeiten jedes Tages des Jahres, ohne das Jahr.
- Hat MAWAQIT eine ungültige Zeit, wird nur diese Zeit übersprungen: Ihr Sensor und ihr Kalenderereignis sind unbekannt, ebenso was daraus berechnet wird, etwa die Zeiten der Nacht bei einem ungültigen Maghrib oder Fajr. Eine Warnung wird ins Protokoll geschrieben.
- Bei Moscheen, die Sabah und Imsak anzeigen, wird Sabah als Fajr verwendet, wie in der MAWAQIT-App. Imsak ist nicht verfügbar.
- Die Integration braucht Internetzugang. Ist MAWAQIT nicht erreichbar, werden die Sensoren bis zur nächsten erfolgreichen Aktualisierung nicht verfügbar ([#142](https://github.com/mawaqit/home-assistant/issues/142)).

## Fehlerbehebung

### MAWAQIT ist nicht in der Liste der Integrationen

Starte Home Assistant nach der Installation der Integration neu und lade dann die Seite in deinem Browser neu. Prüfe bei einer manuellen Installation, dass die Dateien in `custom_components/mawaqit` liegen und nicht in einem Unterordner wie `custom_components/mawaqit/mawaqit`.

### Falsche Anmeldedaten

Verwende die E-Mail-Adresse und das Passwort, die du auf [mawaqit.net](https://mawaqit.net) verwendest. Prüfe, ob du dich dort anmelden kannst. Wenn du dein Passwort vergessen hast, setze es auf mawaqit.net zurück.

### Keine Moschee in meiner Nähe gefunden

Prüfe den Standort deines Zuhauses unter **Einstellungen** > **System** > **Allgemein**, oder suche deine Moschee per Stichwort. Nur auf MAWAQIT registrierte Moscheen können gefunden werden.

### Keine Verbindung zum Server

Home Assistant konnte MAWAQIT nicht erreichen. Prüfe, ob Home Assistant Internetzugang hat und ob sich [mawaqit.net](https://mawaqit.net) in deinem Browser öffnet, und versuche es dann einige Minuten später erneut.

### Die Zeiten stimmen nicht mit meiner Moschee überein

Vergleiche sie mit der Seite deiner Moschee auf [mawaqit.net](https://mawaqit.net). Weichen sie ab, lade die Integration neu, um sie erneut abzurufen. Ist die Seite selbst falsch, wende dich an deine Moschee: Die Integration zeigt an, was sie veröffentlicht.

Sind alle Zeiten um denselben Betrag verschoben, zum Beispiel eine Stunde, prüfe die Zeitzone unter **Einstellungen** > **System** > **Allgemein** sowie die Einstellung **Zeitzone** in deinem Benutzerprofil, die Zeiten in der Zeitzone deines Browsers statt in der des Servers anzeigen kann.

### Die Sensoren sind nicht verfügbar oder unbekannt

Öffne **Einstellungen** > **System** > **Protokolle** und suche nach `mawaqit`. Nicht verfügbare Sensoren bedeuten meist, dass MAWAQIT nicht erreicht werden konnte: Sie kommen mit der nächsten erfolgreichen Aktualisierung zurück, oder wenn du die Integration neu lädst.

### Debug-Protokolle

Um aufzuzeichnen, was die Integration tut, gehe zu **Einstellungen** > **Geräte & Dienste** > **MAWAQIT**, öffne das Menü ⋮ des Eintrags und wähle **Debug-Protokollierung aktivieren**. Reproduziere das Problem und wähle dann **Debug-Protokollierung deaktivieren**: Home Assistant lädt die Protokolldatei herunter. Hänge sie an deine Fehlermeldung an.

Um ab dem Start von Home Assistant zu protokollieren, füge dies zur `configuration.yaml` hinzu und starte neu:

```yaml
logger:
  logs:
    custom_components.mawaqit: debug
```

## Update von Version 3

Version 4 ist eine Neufassung der Integration. [Erstelle vor dem Update ein Backup](https://my.home-assistant.io/redirect/backup/): Eine Rückkehr zu Version 3 ist danach nicht möglich, da das Update die von Version 3 gespeicherten Daten löscht.

Aktualisiere mit HACS und starte Home Assistant dann neu. Deine Konfiguration wird beim Neustart migriert:

- Bestehende Sensoren behalten ihre Entitäts-IDs, wie `sensor.fajr_adhan`, sodass deine Automationen und Dashboards weiter funktionieren. Neue Entitäten, wie die Zeiten der Nacht und der Kalender, folgen der unter [Entitäts-IDs](#entitäts-ids) beschriebenen Benennung.
- Die Sensoren gehören zu einem Gerät mit dem Namen deiner Moschee, und ihre Namen beginnen damit, zum Beispiel „Meine Moschee Fajr-Gebet".
- `sensor.my_mosque` und `sensor.next_salat_preparation` gibt es nicht mehr.
- **Name des nächsten Gebets** verwendet jetzt Werte in Kleinbuchstaben (`fajr`, `dhuhr`, ...) und enthält `shuruq`. Passe Automationen und Templates an, die ihn mit `Fajr`, `Dhuhr` usw. vergleichen.
- Die Moschee wird mit **Neu konfigurieren** statt über die Optionen der Integration gewechselt.

## Entfernen

1. Gehe zu **Einstellungen** > **Geräte & Dienste** > **MAWAQIT**, öffne das Menü ⋮ des Eintrags und wähle **Löschen**. Seine Entitäten werden entfernt.
2. Um die Dateien zu entfernen, öffne **HACS**, dann **MAWAQIT**, und wähle **Entfernen** in seinem Menü ⋮. Lösche bei einer manuellen Installation den Ordner `custom_components/mawaqit`.
3. Starte Home Assistant neu.

Dein MAWAQIT-Konto wird nicht gelöscht. Verwalte es auf [mawaqit.net](https://mawaqit.net).

## Einen Fehler melden

Öffne ein [Issue](https://github.com/mawaqit/home-assistant/issues/new?template=bug_report.yml) und hänge die Diagnosedaten an: Gehe zu **Einstellungen** > **Geräte & Dienste** > **MAWAQIT**, öffne das Menü ⋮ des Eintrags und wähle **Diagnosedaten herunterladen**. Die Datei enthält die von MAWAQIT für deine Moschee empfangenen Gebetszeiten. Dein MAWAQIT-Token, der Standort deines Zuhauses und alles, was deine Moschee identifiziert, werden daraus entfernt.

## Mitwirken

Beiträge sind willkommen, siehe [CONTRIBUTING.md](CONTRIBUTING.md).
