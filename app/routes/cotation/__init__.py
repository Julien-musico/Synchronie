# Route création de grille personnalisée
@cotation_bp.route('/grilles/creer-grille-personalisee', methods=['GET', 'POST'], endpoint='creer_grille_personalisee')
def creer_grille_personalisee():
	"""Affiche le formulaire de création de grille personnalisée."""
	# TODO: Remplacer par la vraie logique si besoin
	return render_template('cotation/creer_grille_personalisee.html')
from flask import Blueprint, render_template

## Removed import of grilles_bp (grilles.py deleted)
from .seances import seances_bp
from .analytics import analytics_bp

cotation_bp = Blueprint('cotation', __name__, url_prefix='/cotation')


# Route catalogue des grilles (remplace l'ancien blueprint grilles)
@cotation_bp.route('/grilles', methods=['GET'])
def grilles():
	"""Affiche le catalogue des grilles d'évaluation."""
	# TODO: Remplacer par la vraie logique si besoin
	return render_template('cotation/grilles.html')
cotation_bp.register_blueprint(seances_bp)
cotation_bp.register_blueprint(analytics_bp)
