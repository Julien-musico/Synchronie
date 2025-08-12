from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from config import config
import os

# Extensions Flask
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

def create_app(config_name=None):
    """Factory pattern simplifié pour Synchronie"""
    app = Flask(__name__)
    
    # Configuration simplifiée
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    app.config.from_object(config[config_name])
    
    # Initialisation extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Configuration login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter.'
    
    # Routes principales
    from app.routes.main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # Initialisation DB en production
    with app.app_context():
        try:
            db.create_all()
            print("✅ Base de données initialisée")
        except Exception as e:
            print(f"⚠️ Erreur DB: {e}")
    
    return app
