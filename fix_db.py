#!/usr/bin/env python3
"""
Script de correction de la base de données pour la production (DEPRECIÉ)
---------------------------------------------------------------------
Contexte: remplacé progressivement par les migrations Alembic.
Objectif initial: corriger/renommer la colonne activites_musicales → activites_realisees.
À supprimer une fois que le déploiement s'appuie exclusivement sur `flask db upgrade`.
"""
from contextlib import suppress
import os
import sys

from sqlalchemy import text  # type: ignore

from app import create_app  # type: ignore
from app.models import db  # type: ignore

def fix_database():
    """Corrige la structure de la base de données"""
    print("🔧 Correction de la base de données Synchronie...")
    print(f"🌍 Environnement: {os.environ.get('FLASK_CONFIG', 'default')}")
    
    # Utiliser la configuration de production
    config_name = os.environ.get('FLASK_CONFIG', 'production')
    app = create_app(config_name)
    
    with app.app_context():
        try:
            print("📊 Vérification de la structure de la base...")
            
            # Vérifier d'abord si la table seances existe
            tables_result = db.session.execute(text("""
                SELECT tablename FROM pg_tables 
                WHERE schemaname = 'public' AND tablename = 'seances'
            """))
            
            tables = [row[0] for row in tables_result]
            print(f"📋 Tables trouvées: {tables}")
            
            if 'seances' not in tables:
                print("⚠️ Table 'seances' n'existe pas, création de toutes les tables...")
                db.create_all()
                print("✅ Tables créées avec succès")
                return True
            
            # Vérifier la colonne activites_realisees
            print("🔍 Vérification des colonnes de la table 'seances'...")
            result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'seances'
                AND column_name IN ('activites_musicales', 'activites_realisees')
            """))
            
            columns = [row[0] for row in result]
            print(f"📋 Colonnes activites trouvées: {columns}")
            
            # Obtenir toutes les colonnes pour diagnostic
            all_columns_result = db.session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'seances'
                ORDER BY ordinal_position
            """))
            
            all_columns = [(row[0], row[1]) for row in all_columns_result]
            print(f"📋 Toutes les colonnes de 'seances': {[col[0] for col in all_columns]}")
            
            # Corriger selon le cas
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
            
            # Vérification finale
            final_result = db.session.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name = 'seances'
                AND column_name = 'activites_realisees'
            """))
            
            final_check = final_result.fetchone()
            if final_check:
                print("🎉 Base de données corrigée avec succès!")
                print("✅ Colonne 'activites_realisees' confirmée dans la table 'seances'")
                return True
            print("❌ La colonne activites_realisees est toujours manquante")
            return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la correction: {e}")
            print(f"🔍 Type d'erreur: {type(e).__name__}")
            import traceback
            traceback.print_exc()
            with suppress(Exception):
                db.session.rollback()
            return False

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 SYNCHRONIE - SCRIPT DE CORRECTION DE BASE DE DONNÉES")
    print("=" * 60)
    
    success = fix_database()
    
    if success:
        print("\n" + "=" * 60)
        print("✅ CORRECTION TERMINÉE AVEC SUCCÈS")
        print("=" * 60)
        sys.exit(0)
    else:
        print("\n" + "=" * 60)
        print("❌ ÉCHEC DE LA CORRECTION")
        print("=" * 60)
        sys.exit(1)
