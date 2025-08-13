#!/usr/bin/env python3
"""
Script de test pour la gestion des séances
"""
from app import create_app  # type: ignore
from app.models import Patient  # type: ignore
from app.services.seance_service import SeanceService  # type: ignore


def test_seances():
    app = create_app()
    with app.app_context():
        print("🔍 Test du système de gestion des séances")
        print("=" * 50)
        
        # Chercher un patient existant
        patients = Patient.query.all()
        if not patients:
            print("❌ Aucun patient trouvé dans la base de données")
            return
        
        patient = patients[0]
        print(f"✅ Patient trouvé: {patient.prenom} {patient.nom}")
        
        # Créer une séance de test
        test_data = {
            'date_seance': '2025-01-15T14:30',
            'duree_minutes': '45',
            'type_seance': 'musicothérapie',
            'objectifs_seance': 'Améliorer l\'expression émotionnelle à travers l\'improvisation musicale',
            'activites_realisees': 'Improvisation au piano, exploration des rythmes, expression libre',
            'observations': 'Patient très engagé, bonne participation, moments d\'émotion',
            'score_engagement': '8'
        }
        
        print("\n📝 Création d'une séance de test...")
        success, message, seance = SeanceService.create_seance(patient.id, test_data)
        
        if success and seance is not None:
            print("✅ Séance créée avec succès!")
            print(f"   📅 Date: {seance.date_seance}")
            print(f"   ⏱️ Durée: {seance.duree_minutes} minutes")
            print(f"   🎯 Type: {seance.type_seance}")
            if hasattr(seance, 'score_engagement'):
                print(f"   ⭐ Score engagement: {seance.score_engagement}/10")
            print(f"   📋 Message: {message}")
        else:
            print(f"❌ Erreur lors de la création: {message}")
        
        # Test des autres fonctions
        print("\n🔍 Test des fonctions de recherche...")
        
        # Toutes les séances
        all_seances = SeanceService.get_all_seances()
        print(f"✅ Total des séances dans le système: {len(all_seances)}")
        
        # Séances du patient
        patient_seances = SeanceService.get_seances_by_patient(patient.id)
        print(f"✅ Séances du patient {patient.prenom}: {len(patient_seances)}")
        
        print("\n🎉 Tests terminés avec succès!")

if __name__ == "__main__":
    test_seances()
