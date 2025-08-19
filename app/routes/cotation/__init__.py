from flask import Blueprint, render_template
from app.models.cotation import GrilleEvaluation
from flask_login import current_user

from .seances import seances_bp
from .analytics import analytics_bp

cotation_bp = Blueprint('cotation', __name__, url_prefix='/cotation')

# Route catalogue des grilles (remplace l'ancien blueprint grilles)
@cotation_bp.route('/grilles', methods=['GET'])
def grilles():
    """Affiche le catalogue des grilles d'évaluation."""
    grilles_standard = GrilleEvaluation.query.filter_by(type_grille='standard', active=True).all()
    grilles_perso = []
    if current_user.is_authenticated:
        grilles_perso = GrilleEvaluation.query.filter_by(type_grille='personnalisee', user_id=current_user.id, active=True).all()
    return render_template(
        'cotation/grilles.html',
        grilles_standard=grilles_standard,
        grilles_perso=grilles_perso
    )

# Route création de grille personnalisée
@cotation_bp.route('/grilles/creer-grille-personalisee', methods=['GET', 'POST'], endpoint='creer_grille_personalisee')
def creer_grille_personalisee():
    """Affiche le formulaire de création de grille personnalisée."""
    # TODO: Remplacer par la vraie logique si besoin
    return render_template('cotation/creer_grille_personalisee.html')

cotation_bp.register_blueprint(seances_bp)
cotation_bp.register_blueprint(analytics_bp)
