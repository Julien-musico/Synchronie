from flask import Blueprint

## Removed import of grilles_bp (grilles.py deleted)
from .seances import seances_bp
from .analytics import analytics_bp

cotation_bp = Blueprint('cotation', __name__, url_prefix='/cotation')

## Removed registration of grilles_bp (no longer exists)
cotation_bp.register_blueprint(seances_bp)
cotation_bp.register_blueprint(analytics_bp)
