"""
Factory pattern pour créer l'application Flask
"""
from flask import Flask
from flask_migrate import Migrate
from config import config

# Import de la base de données depuis les modèles pour éviter les imports circulaires
from app.models import db

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
    try:
        from app.routes.main import main as main_blueprint
        app.register_blueprint(main_blueprint)
        
        from app.routes.api import api as api_blueprint
        app.register_blueprint(api_blueprint, url_prefix='/api')
        
        from app.routes.patients import patients as patients_blueprint
        app.register_blueprint(patients_blueprint, url_prefix='/patients')
    except ImportError as e:
        # En cas d'erreur d'import, créer des routes de base
        print(f"Warning: Could not import blueprints: {e}")
        
        @app.route('/')
        def index():
            return '<h1>Synchronie - Application en cours de démarrage...</h1>'
        
        @app.route('/api/health')
        def health():
            return {'status': 'ok', 'message': 'Application running'}
    
    # Création des tables si elles n'existent pas
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")
    
    return app
