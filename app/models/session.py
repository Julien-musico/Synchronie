from app import db
from datetime import datetime
import enum
import json

class SessionStatus(enum.Enum):
    """Statut de la séance"""
    SCHEDULED = "scheduled"  # Programmée
    COMPLETED = "completed"  # Terminée
    CANCELLED = "cancelled"  # Annulée
    NO_SHOW = "no_show"      # Patient absent

class SessionType(enum.Enum):
    """Type de séance"""
    INDIVIDUAL = "individual"    # Individuelle
    GROUP = "group"             # Groupe
    FAMILY = "family"           # Familiale
    ASSESSMENT = "assessment"   # Évaluation

class Session(db.Model):
    """Modèle de séance de musicothérapie"""
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations de base
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False, default=45)
    session_type = db.Column(db.Enum(SessionType), nullable=False, default=SessionType.INDIVIDUAL)
    status = db.Column(db.Enum(SessionStatus), nullable=False, default=SessionStatus.SCHEDULED)
    
    # Contenu de la séance
    objectives = db.Column(db.Text)  # Objectifs de la séance
    activities = db.Column(db.Text)  # Activités réalisées (JSON)
    observations = db.Column(db.Text)  # Observations du thérapeute
    patient_feedback = db.Column(db.Text)  # Retour du patient
    
    # Traitement audio et IA
    audio_file_path = db.Column(db.String(500))  # Chemin vers le fichier audio
    transcription = db.Column(db.Text)  # Transcription complète
    ai_summary = db.Column(db.Text)  # Synthèse générée par l'IA
    key_moments = db.Column(db.Text)  # Moments clés identifiés (JSON)
    
    # Statut du traitement
    audio_processed = db.Column(db.Boolean, default=False)
    transcription_completed = db.Column(db.Boolean, default=False)
    ai_analysis_completed = db.Column(db.Boolean, default=False)
    
    # Évaluation et cotation
    ratings = db.Column(db.Text)  # Cotations des grilles (JSON)
    global_assessment = db.Column(db.Text)  # Évaluation globale
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    therapist_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def get_activities_list(self):
        """Retourne la liste des activités"""
        if self.activities:
            return json.loads(self.activities)
        return []
    
    def set_activities_list(self, activities_list):
        """Définit la liste des activités"""
        self.activities = json.dumps(activities_list)
    
    def get_key_moments_list(self):
        """Retourne la liste des moments clés"""
        if self.key_moments:
            return json.loads(self.key_moments)
        return []
    
    def set_key_moments_list(self, moments_list):
        """Définit la liste des moments clés"""
        self.key_moments = json.dumps(moments_list)
    
    def get_ratings_dict(self):
        """Retourne les cotations sous forme de dictionnaire"""
        if self.ratings:
            return json.loads(self.ratings)
        return {}
    
    def set_ratings_dict(self, ratings_dict):
        """Définit les cotations"""
        self.ratings = json.dumps(ratings_dict)
    
    def get_duration_display(self):
        """Retourne la durée formatée"""
        hours = self.duration_minutes // 60
        minutes = self.duration_minutes % 60
        if hours > 0:
            return f"{hours}h{minutes:02d}"
        return f"{minutes} min"
    
    def is_ready_for_ai_processing(self):
        """Vérifie si la séance est prête pour le traitement IA"""
        return (self.status == SessionStatus.COMPLETED and 
                self.audio_file_path and 
                not self.ai_analysis_completed)
    
    def get_processing_status(self):
        """Retourne le statut du traitement"""
        if not self.audio_file_path:
            return "Aucun enregistrement"
        elif not self.transcription_completed:
            return "Transcription en cours..."
        elif not self.ai_analysis_completed:
            return "Analyse IA en cours..."
        else:
            return "Traitement terminé"
    
    def mark_audio_processed(self):
        """Marque l'audio comme traité"""
        self.audio_processed = True
        self.updated_at = datetime.utcnow()
    
    def mark_transcription_completed(self, transcription_text):
        """Marque la transcription comme terminée"""
        self.transcription = transcription_text
        self.transcription_completed = True
        self.updated_at = datetime.utcnow()
    
    def mark_ai_analysis_completed(self, summary, key_moments):
        """Marque l'analyse IA comme terminée"""
        self.ai_summary = summary
        self.set_key_moments_list(key_moments)
        self.ai_analysis_completed = True
        self.updated_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<Session {self.date} - {self.patient.get_full_name() if self.patient else "Unknown"}>'
