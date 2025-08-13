"""Service pour la gestion des grilles d'évaluation et cotations (versioning)."""
import json
from typing import Any, Dict, List, Optional, Tuple

from app.models import db
from app.models.cotation import CotationSeance, GrilleEvaluation, GrilleVersion
from app.services.calcul_cotation_service import CalculCotationService
from app.services.validation_service import CotationValidator, ValidationError

try:
    from flask_login import current_user  # type: ignore
except Exception:  # pragma: no cover
    class _U:  # type: ignore
        id = 0
    current_user = _U()  # type: ignore


class CotationService:
    # ------------------- Données prédéfinies ------------------- #
    @staticmethod
    def get_grilles_predefinies() -> Dict[str, Dict[str, Any]]:
        return {
            "amta_standard": {
                "nom": "AMTA - Grille Standard",
                "description": "Grille de l'Association Américaine de Musicothérapie (7 domaines, 28 indicateurs)",
                "reference_scientifique": "AMTA",
                "domaines": [
                    {
                        "nom": "Engagement Musical", 
                        "couleur": "#3498db", 
                        "description": "Participation active aux activités musicales", 
                        "indicateurs": [
                            {"nom": "Attention soutenue", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Initiative musicale", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Persévérance", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Exploration sonore", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "Expression Émotionnelle",
                        "couleur": "#e74c3c",
                        "description": "Capacité d'expression des émotions par la musique",
                        "indicateurs": [
                            {"nom": "Expression spontanée", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Reconnaissance émotionnelle", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Régulation émotionnelle", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Empathie musicale", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "Communication",
                        "couleur": "#2ecc71",
                        "description": "Compétences de communication verbale et non-verbale",
                        "indicateurs": [
                            {"nom": "Expression verbale", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Écoute active", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Communication non-verbale", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Tour de parole", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "Motricité",
                        "couleur": "#f39c12",
                        "description": "Compétences motrices globales et fines",
                        "indicateurs": [
                            {"nom": "Coordination globale", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Motricité fine", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Rythme corporel", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Équilibre postural", "min": 0, "max": 5, "unite": "points"}
                        ]
                    }
                ]
            },
            "imcap_nd": {
                "nom": "IMCAP-ND - Autisme",
                "description": "Individual Music-Centered Assessment Profile for Neurodevelopmental Disorders (spécialisée troubles autistiques)",
                "reference_scientifique": "IMCAP-ND",
                "domaines": [
                    {
                        "nom": "Attention et Engagement",
                        "couleur": "#9b59b6",
                        "description": "Capacité d'attention et d'engagement dans l'activité musicale",
                        "indicateurs": [
                            {"nom": "Attention visuelle", "min": 0, "max": 3, "unite": "niveau"},
                            {"nom": "Attention auditive", "min": 0, "max": 3, "unite": "niveau"},
                            {"nom": "Durée d'engagement", "min": 0, "max": 3, "unite": "niveau"},
                            {"nom": "Qualité de l'engagement", "min": 0, "max": 3, "unite": "niveau"}
                        ]
                    },
                    {
                        "nom": "Interaction Sociale",
                        "couleur": "#1abc9c",
                        "description": "Compétences d'interaction et de communication sociale",
                        "indicateurs": [
                            {"nom": "Contact oculaire", "min": 0, "max": 3, "unite": "niveau"},
                            {"nom": "Imitation", "min": 0, "max": 3, "unite": "niveau"},
                            {"nom": "Tour de rôle", "min": 0, "max": 3, "unite": "niveau"},
                            {"nom": "Initiation sociale", "min": 0, "max": 3, "unite": "niveau"}
                        ]
                    },
                    {
                        "nom": "Flexibilité Cognitive",
                        "couleur": "#34495e",
                        "description": "Adaptation aux changements et flexibilité comportementale",
                        "indicateurs": [
                            {"nom": "Adaptation au changement", "min": 0, "max": 3, "unite": "niveau"},
                            {"nom": "Tolérance à l'imprévu", "min": 0, "max": 3, "unite": "niveau"},
                            {"nom": "Créativité musicale", "min": 0, "max": 3, "unite": "niveau"}
                        ]
                    }
                ]
            },
            "geriatrie_simple": {
                "nom": "Gériatrie - Évaluation Simplifiée",
                "description": "Grille adaptée pour l'évaluation en gérontologie et troubles cognitifs",
                "reference_scientifique": "Adapté MMSE/NPI",
                "domaines": [
                    {
                        "nom": "Cognition",
                        "couleur": "#8e44ad",
                        "description": "Fonctions cognitives et mémoire",
                        "indicateurs": [
                            {"nom": "Reconnaissance mélodique", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Mémoire des paroles", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Attention soutenue", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Orientation temporelle", "min": 0, "max": 4, "unite": "niveau"}
                        ]
                    },
                    {
                        "nom": "Humeur et Bien-être",
                        "couleur": "#e67e22",
                        "description": "État émotionnel et bien-être psychologique",
                        "indicateurs": [
                            {"nom": "Plaisir musical", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Apaisement", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Sourires/rires", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Diminution agitation", "min": 0, "max": 4, "unite": "niveau"}
                        ]
                    },
                    {
                        "nom": "Interaction Sociale",
                        "couleur": "#27ae60",
                        "description": "Relations sociales et communication",
                        "indicateurs": [
                            {"nom": "Échanges verbaux", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Partage musical", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Reconnexion relationnelle", "min": 0, "max": 4, "unite": "niveau"}
                        ]
                    }
                ]
            },
            "pediatrie_globale": {
                "nom": "Pédiatrie - Développement Global",
                "description": "Grille complète pour l'évaluation du développement chez l'enfant",
                "reference_scientifique": "Adapté Bayley/ADOS",
                "domaines": [
                    {
                        "nom": "Développement Moteur",
                        "couleur": "#d35400",
                        "description": "Motricité globale et fine adaptée à l'âge",
                        "indicateurs": [
                            {"nom": "Coordination bi-manuelle", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Rythme et mouvement", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Précision gestuelle", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Tonus postural", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "Langage et Communication",
                        "couleur": "#c0392b",
                        "description": "Développement du langage et des compétences communicatives",
                        "indicateurs": [
                            {"nom": "Vocalises musicales", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Compréhension verbale", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Expression spontanée", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Pragmatique", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "Socio-affectif",
                        "couleur": "#16a085",
                        "description": "Compétences sociales et régulation émotionnelle",
                        "indicateurs": [
                            {"nom": "Attachement thérapeute", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Jeu partagé", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Autorégulation", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Empathie", "min": 0, "max": 5, "unite": "points"}
                        ]
                    }
                ]
            },
            "evaluation_rapide": {
                "nom": "Évaluation Rapide - 3 Domaines",
                "description": "Grille simplifiée pour évaluation rapide en séance (3 domaines essentiels)",
                "reference_scientifique": "Synthèse clinique",
                "domaines": [
                    {
                        "nom": "Engagement",
                        "couleur": "#3498db",
                        "description": "Niveau de participation et d'implication",
                        "indicateurs": [
                            {"nom": "Participation active", "min": 0, "max": 10, "unite": "sur 10"},
                            {"nom": "Initiative", "min": 0, "max": 10, "unite": "sur 10"},
                            {"nom": "Concentration", "min": 0, "max": 10, "unite": "sur 10"}
                        ]
                    },
                    {
                        "nom": "Expression",
                        "couleur": "#e74c3c",
                        "description": "Capacité d'expression personnelle",
                        "indicateurs": [
                            {"nom": "Expression émotionnelle", "min": 0, "max": 10, "unite": "sur 10"},
                            {"nom": "Créativité", "min": 0, "max": 10, "unite": "sur 10"},
                            {"nom": "Spontanéité", "min": 0, "max": 10, "unite": "sur 10"}
                        ]
                    },
                    {
                        "nom": "Interaction",
                        "couleur": "#2ecc71",
                        "description": "Qualité des interactions sociales",
                        "indicateurs": [
                            {"nom": "Communication", "min": 0, "max": 10, "unite": "sur 10"},
                            {"nom": "Coopération", "min": 0, "max": 10, "unite": "sur 10"},
                            {"nom": "Écoute d'autrui", "min": 0, "max": 10, "unite": "sur 10"}
                        ]
                    }
                ]
            }
        }

    # ------------------- Création ------------------- #
    @staticmethod
    def creer_grille_predefinie(type_grille: str) -> Optional[GrilleEvaluation]:
        grilles = CotationService.get_grilles_predefinies()
        if type_grille not in grilles:
            return None
        cfg = grilles[type_grille]
        g = GrilleEvaluation()
        g.nom = cfg["nom"]
        g.description = cfg["description"]
        g.type_grille = "standard"
        g.reference_scientifique = cfg["reference_scientifique"]
        g.domaines_config = json.dumps(cfg["domaines"])
        g.active = True
        g.publique = True
        db.session.add(g)
        db.session.commit()
        CotationService._ensure_initial_version(g)
        return g

    @staticmethod
    def creer_grille_personnalisee(nom: str, description: str, domaines: List[Dict[str, Any]]) -> GrilleEvaluation:
        # Validation du nom
        nom = nom.strip()
        if not nom or len(nom) < 3:
            raise ValueError("Nom de grille requis (min 3 caractères)")
        if len(nom) > 100:
            raise ValueError("Nom trop long (max 100 caractères)")
        
        # Validation des domaines
        try:
            domaines_valides = CotationValidator.valider_grille_complete(domaines) if domaines else []
        except ValidationError as e:
            raise ValueError(f"Domaines invalides: {e}") from e
        
        g = GrilleEvaluation()
        g.nom = nom
        g.description = description.strip()[:500]
        g.type_grille = "personnalisee"
        g.reference_scientifique = None
        g.domaines_config = json.dumps(domaines_valides)
        g.active = True
        g.publique = False
        g.musicotherapeute_id = current_user.id  # type: ignore[attr-defined]
        db.session.add(g)
        db.session.commit()
        CotationService._ensure_initial_version(g)
        return g

    @staticmethod
    def copier_grille(grille_id: int) -> Optional[GrilleEvaluation]:
        src = GrilleEvaluation.query.get(grille_id)
        if not src:
            return None
        if not src.publique and src.musicotherapeute_id != current_user.id:  # type: ignore[attr-defined]
            return None
        g = GrilleEvaluation()
        g.nom = f"{src.nom} (copie)"
        g.description = src.description
        g.type_grille = src.type_grille
        g.reference_scientifique = src.reference_scientifique
        g.domaines_config = src.domaines_config
        g.active = True
        g.publique = False
        g.musicotherapeute_id = current_user.id  # type: ignore[attr-defined]
        db.session.add(g)
        db.session.commit()
        CotationService._ensure_initial_version(g)
        return g

    @staticmethod
    def _ensure_initial_version(grille: GrilleEvaluation) -> None:
        if GrilleVersion.query.filter_by(grille_id=grille.id).first():
            return
        v = GrilleVersion()
        v.grille_id = grille.id
        v.version_num = 1
        v.domaines_config = grille.domaines_config
        v.active = True
        db.session.add(v)
        db.session.commit()

    # ------------------- Edition / suppression ------------------- #
    @staticmethod
    def editer_grille(grille_id: int, nom: Optional[str], description: Optional[str]) -> Optional[GrilleEvaluation]:
        g = GrilleEvaluation.query.get(grille_id)
        if not g:
            return None
        if g.musicotherapeute_id != current_user.id:  # type: ignore[attr-defined]
            return None
        if nom:
            g.nom = nom
        if description is not None:
            g.description = description
        db.session.commit()
        return g

    @staticmethod
    def supprimer_grille(grille_id: int) -> bool:
        g = GrilleEvaluation.query.get(grille_id)
        if not g:
            return False
        if g.musicotherapeute_id != current_user.id:  # type: ignore[attr-defined]
            return False
        g.active = False
        db.session.commit()
        return True

    # ------------------- Mise à jour domaines (versioning) ------------------- #
    @staticmethod
    def update_grille_domaines(grille_id: int, domaines: List[Dict[str, Any]]) -> Optional[GrilleEvaluation]:
        g = GrilleEvaluation.query.get(grille_id)
        if not g:
            return None
        if g.musicotherapeute_id != current_user.id:  # type: ignore[attr-defined]
            return None
        
        # Validation stricte des domaines
        try:
            cleaned = CotationValidator.valider_grille_complete(domaines)
        except ValidationError as e:
            raise ValueError(f"Validation échouée: {e}") from e
        
        last_v = GrilleVersion.query.filter_by(grille_id=g.id).order_by(GrilleVersion.version_num.desc()).first()
        if last_v and last_v.active:
            last_v.active = False
        new_v = GrilleVersion()
        new_v.grille_id = g.id
        new_v.version_num = 1 if not last_v else last_v.version_num + 1
        new_v.domaines_config = json.dumps(cleaned)
        new_v.active = True
        g.domaines = cleaned
        db.session.add(new_v)
        db.session.commit()
        return g

    # ------------------- Calcul / Cotations ------------------- #
    @staticmethod
    def calculer_score_global(scores_detailles: Dict[str, Any], grille: GrilleEvaluation) -> Tuple[float, float, float]:
        return CalculCotationService.calculer_score_global(grille.domaines, scores_detailles)

    @staticmethod
    def creer_cotation(seance_id: int, grille_id: int, scores: Dict[str, Any], observations: str = "") -> CotationSeance:
        g = GrilleEvaluation.query.get(grille_id)
        if not g:
            raise ValueError("Grille d'évaluation introuvable")
        
        # Validation des scores
        try:
            scores_valides, erreurs = CotationValidator.valider_scores_cotation(scores, g.domaines)
            if erreurs:
                raise ValueError(f"Scores invalides: {', '.join(erreurs)}")
        except ValidationError as e:
            raise ValueError(f"Validation scores échouée: {e}") from e
        
        score, max_score, pct = CotationService.calculer_score_global(scores_valides, g)
        cot = CotationSeance()
        cot.seance_id = seance_id
        cot.grille_id = grille_id
        cot.scores_detailles = json.dumps(scores_valides)
        cot.score_global = score
        cot.score_max_possible = max_score
        cot.pourcentage_reussite = pct
        cot.observations_cotation = observations
        db.session.add(cot)
        db.session.commit()
        return cot

    @staticmethod
    def get_evolution_patient(patient_id: int, grille_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        from app.models import Seance
        rows = db.session.query(CotationSeance, Seance).join(
            Seance, CotationSeance.seance_id == Seance.id
        ).filter(
            Seance.patient_id == patient_id,
            CotationSeance.grille_id == grille_id
        ).order_by(Seance.date_seance.desc()).limit(limit).all()
        out: List[Dict[str, Any]] = []
        for cot, seance in rows:
            out.append({
                'date': seance.date_seance.isoformat(),
                'score_global': cot.score_global,
                'pourcentage': cot.pourcentage_reussite,
                'scores_detailles': cot.scores
            })
        return out[::-1]

    # ------------------- Gestion des grilles ------------------- #
    @staticmethod
    def get_grilles_standards() -> List[GrilleEvaluation]:
        """Récupère toutes les grilles standards (publiques)."""
        return GrilleEvaluation.query.filter_by(type_grille='standard', active=True, publique=True).all()

    @staticmethod
    def get_grilles_utilisateur() -> List[GrilleEvaluation]:
        """Récupère les grilles personnalisées de l'utilisateur courant."""
        try:
            user_id = current_user.id  # type: ignore[attr-defined]
            return GrilleEvaluation.query.filter_by(
                type_grille='personnalisee',
                musicotherapeute_id=user_id,
                active=True
            ).all()
        except Exception:
            return []

    @staticmethod
    def get_grille_by_id(grille_id: int) -> Optional[GrilleEvaluation]:
        """Récupère une grille par son ID avec vérification d'accès."""
        grille = GrilleEvaluation.query.get(grille_id)
        if not grille or not grille.active:
            return None
        
        # Vérification d'accès : grille publique ou appartenant à l'utilisateur
        if grille.publique:
            return grille
        
        try:
            user_id = current_user.id  # type: ignore[attr-defined]
            if grille.musicotherapeute_id == user_id:
                return grille
        except Exception:
            pass
        
        return None

    @staticmethod
    def update_grille_complete(grille_id: int, nom: Optional[str], description: Optional[str], 
                             domaines: Optional[List[Dict[str, Any]]]) -> Optional[GrilleEvaluation]:
        """Met à jour complètement une grille (nom, description, domaines)."""
        grille = GrilleEvaluation.query.get(grille_id)
        if not grille or not grille.active:
            return None
        
        # Vérification des droits d'édition
        try:
            user_id = current_user.id  # type: ignore[attr-defined]
            if grille.musicotherapeute_id != user_id:
                return None
        except Exception:
            return None
        
        # Mise à jour des métadonnées
        if nom:
            nom = nom.strip()
            if len(nom) < 3:
                raise ValueError("Nom de grille requis (min 3 caractères)")
            if len(nom) > 100:
                raise ValueError("Nom trop long (max 100 caractères)")
            grille.nom = nom
        
        if description is not None:
            grille.description = description.strip()[:500]
        
        # Mise à jour des domaines si fournis
        if domaines is not None:
            try:
                domaines_valides = CotationValidator.valider_grille_complete(domaines)
            except ValidationError as e:
                raise ValueError(f"Domaines invalides: {e}") from e
            
            # Créer une nouvelle version
            last_version = GrilleVersion.query.filter_by(
                grille_id=grille.id
            ).order_by(GrilleVersion.version_num.desc()).first()
            
            if last_version and last_version.active:
                last_version.active = False
            
            new_version = GrilleVersion()
            new_version.grille_id = grille.id
            new_version.version_num = 1 if not last_version else last_version.version_num + 1
            new_version.domaines_config = json.dumps(domaines_valides)
            new_version.active = True
            
            grille.domaines = domaines_valides
            db.session.add(new_version)
        
        db.session.commit()
        return grille

    @staticmethod
    def get_grilles_disponibles_pour_patient() -> Dict[str, List[Dict[str, Any]]]:
        """Récupère toutes les grilles disponibles pour l'assignation à un patient."""
        standards = CotationService.get_grilles_standards()
        personnalisees = CotationService.get_grilles_utilisateur()
        
        return {
            'standards': [
                {
                    'id': g.id,
                    'nom': g.nom,
                    'description': g.description,
                    'reference_scientifique': g.reference_scientifique,
                    'nb_domaines': len(g.domaines) if g.domaines else 0
                }
                for g in standards
            ],
            'personnalisees': [
                {
                    'id': g.id,
                    'nom': g.nom,
                    'description': g.description,
                    'nb_domaines': len(g.domaines) if g.domaines else 0
                }
                for g in personnalisees
            ]
        }

    @staticmethod
    def sauvegarder_cotation_seance(seance_id: int, grille_id: int, scores: Dict, 
                                   observations: str = "", musicotherapeute_id: Optional[int] = None) -> bool:
        """Sauvegarde une cotation de séance avec les scores détaillés."""
        try:
            # Vérifier si une cotation existe déjà pour cette séance et cette grille
            cotation_existante = CotationSeance.query.filter_by(
                seance_id=seance_id,
                grille_id=grille_id
            ).first()
            
            if cotation_existante:
                # Mettre à jour la cotation existante
                cotation = cotation_existante
            else:
                # Créer une nouvelle cotation
                cotation = CotationSeance(
                    seance_id=seance_id,
                    grille_id=grille_id
                )
                db.session.add(cotation)
            
            # Calculer les scores pondérés et le score global
            grille = GrilleEvaluation.query.get(grille_id)
            if not grille:
                return False
            
            # Sauvegarder les scores détaillés
            cotation.scores_detailles = json.dumps(scores)
            cotation.observations_cotation = observations
            
            # Calculer le score global
            score_global = CotationService._calculer_score_global(scores, grille)
            cotation.score_global = score_global
            
            # Marquer la séance comme cotée
            from app.models.patient import Seance
            seance = Seance.query.get(seance_id)
            if seance and hasattr(seance, 'est_cotee'):
                seance.est_cotee = True
            
            db.session.commit()
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"Erreur lors de la sauvegarde de la cotation: {e}")
            return False
    
    @staticmethod
    def _calculer_score_global(scores: Dict, grille: GrilleEvaluation) -> float:
        """Calcule le score global pondéré d'une cotation."""
        total_score = 0.0
        total_weight = 0.0
        
        for domaine in grille.domaines:
            domaine_id = str(domaine.id)
            if domaine_id in scores:
                domaine_scores = scores[domaine_id]
                domaine_total = 0.0
                domaine_weight = 0.0
                
                for indicateur in domaine.indicateurs:
                    indicateur_id = str(indicateur.id)
                    if indicateur_id in domaine_scores:
                        score_data = domaine_scores[indicateur_id]
                        value = score_data.get('value', 0)
                        poids = score_data.get('poids', 1.0)
                        
                        # Normaliser le score sur 100
                        max_value = indicateur.echelle_max or 5
                        normalized_value = (value / max_value) * 100
                        
                        domaine_total += normalized_value * poids
                        domaine_weight += poids
                
                if domaine_weight > 0:
                    domaine_average = domaine_total / domaine_weight
                    total_score += domaine_average * (domaine.poids or 1.0)
                    total_weight += (domaine.poids or 1.0)
        
        return total_score / total_weight if total_weight > 0 else 0.0
