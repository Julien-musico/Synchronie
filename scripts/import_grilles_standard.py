import json
import os

from app import create_app
from app.models import db
from app.models.cotation import GrilleEvaluation

# Dossier contenant les grilles standard
GRILLES_DIR = os.path.join(os.path.dirname(__file__), '../data/grilles_standard')

app = create_app()

with app.app_context():
    for filename in os.listdir(GRILLES_DIR):
        if filename.endswith('.json'):
            path = os.path.join(GRILLES_DIR, filename)
            with open(path, encoding='utf-8') as f:
                data = json.load(f)
            # Vérifier si la grille existe déjà (par nom)
            existing = GrilleEvaluation.query.filter_by(nom=data.get('nom', filename.replace('.json','').upper())).first()
            if existing:
                print(f"Grille déjà présente : {existing.nom}")
                continue
            grille = GrilleEvaluation()
            grille.nom = data.get('nom', filename.replace('.json','').upper())
            grille.description = data.get('description', '')
            grille.type_grille = 'standard'
            grille.reference_scientifique = data.get('reference_scientifique', filename.replace('.json','').upper())
            grille.domaines_config = json.dumps(data.get('domaines', []))
            grille.active = True
            # grille.publique = True
            db.session.add(grille)
            print(f"Importée : {grille.nom}")
    db.session.commit()
    print("Import terminé.")
