#!/usr/bin/env python3
"""
Script pour patcher la base de données et créer la table PatientGrille
Usage: python patch_db.py
"""

import os
import sys

# Ajouter le répertoire racine au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def patch_database():
    """Crée la table PatientGrille si elle n'existe pas."""
    try:
        from app import create_app, db
        from app.models.cotation import PatientGrille
        
        app = create_app()
        
        with app.app_context():
            print("🔄 Connexion à la base de données...")
            
            # Créer toutes les tables manquantes
            db.create_all()
            
            # Vérifier que la table a été créée
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'patient_grille' in tables:
                print("✅ Table patient_grille créée avec succès!")
                
                # Afficher la structure
                columns = inspector.get_columns('patient_grille')
                print(f"📋 Structure de la table ({len(columns)} colonnes):")
                for col in columns:
                    print(f"   - {col['name']}: {col['type']}")
                    
            else:
                print("❌ Erreur: Table patient_grille non créée")
                return False
                
            print("🎉 Patch appliqué avec succès!")
            return True
            
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("Assurez-vous que Flask et SQLAlchemy sont installés")
        return False
        
    except Exception as e:
        print(f"❌ Erreur lors du patch: {e}")
        return False

if __name__ == "__main__":
    success = patch_database()
    sys.exit(0 if success else 1)
