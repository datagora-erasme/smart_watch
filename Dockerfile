# ubuntu au lieu de python:3.13-slim pour compatibilité avec Playwright
FROM ubuntu:20.04

# Éviter les prompts interactifs
ENV DEBIAN_FRONTEND=noninteractive

# Installer Python 3.13 et les dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update && apt-get install -y \
    python3.13 \
    python3.13-dev \
    python3.13-distutils \
    python3-pip \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Créer des liens symboliques pour python et python3
RUN ln -sf /usr/bin/python3.13 /usr/bin/python3 && \
    ln -sf /usr/bin/python3.13 /usr/bin/python

# Mettre à jour pip pour Python 3.13
RUN python3.13 -m pip install --upgrade pip

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers pour uv
# Liste des dépendances
COPY uv.lock ./
# Fichier de configuration
COPY pyproject.toml ./

# Installer uv
RUN python3.13 -m pip install uv

# Installer les dépendances avec uv
RUN uv sync --no-cache

# Ajouter le venv au PATH
ENV PATH="/app/.venv/bin:$PATH"

# Installer les navigateurs Playwright
RUN python -m playwright install-deps && python -m playwright install

# Copier le reste du code source
COPY . .

# Commande de lancement
CMD ["python", "main.py"]