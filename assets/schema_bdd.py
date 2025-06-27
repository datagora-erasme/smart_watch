from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Text
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
    type_lieu = Column(Text)  # Piscine, mairie, médiathèque, etc.
    url = Column(Text)
    horaires_data_gl = Column(
        Text
    )  # Horaires OSM de référence, pris sur data.grandlyon.com
    horaires_data_gl_json = Column(
        Text
    )  # Conversion JSON des horaires OSM GL, à l'aide de utils/OSMToCustomJson.py


class Executions(Base):
    __tablename__ = "executions"

    id_executions = Column(Integer, primary_key=True, autoincrement=True)
    date_execution = Column(DateTime, default=func.current_timestamp())
    llm_modele = Column(Text)
    llm_fournisseur = Column(Text)  # OPENAI ou MISTRAL
    llm_url = Column(Text)  # http://api.openai.com/v1/ par exemple
    llm_consommation_execution = Column(Text)


class ResultatsExtraction(Base):
    __tablename__ = "resultats_extraction"

    id_resultats_extraction = Column(Integer, primary_key=True, autoincrement=True)
    lieu_id = Column(Text, ForeignKey("lieux.identifiant"), nullable=False)
    id_execution = Column(
        Integer, ForeignKey("executions.id_executions"), nullable=False
    )
    statut_url = Column(Text)
    code_http = Column(Integer)  # 200, 404, etc.
    message_url = Column(Text)
    markdown = Column(
        Text
    )  # Contenu de la page converti en Markdown via HtmlToMarkdown.py
    markdown_horaires = Column(
        Text
    )  # Extraits du Markdown contenant les horaires, détectés par embeddings
    prompt_message = Column(Text)  # Prompt complet envoyé au LLM
    llm_consommation_requete = Column(Text)
    llm_horaires_json = Column(Text)  # Json des horaires extraits par le LLM
    llm_horaires_osm = Column(
        Text
    )  # Conversion des horaires LLM au format OSM via CustomJsonToOSM.py
    horaires_identiques = Column(
        Boolean, default=None
    )  # True = identiques, False = différents, None = non comparé/erreur
    differences_horaires = Column(Text)  # Détails des différences, vide si identiques
