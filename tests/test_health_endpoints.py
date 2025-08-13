import pytest

from app import create_app, db  # type: ignore
from app.models import User  # type: ignore


@pytest.fixture(scope="module")
def app():
    app = create_app('default')
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        # Ensure a user exists
        user = User.query.filter_by(email='tester@example.com').first()  # type: ignore
        if not user:
            user = User(email='tester@example.com')  # type: ignore[call-arg]
            user.set_password('password')  # type: ignore
            db.session.add(user)
            db.session.commit()
        yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def auth_client(app, client):
    # login
    client.post('/login', data={'email':'tester@example.com','password':'password'}, follow_redirects=True)
    return client

# Core endpoint list (GET only) we expect 200 or redirect (302 to login if not auth)
PUBLIC_ENDPOINTS = [
    '/',
]

AUTH_ENDPOINTS = [
    '/patients/',
    '/seances/',
    '/cotation/grilles'
]

def test_public_redirects(client):
    for ep in AUTH_ENDPOINTS:
        r = client.get(ep)
        assert r.status_code in (302, 200)

def test_auth_endpoints(auth_client):
    for ep in AUTH_ENDPOINTS:
        r = auth_client.get(ep)
        assert r.status_code == 200, f"Endpoint {ep} returned {r.status_code}"

def test_create_patient_seance_and_cotation_flow(auth_client):
    # 1. Créer un patient
    patient_payload = {
        'nom': 'Testeur',
        'prenom': 'Alice',
        'email': 'alice@example.com'
    }
    rp = auth_client.post('/patients/create', data=patient_payload, follow_redirects=False)
    assert rp.status_code in (302, 303), f"Patient creation redirect expected, got {rp.status_code}"
    # Récupérer patient_id depuis Location si possible
    # Redirection Location non nécessaire pour la suite
    # Fallback simple: visiter liste patients et chercher lien
    patients_page = auth_client.get('/patients/')
    assert patients_page.status_code == 200
    # Heuristique d'extraction id (non critique si absent)
    patient_id = None
    import re
    m = re.search(rb'/patients/(\d+)', patients_page.data)
    if m:
        patient_id = int(m.group(1))
    assert patient_id is not None, 'Patient ID not found in listing'

    # 2. Créer une séance pour ce patient
    seance_payload = {
        'duree_minutes': '45',
        'type_seance': 'individuelle',
        'objectifs_seance': 'Objectif test',
        'observations': 'Observation test'
    }
    rs = auth_client.post(f'/seances/patient/{patient_id}/create', data=seance_payload, follow_redirects=False)
    assert rs.status_code in (302, 303)

    # 3. Récupérer une séance ID via page patient
    patient_detail = auth_client.get(f'/patients/{patient_id}')
    assert patient_detail.status_code == 200
    ms = re.search(rb'/seances/(\d+)"', patient_detail.data)
    assert ms, 'Seance ID not found in patient detail'
    seance_id = int(ms.group(1))

    # 4. Accéder à interface cotation (devrait être 200 ou 302 si aucune grille encore)
    rc = auth_client.get(f'/cotation/seance/{seance_id}/coter')
    assert rc.status_code == 200, f"Cotation interface returned {rc.status_code}"
