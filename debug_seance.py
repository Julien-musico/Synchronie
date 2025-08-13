#!/usr/bin/env python3
"""
Script de debug pour tester la création de séances
"""

from app import create_app
from app.models import Patient
from app.services.seance_service import SeanceService


def debug_seance_creation():
    app = create_app()
    with app.app_context():
        print("🔍 Debug de la création de séances")
        print("=" * 50)
        
        # Vérifier les patients existants
        patients = Patient.query.all()
        print(f"Patients trouvés: {len(patients)}")
        
        if not patients:
            print("❌ Aucun patient disponible")
            return
        
        patient = patients[0]
        print(f"✅ Patient sélectionné: {patient.prenom} {patient.nom} (ID: {patient.id})")
        
        # Données de test pour la séance
        test_data = {
            'date_seance': '2025-01-15T14:30',
            'duree_minutes': '45',
            'type_seance': 'musicothérapie',
            'objectifs_seance': 'Test de création de séance',
            'activites_realisees': 'Activités de test',
            'observations': 'Observations de test',
            'score_engagement': '7'
        }
        
        print("\n📝 Tentative de création de séance...")
        print(f"Données: {test_data}")
        
        try:
            success, message, seance = SeanceService.create_seance(patient.id, test_data)
            
            if success:
                print(f"✅ SUCCÈS: {message}")
                print(f"   📅 ID Séance: {seance.id}")
                print(f"   📅 Date: {seance.date_seance}")
                print(f"   ⏱️ Durée: {seance.duree_minutes} min")
                print(f"   🎯 Type: {seance.type_seance}")
                print(f"   ⭐ Score: {seance.score_engagement}/10")
            else:
                print(f"❌ ÉCHEC: {message}")
                
        except Exception as e:
            print(f"🚨 ERREUR EXCEPTION: {str(e)}")
            import traceback
            traceback.print_exc()
        
        # Vérifier toutes les séances après tentative
        print(f"\n📊 Séances totales après test: {len(SeanceService.get_all_seances())}")

if __name__ == "__main__":
    debug_seance_creation()
