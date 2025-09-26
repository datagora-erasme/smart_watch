=======================
Utilisation avec Docker
=======================

**SmartWatch** a été conçu pour pouvoir s'exécuter aussi bien localement que dans un conteneur Docker.

Prérequis
---------

*   **Docker** doit être installé et en cours d'exécution sur votre machine.
*   Vous devez avoir cloné le dépôt et configuré votre fichier ``.env`` comme décrit dans les sections :doc:`installation` et :doc:`configuration`.

Méthode recommandée : Docker Compose
------------------------------------

L'utilisation de ``docker-compose`` est la méthode recommandée car elle simplifie le processus de build et de lancement, tout en gérant correctement les variables d'environnement.

1.  **Assurez-vous que votre fichier ``.env`` est présent** à la racine du projet.

2.  **Lancez l'application avec `docker-compose`** :

    .. code-block:: bash

       docker-compose up --build

    Cette commande unique s'occupe de :
    - Construire l'image Docker si elle n'existe pas ou si le `Dockerfile` a changé.
    - Démarrer le conteneur.
    - Injecter les variables d'environnement depuis le fichier ``.env`` de manière sécurisée.

L'application s'exécutera alors dans le conteneur, en utilisant votre configuration locale, décrite dans la page :doc:`configuration`.

.. warning::
   Le choix du modèle d'embedding est particulièrement important lors de l'utilisation avec Docker. Le modèle le plus performant, ``jinaai/jina-embeddings-v3``, consomme beaucoup de RAM et peut entraîner des problèmes de performance ou de stabilité dans un conteneur. Pour une utilisation avec Docker, il est recommandé d'opter pour des modèles plus légers comme ceux de la série ``sentence-transformers``. Pour plus de détails, consultez le guide sur le :doc:`choix des embeddings <choosing_embeddings>`.
