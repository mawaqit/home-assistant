# homeassistant-mawaqit

ٱلسَّلَامُ عَلَيْكُمْ وَرَحْمَةُ ٱللَّٰهِ وَبَرَكَاتُهُ,
as-salāmu ʿalaykum ,

English and French versions below:


@######################## French Version ################@

Ce composant permet d'intégrer les données de votre mosquée mawaqit dans votre installation homeassistant. Pour ce faire, Un compte mawaqit https://mawaqit.net/ est nécessaire.

Le composant est rajouté à homeassistant sous forme d'une integration. Pour l'installation, il faut copier le dossier mawaqit dans le répertoire custom_components de votre installation homeassistant (créez le s'il n'existe pas).

Après le redémarrage de homeassistant, allez dans configuration > intégrations et cherchez "mawaqit". Entrez le login et mot de passe et cliquez sur soumettre. En se basant sur vos coordonnées GPS (latitude/longitude) enregistrées dans homeassistant, le composant cherche les mosquées mawaqit dans un rayon de 20km proche de vous et vous demande de sélectionner votre mosquée préférée.

L'integration permet de rajouter 6 composants de type sensor: les 5 horaires des prières et un sensor sensor.my_mosque qui résume toutes les données de votre mosquée (adresse, site web, jumaa, iqama,...)

Dans le fichier configuration.yaml, vous avez un exemple de code pour créer des automatismes dans homeassistant avec les sensors mawaqit notamment pour lancer l'athan à l'heure de la prière ou encore pour lancer des actions spécifiques (lire le coran, augmenter le chauffage 10 min avant Al-fajr, ouvrer les volets lors du shuruq ...etc)  15 minutes avant l'appel à la prière. Les actions sont à adapter en fonction de vote installation homeassistant.

![Alt text](/image1.png?raw=true "Optional Title")
![Alt text](/image2.png?raw=true "Optional Title")

@######################## English Version ################@

The component permits to link homeassistant to the nearest mawaqit mosque in your neighborhood.

Data of the mosque and prayer times are added as sensors to home assistant.
For the integration, an account at mawaqit is needed. More information on mawaqit is available at https://mawaqit.net/.

The component is added as an integration to homeassistant. for its installation, you need to copy the mawaqit folder into  the custom_components directory of your homeassistant installation (create it if it does not exist).

After restarting homeassistant, you search for "mawaqit" within the homeassistant integrations. You enter your mawaqit login/password and based on your homeassistant latitude/longitude coordinates, the component searches for the nearest mawaqit mosque. You are then asked to select your preferred mosque in the neighborhood.

6 sensors are added: the 5 prayer times and a my_mosque sensor with comprehensive data on your mosque (address, jumaa, website, phone...)

In the configuration.yaml file, you have an example of needed code and automations to interact with the mawaqit sensors. For instance, you have the athan automation at prayer time or specefic actions to trigger few minutes before the athan call. The actions specified in the automations are to adjust based on your homeassistant installation

@######################## Arabic Version ################@
