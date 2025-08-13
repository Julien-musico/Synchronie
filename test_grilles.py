#!/usr/bin/env python3
"""Test des grilles de cotation"""

from app import create_app, db
from app.models.cotation import PatientGrille
from app.services.cotation_service import CotationService

def test_grilles():
    app = create_app()
    with app.app_context():
        # Créer les tables manquantes
        db.create_all()
        print('✅ Tables créées')
        
        try:
            # Créer une grille AMTA
            grille1 = CotationService.creer_grille_predefinie('amta_standard')
            if grille1:
                print(f'✅ Grille AMTA créée avec ID: {grille1.id}')
            
            # Créer une grille rapide
            grille2 = CotationService.creer_grille_predefinie('evaluation_rapide')
            if grille2:
                print(f'✅ Grille évaluation rapide créée avec ID: {grille2.id}')
                
            # Créer une grille IMCAP
            grille3 = CotationService.creer_grille_predefinie('imcap_nd')
            if grille3:
                print(f'✅ Grille IMCAP-ND créée avec ID: {grille3.id}')
                
            print('🎉 Toutes les grilles de test créées!')
            
        except Exception as e:
            print(f'❌ Erreur: {e}')
            import traceback
            traceback.print_exc()

if __name__ == '__main__':
    test_grilles()
