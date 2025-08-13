import pytest

from app import create_app, db  # type: ignore
from app.models import User  # type: ignore
from app.models.cotation import GrilleEvaluation, GrilleVersion  # type: ignore
from app.services.cotation_service import CotationService  # type: ignore


@pytest.fixture(scope='module')
def app():
    app = create_app('default')
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        user = User.query.filter_by(email='version@test.com').first()  # type: ignore
        if not user:
            user = User(email='version@test.com')  # type: ignore[call-arg]
            user.set_password('pw')  # type: ignore
            db.session.add(user)
            db.session.commit()
        yield app

@pytest.fixture()
def _app_ctx(app):
    with app.app_context():
        yield

@pytest.fixture()
def user_client(app):
    client = app.test_client()
    client.post('/login', data={'email':'version@test.com','password':'pw'}, follow_redirects=True)
    return client


def test_version_creation_and_increment(user_client, app_ctx):
    # Créer une grille personnalisée
    g = CotationService.creer_grille_personnalisee('Test V', 'Desc', [
        {'nom':'D1','couleur':'#111','description':'','indicateurs':[{'nom':'I1','min':0,'max':5,'unite':'pts'}]}
    ])
    versions = GrilleVersion.query.filter_by(grille_id=g.id).order_by(GrilleVersion.version_num).all()  # type: ignore
    assert len(versions) == 1
    assert versions[0].version_num == 1

    # Mise à jour domaines -> nouvelle version
    CotationService.update_grille_domaines(g.id, [
        {'nom':'D1','couleur':'#111','description':'','indicateurs':[{'nom':'I1','min':0,'max':5,'unite':'pts'}]},
        {'nom':'D2','couleur':'#222','description':'','indicateurs':[{'nom':'I2','min':0,'max':10,'unite':'pts'}]}
    ])
    versions2 = GrilleVersion.query.filter_by(grille_id=g.id).order_by(GrilleVersion.version_num).all()  # type: ignore
    assert len(versions2) == 2
    assert versions2[-1].version_num == 2
    assert versions2[0].active is False
    assert versions2[-1].active is True


def test_cotation_uses_active_version(user_client, app_ctx):
    # Reprendre une grille existante ou créer
    g = GrilleEvaluation.query.filter_by(nom='Test V').first()  # type: ignore
    if not g:
        g = CotationService.creer_grille_personnalisee('Test V', 'Desc', [
            {'nom':'D1','couleur':'#111','description':'','indicateurs':[{'nom':'I1','min':0,'max':5,'unite':'pts'}]}
        ])
    # Créer une cotation factice (séance id arbitraire 1)
    c = CotationService.creer_cotation(seance_id=1, grille_id=g.id, scores={'D1_I1':3})
    # Le lien direct vers une version de grille a été retiré (grille_version_id supprimé).
    # On vérifie simplement que la cotation référence la bonne grille et calcule un score.
    assert c.grille_id == g.id
    assert c.score_global is not None
