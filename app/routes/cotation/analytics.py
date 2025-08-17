"""
Routes pour les analyses et statistiques liées à la cotation thérapeutique.
"""

from flask import Blueprint, jsonify
from flask_login import login_required, current_user

from app.services.analytics_service import AnalyticsService

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')


@analytics_bp.route('/scores-grilles')
@login_required
def scores_grilles():
    """API : Scores moyens par grille (Top 8)."""
    data = AnalyticsService.scores_moyens_par_grille(current_user.id, 8)
    return jsonify({'items': data})
