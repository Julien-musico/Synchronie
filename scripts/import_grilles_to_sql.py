import json
import os

import psycopg2


def get_connection():
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        return psycopg2.connect(db_url)
    return psycopg2.connect(
        dbname=os.environ.get('DB_NAME', 'synchronie'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', 'postgres'),
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432')
    )

def import_grilles():
    conn = get_connection()
    cur = conn.cursor()
    GRILLES_DIR = os.path.join(os.path.dirname(__file__), '../data/grilles_standard')
    for filename in os.listdir(GRILLES_DIR):
        if filename.endswith('.json'):
            with open(os.path.join(GRILLES_DIR, filename), encoding='utf-8') as f:
                grille_data = json.load(f)
            # Insert grille
            cur.execute(
                "INSERT INTO grille (nom, description, type_grille, reference_scientifique) VALUES (%s, %s, %s, %s) RETURNING id",
                (
                    grille_data.get('nom'),
                    grille_data.get('description'),
                    grille_data.get('type_grille', 'standard'),
                    grille_data.get('reference_scientifique')
                )
            )
            grille_id = cur.fetchone()[0]
            # Insert domaines and indicateurs
            for domaine in grille_data.get('domaines', []):
                cur.execute(
                    "INSERT INTO domaine (nom, description) VALUES (%s, %s) RETURNING id",
                    (domaine.get('nom'), domaine.get('description'))
                )
                domaine_id = cur.fetchone()[0]
                for indicateur in domaine.get('indicateurs', []):
                    cur.execute(
                        "INSERT INTO indicateur (nom, description) VALUES (%s, %s) RETURNING id",
                        (indicateur.get('nom'), indicateur.get('description'))
                    )
                    indicateur_id = cur.fetchone()[0]
                    # Link domaine and indicateur
                    cur.execute(
                        "INSERT INTO domaine_indicateur (domaine_id, indicateur_id) VALUES (%s, %s)",
                        (domaine_id, indicateur_id)
                    )
                # Link grille and domaine
                cur.execute(
                    "INSERT INTO grille_domaine (grille_id, domaine_id) VALUES (%s, %s)",
                    (grille_id, domaine_id)
                )
    conn.commit()
    cur.close()
    conn.close()
    print("Import terminé !")

if __name__ == '__main__':
    import_grilles()
