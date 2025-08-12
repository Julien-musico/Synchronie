import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Configuration de base de l'application"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Base de données
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://localhost/synchronie_dev'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload de fichiers
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB max file size
    ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'flac', 'm4a', 'ogg', 'aac'}
    
    # API Keys IA
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    MISTRAL_API_KEY = os.environ.get('MISTRAL_API_KEY')
    
    # Email configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    
    # Celery configuration pour tâches asynchrones
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL') or 'redis://localhost:6379'
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND') or 'redis://localhost:6379'
    
    # Pagination
    PATIENTS_PER_PAGE = 20
    SESSIONS_PER_PAGE = 10
    
    # Rapports automatiques
    AUTOMATIC_REPORTS_INTERVAL = 6  # weeks
    
    # Conformité RGPD
    DATA_RETENTION_YEARS = 10
    ANONYMIZATION_DELAY_YEARS = 5

class DevelopmentConfig(Config):
    """Configuration pour le développement"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'postgresql://localhost/synchronie_dev'

class TestingConfig(Config):
    """Configuration pour les tests"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql://localhost/synchronie_test'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Configuration pour la production"""
    DEBUG = False
    
    # Render fournit DATABASE_URL, mais il faut ajuster pour SQLAlchemy 2.0
    database_url = os.environ.get('DATABASE_URL')
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    SQLALCHEMY_DATABASE_URI = database_url
    
    # Configuration de sécurité renforcée
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuration spécifique Render
    UPLOAD_FOLDER = '/tmp/uploads'  # Render utilise un filesystem temporaire
    
    # Logging pour debug via Render
    import logging
    logging.basicConfig(level=logging.INFO)

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
