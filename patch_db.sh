#!/bin/bash

# Script pour patcher la base de données sur Render
# Usage: ./patch_db.sh

echo "🔧 Début du patch de base de données..."

# Vérifier que psql est disponible
if ! command -v psql &> /dev/null; then
    echo "❌ psql n'est pas installé"
    exit 1
fi

# Vérifier que DATABASE_URL est définie
if [ -z "$DATABASE_URL" ]; then
    echo "❌ Variable d'environnement DATABASE_URL non définie"
    exit 1
fi

echo "✅ Connexion à la base de données..."

# Exécuter le patch SQL
psql "$DATABASE_URL" -f sql/schema_patch.sql

if [ $? -eq 0 ]; then
    echo "✅ Patch appliqué avec succès!"
    
    # Vérifier que les colonnes problématiques ont été supprimées
    echo "🔍 Vérification des modifications..."
    
    psql "$DATABASE_URL" -c "SELECT column_name FROM information_schema.columns WHERE table_name = 'cotation_seance' AND column_name = 'grille_version_id';"
    
    if [ $? -eq 0 ]; then
        echo "✅ Vérification terminée"
    else
        echo "⚠️ Erreur lors de la vérification"
    fi
    
else
    echo "❌ Erreur lors de l'application du patch"
    exit 1
fi

echo "🎉 Patch de base de données terminé!"
