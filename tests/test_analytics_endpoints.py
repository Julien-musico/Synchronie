import pytest
from app import create_app, db
from app.models import User
from app.services.cotation_service import CotationService

@pytest.fixture(scope='module')
def app():
    app = create_app('default')
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        user = User.query.filter_by(email='analytics@test.com').first()  # type: ignore
        if not user:
            user = User(email='analytics@test.com')  # type: ignore[call-arg]
            user.set_password('pw')  # type: ignore
            db.session.add(user)
            db.session.commit()
        yield app

@pytest.fixture()
def client(app):
    c = app.test_client()
    c.post('/login', data={'email':'analytics@test.com','password':'pw'}, follow_redirects=True)
    return c

def test_dashboard_analytics_endpoint(client, app):
    """Test l'endpoint des statistiques globales"""
    with app.app_context():
        # Créer quelques données de test
        CotationService.creer_grille_personnalisee('Test Analytics', 'Description', [
            {'nom': 'TestDom', 'couleur': '#000', 'description': '', 'indicateurs': [
                {'nom': 'TestInd', 'min': 0, 'max': 10, 'unite': 'pts'}
            ]}
        ])
        
        response = client.get('/cotation/analytics/dashboard')
        assert response.status_code == 200
        data = response.get_json()
        assert 'nb_patients' in data
        assert 'nb_grilles' in data
        assert 'score_moyen_30j' in data
        assert data['nb_grilles'] >= 1  # Au moins la grille créée

def test_patients_risque_endpoint(client, app):
    """Test l'endpoint des patients à risque"""
    response = client.get('/cotation/analytics/patients-risque?seuil=30')
    assert response.status_code == 200
    data = response.get_json()
    assert 'patients_risque' in data
    assert 'seuil_utilise' in data
    assert data['seuil_utilise'] == 30.0
    assert isinstance(data['patients_risque'], list)

def test_rapport_mensuel_endpoint(client, app):
    """Test l'endpoint du rapport mensuel"""
    response = client.get('/cotation/analytics/rapport-mensuel/2024/12')
    assert response.status_code == 200
    data = response.get_json()
    assert 'periode' in data
    assert 'nb_seances' in data
    assert 'nb_cotations' in data
    assert data['periode'] == '12/2024'

def test_rapport_mensuel_periode_invalide(client, app):
    """Test validation de période invalide"""
    response = client.get('/cotation/analytics/rapport-mensuel/2024/13')
    assert response.status_code == 400
    data = response.get_json()
    assert 'error' in data
    assert 'invalide' in data['error']
