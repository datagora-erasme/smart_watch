Présentation du projet
======================

Le projet SmartWatch a été créé dans le but de fiabiliser et d'automatiser l'intégration des horaires d'ouverture de lieux publics dans le site data.grandlyon.com.

Les modifications régulières ainsi que le grand nombre de sites concernés (~200) rendent cette opération fastidieuse et chronophage si elle est effectuée manuellement.

L'idée de recourir à l'intelligence artificielle a donc germé, donnant naissance au projet SmartWatch.

Le but de ce projet consiste à exploiter des méthodes probabilistes (des LLM) dans le but d'obtenir des résultats structurés et déterministes.

L'enjeu est de contraindre la sortie du LLM afin d'obtenir des données fiables, reproductibles et structurées.

Dans une démarche d'IA responsable, le projet intègre également le suivi de la consommation carbone des modèles utilisés.

Sommaire
========

Cette documentation détaille les divers modules du projet Smart Watch, leurs interactions et leur architecture technique. Elle est organisée de la manière suivante :

* **Introduction** : Cette section, qui présente le projet.
* **Démarrage** : Contient les guides pour l'installation, la configuration et l'utilisation du projet.
    * :doc:`Installation <installation>`
    * :doc:`Utilisation avec Docker <docker>`
    * :doc:`Configuration du projet <configuration>`
* **Architecture technique** : Fournit une vue d'ensemble de l'architecture du projet.
    * :doc:`Point d'entrée (main.py) <../source/main>`
    * :doc:`Diagramme d'architecture <../architecture/diagramme>`
    * :doc:`Description des modules <../architecture/modules>`
    * :doc:`Base de données <../architecture/bdd>`
    * :doc:`Stack technique <../architecture/stack>`
* **Documentation des Modules** : Offre une documentation détaillée pour chaque module spécifique du projet.
    * :doc:`Configuration <../source/modules/config/index>`
    * :doc:`Core <../source/modules/core/index>`
    * :doc:`Processing <../source/modules/processing/index>`
    * :doc:`Utils <../source/modules/utils/index>`
    * :doc:`Reporting <../source/modules/reporting/index>`
