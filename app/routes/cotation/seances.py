"""
Routes pour la cotation des séances et l'interface utilisateur associée.
"""

from flask import Blueprint, render_template
from flask_login import login_required, current_user

from app.models import Seance, Patient, db


seances_bp = Blueprint('seances', __name__, url_prefix='/seances')


@seances_bp.route('/a-coter')
@login_required
def seances_a_coter():
    """Liste les séances disponibles pour cotation avec nombre de cotations et dernière cotation."""
    seances = db.session.query(Seance).join(Patient).filter(Patient.user_id == current_user.id).order_by(
        Seance.date_seance.desc()).all()
    seances_info = []
    for seance in seances:
        seances_info.append({
            'seance': seance,
            'nb_cotations': 0,
            'derniere_cotation': None
        })
    return render_template('cotation/seances_a_coter.html', seances_info=seances_info)
