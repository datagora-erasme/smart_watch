Markdown Filtering Configuration
================================

Le module ``MarkdownFilteringConfigManager`` configure le filtrage sémantique des textes Markdown. Son rôle est de paramétrer le processus qui identifie et extrait les sections de texte pertinentes (comme les horaires d'ouverture) en utilisant des modèles d'embeddings.

Fonctionnalités
---------------

- **Détection du Fournisseur d'Embeddings** : Comme pour les LLMs, le fournisseur est détecté automatiquement selon les variables d'environnement, avec la priorité suivante :
    1. **OpenAI** (ou compatible) si ``EMBED_API_KEY_OPENAI`` est définie.
    2. **Mistral** si ``EMBED_API_KEY_MISTRAL`` est définie.
    3. **Modèle Local** par défaut.
- **Paramètres de Filtrage Sémantique** : Configure tous les aspects du filtrage :
    - ``REFERENCE_PHRASES`` : Une liste de phrases de référence (séparées par ``;;``) contre lesquelles le contenu est comparé.
    - ``SIMILARITY_THRESHOLD`` : Le score de similarité (entre 0.0 et 1.0) requis pour qu'un morceau de texte soit considéré comme pertinent.
    - ``CHUNK_SIZE`` et ``CHUNK_OVERLAP`` : La taille des segments de texte et leur chevauchement lors de la création des embeddings.
- **Validation Rigoureuse** : La méthode ``validate`` vérifie la cohérence des paramètres (ex: ``CHUNK_OVERLAP`` doit être inférieur à ``CHUNK_SIZE``), la validité de leurs valeurs, et la présence des clés d'API pour les fournisseurs distants.

.. admonition:: Usage

   Ce gestionnaire est instancié par le :doc:`ConfigManager <../core/ConfigManager>`. L'application accède à ses paramètres via ``ConfigManager.markdown_filtering`` pour configurer le ``MarkdownProcessor``.

Modules
-------

.. automodule:: src.smart_watch.config.markdown_filtering_config
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__
   :show-inheritance:
