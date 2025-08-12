"""
Modèles de base pour l'application Synchronie
"""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

# Créer une instance de db que nous importerons dans __init__.py
db = SQLAlchemy()

class TimestampMixin:
    """Mixin pour ajouter des timestamps automatiques"""
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    date_modification = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

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
    
    # Informations médicales
    pathologie = db.Column(db.String(200))
    objectifs_therapeutiques = db.Column(db.Text)
    commentaires = db.Column(db.Text)
    
    # Statut
    actif = db.Column(db.Boolean, default=True, nullable=False)
    
    # Relations
    seances = db.relationship('Seance', backref='patient', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Patient {self.prenom} {self.nom}>'
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour l'API"""
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
            'nb_seances': len(self.seances)
        }

class Seance(TimestampMixin, db.Model):
    """Modèle pour les séances de musicothérapie"""
    __tablename__ = 'seances'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    
    # Informations de la séance
    date_seance = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
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
    
    def to_dict(self):
        """Convertit l'objet en dictionnaire pour l'API"""
        return {
            'id': self.id,
            'patient_id': self.patient_id,
            'date_seance': self.date_seance.isoformat(),
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
