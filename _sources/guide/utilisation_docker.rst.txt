=======================
Utilisation avec Docker
=======================

**SmartWatch** a été conçu pour pouvoir s'exécuter aussi bien localement que dans un conteneur Docker.

Prérequis
---------

*   **Docker** doit être installé et en cours d'exécution sur votre machine.
*   Vous devez avoir cloné le dépôt et configuré votre fichier ``.env`` comme décrit dans les sections :doc:`installation` et :doc:`configuration`.

Étapes
------

1.  **Construire l'image Docker**

    À la racine du projet (où se trouve le `Dockerfile`), exécutez la commande suivante pour construire l'image, nommée `smartwatch` pour cet exemple.

    .. code-block:: bash

       docker build -t smartwatch .

2.  **Exécuter le conteneur**

    Une fois l'image construite, vous pouvez lancer l'application avec la commande suivante :

    .. code-block:: bash

       docker run --rm --env-file .env smartwatch

L'application s'exécutera alors dans le conteneur, en utilisant votre configuration locale.
