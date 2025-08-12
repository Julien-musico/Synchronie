from app import create_app
from app.services.seance_service import SeanceService
from datetime import datetime

app = create_app()

with app.app_context():
    service = SeanceService()
    
    # Test de création de séance
    print('Test de création de séance...')
    donnees = {
        'date_seance': datetime.now().date(),
        'duree_minutes': 45,
        'type_seance': 'individuelle',
        'objectifs_seance': 'Test d objectifs',
        'activites_realisees': 'Écoute musicale, improvisation vocale',
        'instruments_utilises': 'Piano, voix',
        'observations': 'Patient très réceptif',
        'humeur_debut': 'calme',
        'humeur_fin': 'joyeux',
        'participation': 'active'
    }
    
    try:
        success, message, seance = service.create_seance(1, donnees)
        if success:
            print(f'✅ SUCCÈS: Séance créée avec ID: {seance.id}')
        else:
            print(f'❌ ÉCHEC: {message}')
    except Exception as e:
        print(f'❌ ÉCHEC: {e}')
        import traceback
        traceback.print_exc()
