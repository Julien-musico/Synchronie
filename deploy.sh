#!/bin/bash
# Script de déploiement pour Render.com

echo "🚀 Démarrage du déploiement Synchronie..."

# Installation des dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Exécution des migrations de base de données
echo "🗄️ Exécution des migrations de base de données..."
python -c "
from app import create_app
from flask_migrate import upgrade
import os

print('Configuration des migrations...')
app = create_app('production')

with app.app_context():
    try:
        print('Exécution des migrations...')
        upgrade()
        print('✅ Migrations appliquées avec succès')
    except Exception as e:
        print(f'❌ Erreur lors des migrations: {e}')
        print('Tentative de création manuelle de la colonne...')
        
        from app.models import db
        from sqlalchemy import text
        
        try:
            # Vérifier si la table existe
            result = db.session.execute(text(\"\"\"
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'seances'
            \"\"\"))
            
            columns = [row[0] for row in result]
            print(f'Colonnes existantes: {columns}')
            
            if 'activites_musicales' in columns and 'activites_realisees' not in columns:
                print('Renommage de activites_musicales en activites_realisees...')
                db.session.execute(text('ALTER TABLE seances RENAME COLUMN activites_musicales TO activites_realisees'))
                db.session.commit()
                print('✅ Colonne renommée avec succès')
            elif 'activites_realisees' not in columns:
                print('Ajout de la colonne activites_realisees...')
                db.session.execute(text('ALTER TABLE seances ADD COLUMN activites_realisees TEXT'))
                db.session.commit()
                print('✅ Colonne ajoutée avec succès')
            else:
                print('✅ La colonne activites_realisees existe déjà')
                
        except Exception as e2:
            print(f'❌ Erreur lors de la correction manuelle: {e2}')
            exit(1)
"

echo "✅ Déploiement terminé avec succès!"
