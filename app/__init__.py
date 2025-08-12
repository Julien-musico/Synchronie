"""
Factory pattern pour créer l'application Flask
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import config

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_name='default'):
    """
    Factory function pour créer l'application Flask
    
    Args:
        config_name (str): Nom de la configuration à utiliser
        
    Returns:
        Flask: Instance de l'application Flask configurée
    """
    app = Flask(__name__)
    
    # Chargement de la configuration
    app.config.from_object(config[config_name])
    
    # Initialisation des extensions avec l'app
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Enregistrement des blueprints (routes)
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    from app.routes.api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    from app.routes.patients import patients as patients_blueprint
    app.register_blueprint(patients_blueprint, url_prefix='/patients')
    
    # Création des tables si elles n'existent pas
    with app.app_context():
        db.create_all()
    
    return app
