"""
Factory pattern pour créer l'application Flask
"""
from flask import Flask, redirect, url_for
from flask_migrate import Migrate

try:
    from flask_login import LoginManager  # type: ignore
    _LOGIN_AVAILABLE = True
except Exception:  # pragma: no cover
    LoginManager = None  # type: ignore
    _LOGIN_AVAILABLE = False
# Import de la base de données depuis les modèles pour éviter les imports circulaires
from app.models import User, db
from config import config  # type: ignore

migrate = Migrate()

def create_app(config_name: str = 'default') -> Flask:
    """
    Factory function pour créer l'application Flask
    
    Args:
        config_name (str): Nom de la configuration à utiliser
        
    Returns:
        Flask: Instance de l'application Flask configurée
    """
    app = Flask(__name__)
    
    # Chargement de la configuration
    app.config.from_object(config[config_name])  # type: ignore

    # Filtres Jinja personnalisés
    def nl2br(value: str) -> str:
        """Convertit les retours ligne en balises <br>."""
        return value.replace('\r\n', '\n').replace('\n', '<br>') if isinstance(value, str) else value  # type: ignore
    app.jinja_env.filters['nl2br'] = nl2br  # type: ignore
    
    # Initialisation des extensions avec l'app
    db.init_app(app)
    migrate.init_app(app, db)

    # Auth réelle : LoginManager + User loader
    if _LOGIN_AVAILABLE and LoginManager:  # type: ignore
        login_manager = LoginManager()  # type: ignore[call-arg]
        # Endpoint complet du formulaire de connexion
        login_manager.login_view = 'auth.login'  # type: ignore[attr-defined]
        login_manager.init_app(app)  # type: ignore[attr-defined]

        @login_manager.user_loader  # type: ignore[attr-defined]
        def load_user(user_id: str):  # type: ignore
            try:
                return User.query.get(int(user_id))  # type: ignore
            except Exception:
                return None  # type: ignore
    else:
        app.logger.warning("Flask-Login indisponible: activer flask_login pour protéger les routes.")
    
    # Enregistrement des blueprints (routes) avec robustesse
    from importlib import import_module
    def safe_register(import_path: str, attr: str, url_prefix: str | None = None) -> bool:
        try:
            module = import_module(import_path)
            bp = getattr(module, attr)
            if url_prefix:
                app.register_blueprint(bp, url_prefix=url_prefix)
            else:
                app.register_blueprint(bp)
            app.logger.info(f"Blueprint '{import_path}.{attr}' chargé avec succès.")
            return True
        except Exception as e:  # noqa
            import traceback
            tb = traceback.format_exc()
            app.logger.error(f"Blueprint '{import_path}.{attr}' non chargé: {e}\nTraceback:\n{tb}")
            print(f"[SAFE_REGISTER] ERREUR: Blueprint '{import_path}.{attr}' non chargé: {e}\nTraceback:\n{tb}")
            return False

    safe_register('app.routes.main', 'main')
    safe_register('app.routes.auth', 'auth')
    safe_register('app.routes.api', 'api', '/api')
    safe_register('app.routes.patients', 'patients', '/patients')
    safe_register('app.routes.seances', 'seances', '/seances')
    safe_register('app.routes.audio', 'audio', '/audio')
    # Legacy grilles blueprint removed in favor of cotation routes
    cotation_ok = safe_register('app.routes.cotation', 'cotation_bp')

    if not cotation_ok:
        @app.route('/cotation/grilles')  # type: ignore
        def cotation_placeholder():  # type: ignore
            return '<h2>Cotation indisponible (initialisation en cours)</h2>'

    # Redirections des anciennes routes /grilles vers la nouvelle page unifiée
    @app.route('/grilles')  # type: ignore
    @app.route('/grilles/')  # type: ignore
    @app.route('/grilles/<path:subpath>')  # type: ignore
    def redirect_legacy_grilles(subpath: str | None = None):  # type: ignore
        return redirect(url_for('cotation.grilles'), code=302)

    # Contexte global pour les templates
    @app.context_processor  # type: ignore
    def inject_flags():  # type: ignore
        return {
            'has_cotation': cotation_ok
        }

    # Commande CLI utilitaire pour debug
    try:
        @app.cli.command('list-endpoints')  # type: ignore
        def list_endpoints():  # type: ignore
            for rule in sorted(app.url_map.iter_rules(), key=lambda r: r.rule):
                print(f"{rule.endpoint:30s} -> {rule.rule}")
    except Exception:
        pass
    
    # Création des tables si elles n'existent pas
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Warning: Could not create tables: {e}")
    
    return app
