============
Introduction
============

Le projet SmartWatch a été créé dans le but de fiabiliser et de semi-automatiser l'intégration des horaires d'ouverture de lieux publics sur le site data.grandlyon.com.

Ces données étaient auparavant collectées manuellement sur les sites web des mairies, des bibliothèques et des piscines, puis intégrées manuellement sur datagrandlyon.com.

Les modifications régulières ainsi que le grand nombre de sites concernés (~200) rendaient cette opération fastidieuse et chronophage.

L'idée de recourir à l'intelligence artificielle a donc germé, donnant naissance au projet SmartWatch.

Le but (et l'enjeu) de ce projet consiste à combiner l'utilisation de méthodes probabilistes afin d'obtenir des résultats déterministes et structurés.

L'utilisation de sorties structurées au format JSON est une fonctionnalité récente dans les LLM, mais la réduction des hallucinations dans les réponses demeure un défi, de même que la capacité d'un LLM à remplir des structures complexes.

Cette documentation détaille les divers modules conçus à cette fin, leurs interactions et leur architecture technique.