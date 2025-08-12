from app import db
from datetime import datetime
import enum

class RapportType(enum.Enum):
    """Types de rapports"""
    PERIODIC = "periodic"      # Rapport périodique automatique
    INITIAL = "initial"        # Bilan initial
    FINAL = "final"           # Bilan final
    INTERIM = "interim"       # Rapport intermédiaire sur demande
    INCIDENT = "incident"     # Rapport d'incident

class RapportStatus(enum.Enum):
    """Statut du rapport"""
    DRAFT = "draft"           # Brouillon
    GENERATED = "generated"   # Généré automatiquement
    REVIEWED = "reviewed"     # Relu par le thérapeute
    VALIDATED = "validated"   # Validé et diffusé
    ARCHIVED = "archived"     # Archivé

class Rapport(db.Model):
    """Modèle de rapport thérapeutique"""
    __tablename__ = 'rapports'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations de base
    title = db.Column(db.String(200), nullable=False)
    rapport_type = db.Column(db.Enum(RapportType), nullable=False)
    status = db.Column(db.Enum(RapportStatus), nullable=False, default=RapportStatus.DRAFT)
    
    # Période couverte
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Contenu du rapport
    executive_summary = db.Column(db.Text)  # Synthèse exécutive
    detailed_analysis = db.Column(db.Text)  # Analyse détaillée
    progress_assessment = db.Column(db.Text)  # Évaluation des progrès
    recommendations = db.Column(db.Text)  # Recommandations
    
    # Données quantitatives
    sessions_count = db.Column(db.Integer)  # Nombre de séances
    attendance_rate = db.Column(db.Float)  # Taux de présence
    average_scores = db.Column(db.JSON)  # Scores moyens par domaine
    score_evolution = db.Column(db.JSON)  # Évolution des scores
    
    # Contenu généré par IA
    ai_insights = db.Column(db.Text)  # Insights générés par l'IA
    key_observations = db.Column(db.JSON)  # Observations clés (liste)
    suggested_objectives = db.Column(db.JSON)  # Objectifs suggérés
    
    # Personnalisation
    therapist_notes = db.Column(db.Text)  # Notes ajoutées par le thérapeute
    custom_sections = db.Column(db.JSON)  # Sections personnalisées
    
    # Diffusion
    recipients = db.Column(db.JSON)  # Liste des destinataires
    sent_at = db.Column(db.DateTime)  # Date d'envoi
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    generated_by_ai = db.Column(db.Boolean, default=False)
    
    # Relations
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    def get_period_duration_weeks(self):
        """Retourne la durée de la période en semaines"""
        delta = self.period_end - self.period_start
        return delta.days / 7
    
    def get_sessions_in_period(self):
        """Retourne les séances de la période"""
        from app.models.session import Session
        return Session.query.filter(
            Session.patient_id == self.patient_id,
            Session.date >= self.period_start,
            Session.date <= self.period_end
        ).order_by(Session.date).all()
    
    def calculate_attendance_rate(self):
        """Calcule le taux de présence"""
        sessions = self.get_sessions_in_period()
        if not sessions:
            return 0.0
        
        completed_sessions = [s for s in sessions if s.status.value == 'completed']
        return len(completed_sessions) / len(sessions) * 100
    
    def generate_automatic_content(self):
        """Génère le contenu automatique du rapport"""
        sessions = self.get_sessions_in_period()
        
        # Mise à jour des statistiques de base
        self.sessions_count = len(sessions)
        self.attendance_rate = self.calculate_attendance_rate()
        
        # Génération du titre si pas défini
        if not self.title:
            self.title = f"Rapport {self.rapport_type.value} - {self.patient.get_full_name()} - {self.period_end.strftime('%m/%Y')}"
    
    def is_editable(self):
        """Vérifie si le rapport peut être modifié"""
        return self.status in [RapportStatus.DRAFT, RapportStatus.GENERATED]
    
    def can_be_sent(self):
        """Vérifie si le rapport peut être envoyé"""
        return self.status in [RapportStatus.REVIEWED, RapportStatus.VALIDATED] and self.recipients
    
    def mark_as_reviewed(self, therapist_notes=None):
        """Marque le rapport comme relu"""
        self.status = RapportStatus.REVIEWED
        if therapist_notes:
            self.therapist_notes = therapist_notes
        self.updated_at = datetime.utcnow()
    
    def mark_as_validated(self):
        """Marque le rapport comme validé"""
        self.status = RapportStatus.VALIDATED
        self.updated_at = datetime.utcnow()
    
    def mark_as_sent(self):
        """Marque le rapport comme envoyé"""
        self.sent_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def get_next_report_due_date(self, interval_weeks=6):
        """Calcule la date du prochain rapport"""
        from datetime import timedelta
        return self.period_end + timedelta(weeks=interval_weeks)
    
    def __repr__(self):
        return f'<Rapport {self.title}>'
