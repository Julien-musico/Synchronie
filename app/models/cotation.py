"""Modèles pour le système de cotation thérapeutique."""
import json
from datetime import datetime, timezone
from typing import Any, Dict

from . import TimestampMixin, db

# Nouveau modèle pour la table 'grille'
class Grille(db.Model):
    __tablename__ = 'grille'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type_grille = db.Column(db.String(50), nullable=False)  # 'standardisée', 'personnalisée'
    reference_scientifique = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    user = db.relationship('User', backref='grilles_new')

    def __repr__(self):
        return f'<Grille {self.nom}>'

    @property
    def domaines(self):
        domaines = Domaine.query.join(GrilleDomaine, Domaine.id == GrilleDomaine.domaine_id)
        domaines = domaines.filter(GrilleDomaine.grille_id == self.id).all() or []
        result = []
        for domaine in domaines:
            indicateurs = Indicateur.query.join(DomaineIndicateur, Indicateur.id == DomaineIndicateur.indicateur_id)
            indicateurs = indicateurs.filter(DomaineIndicateur.domaine_id == domaine.id).all() or []
            indicateurs_list = [
                {
                    'id': indicateur.id,
                    'nom': indicateur.nom,
                    'description': indicateur.description,
                    'echelle_min': indicateur.echelle_min,
                    'echelle_max': indicateur.echelle_max,
                    'unite': indicateur.unite,
                    'poids': indicateur.poids
                }
                for indicateur in indicateurs
            ]
            result.append({
                'id': domaine.id,
                'nom': domaine.nom,
                'description': domaine.description,
                'couleur': domaine.couleur,
                'poids': domaine.poids,
                'indicateurs': indicateurs_list
            })
        return result


# Table de liaison grille <-> domaine
class GrilleDomaine(db.Model):
    __tablename__ = 'grille_domaine'
    id = db.Column(db.Integer, primary_key=True)
    grille_id = db.Column(db.Integer, db.ForeignKey('grille.id'), nullable=False)
    domaine_id = db.Column(db.Integer, db.ForeignKey('domaine.id'), nullable=False)

# Table de liaison domaine <-> indicateur
class DomaineIndicateur(db.Model):
    __tablename__ = 'domaine_indicateur'
    id = db.Column(db.Integer, primary_key=True)
    domaine_id = db.Column(db.Integer, db.ForeignKey('domaine.id'), nullable=False)
    indicateur_id = db.Column(db.Integer, db.ForeignKey('indicateur.id'), nullable=False)

# Modèles de base Domaine et Indicateur
class Domaine(db.Model):
    __tablename__ = 'domaine'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    couleur = db.Column(db.String(20))
    poids = db.Column(db.Float)

class Indicateur(db.Model):
    __tablename__ = 'indicateur'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    echelle_min = db.Column(db.Float)
    echelle_max = db.Column(db.Float)
    unite = db.Column(db.String(20))
    poids = db.Column(db.Float)


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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)  # Propriétaire de la grille
    user = db.relationship('User', backref='grilles')
    
    # Configuration JSON de la grille
    domaines_config = db.Column(db.Text, nullable=False)  # JSON des domaines et indicateurs
    
    # Statut
    active = db.Column(db.Boolean, default=True)
    
    # Relations
    cotations = db.relationship('CotationSeance', backref='grille', lazy=True)
    versions = db.relationship('GrilleVersion', backref='grille', lazy=True, order_by='GrilleVersion.version_num')  # type: ignore
    
    def __repr__(self):
        return f'<GrilleEvaluation {self.nom}>'
    
    @property
    def domaines(self):
        """Retourne les domaines liés à la grille, avec indicateurs, sous forme de dicts sérialisables."""
        domaines = Domaine.query.join(GrilleDomaine, Domaine.id == GrilleDomaine.domaine_id)
        domaines = domaines.filter(GrilleDomaine.grille_id == self.id).all() or []
        result = []
        for domaine in domaines:
            indicateurs = Indicateur.query.join(DomaineIndicateur, Indicateur.id == DomaineIndicateur.indicateur_id)
            indicateurs = indicateurs.filter(DomaineIndicateur.domaine_id == domaine.id).all() or []
            indicateurs_list = [
                {
                    'id': indicateur.id if indicateur.id is not None else '',
                    'nom': indicateur.nom if indicateur.nom is not None else '',
                    'description': indicateur.description if indicateur.description is not None else '',
                    'echelle_min': indicateur.echelle_min if indicateur.echelle_min is not None else 0,
                    'echelle_max': indicateur.echelle_max if indicateur.echelle_max is not None else 0,
                    'unite': indicateur.unite if indicateur.unite is not None else '',
                    'poids': indicateur.poids if indicateur.poids is not None else 0
                }
                for indicateur in indicateurs
            ]
            result.append({
                'id': domaine.id if domaine.id is not None else '',
                'nom': domaine.nom if domaine.nom is not None else '',
                'description': domaine.description if domaine.description is not None else '',
                'couleur': domaine.couleur if domaine.couleur is not None else '',
                'poids': domaine.poids if domaine.poids is not None else 0,
                'indicateurs': indicateurs_list
            })
        return result

    # ...existing code...

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


class PatientGrille(TimestampMixin, db.Model):
    """Association entre un patient et ses grilles de cotation assignées."""
    __tablename__ = 'patient_grille'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    grille_id = db.Column(db.Integer, db.ForeignKey('grille_evaluation.id'), nullable=False)
    
    # Configuration spécifique au patient
    priorite = db.Column(db.Integer, default=1)  # Ordre d'importance pour ce patient
    active = db.Column(db.Boolean, default=True)
    
    # Métadonnées
    assignee_par = db.Column(db.Integer)  # ID du thérapeute qui a assigné
    date_assignation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    date_fin = db.Column(db.DateTime)  # Date de fin d'utilisation
    
    # Commentaires d'assignation
    commentaires = db.Column(db.Text)
    
    # Contrainte d'unicité
    __table_args__ = (db.UniqueConstraint('patient_id', 'grille_id', name='_patient_grille_uc'),)
    
    # Relations
    patient = db.relationship('Patient', backref='grilles_assignees')
    grille = db.relationship('GrilleEvaluation', backref='patients_assignes')
    
    def __repr__(self):  # type: ignore
        return f'<PatientGrille patient_id={self.patient_id} grille_id={self.grille_id}>'
