# homeassistant-mawaqit
English and Arabic versions below:
Al Salam Aleikom,

ce composent permet d'intégrer les données d'une mosquée mawaqit dans son installation homeassistant. Pour ce faire, Un compte mawaqit est nécessaire. Visitez https://mawaqit.net/ pour créer un compte.

Le composent est rajouté à homeassistant sous forme d'integrations. Pour l'installation, il faur copier le dossier mawaqit dans le répertoire custom_components de votre installation homeassistant (créez le s'il n'existe pas).

Après le redémarrage de homeassistant, allez dans configuration>intégrations et cherchez "mawaqit". Entre le login et mot de posse et cliquez sur soumettre. En se basant sur vos coordonnées latitude/longitude enregistrés dans homeassistant, le composent cherche les mosquée mawaqit dans un rayon de 20km proche de vous et vous demande de sélectionner votre mosquée préférée.

L'integration permet de rajouter 6 composants de type sensor: les 5 horaires des prières et un sensor résumant toute les données de votre mosquée (adresse, site web, jumaa, iqama,...)

Dans le fichier configuration.yaml, vous avez un exemple de code pour créer des automatismes dans homeassistant avec les sensors mawaqit notamment pour lancer l'athan à l'heure de prière ou encore lancer des actions spécifiques (lire le coran par exemple) avant 15 minutes de l'appel à la prière. les actions sont à adapter en fonction de vote installation homeassistant.


@######################## English Version ################@

The component permits to link homeassistant with the nearest mawaqit mosque in your neighborhood. Data of the mosque and prayer times are added as sensors to home assistant.
For the integration, an account on mawaqit is needed. more information on mawaqit is available at https://mawaqit.net/.

The component is added as an integration to homeassistant. for its installation, you need to copy the mawaqit folder into  the custom_components directory of your homeassistant installation (create it if it does not exist).

After restarting homeassistant, you search for "mawaqit" in homeassistant integrations. You enter your mawaqit login/password. Based on your homeassistant latitude/longitude coordinates, the component searches for the nearest mawaqit mosque. You are then asked to select your preferred mosque in the neighborhood.

6 sensors are added: the 5 prayer times and a my_mosque sensor with comprehensive data on your mosque (address, jumaa, website, phone...)

In the configuration.yaml file, you have needed code and automations to hava athan iqama at prayer time.

@######################## Arabic Version ################@
