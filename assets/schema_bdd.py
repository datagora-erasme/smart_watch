from sqlalchemy import Column, DateTime, ForeignKey, Integer, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

"""
Définition du schéma de la base de données
"""


Base = declarative_base()


class Lieux(Base):
    __tablename__ = "lieux"

    identifiant = Column(Text, primary_key=True)
    nom = Column(Text)
    type_lieu = Column(Text)
    url = Column(Text)
    horaires_data_gl = Column(Text)  # Horaires OSM de référence


class Executions(Base):
    __tablename__ = "executions"

    id_executions = Column(Integer, primary_key=True, autoincrement=True)
    date_execution = Column(DateTime, default=func.current_timestamp())
    llm_modele = Column(Text)
    llm_fournisseur = Column(Text)
    llm_url = Column(Text)
    llm_consommation_totale = Column(Text)


class ResultatsExtraction(Base):
    __tablename__ = "resultats_extraction"

    id_resultats_extraction = Column(Integer, primary_key=True, autoincrement=True)
    lieu_id = Column(Text, ForeignKey("lieux.identifiant"), nullable=False)
    id_execution = Column(
        Integer, ForeignKey("executions.id_executions"), nullable=False
    )
    statut_url = Column(Text)
    code_http = Column(Integer)
    message_url = Column(Text)
    markdown = Column(Text)
    prompt_message = Column(Text)
    llm_consommation_requete = Column(Text)
    llm_horaires_json = Column(Text)
    llm_horaires_osm = Column(Text)
