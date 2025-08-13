"""
Service pour la gestion des grilles d'évaluation et cotations
"""
from typing import List, Dict, Any, Optional, Tuple
from app.models import db
from app.models.cotation import GrilleEvaluation, CotationSeance
try:  # Accès utilisateur courant pour scoping propriétaire
    from flask_login import current_user  # type: ignore
except Exception:  # pragma: no cover - fallback analyse statique
    class _U:  # type: ignore
        id = 0
    current_user = _U()  # type: ignore
import json

class CotationService:
    """Service pour toutes les opérations de cotation thérapeutique"""
    
    @staticmethod
    def get_grilles_predefinies() -> Dict[str, Dict[str, Any]]:
        """Retourne les grilles d'évaluation scientifiquement validées"""
        return {
            "amta_standard": {
                "nom": "AMTA - Grille Standard",
                "description": "Grille de l'Association Américaine de Musicothérapie (7 domaines, 28 indicateurs)",
                "reference_scientifique": "AMTA",
                "couleur_theme": "#e74c3c",  # Rouge professionnel
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
                        "couleur": "#e67e22",
                        "description": "Capacité à exprimer et réguler les émotions",
                        "indicateurs": [
                            {"nom": "Expression spontanée", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Régulation émotionnelle", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Reconnaissance émotions", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Empathie musicale", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "Communication",
                        "couleur": "#9b59b6",
                        "description": "Interaction verbale et non-verbale",
                        "indicateurs": [
                            {"nom": "Communication verbale", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Communication non-verbale", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Écoute active", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Turn-taking", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "Motricité",
                        "couleur": "#1abc9c",
                        "description": "Habiletés motrices fines et globales",
                        "indicateurs": [
                            {"nom": "Coordination fine", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Coordination globale", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Rythme corporel", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Contrôle gestuel", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "Cognition",
                        "couleur": "#f39c12",
                        "description": "Fonctions cognitives et apprentissage",
                        "indicateurs": [
                            {"nom": "Attention", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Mémoire", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Séquençage", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Résolution problèmes", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "Socialisation",
                        "couleur": "#e74c3c",
                        "description": "Interactions sociales et comportement de groupe",
                        "indicateurs": [
                            {"nom": "Interaction pairs", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Respect règles", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Collaboration", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Leadership", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "Estime de Soi",
                        "couleur": "#27ae60",
                        "description": "Confiance en soi et image de soi",
                        "indicateurs": [
                            {"nom": "Confiance en soi", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Prise de risques", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Fierté accomplissements", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Autonomie", "min": 0, "max": 5, "unite": "points"}
                        ]
                    }
                ]
            },
            "imcap_nd": {
                "nom": "IMCAP-ND - Troubles Autistiques",
                "description": "Échelle spécialisée pour troubles du spectre autistique (fiabilité 98%)",
                "reference_scientifique": "IMCAP-ND",
                "couleur_theme": "#8e44ad",
                "domaines": [
                    {
                        "nom": "Engagement Social",
                        "couleur": "#3498db",
                        "description": "Interaction et connection sociale",
                        "indicateurs": [
                            {"nom": "Regard dirigé", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Sourire social", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Imitation spontanée", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Jeu partagé", "min": 0, "max": 4, "unite": "niveau"}
                        ]
                    },
                    {
                        "nom": "Communication",
                        "couleur": "#e67e22",
                        "description": "Expression et compréhension communicative",
                        "indicateurs": [
                            {"nom": "Vocalises intentionnelles", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Gestes communicatifs", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Compréhension consignes", "min": 0, "max": 4, "unite": "niveau"}
                        ]
                    },
                    {
                        "nom": "Flexibilité",
                        "couleur": "#1abc9c",
                        "description": "Adaptation aux changements",
                        "indicateurs": [
                            {"nom": "Transition activités", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Nouveaux instruments", "min": 0, "max": 4, "unite": "niveau"},
                            {"nom": "Changement rythme", "min": 0, "max": 4, "unite": "niveau"}
                        ]
                    }
                ]
            },
            "mrs_receptive": {
                "nom": "MRS - Musicothérapie Réceptive",
                "description": "Optimisée pour écoute musicale et relaxation (r=0.91)",
                "reference_scientifique": "MRS",
                "couleur_theme": "#16a085",
                "domaines": [
                    {
                        "nom": "Réceptivité",
                        "couleur": "#3498db",
                        "description": "Capacité d'écoute et d'absorption musicale",
                        "indicateurs": [
                            {"nom": "Attention auditive", "min": 0, "max": 10, "unite": "minutes"},
                            {"nom": "Détente corporelle", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Réponse émotionnelle", "min": 0, "max": 5, "unite": "points"}
                        ]
                    },
                    {
                        "nom": "État de Conscience",
                        "couleur": "#9b59b6",
                        "description": "Niveau d'éveil et de présence",
                        "indicateurs": [
                            {"nom": "Vigilance", "min": 0, "max": 5, "unite": "points"},
                            {"nom": "Méditation musicale", "min": 0, "max": 5, "unite": "points"}
                        ]
                    }
                ]
            }
        }
    
    @staticmethod
    def creer_grille_predefinie(type_grille: str) -> Optional[GrilleEvaluation]:
        """Crée une grille prédéfinie en base de données"""
        grilles = CotationService.get_grilles_predefinies()
        
        if type_grille not in grilles:
            return None
        
        config = grilles[type_grille]
        grille = GrilleEvaluation(
            nom=config["nom"],
            description=config["description"],
            type_grille="standard",
            reference_scientifique=config["reference_scientifique"],
            domaines_config=json.dumps(config["domaines"]),
            active=True,
            publique=True
        )
        db.session.add(grille)
        db.session.commit()
        return grille

    # ------------------- Grilles personnalisées & gestion ------------------- #
    @staticmethod
    def creer_grille_personnalisee(nom: str, description: str, domaines: List[Dict[str, Any]]) -> GrilleEvaluation:
        """Crée une grille personnalisée pour l'utilisateur courant."""
        grille = GrilleEvaluation(
            nom=nom,
            description=description,
            type_grille="personnalisee",
            reference_scientifique=None,
            domaines_config=json.dumps(domaines),
            active=True,
            publique=False,
            musicotherapeute_id=current_user.id  # type: ignore[attr-defined]
        )
        db.session.add(grille)
        db.session.commit()
        return grille

    @staticmethod
    def copier_grille(grille_id: int) -> Optional[GrilleEvaluation]:
        """Copie une grille (publique ou appartenant à un autre utilisateur) dans l'espace courant."""
        origine = GrilleEvaluation.query.get(grille_id)
        if not origine:
            return None
        # Autorisé si publique ou déjà propriétaire
        if not origine.publique and origine.musicotherapeute_id != current_user.id:  # type: ignore[attr-defined]
            return None
        copie = GrilleEvaluation(
            nom=f"{origine.nom} (copie)",
            description=origine.description,
            type_grille=origine.type_grille,
            reference_scientifique=origine.reference_scientifique,
            domaines_config=origine.domaines_config,
            active=True,
            publique=False,
            musicotherapeute_id=current_user.id  # type: ignore[attr-defined]
        )
        db.session.add(copie)
        db.session.commit()
        return copie

    @staticmethod
    def editer_grille(grille_id: int, nom: Optional[str], description: Optional[str]) -> Optional[GrilleEvaluation]:
        """Modifie nom / description d'une grille appartenant à l'utilisateur."""
        grille = GrilleEvaluation.query.get(grille_id)
        if not grille:
            return None
        if grille.musicotherapeute_id != current_user.id:  # type: ignore[attr-defined]
            return None
        if nom:
            grille.nom = nom
        if description is not None:
            grille.description = description
        db.session.commit()
        return grille

    @staticmethod
    def supprimer_grille(grille_id: int) -> bool:
        """Désactive (soft delete) une grille appartenant à l'utilisateur."""
        grille = GrilleEvaluation.query.get(grille_id)
        if not grille:
            return False
        if grille.musicotherapeute_id != current_user.id:  # type: ignore[attr-defined]
            return False
        grille.active = False
        db.session.commit()
        return True

    @staticmethod
    def update_grille_domaines(grille_id: int, domaines: List[Dict[str, Any]]) -> Optional[GrilleEvaluation]:
        """Remplace la configuration des domaines d'une grille (avec vérification de propriété).

        Validation minimale: chaque domaine doit avoir nom, couleur, description, indicateurs (liste).
        """
        grille = GrilleEvaluation.query.get(grille_id)
        if not grille:
            return None
        if grille.musicotherapeute_id != current_user.id:  # type: ignore[attr-defined]
            return None
        # Nettoyage léger
        cleaned: List[Dict[str, Any]] = []
        for d in domaines:
            if not isinstance(d, dict):
                continue
            nom = str(d.get('nom', '')).strip()
            if not nom:
                continue
            indicateurs = d.get('indicateurs', []) or []
            indicateurs_clean = []
            for ind in indicateurs:
                if not isinstance(ind, dict):
                    continue
                nom_ind = str(ind.get('nom', '')).strip()
                if not nom_ind:
                    continue
                try:
                    min_v = float(ind.get('min', 0))
                    max_v = float(ind.get('max', 0))
                except Exception:
                    min_v, max_v = 0, 0
                unite = str(ind.get('unite', 'points'))
                indicateurs_clean.append({
                    'nom': nom_ind,
                    'min': min_v,
                    'max': max_v,
                    'unite': unite
                })
            cleaned.append({
                'nom': nom,
                'couleur': d.get('couleur', '#667eea'),
                'description': d.get('description', ''),
                'indicateurs': indicateurs_clean
            })
        grille.domaines = cleaned
        db.session.commit()
        return grille
    
    @staticmethod
    def calculer_score_global(scores_detailles: Dict[str, Any], grille: GrilleEvaluation) -> Tuple[float, float, float]:
        """
        Calcule le score global, maximum possible et pourcentage
        
        Returns:
            Tuple[float, float, float]: (score_obtenu, score_max, pourcentage)
        """
        score_total = 0.0
        score_max_total = 0.0
        
        domaines = grille.domaines
        
        for domaine in domaines:
            domaine_nom = domaine["nom"]
            if domaine_nom in scores_detailles:
                for indicateur in domaine["indicateurs"]:
                    indicateur_nom = indicateur["nom"]
                    cle_score = f"{domaine_nom}_{indicateur_nom}"
                    
                    if cle_score in scores_detailles:
                        score_total += float(scores_detailles[cle_score])
                    
                    score_max_total += float(indicateur["max"])
        
        pourcentage = (score_total / score_max_total * 100) if score_max_total > 0 else 0
        
        return score_total, score_max_total, pourcentage
    
    @staticmethod
    def creer_cotation(seance_id: int, grille_id: int, scores: Dict[str, Any], observations: str = "") -> CotationSeance:
        """Crée une nouvelle cotation pour une séance"""
        grille = GrilleEvaluation.query.get(grille_id)
        if not grille:
            raise ValueError("Grille d'évaluation introuvable")
        
        score_global, score_max, pourcentage = CotationService.calculer_score_global(scores, grille)
        
        cotation = CotationSeance(
            seance_id=seance_id,
            grille_id=grille_id,
            scores_detailles=json.dumps(scores),
            score_global=score_global,
            score_max_possible=score_max,
            pourcentage_reussite=pourcentage,
            observations_cotation=observations
        )
        
        db.session.add(cotation)
        db.session.commit()
        
        return cotation
    
    @staticmethod
    def get_evolution_patient(patient_id: int, grille_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """Récupère l'évolution des scores d'un patient"""
        from app.models import Seance
        
        cotations = db.session.query(CotationSeance, Seance).join(
            Seance, CotationSeance.seance_id == Seance.id
        ).filter(
            Seance.patient_id == patient_id,
            CotationSeance.grille_id == grille_id
        ).order_by(Seance.date_seance.desc()).limit(limit).all()
        
        evolution = []
        for cotation, seance in cotations:
            evolution.append({
                "date": seance.date_seance.isoformat(),
                "score_global": cotation.score_global,
                "pourcentage": cotation.pourcentage_reussite,
                "scores_detailles": cotation.scores
            })
        
        return evolution[::-1]  # Ordre chronologique
