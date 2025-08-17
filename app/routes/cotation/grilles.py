
"""
Routes pour la gestion des grilles d'évaluation (standardisées et personnalisées).
"""
from flask import Blueprint, render_template
from flask_login import login_required
from app.models.cotation import Grille, GrilleDomaine, DomaineIndicateur

grilles_bp = Blueprint('grilles', __name__, url_prefix='/grilles')

@grilles_bp.route('/', endpoint='grilles')
@login_required
def grilles():
    """Affiche toutes les grilles standardisées avec le nombre de domaines et d'indicateurs."""
    grilles_standardisees = Grille.query.filter_by(type_grille="standardisée").all()
    for grille in grilles_standardisees:
        domaines = GrilleDomaine.query.filter_by(grille_id=grille.id).all()
        grille.nb_domaines = len(domaines)
        nb_indicateurs = 0
        for gd in domaines:
            indicateurs = DomaineIndicateur.query.filter_by(domaine_id=gd.domaine_id).all()
            nb_indicateurs += len(indicateurs)
        grille.nb_indicateurs = nb_indicateurs
    return render_template('cotation/grilles.html', grilles_standardisees=grilles_standardisees)

@grilles_bp.route('/creer-grille-personalisee', endpoint='creer_grille_personalisee')
@login_required
def creer_grille_personalisee():
    return render_template('cotation/creer_grille_personalisee.html')
