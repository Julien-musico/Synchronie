import json
from pathlib import Path

# Chemin du fichier JSON CARS
json_path = Path('data/grilles_standard/cars.json')
with open(json_path, encoding='utf-8') as f:
    grille = json.load(f)

# Génère le SQL pour la grille
print("-- Grille CARS\nINSERT INTO grille (nom, description, type_grille, reference_scientifique)\nSELECT '{0}', '{1}', '{2}', '{3}'\nWHERE NOT EXISTS (SELECT 1 FROM grille WHERE nom = '{0}');\n".format(
    grille['nom'],
    grille['description'].replace("'", "''"),
    grille.get('type', 'standardisée'),
    grille.get('reference_scientifique', '')
))
print(f"-- SELECT id FROM grille WHERE nom = '{grille['nom']}';\n")

for domaine in grille['domaines']:
    print(f"-- Domaine : {domaine['nom']}")
    print(f"INSERT INTO domaine (nom, description)\nSELECT '{domaine['nom']}', ''\nWHERE NOT EXISTS (SELECT 1 FROM domaine WHERE nom = '{domaine['nom']}');")
    print(f"SELECT id FROM domaine WHERE nom = '{domaine['nom']}';")
    print("-- INSERT INTO grille_domaine (grille_id, domaine_id) ...")
    for indicateur in domaine['indicateurs']:
        print(f"-- Indicateur : {indicateur['nom']}")
        print(f"INSERT INTO indicateur (nom, description)\nSELECT '{indicateur['nom']}', ''\nWHERE NOT EXISTS (SELECT 1 FROM indicateur WHERE nom = '{indicateur['nom']}');")
        print(f"SELECT id FROM indicateur WHERE nom = '{indicateur['nom']}';")
    print("-- INSERT INTO domaine_indicateur (domaine_id, indicateur_id) ...")
    print()
print("-- Répète les liaisons grille_domaine et domaine_indicateur avec les IDs obtenus.")
