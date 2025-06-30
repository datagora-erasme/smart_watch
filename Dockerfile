FROM python:3.13-slim

# Installer les dépendances système nécessaires (ex: pour polars, connectorx, etc.)
RUN apt-get update && apt-get install -y gcc libpq-dev curl && rm -rf /var/lib/apt/lists/*

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt ./

# Installer les dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code source
COPY . .

# Commande de lancement (adapter si besoin)
CMD ["python", "main.py"]
