from flask import Blueprint

from .grilles import grilles_bp
from .seances import seances_bp
from .analytics import analytics_bp

cotation_bp = Blueprint('cotation', __name__, url_prefix='/cotation')

cotation_bp.register_blueprint(grilles_bp)
cotation_bp.register_blueprint(seances_bp)
cotation_bp.register_blueprint(analytics_bp)
