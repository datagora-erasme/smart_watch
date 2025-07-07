============
Installation
============

Ce guide indique comment installer **SmartWatch** sur une machine locale, pour le développement ou l'utilisation directe.

Prérequis
---------

Avant de commencer, assurez-vous d'avoir :

*   **Python 3.13** installé sur votre système.
*   **Git** pour cloner le dépôt.
*   **une clé API** pour un modèle de langage (LLM) compatible OpenAI ou Mistral.

Étapes d'installation
---------------------

1.  **Cloner le dépôt Git**

    Ouvrez un terminal et exécutez la commande suivante pour cloner le projet depuis GitHub :

    .. code-block:: bash

       git clone https://github.com/datagora-erasme/smart_watch
       cd smart_watch

2.  **Créer un environnement virtuel**

    Il est fortement recommandé d'utiliser un environnement virtuel pour isoler les dépendances du projet.

    .. code-block:: bash

       python -m venv .venv

3.  **Activer l'environnement virtuel**

    *   Sur **Windows** :

        .. code-block:: bash

           .venv\Scripts\activate

    *   Sur **Linux ou macOS** :

        .. code-block:: bash

           source .venv/bin/activate


4.  **Installer les dépendances**

    Installez toutes les bibliothèques Python requises à l'aide du fichier ``requirements.txt``.

    .. code-block:: bash

       pip install -r requirements.txt

Une fois ces étapes terminées, votre environnement est prêt. Vous pouvez passer à la section :doc:`configuration` pour configurer l'application.
