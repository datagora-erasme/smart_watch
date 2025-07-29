FROM python:3.13-slim

# Installer les dépendances système nécessaires
RUN apt-get update && apt-get install -y gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers pour uv
# Liste des dépendances
COPY uv.lock ./
# Fichier de configuration
COPY pyproject.toml ./

# Installer uv
RUN pip install uv

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
