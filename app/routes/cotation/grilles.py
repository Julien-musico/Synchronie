
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
    from flask_login import current_user
    # Grilles personnalisées de l'utilisateur
    grilles_user = Grille.query.filter_by(type_grille="personnalisée", user_id=current_user.id).all() if current_user.is_authenticated else []
    # Grilles publiques et standardisées
    grilles_publiques = Grille.query.filter(Grille.type_grille.in_(["standardisée", "publique"]))
    grilles_publiques = grilles_publiques.all()
    # Ajoute domaines/indicateurs pour affichage
    for grille in grilles_publiques:
        grille.domaines = grille.domaines  # propriété du modèle
    for grille in grilles_user:
        grille.domaines = grille.domaines
    return render_template('cotation/grilles.html', grilles_user=grilles_user, grilles_publiques=grilles_publiques)

@grilles_bp.route('/creer-grille-personalisee', endpoint='creer_grille_personalisee')
@login_required
def creer_grille_personalisee():
    return render_template('cotation/creer_grille_personalisee.html')
