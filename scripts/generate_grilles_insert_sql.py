import os
import json
from datetime import datetime

DATA_DIR = 'data/grilles_standard'
SQL_FILE = 'scripts/grilles_insert.sql'

def escape_sql(value):
    if value is None:
        return 'NULL'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return "'" + str(value).replace("'", "''") + "'"

def main():
    inserts = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith('.json'):
            path = os.path.join(DATA_DIR, filename)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            nom = escape_sql(data.get('nom', filename.replace('.json','').upper()))
            description = escape_sql(data.get('description', ''))
            type_grille = escape_sql(data.get('type_grille', 'standard'))
            reference = escape_sql(data.get('reference_scientifique', ''))
            user_id = 'NULL'  # Standard grille, pas d'utilisateur
            domaines_config = escape_sql(json.dumps(data.get('domaines_config', {}), ensure_ascii=False))
            active = 'true'
            publique = 'true'
            now = escape_sql(datetime.now().isoformat())
            sql = f"INSERT INTO public.grille_evaluation (nom, description, type_grille, reference_scientifique, user_id, domaines_config, active, publique, date_creation, date_modification) VALUES ({nom}, {description}, {type_grille}, {reference}, {user_id}, {domaines_config}, {active}, {publique}, {now}, {now});"
            inserts.append(sql)
    with open(SQL_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(inserts))
    print(f"Fichier SQL généré : {SQL_FILE} ({len(inserts)} requêtes)")

if __name__ == '__main__':
    main()
