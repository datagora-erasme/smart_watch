Markdown Cleaner
================

Le module ``MarkdownCleaner`` nettoie et normalise le contenu Markdown obtenu après la conversion de pages web HTML. Il prépare ainsi le texte pour une analyse efficace par les modèles de langage.

Fonctionnalités
---------------

- Élimine tous les types de liens Markdown et les images autonomes, ne conservant que le texte pertinent.
- Supprime les lignes qui ne contiennent que des caractères de mise en forme (comme `---`, `###`, `* * *`).
- Applique un ensemble de remplacements de caractères définis dans la configuration pour corriger les erreurs de formatage courantes (espaces multiples, etc.).
- Élimine les lignes vides consécutives et les lignes de contenu identiques qui se suivent.

.. admonition:: Usage

   La classe ``MarkdownCleaner`` est utilisé dans le :doc:`pipeline principal <../../../architecture/diagramme>` de ``main.py``. La fonction ``process_markdown_cleaning`` récupère les textes bruts depuis la colonne ``markdown_brut`` de la table ``resultats_extraction`` (cf :doc:`bdd <../../../architecture/bdd>`), les nettoie, et enregistre la version nettoyée dans la colonne ``markdown_nettoye`` de la même table.

Modules
-------

.. automodule:: src.smart_watch.utils.MarkdownCleaner
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :inherited-members:
   :show-inheritance:
