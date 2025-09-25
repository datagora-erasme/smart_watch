URL Processor
=============

Le ``URLProcessor`` est la deuxième étape du pipeline. Il est chargé de récupérer le contenu web pour chaque lieu et de le convertir en Markdown brut.

Fonctionnalités
---------------

- **Traitement des URLs en Attente** : Récupère la liste des URLs à traiter pour l'exécution en cours auprès du :doc:`DatabaseProcessor <database_processor>`.
- **Récupération de Contenu Web** : Pour chaque URL, il utilise la fonction ``retrieve_url`` (du module ``URLRetriever``) qui se sert de Playwright pour naviguer sur la page et en extraire le contenu HTML.
- **Conversion en Markdown** : Le contenu HTML récupéré est immédiatement converti en Markdown brut.
- **Mise à Jour de la Base de Données** : Le statut de la requête (succès, erreur), le code HTTP, et le Markdown brut sont sauvegardés en base de données via le :doc:`DatabaseProcessor <database_processor>`.

.. admonition:: Note sur le traitement séquentiel

   Bien qu'initialement conçu pour un traitement parallèle, ce processeur fonctionne de manière **séquentielle**. L'utilisation de l'API synchrone de Playwright pour la récupération des URLs ne permet pas une parallélisation simple avec des threads.

Modules
-------

.. automodule:: src.smart_watch.processing.urlprocessor
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
