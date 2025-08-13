#!/usr/bin/env python3
"""
Script de migration pour corriger les problèmes de base de données
"""
import os
import psycopg2
from urllib.parse import urlparse

def execute_sql_patch():
    """Exécute le patch SQL pour corriger la base de données"""
    
    # Récupérer l'URL de la base de données depuis les variables d'environnement
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        print("❌ Variable DATABASE_URL non trouvée")
        return False
    
    # Parser l'URL de la base de données
    parsed = urlparse(database_url)
    
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port,
            database=parsed.path[1:],  # Retirer le '/' initial
            user=parsed.username,
            password=parsed.password,
            sslmode='require'
        )
        
        print("✅ Connexion à la base de données établie")
        
        # Lire le fichier de patch
        with open('sql/schema_patch.sql', 'r', encoding='utf-8') as f:
            sql_patch = f.read()
        
        # Exécuter le patch
        with conn.cursor() as cursor:
            cursor.execute(sql_patch)
            conn.commit()
            print("✅ Patch SQL exécuté avec succès")
        
        # Vérifier que les colonnes problématiques ont été supprimées
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'cotation_seance' 
                AND column_name = 'grille_version_id'
            """)
            if cursor.fetchone():
                print("⚠️ La colonne grille_version_id existe encore dans cotation_seance")
            else:
                print("✅ Colonne grille_version_id supprimée de cotation_seance")
        
        conn.close()
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Erreur PostgreSQL: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == '__main__':
    print("🔧 Début de la migration de base de données...")
    if execute_sql_patch():
        print("🎉 Migration terminée avec succès!")
    else:
        print("💥 Échec de la migration")
        exit(1)
