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
    type_lieu = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    horaires_data_gl = Column(Text, nullable=True)
    horaires_data_gl_json = Column(Text, nullable=True)

    # Relations
    resultats = relationship("ResultatsExtraction", back_populates="lieu")


class Executions(Base):
    """Table des exécutions du programme."""

    __tablename__ = "executions"

    id_execution = Column(Integer, primary_key=True, autoincrement=True)
    date_execution = Column(DateTime, nullable=False)
    llm_modele = Column(Text, nullable=True)
    llm_fournisseur = Column(Text, nullable=True)
    llm_url = Column(Text, nullable=True)
    llm_consommation_execution = Column(Float, nullable=True, default=0.0)

    # Relations
    resultats = relationship("ResultatsExtraction", back_populates="execution")


class ResultatsExtraction(Base):
    """Table des résultats d'extraction pour chaque lieu et exécution."""

    __tablename__ = "resultats_extraction"

    id_resultats_extraction = Column(Integer, primary_key=True, autoincrement=True)
    lieu_id = Column(Text, ForeignKey("lieux.identifiant"), nullable=False)
    id_execution = Column(
        Integer, ForeignKey("executions.id_execution"), nullable=False
    )
    statut_url = Column(Text, default="")
    code_http = Column(Integer, default=0)
    message_url = Column(Text, default="")
    markdown_brut = Column(Text, default="")
    markdown_nettoye = Column(Text, default="")
    markdown_filtre = Column(Text, default="")
    prompt_message = Column(Text, default="")
    llm_consommation_requete = Column(Float, nullable=True, default=0.0)
    llm_horaires_json = Column(Text, default="")
    llm_horaires_osm = Column(Text, default="")
    horaires_identiques = Column(Boolean, nullable=True)
    differences_horaires = Column(Text, default="")
    erreurs_pipeline = Column(Text, default="")

    # Relations
    lieu = relationship("Lieux", back_populates="resultats")
    execution = relationship("Executions", back_populates="resultats")
