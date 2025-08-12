#!/usr/bin/env python3
"""
Script de correction de la base de données pour la production
Corrige le problème de la colonne activites_realisees manquante
"""
import os
from app import create_app
from app.models import db
from sqlalchemy import text

def fix_database():
    """Corrige la structure de la base de données"""
    print("🔧 Correction de la base de données Synchronie...")
    
    # Utiliser la configuration de production
    config_name = os.environ.get('FLASK_CONFIG', 'production')
    app = create_app(config_name)
    
    with app.app_context():
        try:
            print("📊 Vérification de la structure de la base...")
            
            # Créer toutes les tables si elles n'existent pas
            db.create_all()
            print("✅ Tables vérifiées/créées")
            
            # Vérifier la colonne activites_realisees
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'seances'
                AND column_name IN ('activites_musicales', 'activites_realisees')
            """))
            
            columns = [row[0] for row in result]
            print(f"📋 Colonnes trouvées dans 'seances': {columns}")
            
            if 'activites_musicales' in columns and 'activites_realisees' not in columns:
                print("🔄 Renommage activites_musicales → activites_realisees...")
                db.session.execute(text(
                    'ALTER TABLE seances RENAME COLUMN activites_musicales TO activites_realisees'
                ))
                db.session.commit()
                print("✅ Migration de colonne réussie!")
                
            elif 'activites_realisees' not in columns:
                print("➕ Ajout de la colonne activites_realisees...")
                db.session.execute(text(
                    'ALTER TABLE seances ADD COLUMN activites_realisees TEXT'
                ))
                db.session.commit()
                print("✅ Colonne ajoutée avec succès!")
                
            else:
                print("✅ La colonne activites_realisees existe déjà")
            
            # Vérifier le résultat final
            result_final = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'seances'
                ORDER BY ordinal_position
            """))
            
            all_columns = [row[0] for row in result_final]
            print(f"📋 Structure finale de la table 'seances': {all_columns}")
            
            if 'activites_realisees' in all_columns:
                print("🎉 Base de données corrigée avec succès!")
                return True
            else:
                print("❌ La colonne activites_realisees est toujours manquante")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la correction: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()
            return False

if __name__ == "__main__":
    success = fix_database()
    exit(0 if success else 1)
