from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

"""
Définition du schéma de la base de données
"""


Base = declarative_base()


class Lieux(Base):
    """Table des lieux avec leurs informations de base."""

    __tablename__ = "lieux"

    identifiant = Column(Text, primary_key=True)
    nom = Column(Text, nullable=True)
    type_lieu = Column(Text, nullable=True)  # Piscine, bibliotheque, mairie
    url = Column(Text, nullable=True)
    horaires_data_gl = Column(
        Text, nullable=True
    )  # Horaires de référence, pris sur data.grandlyon.com
    horaires_data_gl_json = Column(
        Text, nullable=True
    )  # Conversion JSON des horaires OSM GL, à l'aide de OSMToCustomJson.py

    # Relations
    resultats = relationship("ResultatsExtraction", back_populates="lieu")


class Executions(Base):
    """Table des exécutions du programme."""

    __tablename__ = "executions"

    id_executions = Column(Integer, primary_key=True, autoincrement=True)
    date_execution = Column(DateTime, nullable=False)
    llm_modele = Column(Text, nullable=True)
    llm_fournisseur = Column(Text, nullable=True)  # OPENAI ou MISTRAL
    llm_url = Column(Text, nullable=True)  # http://api.openai.com/v1/ par exemple
    llm_consommation_execution = Column(Float, nullable=True, default=0.0)  # En kg CO2

    # Relations
    resultats = relationship("ResultatsExtraction", back_populates="execution")


class ResultatsExtraction(Base):
    """Table des résultats d'extraction pour chaque lieu et exécution."""

    __tablename__ = "resultats_extraction"

    id_resultats_extraction = Column(Integer, primary_key=True, autoincrement=True)
    lieu_id = Column(Text, ForeignKey("lieux.identifiant"), nullable=False)
    id_execution = Column(
        Integer, ForeignKey("executions.id_executions"), nullable=False
    )

    # Extraction URL
    statut_url = Column(Text, default="")
    code_http = Column(Integer, default=0)  # 200, 404, etc.
    message_url = Column(Text, default="")

    # Traçabilité du markdown (3 étapes)
    markdown_brut = Column(Text, default="")  # Markdown brut depuis l'URL
    markdown_nettoye = Column(
        Text, default=""
    )  # Markdown après nettoyage (suppr liens, formatage)
    markdown_filtre = Column(Text, default="")  # Markdown après filtrage sémantique

    # Extraction LLM
    prompt_message = Column(Text, default="")
    llm_consommation_requete = Column(Float, nullable=True, default=0.0)  # En kg CO2
    llm_horaires_json = Column(Text, default="")
    llm_horaires_osm = Column(Text, default="")

    # Comparaison avec data.grandlyon.com
    horaires_identiques = Column(Boolean, nullable=True)
    differences_horaires = Column(Text, default="")

    # Chaîne d'erreurs détaillée
    erreurs_pipeline = Column(Text, default="")

    # Relations
    lieu = relationship("Lieux", back_populates="resultats")
    execution = relationship("Executions", back_populates="resultats")
