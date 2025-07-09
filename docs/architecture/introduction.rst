============
Introduction
============

Le projet SmartWatch a été créé dans le but de fiabiliser et d'automatiser l'intégration des horaires d'ouverture de lieux publics sur le site data.grandlyon.com.

Ces données étaient collectées manuellement sur les sites web des mairies, des bibliothèques et des piscines, puis intégrées sur datagrandlyon.com.

Les modifications régulières ainsi que le grand nombre de sites concernés (~200) rendaient cette opération fastidieuse et chronophage.

L'idée de recourir à l'intelligence artificielle a donc germé, donnant naissance au projet SmartWatch.

Le but (et l'enjeu) de ce projet consiste à exploiter des méthodes probabilistes (des LLM) dans le but d'obtenir des résultats déterministes et structurés.

L'utilisation de sorties structurées au format JSON est une fonctionnalité récente dans les LLM, mais la réduction des hallucinations dans les réponses demeure un défi, de même que la capacité d'un LLM à remplir des structures complexes.

Dans une démarche d'IA responsable, le projet intègre également le suivi de la consommation carbone des modèles utilisés.

Cette documentation détaille les divers modules conçus à cette fin, leurs interactions et leur architecture technique.