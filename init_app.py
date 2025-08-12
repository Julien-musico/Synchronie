#!/usr/bin/env python3
"""
Script d'initialisation pour Synchronie sur Render
Exécuté au premier démarrage pour configurer la base de données
"""

import os
import sys

# Ajouter le répertoire racine au path Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def init_database():
    """Initialise la base de données et les données par défaut"""
    try:
        from app import create_app, db
        from app.models.user import User, UserRole
        from app.models.grille import Grille, GrilleType
        
        print("🗄️ Initialisation de la base de données...")
        
        # Créer l'application
        app = create_app('production')
        
        with app.app_context():
            # Créer toutes les tables
            db.create_all()
            print("✅ Tables créées")
            
            # Créer l'utilisateur admin si nécessaire
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
                print("✅ Utilisateur admin créé")
            else:
                print("ℹ️ Utilisateur admin existant")
            
            # Ajouter les grilles par défaut si nécessaire
            if Grille.query.count() == 0:
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
                grille_amta.scoring_scale = {
                    'min': 1, 
                    'max': 5, 
                    'labels': ['Très faible', 'Faible', 'Moyen', 'Bon', 'Excellent']
                }
                grille_amta.weightings = {
                    'cognitive': 0.3, 
                    'emotional': 0.3, 
                    'social': 0.25, 
                    'physical': 0.15
                }
                
                db.session.add(grille_amta)
                db.session.commit()
                print("✅ Grilles par défaut ajoutées")
            else:
                print("ℹ️ Grilles déjà présentes")
        
        print("🎵 Initialisation terminée avec succès!")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
