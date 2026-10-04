# MAWAQIT pour Home Assistant

ٱلسَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ

[English](README.md) | **Français** | [Deutsch](README.de.md) | [Nederlands](README.nl.md)

Cette intégration ajoute à Home Assistant les horaires de prière de votre mosquée [MAWAQIT](https://mawaqit.net) : les cinq prières, l'Imsak, le Shuruq, les iqamas, la Jumu'a, les moments de la nuit et la date hégirienne, sous forme de sensors et d'un calendrier. Utilisez-les pour lancer l'adhan, recevoir un rappel avant l'iqama, chauffer la maison avant Fajr, ouvrir les volets au Shuruq ou vous réveiller pour le souhour pendant le Ramadan.

- [Prérequis](#prérequis)
- [Installation](#installation)
- [Configuration](#configuration)
- [Entités](#entités)
- [Adhans](#adhans)
- [Exemples d'automatisations](#exemples-dautomatisations)
- [Mises à jour des données](#mises-à-jour-des-données)
- [Limitations connues](#limitations-connues)
- [Dépannage](#dépannage)
- [Mise à jour depuis la version 3](#mise-à-jour-depuis-la-version-3)
- [Suppression](#suppression)
- [Signaler un bug](#signaler-un-bug)

## Prérequis

- Un compte MAWAQIT. Il est gratuit : créez-en un sur [mawaqit.net](https://mawaqit.net) si vous n'en avez pas.
- Home Assistant **2025.3** ou plus récent.
- [HACS](https://www.hacs.xyz/), sauf si vous installez l'intégration manuellement.
- Pour lister les mosquées autour de vous pendant la configuration, l'emplacement de votre domicile renseigné dans [**Paramètres** > **Système** > **Général**](https://my.home-assistant.io/redirect/general/). Vous pouvez aussi chercher votre mosquée par son nom.

## Installation

### Avec HACS

[![Ouvrir le dépôt MAWAQIT dans HACS sur votre Home Assistant.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mawaqit&repository=home-assistant&category=integration)

Le bouton ci-dessus ouvre directement le dépôt dans HACS. Sinon :

1. Dans Home Assistant, ouvrez **HACS**, puis le menu ⋮ en haut à droite, et choisissez **Dépôts personnalisés**.
2. Dans **Dépôt**, entrez `https://github.com/mawaqit/home-assistant`. Dans **Type**, choisissez **Intégration**, puis **Ajouter**.
3. Cherchez **MAWAQIT** dans HACS, ouvrez-la et choisissez **Télécharger**.
4. Redémarrez Home Assistant.

HACS vous préviendra ensuite quand une nouvelle version est disponible.

### Manuellement

1. Téléchargez **[mawaqit.zip](https://github.com/mawaqit/home-assistant/releases/latest/download/mawaqit.zip)** depuis la dernière release.
2. Extrayez-le dans `custom_components/mawaqit` dans le dossier de configuration de Home Assistant, celui qui contient `configuration.yaml`. Créez les dossiers s'ils n'existent pas.
3. Redémarrez Home Assistant.

Ne téléchargez pas le dépôt lui-même : la branche `main` contient des changements pas encore publiés. Pour mettre à jour, refaites ces étapes avec la nouvelle release.

## Configuration

[![Commencer la configuration de MAWAQIT sur votre Home Assistant.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=mawaqit)

1. Allez dans [**Paramètres** > **Appareils et services**](https://my.home-assistant.io/redirect/integrations/), choisissez **Ajouter une intégration** et cherchez **MAWAQIT**.
2. Entrez l'adresse e-mail et le mot de passe de votre compte MAWAQIT.
3. Choisissez comment trouver votre mosquée :
   - **Mosquées autour de ma position** : les mosquées autour de l'emplacement de votre domicile dans Home Assistant. S'il n'y en a aucune, un mot-clé vous est demandé à la place.
   - **Rechercher par mot-clé** : le nom de la mosquée ou de sa ville. Les résultats s'affichent 5 par 5 : choisissez **Page suivante** ou **Page précédente** pour les parcourir, ou **Nouvelle recherche** pour changer de mot-clé. Laissez le mot-clé vide pour revenir au choix de la recherche.
4. Choisissez votre mosquée.

Votre mot de passe MAWAQIT n'est pas enregistré : Home Assistant garde à la place un jeton fourni par MAWAQIT.

### Suivre plusieurs mosquées

Pour suivre aussi une autre mosquée, par exemple celle près de votre travail, ajoutez de nouveau l'intégration comme décrit ci-dessus et choisissez cette mosquée. Si une autre mosquée est déjà configurée et fonctionne, sa connexion est réutilisée : elle ne vous est pas redemandée. Chaque mosquée a son propre appareil et ses propres entités, dont les identifiants commencent par le nom de la mosquée. Une même mosquée ne peut pas être configurée deux fois.

### Changer de mosquée

Pour suivre une autre mosquée à la place d'une mosquée déjà configurée, allez dans **Paramètres** > **Appareils et services** > **MAWAQIT**, ouvrez le menu ⋮ de son entrée et choisissez **Reconfigurer**. Ses entités gardent leurs identifiants, donc vos automatisations et tableaux de bord continuent de fonctionner.

### Se reconnecter

Si MAWAQIT n'accepte plus votre connexion, par exemple après un changement de mot de passe, Home Assistant vous demande de vous reconnecter : dans **Paramètres** > **Appareils et services**, choisissez **Reconfigurer** sur la carte MAWAQIT et entrez votre adresse e-mail et votre nouveau mot de passe. Vos entités et leurs réglages sont conservés. Les autres mosquées configurées avec la même connexion sont reconnectées en même temps.

## Entités

L'intégration ajoute un appareil au nom de votre mosquée, avec un lien vers sa page MAWAQIT, et les entités ci-dessous. Tous les sensors sauf **Nom de la prochaine prière** et la date hégirienne sont des horodatages : Home Assistant les affiche comme une heure, et vous pouvez les utiliser directement dans un déclencheur horaire.

| Entité                                                                  | Description                                                                                                                                                  |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Prière Fajr, Prière Dhuhr, Prière Asr, Prière Maghrib, Prière Isha      | L'adhan des cinq prières du jour.                                                                                                                            |
| Shuruq                                                                  | Le lever du soleil, tel que publié par la mosquée.                                                                                                           |
| Imsak                                                                   | L'Imsak, tel qu'affiché par votre mosquée, avant Fajr. Créé seulement si votre mosquée le publie sur MAWAQIT.                                                |
| Iqama Fajr, Iqama Dhuhr, Iqama Asr, Iqama Maghrib, Iqama Isha           | L'iqama des cinq prières. Créées seulement si votre mosquée publie ses iqamas sur MAWAQIT.                                                                    |
| Prière Jumua, Deuxième prière Jumua, Troisième prière Jumua             | La Jumu'a du vendredi qui vient, ou du jour le vendredi. Seules celles de votre mosquée sont créées.                                                         |
| Fin du premier tiers, Milieu de la nuit, Début du dernier tiers         | La nuit du Maghrib au Fajr suivant : la fin de son premier tiers, son milieu et le début de son dernier tiers.                                               |
| Nom de la prochaine prière                                              | La prochaine prière : `fajr`, `shuruq`, `dhuhr`, `asr`, `maghrib` ou `isha`. L'interface l'affiche traduite (par ex. « Dhohr »), mais les automatisations voient toujours ces valeurs. La Jumu'a n'en fait pas partie : le vendredi, c'est `dhuhr`. |
| Heure de la prochaine prière                                            | L'heure de la prochaine prière.                                                                                                                              |
| Mois hégirien                                                           | Le mois de la date hégirienne de votre mosquée : `muharram`, `safar`, `rabi_al_awwal`, `rabi_al_thani`, `jumada_al_ula`, `jumada_al_akhirah`, `rajab`, `shaban`, `ramadan`, `shawwal`, `dhu_al_qidah` ou `dhu_al_hijjah`. L'interface l'affiche traduit (par ex. « Chaabane »), mais les automatisations voient toujours ces valeurs. |
| Jour hégirien, Année hégirienne                                         | Le jour, de 1 à 30, et l'année de la date hégirienne de votre mosquée.                                                                                       |
| Horaires des prières (calendrier)                                       | Toutes les prières du mois en cours et du mois suivant, voir ci-dessous.                                                                                     |

### Le calendrier des horaires des prières

Chaque prière est un événement nommé `Fajr`, `Shuruq`, `Dhuhr`, `Asr`, `Maghrib` ou `Isha`, et le vendredi `Jumua`, `Jumua 2` et `Jumua 3`. Il commence à l'adhan et se termine à l'iqama si votre mosquée la publie, sinon il se termine dès qu'il commence. Les moments de la nuit sont des événements nommés `End of the first third`, `Middle of the night` et `Start of the last third`, qui se terminent dès qu'ils commencent.

Ces noms restent en anglais quelle que soit votre langue, pour qu'une automatisation qui les utilise fonctionne chez tout le monde. Utilisez le calendrier avec un déclencheur `calendar`, comme dans l'[exemple de rappel avant l'iqama](#exemples-dautomatisations).

### La date hégirienne

Les sensors de la date hégirienne montrent la date affichée sur les écrans de votre mosquée. MAWAQIT la calcule avec le calendrier islamique, décalé de l'ajustement que votre mosquée fixe après l'observation de la lune, ou que MAWAQIT fixe pour toutes les mosquées d'un pays. Elle change à minuit dans le fuseau horaire de la mosquée, pas au Maghrib.

Seule la date du jour est connue : l'ajustement est décidé jour après jour, l'intégration ne peut donc pas savoir à l'avance quand le Ramadan commence ou se termine. Pour lancer une automatisation pendant le Ramadan, utilisez une condition sur **Mois hégirien**, comme dans l'[exemple du souhour](#exemples-dautomatisations).

Pour afficher la date complète sur un tableau de bord, par exemple `22 Rabi' al-Akhir 1448`, ajoutez une carte **Markdown** avec ce contenu et [vos identifiants](#identifiants-des-entités). `state_translated` affiche le mois dans votre langue :

```yaml
type: markdown
content: >
  {{ states('sensor.my_mosque_hijri_day') }}
  {{ state_translated('sensor.my_mosque_hijri_month') }}
  {{ states('sensor.my_mosque_hijri_year') }}
```

### Identifiants des entités

Les identifiants des entités sont formés du nom de la mosquée et du nom de l'entité, **dans la langue qu'avait Home Assistant quand vous avez configuré l'intégration**. Pour une mosquée nommée « Ma Mosquée » :

| Langue   | Fajr                            | Prochaine prière                                 | Calendrier                                |
| -------- | ------------------------------- | ------------------------------------------------ | ----------------------------------------- |
| Français | `sensor.ma_mosquee_priere_fajr` | `sensor.ma_mosquee_nom_de_la_prochaine_priere`   | `calendar.ma_mosquee_horaires_des_prieres` |
| Anglais  | `sensor.ma_mosquee_fajr_prayer` | `sensor.ma_mosquee_next_salat_name`              | `calendar.ma_mosquee_prayer_times`        |

Un identifiant copié d'un exemple ou d'un autre utilisateur peut donc ne pas exister chez vous. Pour trouver les vôtres, allez dans **Paramètres** > **Appareils et services** > **MAWAQIT** et ouvrez l'appareil de votre mosquée : choisissez une entité, puis l'icône ⚙️, pour voir son identifiant. Vous pouvez aussi le renommer à cet endroit. Dans l'éditeur d'automatisations, vous pouvez aussi choisir les entités par leur nom au lieu de taper leur identifiant.

Changer la langue de Home Assistant plus tard ne change pas les identifiants, seulement les noms affichés dans l'interface.

## Adhans

Les adhans des écrans MAWAQIT des mosquées sont disponibles dans le navigateur de médias. Écoutez-les dans **Médias** > **MAWAQIT**, avec **Ce navigateur** comme lecteur, et jouez-les sur une enceinte avec l'action **Lire un média**. Ils sont lus depuis les serveurs MAWAQIT : votre enceinte doit avoir accès à internet.

| Adhan      | Identifiant du média                   | Version Fajr                                |
| ---------- | -------------------------------------- | ------------------------------------------- |
| La Mecque  | `media-source://mawaqit/adhan-maquah`  | `media-source://mawaqit/adhan-maquah-fajr`  |
| Médine     | `media-source://mawaqit/adhan-madina`  | `media-source://mawaqit/adhan-madina-fajr`  |
| Al-Qods    | `media-source://mawaqit/adhan-quds`    | `media-source://mawaqit/adhan-quds-fajr`    |
| Al-Afassy  | `media-source://mawaqit/adhan-afassy`  | `media-source://mawaqit/adhan-afassy-fajr`  |
| Algérie    | `media-source://mawaqit/adhan-algeria` | `media-source://mawaqit/adhan-algeria-fajr` |
| Égypte     | `media-source://mawaqit/adhan-egypt`   | `media-source://mawaqit/adhan-egypt-fajr`   |
| Bip        | `media-source://mawaqit/bip`           |                                             |

## Exemples d'automatisations

Remplacez les identifiants ci-dessous par les vôtres, voir [Identifiants des entités](#identifiants-des-entités). Pour utiliser un exemple, créez une automatisation, ouvrez son menu ⋮, choisissez **Modifier en YAML** et collez-le.

Jouer l'adhan de La Mecque sur une enceinte à Isha :

```yaml
alias: Adhan d'Isha
triggers:
  - trigger: time
    at: sensor.ma_mosquee_priere_isha
actions:
  - action: media_player.play_media
    target:
      entity_id: media_player.salon
    data:
      media_content_id: media-source://mawaqit/adhan-maquah
      media_content_type: audio/mpeg
```

Allumer le chauffage 20 minutes avant Fajr, avec un décalage :

```yaml
alias: Chauffage avant Fajr
triggers:
  - trigger: time
    at:
      entity_id: sensor.ma_mosquee_priere_fajr
      offset: "-00:20:00"
actions:
  - action: climate.turn_on
    target:
      entity_id: climate.chambre
```

Allumer la lumière de la chambre au début du dernier tiers de la nuit :

```yaml
alias: Dernier tiers de la nuit
triggers:
  - trigger: time
    at: sensor.ma_mosquee_debut_du_dernier_tiers
actions:
  - action: light.turn_on
    target:
      entity_id: light.chambre
```

Recevoir une notification 5 minutes avant chaque iqama. L'exemple utilise le calendrier et les noms de ses événements, il fonctionne donc dans toutes les langues :

```yaml
alias: Rappel avant l'iqama
triggers:
  - trigger: calendar
    event: end # start pour l'adhan
    entity_id: calendar.ma_mosquee_horaires_des_prieres
    offset: "-00:05:00"
conditions:
  # Les prières sans iqama se terminent dès qu'elles commencent.
  - condition: template
    value_template: "{{ trigger.calendar_event.end != trigger.calendar_event.start }}"
actions:
  - action: notify.notify
    data:
      message: "Iqama de {{ trigger.calendar_event.summary }} dans 5 minutes"
mode: queued
```

Se réveiller pour le souhour 45 minutes avant Fajr, seulement pendant le Ramadan. La date hégirienne change à minuit : le réveil sonne donc aussi avant le premier jour de jeûne, et pas le matin de l'Aïd :

```yaml
alias: Souhour
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

## Mises à jour des données

- L'intégration récupère les horaires de toute l'année auprès de MAWAQIT à son démarrage, puis toutes les 12 heures. Les changements faits par votre mosquée apparaissent dans les 12 heures, ou tout de suite si vous rechargez l'intégration : **Paramètres** > **Appareils et services** > **MAWAQIT**, menu ⋮ de l'entrée, **Recharger**. Si une mise à jour échoue, les sensors gardent les horaires déjà récupérés et l'intégration réessaie toutes les 15 minutes.
- Les sensors de l'Imsak, des iqamas et de la Jumu'a sont ajoutés dès que votre mosquée les publie, donc eux aussi dans les 12 heures. Si elle arrête de les publier, ils restent et passent à inconnu. Après un rechargement ou un redémarrage, Home Assistant les indique comme n'étant plus fournis, et vous pouvez les supprimer.
- Les sensors des prières, de l'Imsak, des iqamas et de la Jumu'a passent au jour suivant au milieu de la nuit, pas à minuit : après Isha, ils montrent encore les horaires de la journée qui se termine.
- Les moments de la nuit passent à la nuit suivante au Fajr.
- **Nom de la prochaine prière** et **Heure de la prochaine prière** changent à l'heure de chaque prière.
- Les réglages de la date hégirienne de votre mosquée sont récupérés toutes les heures : un changement après l'observation de la lune apparaît donc dans l'heure. Les sensors de la date hégirienne passent au jour suivant à minuit, dans le fuseau horaire de la mosquée. Si une mise à jour échoue, ils gardent les réglages déjà récupérés et l'intégration réessaie toutes les 15 minutes.

Les horaires sont publiés par la mosquée dans son fuseau horaire, et Home Assistant les affiche dans le vôtre. C'est le même instant : une mosquée dans un autre fuseau horaire est affichée à votre heure locale.

## Limitations connues

- Le calendrier ne montre que le mois en cours et le mois suivant : MAWAQIT donne les horaires de chaque jour de l'année, sans l'année.
- Si MAWAQIT a un horaire invalide, seul cet horaire est ignoré : son sensor et son événement du calendrier sont inconnus, ainsi que ce qui en est calculé, comme les moments de la nuit pour un Maghrib ou un Fajr invalide. Un avertissement est écrit dans les journaux.
- Pour les mosquées qui affichent Sabah et Imsak, Sabah est utilisé comme Fajr, comme dans l'application MAWAQIT.

## Dépannage

### MAWAQIT n'est pas dans la liste des intégrations

Redémarrez Home Assistant après avoir installé l'intégration, puis rafraîchissez la page de votre navigateur. Pour une installation manuelle, vérifiez que les fichiers sont dans `custom_components/mawaqit` et pas dans un sous-dossier, comme `custom_components/mawaqit/mawaqit`.

### Mauvais identifiant ou mot de passe

Utilisez l'adresse e-mail et le mot de passe que vous utilisez sur [mawaqit.net](https://mawaqit.net). Vérifiez que vous arrivez à vous y connecter. Si vous avez oublié votre mot de passe, réinitialisez-le sur mawaqit.net.

### Aucune mosquée trouvée autour de ma position

Vérifiez l'emplacement de votre domicile dans **Paramètres** > **Système** > **Général**, ou cherchez votre mosquée par mot-clé. Seules les mosquées inscrites sur MAWAQIT peuvent être trouvées.

### Impossible de se connecter au serveur

Home Assistant n'a pas pu joindre MAWAQIT. Vérifiez que Home Assistant a accès à internet et que [mawaqit.net](https://mawaqit.net) s'ouvre dans votre navigateur, puis réessayez quelques minutes plus tard.

### Les horaires ne correspondent pas à ma mosquée

Comparez-les avec la page de votre mosquée sur [mawaqit.net](https://mawaqit.net). S'ils diffèrent, rechargez l'intégration pour les récupérer à nouveau. Si la page elle-même est fausse, contactez votre mosquée : l'intégration affiche ce qu'elle publie.

Si tous les horaires sont décalés de la même durée, par exemple une heure, vérifiez le fuseau horaire dans **Paramètres** > **Système** > **Général**, ainsi que le réglage **Fuseau horaire** de votre profil, qui peut afficher les heures dans le fuseau de votre navigateur plutôt que dans celui du serveur.

### Les sensors sont indisponibles ou inconnus

Ouvrez **Paramètres** > **Système** > **Journaux** et cherchez `mawaqit`. Des sensors indisponibles signifient en général que MAWAQIT n'a pas pu être joint au démarrage de l'intégration : ils reviennent dès qu'il peut l'être, ou quand vous rechargez l'intégration.

### Journaux de débogage

Pour enregistrer ce que fait l'intégration, allez dans **Paramètres** > **Appareils et services** > **MAWAQIT**, ouvrez le menu ⋮ de l'entrée et choisissez **Activer la journalisation de débogage**. Reproduisez le problème, puis choisissez **Désactiver la journalisation de débogage** : Home Assistant télécharge le fichier de journal. Joignez-le à votre signalement de bug.

Pour enregistrer dès le démarrage de Home Assistant, ajoutez ceci à `configuration.yaml` et redémarrez :

```yaml
logger:
  logs:
    custom_components.mawaqit: debug
```

## Mise à jour depuis la version 3

La version 4 est une réécriture de l'intégration. Avant de mettre à jour, [faites une sauvegarde](https://my.home-assistant.io/redirect/backup/) : revenir à la version 3 ensuite n'est pas possible, car la mise à jour supprime les données enregistrées par la version 3.

Mettez à jour avec HACS, puis redémarrez Home Assistant. Votre configuration est migrée pendant le redémarrage :

- Les sensors existants gardent leurs identifiants, comme `sensor.fajr_adhan`, donc vos automatisations et tableaux de bord continuent de fonctionner. Les nouvelles entités, comme les moments de la nuit et le calendrier, suivent le nommage décrit dans [Identifiants des entités](#identifiants-des-entités).
- Les sensors appartiennent à un appareil au nom de votre mosquée, et leurs noms commencent par celui-ci, par exemple « Ma Mosquée Prière Fajr ».
- `sensor.my_mosque` et `sensor.next_salat_preparation` n'existent plus.
- **Nom de la prochaine prière** utilise désormais des valeurs en minuscules (`fajr`, `dhuhr`, ...) et inclut `shuruq`. Mettez à jour les automatisations et templates qui le comparent à `Fajr`, `Dhuhr`, etc.
- La mosquée se change avec **Reconfigurer** au lieu des options de l'intégration.

## Suppression

1. Allez dans **Paramètres** > **Appareils et services** > **MAWAQIT**, ouvrez le menu ⋮ de l'entrée et choisissez **Supprimer**. Ses entités sont supprimées. Recommencez pour chaque mosquée.
2. Pour supprimer les fichiers, ouvrez **HACS**, puis **MAWAQIT**, et choisissez **Supprimer** dans son menu ⋮. Pour une installation manuelle, supprimez le dossier `custom_components/mawaqit`.
3. Redémarrez Home Assistant.

Votre compte MAWAQIT n'est pas supprimé. Gérez-le sur [mawaqit.net](https://mawaqit.net).

## Signaler un bug

Ouvrez une [issue](https://github.com/mawaqit/home-assistant/issues/new?template=bug_report.yml) et joignez les diagnostics : allez dans **Paramètres** > **Appareils et services** > **MAWAQIT**, ouvrez le menu ⋮ de l'entrée et choisissez **Télécharger les diagnostics**. Le fichier contient les horaires reçus de MAWAQIT pour votre mosquée. Votre jeton MAWAQIT, l'emplacement de votre domicile et tout ce qui identifie votre mosquée en sont retirés.

## Contribuer

Les contributions sont les bienvenues, voir [CONTRIBUTING.md](CONTRIBUTING.md).
