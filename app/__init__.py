from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail
from config import config
import os

# Extensions Flask
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
mail = Mail()

def create_app(config_name=None):
    """Factory pattern pour créer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    
    # Configuration de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    login_manager.login_message_category = 'info'
    
    # Création du dossier uploads s'il n'existe pas
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Enregistrement des blueprints
    from app.routes.main import bp as main_bp
    app.register_blueprint(main_bp)
    
    from app.routes.auth import bp as auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    from app.routes.patients import bp as patients_bp
    app.register_blueprint(patients_bp, url_prefix='/patients')
    
    from app.routes.sessions import bp as sessions_bp
    app.register_blueprint(sessions_bp, url_prefix='/sessions')
    
    from app.routes.grilles import bp as grilles_bp
    app.register_blueprint(grilles_bp, url_prefix='/grilles')
    
    from app.routes.rapports import bp as rapports_bp
    app.register_blueprint(rapports_bp, url_prefix='/rapports')
    
    # Import des modèles pour les migrations
    from app.models import user, patient, session, grille, rapport
    
    return app

@login_manager.user_loader
def load_user(user_id):
    """Callback pour charger un utilisateur"""
    from app.models.user import User
    return User.query.get(int(user_id))
