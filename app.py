"""
Point d'entrée principal pour Synchronie
Utilisé pour le développement local et les commandes CLI
"""

import os
import sys

# Configuration pour détection d'environnement
if 'render.com' in os.environ.get('RENDER_EXTERNAL_URL', ''):
    os.environ.setdefault('FLASK_ENV', 'production')

from app import create_app, db
from app.models import *

# Créer l'application avec détection automatique d'environnement
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Contexte du shell Flask pour le développement"""
    return {
        'db': db,
        'User': User,
        'Patient': Patient,
        'Session': Session,
        'Grille': Grille,
        'GrilleAssignment': GrilleAssignment,
        'Rapport': Rapport
    }

@app.cli.command()
def init_db():
    """Initialise la base de données"""
    db.create_all()
    print("Base de données initialisée !")

@app.cli.command()
def create_admin():
    """Crée un utilisateur administrateur"""
    from app.models.user import User, UserRole
    
    admin = User(
        username='admin',
        email='admin@synchronie.fr',
        first_name='Admin',
        last_name='System',
        role=UserRole.ADMIN
    )
    admin.set_password('admin123')  # À changer en production !
    
    db.session.add(admin)
    db.session.commit()
    print("Utilisateur admin créé (username: admin, password: admin123)")

@app.cli.command()
def seed_grilles():
    """Ajoute les grilles d'évaluation par défaut"""
    from app.models.grille import Grille, GrilleType
    from app.models.user import User
    
    # Récupérer l'admin pour créer les grilles templates
    admin = User.query.filter_by(role='admin').first()
    if not admin:
        print("Aucun administrateur trouvé. Créez d'abord un admin avec 'flask create-admin'")
        return
    
    # Grille Standard AMTA
    grille_amta = Grille(
        name="Grille Standard AMTA",
        description="Grille complète de l'Association Américaine de Musicothérapie",
        grille_type=GrilleType.STANDARD_AMTA,
        is_template=True,
        target_population="Tout public",
        reliability_score=0.89,
        validation_reference="American Music Therapy Association Standards",
        creator_id=admin.id
    )
    
    # Utiliser les données du template
    template_data = grille_amta.get_template_data()
    if template_data:
        grille_amta.set_domains_dict(template_data['domains'])
        grille_amta.scoring_scale = template_data['scoring_scale']
        grille_amta.weightings = template_data['weightings']
    
    # Grille Simplifiée
    grille_simple = Grille(
        name="Grille Simplifiée",
        description="Évaluation rapide en 3 domaines essentiels",
        grille_type=GrilleType.SIMPLIFIED,
        is_template=True,
        target_population="Évaluation rapide",
        creator_id=admin.id
    )
    
    template_data_simple = grille_simple.get_template_data()
    if template_data_simple:
        grille_simple.set_domains_dict(template_data_simple['domains'])
        grille_simple.scoring_scale = template_data_simple['scoring_scale']
        grille_simple.weightings = template_data_simple['weightings']
    
    db.session.add(grille_amta)
    db.session.add(grille_simple)
    db.session.commit()
    
    print("Grilles d'évaluation par défaut ajoutées !")

if __name__ == '__main__':
    # Configuration pour Render ou développement local
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    # Détection automatique de l'environnement
    if os.environ.get('RENDER'):
        # Environnement Render
        print("🚀 Démarrage sur Render en mode production")
        app.run(host='0.0.0.0', port=port, debug=False)
    else:
        # Environnement local
        print("🔧 Démarrage en mode développement local")
        app.run(host='0.0.0.0', port=port, debug=debug)
