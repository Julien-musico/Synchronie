from app import db
from datetime import datetime
import json
import enum

class GrilleType(enum.Enum):
    """Types de grilles d'évaluation"""
    STANDARD_AMTA = "standard_amta"
    IMCAP_ND = "imcap_nd"
    MRS = "mrs"
    ACTIVE_GRILLE = "active_grille"
    SIMPLIFIED = "simplified"
    CUSTOM = "custom"

class DomainType(enum.Enum):
    """Domaines thérapeutiques principaux"""
    COGNITIVE = "cognitive"
    EMOTIONAL = "emotional"
    SOCIAL = "social"
    PHYSICAL = "physical"
    COMMUNICATION = "communication"
    BEHAVIORAL = "behavioral"
    CREATIVE = "creative"

class Grille(db.Model):
    """Modèle de grille d'évaluation thérapeutique"""
    __tablename__ = 'grilles'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Informations de base
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    grille_type = db.Column(db.Enum(GrilleType), nullable=False)
    
    # Structure de la grille
    domains = db.Column(db.Text, nullable=False)  # JSON avec domaines et indicateurs
    scoring_scale = db.Column(db.JSON)  # Échelle de cotation (ex: 1-5, 0-10)
    weightings = db.Column(db.JSON)  # Pondérations des domaines
    
    # Configuration
    is_active = db.Column(db.Boolean, default=True)
    is_template = db.Column(db.Boolean, default=False)  # Template prédéfini ou custom
    target_population = db.Column(db.String(200))  # Population cible
    
    # Validation scientifique
    reliability_score = db.Column(db.Float)  # Score de fiabilité si connu
    validation_reference = db.Column(db.Text)  # Référence de validation
    
    # Métadonnées
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assignments = db.relationship('GrilleAssignment', backref='grille', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_domains_dict(self):
        """Retourne la structure des domaines"""
        if self.domains:
            return json.loads(self.domains)
        return {}
    
    def set_domains_dict(self, domains_dict):
        """Définit la structure des domaines"""
        self.domains = json.dumps(domains_dict)
    
    def get_domain_names(self):
        """Retourne la liste des noms de domaines"""
        domains = self.get_domains_dict()
        return list(domains.keys())
    
    def get_total_indicators(self):
        """Retourne le nombre total d'indicateurs"""
        domains = self.get_domains_dict()
        total = 0
        for domain_data in domains.values():
            total += len(domain_data.get('indicators', []))
        return total
    
    def calculate_weighted_score(self, ratings_dict):
        """Calcule le score pondéré à partir des cotations"""
        if not ratings_dict or not self.weightings:
            return None
        
        total_score = 0
        total_weight = 0
        
        for domain, weight in self.weightings.items():
            if domain in ratings_dict:
                domain_scores = ratings_dict[domain]
                if domain_scores:
                    avg_domain_score = sum(domain_scores.values()) / len(domain_scores)
                    total_score += avg_domain_score * weight
                    total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else None
    
    def get_template_data(self):
        """Retourne les données du template pour une grille prédéfinie"""
        templates = {
            GrilleType.STANDARD_AMTA: {
                "name": "Grille Standard AMTA",
                "description": "Grille complète de l'Association Américaine de Musicothérapie",
                "domains": {
                    "cognitive": {
                        "name": "Fonctions cognitives",
                        "indicators": ["attention", "mémoire", "orientation", "fonctions_exécutives"]
                    },
                    "emotional": {
                        "name": "Régulation émotionnelle", 
                        "indicators": ["expression_émotions", "gestion_stress", "estime_soi", "motivation"]
                    },
                    "social": {
                        "name": "Interactions sociales",
                        "indicators": ["communication", "coopération", "empathie", "respect_règles"]
                    },
                    "physical": {
                        "name": "Fonctions motrices",
                        "indicators": ["motricité_fine", "motricité_globale", "coordination", "tonus"]
                    }
                },
                "scoring_scale": {"min": 1, "max": 5, "labels": ["Très faible", "Faible", "Moyen", "Bon", "Excellent"]},
                "weightings": {"cognitive": 0.3, "emotional": 0.3, "social": 0.25, "physical": 0.15}
            },
            GrilleType.SIMPLIFIED: {
                "name": "Grille Simplifiée",
                "description": "Évaluation rapide en 3 domaines essentiels",
                "domains": {
                    "engagement": {
                        "name": "Engagement musical",
                        "indicators": ["participation", "intérêt", "initiative"]
                    },
                    "expression": {
                        "name": "Expression créative",
                        "indicators": ["créativité", "expression_émotions", "communication"]
                    },
                    "bien_être": {
                        "name": "Bien-être général",
                        "indicators": ["relaxation", "plaisir", "confiance"]
                    }
                },
                "scoring_scale": {"min": 1, "max": 3, "labels": ["Faible", "Moyen", "Élevé"]},
                "weightings": {"engagement": 0.4, "expression": 0.35, "bien_être": 0.25}
            }
        }
        return templates.get(self.grille_type)
    
    def __repr__(self):
        return f'<Grille {self.name}>'

class GrilleAssignment(db.Model):
    """Association entre un patient et une grille d'évaluation"""
    __tablename__ = 'grille_assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Relations
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    grille_id = db.Column(db.Integer, db.ForeignKey('grilles.id'), nullable=False)
    
    # Configuration personnalisée
    custom_objectives = db.Column(db.Text)  # Objectifs spécifiques pour ce patient
    custom_weightings = db.Column(db.JSON)  # Pondérations personnalisées
    
    # Statut
    is_active = db.Column(db.Boolean, default=True)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_effective_weightings(self):
        """Retourne les pondérations effectives (personnalisées ou par défaut)"""
        return self.custom_weightings or self.grille.weightings
    
    def __repr__(self):
        return f'<GrilleAssignment Patient:{self.patient_id} Grille:{self.grille_id}>'
