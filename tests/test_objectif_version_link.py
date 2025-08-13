import pytest
from app import create_app, db
from app.models import User
from app.models.cotation import GrilleVersion
from app.services.cotation_service import CotationService
from app.services.objectif_service import ObjectifService

@pytest.fixture(scope='module')
def app():
    app = create_app('default')
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        user = User.query.filter_by(email='obj@test.com').first()  # type: ignore
        if not user:
            user = User(email='obj@test.com')  # type: ignore[call-arg]
            user.set_password('pw')  # type: ignore
            db.session.add(user)
            db.session.commit()
        yield app

@pytest.fixture()
def client(app):
    c = app.test_client()
    c.post('/login', data={'email':'obj@test.com','password':'pw'}, follow_redirects=True)
    return c


def test_objectif_links_active_version(client, app):
    with app.app_context():
        g = CotationService.creer_grille_personnalisee('Obj Grille', 'Desc', [
            {'nom':'DX','couleur':'#000','description':'','indicateurs':[{'nom':'IX','min':0,'max':5,'unite':'pts'}]}
        ])
        active_v = GrilleVersion.query.filter_by(grille_id=g.id, active=True).first()  # type: ignore
        obj = ObjectifService.creer_objectif(patient_id=1, grille_id=g.id, domaine_cible='DX', indicateur_cible='IX', score_cible=4)
        assert obj.grille_version_id == (active_v.id if active_v else None)
        # Mise à jour de la grille -> nouvelle version
        CotationService.update_grille_domaines(g.id, [
            {'nom':'DX','couleur':'#000','description':'','indicateurs':[{'nom':'IX','min':0,'max':5,'unite':'pts'}]},
            {'nom':'DY','couleur':'#111','description':'','indicateurs':[{'nom':'IY','min':0,'max':10,'unite':'pts'}]}
        ])
        new_active = GrilleVersion.query.filter_by(grille_id=g.id, active=True).first()  # type: ignore
        # Créer un second objectif
        obj2 = ObjectifService.creer_objectif(patient_id=1, grille_id=g.id, domaine_cible='DY', indicateur_cible='IY', score_cible=8)
        assert obj2.grille_version_id == (new_active.id if new_active else None)
