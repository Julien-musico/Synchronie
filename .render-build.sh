#!/bin/bash

# Build script pour Render.com
echo "🎵 Déploiement de Synchronie sur Render..."

# Installation des dépendances
echo "📦 Installation des dépendances Python..."
pip install -r requirements.txt

# Configuration initiale de l'application
echo "🏗️ Configuration initiale de l'application..."
python init_app.py

echo "✅ Build terminé avec succès !"
