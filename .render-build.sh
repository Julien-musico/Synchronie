#!/bin/bash

# Build script pour Render.com
echo "🎵 Déploiement de Synchronie sur Render..."

# Installation des dépendances
echo "📦 Installation des dépendances Python..."
pip install -r requirements.txt

# Mise à jour de la base de données
echo "🗄️ Mise à jour de la base de données..."
python -c "
from app import create_app, db
app = create_app('production')
with app.app_context():
    db.create_all()
    print('Base de données initialisée')
"

# Création de l'utilisateur admin si nécessaire
echo "👤 Vérification utilisateur admin..."
python -c "
from app import create_app, db
from app.models.user import User, UserRole
import os

app = create_app('production')
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            email=os.environ.get('ADMIN_EMAIL', 'admin@synchronie.fr'),
            first_name='Admin',
            last_name='System',
            role=UserRole.ADMIN
        )
        admin.set_password(os.environ.get('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin)
        db.session.commit()
        print('Utilisateur admin créé')
    else:
        print('Utilisateur admin existant')
"

# Ajout des grilles par défaut si nécessaire
echo "📋 Vérification grilles d'évaluation..."
python -c "
from app import create_app, db
from app.models.grille import Grille, GrilleType
from app.models.user import User

app = create_app('production')
with app.app_context():
    if Grille.query.count() == 0:
        admin = User.query.filter_by(role='admin').first()
        if admin:
            # Grille AMTA
            grille_amta = Grille(
                name='Grille Standard AMTA',
                description='Grille complète de l\'Association Américaine de Musicothérapie',
                grille_type=GrilleType.STANDARD_AMTA,
                is_template=True,
                creator_id=admin.id
            )
            grille_amta.set_domains_dict({
                'cognitive': {
                    'name': 'Fonctions cognitives',
                    'indicators': ['attention', 'mémoire', 'orientation', 'fonctions_exécutives']
                },
                'emotional': {
                    'name': 'Régulation émotionnelle',
                    'indicators': ['expression_émotions', 'gestion_stress', 'estime_soi', 'motivation']
                },
                'social': {
                    'name': 'Interactions sociales',
                    'indicators': ['communication', 'coopération', 'empathie', 'respect_règles']
                },
                'physical': {
                    'name': 'Fonctions motrices',
                    'indicators': ['motricité_fine', 'motricité_globale', 'coordination', 'tonus']
                }
            })
            grille_amta.scoring_scale = {'min': 1, 'max': 5, 'labels': ['Très faible', 'Faible', 'Moyen', 'Bon', 'Excellent']}
            grille_amta.weightings = {'cognitive': 0.3, 'emotional': 0.3, 'social': 0.25, 'physical': 0.15}
            
            db.session.add(grille_amta)
            db.session.commit()
            print('Grilles par défaut ajoutées')
    else:
        print('Grilles déjà présentes')
"

echo "✅ Déploiement terminé avec succès !"
