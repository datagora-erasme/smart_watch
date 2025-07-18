.. _main:

#####################
Orchestrateur ``main.py``
#####################

Le fichier ``main.py`` est le point d'entrée principal de l'application **SmartWatch**. 
Il orchestre l'ensemble du processus d'extraction, de traitement et de comparaison des horaires.

Principaux composants
======================

Le script est structuré autour de la classe ``HoraireExtractor`` qui encapsule la logique métier, 
et d'une fonction ``main()`` qui sert de point d'entrée.

Modules
-------

.. automodule:: main
   :members:
   :undoc-members:
   :private-members:
   :special-members: __init__, __call__
   :inherited-members:
   :show-inheritance:

La logique métier est organisé dans un pipeline séquentiel, détaillé dans la page :doc:`../architecture/diagramme`.