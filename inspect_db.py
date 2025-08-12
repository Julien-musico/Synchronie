#!/usr/bin/env python3
"""
Script pour inspecter et corriger la structure de la base de données
"""
from app import create_app
from app.models import db

def inspect_seances_table():
    app = create_app()
    with app.app_context():
        print("🔍 Inspection de la table seances")
        print("=" * 40)
        
        try:
            inspector = db.inspect(db.engine)
            columns = inspector.get_columns('seances')
            print("Colonnes existantes:")
            for col in columns:
                print(f"- {col['name']}: {col['type']}")
                
            # Vérifier si la colonne activites_realisees existe
            column_names = [col['name'] for col in columns]
            if 'activites_realisees' in column_names:
                print("\n✅ La colonne 'activites_realisees' existe")
            elif 'activites_musicales' in column_names:
                print("\n⚠️ La colonne 'activites_musicales' existe, il faut la renommer")
                # Exécuter la migration
                try:
                    db.engine.execute("ALTER TABLE seances RENAME COLUMN activites_musicales TO activites_realisees")
                    print("✅ Colonne renommée avec succès")
                except Exception as e:
                    print(f"❌ Erreur lors du renommage: {e}")
            else:
                print("\n❌ Aucune des deux colonnes n'existe")
                
        except Exception as e:
            print(f"❌ Erreur lors de l'inspection: {e}")

if __name__ == "__main__":
    inspect_seances_table()
