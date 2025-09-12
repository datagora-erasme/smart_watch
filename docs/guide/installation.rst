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

    Ensuite, accédez au répertoire du projet :

    .. code-block:: bash

       cd smart_watch

2.  **Créer un environnement virtuel et installer les dépendances**

    Vous avez deux options pour cette étape :

    **Option A : Avec `pip` (méthode classique)**

    Créez un environnement virtuel :

    .. code-block:: bash

       python -m venv .venv

    Activez l'environnement virtuel :

    *   Sur **Windows** :

        .. code-block:: bash

           .venv\Scripts\activate

    *   Sur **Linux ou macOS** :

        .. code-block:: bash

           source .venv/bin/activate

    Installez les dépendances :

    .. code-block:: bash

       pip install -r requirements.txt

    **Option B : Avec `uv` (méthode recommandée, plus rapide)**

    Installez d'abord `uv` si ce n'est pas déjà fait :

    .. code-block:: bash

       pip install uv

    Créez, activez et installez les dépendances en une seule commande :

    .. code-block:: bash

       uv sync

    Pour activer l'environnement par la suite :

    *   Sur **Windows** :

        .. code-block:: bash

           .venv\Scripts\activate

    *   Sur **Linux ou macOS** :

        .. code-block:: bash

           source .venv/bin/activate

3.  **Installez les navigateurs Playwright :**

    .. code-block:: bash

       python -m playwright install

    Sur Linux, si des dépendances système sont manquantes, exécutez d'abord :

    .. code-block:: bash

       python -m playwright install-deps

    Sur Windows, la commande `install` suffit généralement.

Si vous préférez l'option conteneurisée, vous pouvez suivre les instructions de la page :doc:`docker` pour exécuter l'application dans un conteneur Docker.

Une fois ces étapes terminées, votre environnement est prêt. Vous pouvez passer à la section :doc:`configuration` pour configurer l'application.
