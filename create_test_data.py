"""
Script de création de données de test pour Synchronie
"""

import random
from datetime import datetime, timedelta

from app import create_app, db
from app.models import Patient, Seance, User
from app.models.cotation import GrilleEvaluation
from app.services.cotation_service import CotationService


def creer_donnees_test():
    """Crée des données de test pour l'application"""
    
    # Créer un utilisateur test si il n'existe pas
    user = User.query.filter_by(email='test@musicotherapeute.fr').first()
    if not user:
        user = User(
            email='test@musicotherapeute.fr',
            nom='Musicothérapeute',
            prenom='Test'
        )
        user.set_password('test123')
        db.session.add(user)
        db.session.commit()
        print("✅ Utilisateur test créé")
    else:
        print("ℹ️ Utilisateur test existe déjà")

    # Créer quelques patients de test
    patients_data = [
        {'nom': 'Martin', 'prenom': 'Jean', 'pathologie': 'Alzheimer précoce'},
        {'nom': 'Durand', 'prenom': 'Marie', 'pathologie': 'Troubles autistiques'},
        {'nom': 'Bernard', 'prenom': 'Pierre', 'pathologie': 'AVC récent'},
        {'nom': 'Petit', 'prenom': 'Sophie', 'pathologie': 'Dépression sévère'},
        {'nom': 'Garcia', 'prenom': 'Carlos', 'pathologie': 'TDAH'},
    ]
    
    patients_crees = []
    for data in patients_data:
        existing = Patient.query.filter_by(
            nom=data['nom'], 
            prenom=data['prenom'], 
            user_id=user.id
        ).first()
        
        if not existing:
            patient = Patient(
                nom=data['nom'],
                prenom=data['prenom'],
                pathologie=data['pathologie'],
                user_id=user.id,
                date_naissance=datetime.now() - timedelta(days=random.randint(365*20, 365*80))
            )
            db.session.add(patient)
            patients_crees.append(patient)
    
    db.session.commit()
    
    # Récupérer tous les patients de l'utilisateur
    patients = Patient.query.filter_by(user_id=user.id).all()
    print(f"✅ {len(patients)} patients disponibles")

    # Créer des séances de test
    for _i, patient in enumerate(patients[:3]):  # Seulement pour les 3 premiers
        # 2-4 séances par patient
        nb_seances = random.randint(2, 4)
        for j in range(nb_seances):
            existing_seance = Seance.query.filter_by(
                patient_id=patient.id,
                date=datetime.now() - timedelta(days=j*7)
            ).first()
            
            if not existing_seance:
                seance = Seance(
                    patient_id=patient.id,
                    user_id=user.id,
                    date=datetime.now() - timedelta(days=j*7),
                    duree=random.randint(30, 60),
                    transcription_text=f"Séance de musicothérapie {j+1} avec {patient.prenom}. "
                                     f"Bonne participation du patient. Réactivité aux stimuli musicaux. "
                                     f"Amélioration progressive de l'attention et de la concentration.",
                    synthese_therapeutique=f"Évolution positive observée chez {patient.prenom}. "
                                         f"Recommandation: continuer avec les mêmes techniques."
                )
                db.session.add(seance)
    
    db.session.commit()
    seances = Seance.query.filter_by(user_id=user.id).all()
    print(f"✅ {len(seances)} séances créées")

    # Créer quelques grilles standard
    grilles_standard = [
        {
            'nom': 'AMTA - Évaluation Standard',
            'description': 'Grille d\'évaluation basée sur les standards de l\'Association Américaine de Musicothérapie',
            'reference_scientifique': 'AMTA',
            'est_publique': True,
            'domaines': [
                {
                    'nom': 'Communication',
                    'description': 'Capacités de communication verbale et non-verbale',
                    'couleur': '#3498db',
                    'indicateurs': [
                        {'nom': 'Expression verbale', 'min': 0, 'max': 10, 'unite': 'pts'},
                        {'nom': 'Compréhension', 'min': 0, 'max': 10, 'unite': 'pts'},
                        {'nom': 'Communication non-verbale', 'min': 0, 'max': 10, 'unite': 'pts'}
                    ]
                },
                {
                    'nom': 'Motricité',
                    'description': 'Coordination et motricité fine/globale',
                    'couleur': '#e74c3c',
                    'indicateurs': [
                        {'nom': 'Motricité fine', 'min': 0, 'max': 10, 'unite': 'pts'},
                        {'nom': 'Motricité globale', 'min': 0, 'max': 10, 'unite': 'pts'},
                        {'nom': 'Coordination', 'min': 0, 'max': 10, 'unite': 'pts'}
                    ]
                },
                {
                    'nom': 'Émotionnel',
                    'description': 'Gestion émotionnelle et bien-être',
                    'couleur': '#f39c12',
                    'indicateurs': [
                        {'nom': 'Stabilité émotionnelle', 'min': 0, 'max': 10, 'unite': 'pts'},
                        {'nom': 'Expression émotionnelle', 'min': 0, 'max': 10, 'unite': 'pts'},
                        {'nom': 'Auto-régulation', 'min': 0, 'max': 10, 'unite': 'pts'}
                    ]
                }
            ]
        }
    ]

    for grille_data in grilles_standard:
        existing = GrilleEvaluation.query.filter_by(
            nom=grille_data['nom'],
            user_id=None  # Grille publique
        ).first()
        
        if not existing:
            try:
                grille = CotationService.creer_grille_personnalisee(
                    nom=grille_data['nom'],
                    description=grille_data['description'],
                    domaines_data=grille_data['domaines'],
                    user_id=None,  # Grille publique
                    reference_scientifique=grille_data['reference_scientifique']
                )
                
                # Marquer comme publique
                grille.est_publique = True
                db.session.commit()
                print(f"✅ Grille {grille_data['nom']} créée")
                
            except Exception as e:
                print(f"❌ Erreur création grille {grille_data['nom']}: {e}")
                db.session.rollback()

    # Créer une grille personnalisée pour l'utilisateur
    if not GrilleEvaluation.query.filter_by(nom='Ma Grille Personnalisée', user_id=user.id).first():
        try:
            CotationService.creer_grille_personnalisee(
                nom='Ma Grille Personnalisée',
                description='Grille adaptée à ma pratique clinique',
                domaines=[
                    {
                        'nom': 'Attention',
                        'description': 'Capacité d\'attention et concentration',
                        'couleur': '#9b59b6',
                        'indicateurs': [
                            {'nom': 'Attention soutenue', 'min': 0, 'max': 5, 'unite': 'pts'},
                            {'nom': 'Concentration', 'min': 0, 'max': 5, 'unite': 'pts'}
                        ]
                    }
                ],
                user_id=user.id
            )
            print("✅ Grille personnalisée créée")
        except Exception as e:
            print(f"❌ Erreur création grille personnalisée: {e}")

    print("\n🎯 Données de test créées avec succès!")
    print("📧 Email: test@musicotherapeute.fr")
    print("🔑 Mot de passe: test123")
    print("\n🚀 Vous pouvez maintenant tester:")
    print("- Navigation vers les grilles de cotation")
    print("- Voir les séances à coter")
    print("- Consulter les statistiques analytics")

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        creer_donnees_test()
