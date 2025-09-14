"""
Modèles de base pour l'application Synchronie
"""
from datetime import datetime, timezone

from flask_login import UserMixin  # type: ignore
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash  # type: ignore

# Créer une instance de db que nous importerons dans __init__.py
db = SQLAlchemy()

class TimestampMixin:
    """Mixin pour ajouter des timestamps automatiques"""
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    date_modification = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

class User(TimestampMixin, UserMixin, db.Model):
    """Utilisateur (musicothérapeute)."""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    nom = db.Column(db.String(120))
    mot_de_passe_hash = db.Column(db.String(255), nullable=False)
    actif = db.Column(db.Boolean, default=True, nullable=False)

    def set_password(self, password: str) -> None:  # type: ignore
        self.mot_de_passe_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:  # type: ignore
        return check_password_hash(self.mot_de_passe_hash, password)

    def get_id(self):  # type: ignore
        return str(self.id)

    def __repr__(self):  # type: ignore
        return f"<User {self.email}>"

class Patient(TimestampMixin, db.Model):
    """Modèle pour les patients"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    date_naissance = db.Column(db.Date)
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    adresse = db.Column(db.Text)
    # Musicothérapeute propriétaire (optionnel si multi-utilisateurs)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    user = db.relationship('User', backref='patients')
    
    # Informations médicales
    pathologie = db.Column(db.String(200))
    objectifs_therapeutiques = db.Column(db.Text)
    commentaires = db.Column(db.Text)
    
    # Statut
    actif = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relations
    seances = db.relationship('Seance', backref='patient', lazy=True, cascade='all, delete-orphan')

    def __init__(
        self,
        nom: str,
        prenom: str,
        date_naissance: 'datetime.date | None' = None,  # type: ignore[name-defined]
        telephone: 'str | None' = None,
        email: 'str | None' = None,
        adresse: 'str | None' = None,
        user_id: 'int | None' = None,
        pathologie: 'str | None' = None,
        objectifs_therapeutiques: 'str | None' = None,
        commentaires: 'str | None' = None,
        actif: bool = True,
        **kwargs
    ) -> None:  # type: ignore[override]
        super().__init__(**kwargs)
        self.nom = nom
        self.prenom = prenom
        self.date_naissance = date_naissance
        self.telephone = telephone
        self.email = email
        self.adresse = adresse
        self.user_id = user_id
        self.pathologie = pathologie
        self.objectifs_therapeutiques = objectifs_therapeutiques
        self.commentaires = commentaires
        self.actif = actif
    
    def __repr__(self):
        return f'<Patient {self.prenom} {self.nom}>'
    
    def to_dict(self) -> dict[str, object]:
        """Convertit l'objet en dictionnaire pour l'API"""
        nb_seances = self.seances and len(list(self.seances)) if isinstance(self.seances, list) else 0  # type: ignore
        return {
            'id': self.id,
            'nom': self.nom,
            'prenom': self.prenom,
            'date_naissance': self.date_naissance.isoformat() if self.date_naissance else None,
            'telephone': self.telephone,
            'email': self.email,
            'pathologie': self.pathologie,
            'actif': self.actif,
            'date_creation': self.date_creation.isoformat(),
            'nb_seances': nb_seances
        }

class Seance(TimestampMixin, db.Model):
    """Modèle pour les séances de musicothérapie"""
    __tablename__ = 'seances'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    # Informations de la séance
    date_seance = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    duree_minutes = db.Column(db.Integer)  # Durée en minutes
    type_seance = db.Column(db.String(50))  # individuelle, groupe, etc.
    
    # Contenu de la séance
    objectifs_seance = db.Column(db.Text)
    activites_realisees = db.Column(db.Text)
    instruments_utilises = db.Column(db.Text)
    
    # Observations et évaluation
    observations = db.Column(db.Text)
    humeur_debut = db.Column(db.String(50))
    humeur_fin = db.Column(db.String(50))
    participation = db.Column(db.String(50))
    
    # IA et transcription
    transcription_audio = db.Column(db.Text)
    synthese_ia = db.Column(db.Text)
    fichier_audio = db.Column(db.String(255))  # Chemin vers le fichier audio
    
    # Cotation thérapeutique (à développer)
    score_engagement = db.Column(db.Integer)  # 1-10
    score_expression = db.Column(db.Integer)  # 1-10
    score_interaction = db.Column(db.Integer)  # 1-10
    
    def __repr__(self):
        return f'<Seance {self.date_seance} - Patient {self.patient_id}>'
    
    def to_dict(self) -> dict[str, object]:
        """Convertit l'objet en dictionnaire pour l'API"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'date_seance': self.date_seance.isoformat() if self.date_seance else None,
            'duree_minutes': self.duree_minutes,
            'type_seance': self.type_seance,
            'objectifs_seance': self.objectifs_seance,
            'observations': self.observations,
            'humeur_debut': self.humeur_debut,
            'humeur_fin': self.humeur_fin,
            'participation': self.participation,
            'score_engagement': self.score_engagement,
            'score_expression': self.score_expression,
            'score_interaction': self.score_interaction,
            'synthese_ia': self.synthese_ia
        }
