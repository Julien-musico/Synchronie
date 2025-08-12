from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import enum

class UserRole(enum.Enum):
    """Rôles utilisateur dans l'application"""
    THERAPIST = "therapist"  # Musicothérapeute
    SUPERVISOR = "supervisor"  # Superviseur/Responsable
    ADMIN = "admin"  # Administrateur système

class User(UserMixin, db.Model):
    """Modèle utilisateur pour l'authentification et la gestion des droits"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations personnelles
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    
    # Authentification
    password_hash = db.Column(db.String(255), nullable=False)
    
    # Rôle et permissions
    role = db.Column(db.Enum(UserRole), nullable=False, default=UserRole.THERAPIST)
    is_active = db.Column(db.Boolean, default=True)
    
    # Informations professionnelles
    license_number = db.Column(db.String(50))  # Numéro de licence/diplôme
    institution = db.Column(db.String(200))  # Établissement d'exercice
    specialities = db.Column(db.Text)  # Spécialités (JSON)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relations
    patients = db.relationship('Patient', backref='therapist', lazy='dynamic')
    sessions = db.relationship('Session', backref='therapist', lazy='dynamic')
    grilles_created = db.relationship('Grille', backref='creator', lazy='dynamic')
    
    def set_password(self, password):
        """Définit le mot de passe hashé"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie le mot de passe"""
        return check_password_hash(self.password_hash, password)
    
    def get_full_name(self):
        """Retourne le nom complet"""
        return f"{self.first_name} {self.last_name}"
    
    def has_role(self, role):
        """Vérifie si l'utilisateur a un rôle spécifique"""
        if isinstance(role, str):
            role = UserRole(role)
        return self.role == role
    
    def can_access_patient(self, patient):
        """Vérifie si l'utilisateur peut accéder aux données d'un patient"""
        if self.role in [UserRole.ADMIN, UserRole.SUPERVISOR]:
            return True
        return self.id == patient.therapist_id
    
    def __repr__(self):
        return f'<User {self.username}>'
