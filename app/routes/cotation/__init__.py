from flask import Blueprint, render_template
from app.models.cotation import GrilleEvaluation
from flask_login import current_user

from .seances import seances_bp
from .analytics import analytics_bp

cotation_bp = Blueprint('cotation', __name__, url_prefix='/cotation')

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
# Route détail d'une grille (nécessaire pour le lien dans grilles.html)
@cotation_bp.route('/grille/<int:grille_id>', methods=['GET'], endpoint='grille_detail')
def grille_detail(grille_id):
    grille = GrilleEvaluation.query.get_or_404(grille_id)
    return render_template('cotation/grille_detail.html', grille=grille)

# Route création de grille personnalisée
@cotation_bp.route('/grilles/creer-grille-personalisee', methods=['GET', 'POST'], endpoint='creer_grille_personalisee')
def creer_grille_personalisee():
    """Affiche le formulaire de création de grille personnalisée."""
    # TODO: Remplacer par la vraie logique si besoin
    return render_template('cotation/creer_grille_personalisee.html')

cotation_bp.register_blueprint(seances_bp)
cotation_bp.register_blueprint(analytics_bp)
