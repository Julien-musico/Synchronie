import json
import os
from pathlib import Path

import psycopg2

# Utilisation des variables d'environnement pour la sécurité
DB_NAME = os.getenv('POSTGRES_DB', 'synchronie')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'your_password')
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')

conn = psycopg2.connect(
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=DB_PORT
)
cur = conn.cursor()

data_dir = Path('data/grilles_standard')
for filename in os.listdir(data_dir):
    if filename.endswith('.json'):
        with open(data_dir / filename, encoding='utf-8') as f:
            grille = json.load(f)
            # Vérifier si la grille existe déjà
            cur.execute("SELECT id FROM grille WHERE nom=%s", (grille["nom"],))
            result = cur.fetchone()
            if result:
                grille_id = result[0]
            else:
                cur.execute(
                    "INSERT INTO grille (nom, description, type_grille, reference_scientifique) VALUES (%s, %s, %s, %s) RETURNING id",
                    (grille["nom"], grille["description"], grille.get("type", "standardisée"), grille.get("reference_scientifique", ""))
                )
                grille_id = cur.fetchone()[0]
            for domaine in grille["domaines"]:
                # Vérifier si le domaine existe déjà
                cur.execute("SELECT id FROM domaine WHERE nom=%s", (domaine["nom"],))
                result = cur.fetchone()
                if result:
                    domaine_id = result[0]
                else:
                    cur.execute("INSERT INTO domaine (nom, description) VALUES (%s, %s) RETURNING id", (domaine["nom"], ""))
                    domaine_id = cur.fetchone()[0]
                # Lier le domaine à la grille
                cur.execute("SELECT 1 FROM grille_domaine WHERE grille_id=%s AND domaine_id=%s", (grille_id, domaine_id))
                if not cur.fetchone():
                    cur.execute("INSERT INTO grille_domaine (grille_id, domaine_id) VALUES (%s, %s)", (grille_id, domaine_id))
                for indicateur in domaine["indicateurs"]:
                    # Vérifier si l'indicateur existe déjà
                    cur.execute("SELECT id FROM indicateur WHERE nom=%s", (indicateur["nom"],))
                    result = cur.fetchone()
                    if result:
                        indicateur_id = result[0]
                    else:
                        cur.execute("INSERT INTO indicateur (nom, description) VALUES (%s, %s) RETURNING id", (indicateur["nom"], ""))
                        indicateur_id = cur.fetchone()[0]
                    # Lier l'indicateur au domaine
                    cur.execute("SELECT 1 FROM domaine_indicateur WHERE domaine_id=%s AND indicateur_id=%s", (domaine_id, indicateur_id))
                    if not cur.fetchone():
                        cur.execute("INSERT INTO domaine_indicateur (domaine_id, indicateur_id) VALUES (%s, %s)", (domaine_id, indicateur_id))
conn.commit()
cur.close()
conn.close()

print('Import des grilles standardisées terminé.')
