"""Modèles pour le système de cotation thérapeutique."""
import json
from typing import Any, Dict, List
from . import db, TimestampMixin

class GrilleEvaluation(TimestampMixin, db.Model):
    """Grilles d'évaluation thérapeutique (prédéfinies ou personnalisées).

    NOTE: Nom de table aligné sur le script SQL déployé (grille_evaluation).
    """
    __tablename__ = 'grille_evaluation'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type_grille = db.Column(db.String(50), nullable=False)  # 'standard', 'personnalisee'
    reference_scientifique = db.Column(db.String(100))  # Ex: 'AMTA', 'IMCAP-ND'
    musicotherapeute_id = db.Column(db.Integer, nullable=True, index=True)  # Propriétaire de la grille
    
    # Configuration JSON de la grille
    domaines_config = db.Column(db.Text, nullable=False)  # JSON des domaines et indicateurs
    
    # Statut
    active = db.Column(db.Boolean, default=True)
    publique = db.Column(db.Boolean, default=False)  # Partageable entre thérapeutes
    
    # Relations
    cotations = db.relationship('CotationSeance', backref='grille', lazy=True)
    versions = db.relationship('GrilleVersion', backref='grille', lazy=True, order_by='GrilleVersion.version_num')  # type: ignore
    
    def __repr__(self):
        return f'<GrilleEvaluation {self.nom}>'
    
    @property
    def domaines(self):
        """Retourne les domaines de la grille décodés depuis JSON"""
        try:
            return json.loads(self.domaines_config)  # type: ignore
        except Exception:
            return []
    
    @domaines.setter
    def domaines(self, value: List[Dict[str, Any]]) -> None:  # liste de domaines
        """Encode les domaines en JSON"""
        self.domaines_config = json.dumps(value)

class CotationSeance(TimestampMixin, db.Model):
    """Cotation d'une séance selon une grille d'évaluation.

    NOTE: Nom de table aligné sur le script SQL déployé (cotation_seance).
    """
    __tablename__ = 'cotation_seance'
    
    id = db.Column(db.Integer, primary_key=True)
    seance_id = db.Column(db.Integer, db.ForeignKey('seances.id'), nullable=False)
    grille_id = db.Column(db.Integer, db.ForeignKey('grille_evaluation.id'), nullable=False)
    
    # Scores par domaine (JSON)
    scores_detailles = db.Column(db.Text, nullable=False)  # JSON des scores par indicateur
    
    # Score global calculé
    score_global = db.Column(db.Float)
    score_max_possible = db.Column(db.Float)
    pourcentage_reussite = db.Column(db.Float)
    
    # Observations
    observations_cotation = db.Column(db.Text)
    
    def __repr__(self):
        return f'<CotationSeance seance_id={self.seance_id} score={self.score_global}>'
    
    @property
    def scores(self):
        """Retourne les scores décodés depuis JSON"""
        try:
            return json.loads(self.scores_detailles)  # type: ignore
        except Exception:
            return {}
    
    @scores.setter
    def scores(self, value: Dict[str, Any]) -> None:  # mapping indicateur -> valeur
        """Encode les scores en JSON"""
        self.scores_detailles = json.dumps(value)

class ObjectifTherapeutique(TimestampMixin, db.Model):
    """Objectifs thérapeutiques personnalisés par patient.

    NOTE: Nom de table aligné sur le script SQL déployé (objectif_therapeutique).
    """
    __tablename__ = 'objectif_therapeutique'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    grille_id = db.Column(db.Integer, db.ForeignKey('grille_evaluation.id'), nullable=False)
    
    # Configuration des objectifs
    domaine_cible = db.Column(db.String(100), nullable=False)
    indicateur_cible = db.Column(db.String(100), nullable=False)
    score_initial = db.Column(db.Float)
    score_cible = db.Column(db.Float, nullable=False)
    echeance = db.Column(db.Date)
    
    # Statut
    atteint = db.Column(db.Boolean, default=False)
    actif = db.Column(db.Boolean, default=True)
    
    # Description
    description = db.Column(db.Text)
    
    def __repr__(self):
        return f'<ObjectifTherapeutique patient_id={self.patient_id} domaine={self.domaine_cible}>'


class GrilleVersion(TimestampMixin, db.Model):
    """Version historisée d'une grille d'évaluation.

    Permet de conserver l'état des domaines/indicateurs utilisé lors des cotations.
    """
    __tablename__ = 'grille_version'

    id = db.Column(db.Integer, primary_key=True)
    grille_id = db.Column(db.Integer, db.ForeignKey('grille_evaluation.id'), nullable=False, index=True)
    version_num = db.Column(db.Integer, nullable=False)
    domaines_config = db.Column(db.Text, nullable=False)
    active = db.Column(db.Boolean, default=True, nullable=False)
    # NOTE: La relation vers CotationSeance a été retirée car il n'existe plus
    # de clé étrangère grille_version_id dans la table cotation_seance.
    # Ancienne ligne supprimée:
    # cotations = db.relationship('CotationSeance', backref='grille_version', lazy=True)

    def __repr__(self):  # type: ignore
        return f'<GrilleVersion grille_id={self.grille_id} v={self.version_num}>'
