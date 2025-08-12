from app import db
from datetime import datetime
import enum
import json

class Gender(enum.Enum):
    """Énumération pour le genre"""
    MALE = "M"
    FEMALE = "F"
    OTHER = "O"
    NOT_SPECIFIED = "N"

class PatientStatus(enum.Enum):
    """Statut du patient dans le suivi"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    DISCONTINUED = "discontinued"

class Patient(db.Model):
    """Modèle patient pour la gestion des dossiers"""
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations démographiques
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False)
    gender = db.Column(db.Enum(Gender), nullable=False)
    
    # Informations de contact
    address = db.Column(db.Text)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    emergency_contact = db.Column(db.Text)  # JSON avec nom, téléphone, relation
    
    # Informations médicales
    pathologies = db.Column(db.Text)  # JSON avec liste des pathologies
    medical_history = db.Column(db.Text)  # Historique médical général
    medications = db.Column(db.Text)  # JSON avec liste des médicaments
    allergies = db.Column(db.Text)  # Allergies connues
    contraindications = db.Column(db.Text)  # Contre-indications spécifiques
    
    # Informations musicothérapeutiques
    music_preferences = db.Column(db.Text)  # JSON avec préférences musicales
    instruments_played = db.Column(db.Text)  # JSON avec instruments pratiqués
    therapeutic_objectives = db.Column(db.Text)  # Objectifs thérapeutiques
    initial_assessment = db.Column(db.Text)  # Évaluation initiale
    
    # Suivi administratif
    status = db.Column(db.Enum(PatientStatus), nullable=False, default=PatientStatus.ACTIVE)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    therapist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    sessions = db.relationship('Session', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    rapports = db.relationship('Rapport', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    grille_assignments = db.relationship('GrilleAssignment', backref='patient', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_full_name(self):
        """Retourne le nom complet du patient"""
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        """Calcule l'âge du patient"""
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    def get_pathologies_list(self):
        """Retourne la liste des pathologies"""
        if self.pathologies:
            return json.loads(self.pathologies)
        return []
    
    def set_pathologies_list(self, pathologies_list):
        """Définit la liste des pathologies"""
        self.pathologies = json.dumps(pathologies_list)
    
    def get_music_preferences_dict(self):
        """Retourne les préférences musicales sous forme de dictionnaire"""
        if self.music_preferences:
            return json.loads(self.music_preferences)
        return {}
    
    def set_music_preferences_dict(self, preferences_dict):
        """Définit les préférences musicales"""
        self.music_preferences = json.dumps(preferences_dict)
    
    def get_emergency_contact_dict(self):
        """Retourne le contact d'urgence sous forme de dictionnaire"""
        if self.emergency_contact:
            return json.loads(self.emergency_contact)
        return {}
    
    def set_emergency_contact_dict(self, contact_dict):
        """Définit le contact d'urgence"""
        self.emergency_contact = json.dumps(contact_dict)
    
    def get_total_sessions(self):
        """Retourne le nombre total de séances"""
        return self.sessions.count()
    
    def get_last_session_date(self):
        """Retourne la date de la dernière séance"""
        last_session = self.sessions.order_by(Session.date.desc()).first()
        return last_session.date if last_session else None
    
    def is_due_for_report(self, report_interval_weeks=6):
        """Vérifie si un rapport périodique est dû"""
        from datetime import timedelta
        last_report = self.rapports.order_by(Rapport.created_at.desc()).first()
        
        if not last_report:
            # Premier rapport après au moins 2 séances
            return self.get_total_sessions() >= 2
        
        # Vérifier si l'intervalle est dépassé
        cutoff_date = last_report.created_at.date() + timedelta(weeks=report_interval_weeks)
        return datetime.now().date() > cutoff_date and \
               self.sessions.filter(Session.date > last_report.created_at.date()).count() >= 2
    
    def __repr__(self):
        return f'<Patient {self.get_full_name()}>'
