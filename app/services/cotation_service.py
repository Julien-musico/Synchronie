"""Service pour la gestion des grilles d'évaluation et cotations (versioning)."""
from typing import List, Dict, Any, Optional, Tuple
import json
from app.models import db
from app.services.calcul_cotation_service import CalculCotationService
from app.models.cotation import GrilleEvaluation, CotationSeance, GrilleVersion

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
                    {"nom": "Engagement Musical", "couleur": "#3498db", "description": "Participation active aux activités musicales", "indicateurs": [
                        {"nom": "Attention soutenue", "min": 0, "max": 5, "unite": "points"},
                        {"nom": "Initiative musicale", "min": 0, "max": 5, "unite": "points"},
                        {"nom": "Persévérance", "min": 0, "max": 5, "unite": "points"},
                        {"nom": "Exploration sonore", "min": 0, "max": 5, "unite": "points"}
                    ]}
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
        g = GrilleEvaluation()
        g.nom = nom
        g.description = description
        g.type_grille = "personnalisee"
        g.reference_scientifique = None
        g.domaines_config = json.dumps(domaines)
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
        cleaned: List[Dict[str, Any]] = []
        for dom in domaines:
            if not isinstance(dom, dict):
                continue
            nom = str(dom.get('nom', '')).strip()
            if not nom:
                continue
            indicateurs_clean = []
            for ind in dom.get('indicateurs', []) or []:
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
                indicateurs_clean.append({
                    'nom': nom_ind,
                    'min': min_v,
                    'max': max_v,
                    'unite': str(ind.get('unite', 'points'))
                })
            cleaned.append({
                'nom': nom,
                'couleur': dom.get('couleur', '#667eea'),
                'description': dom.get('description', ''),
                'indicateurs': indicateurs_clean
            })
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
        score, max_score, pct = CotationService.calculer_score_global(scores, g)
        v = GrilleVersion.query.filter_by(grille_id=grille_id, active=True).order_by(GrilleVersion.version_num.desc()).first()
        cot = CotationSeance()
        cot.seance_id = seance_id
        cot.grille_id = grille_id
        cot.grille_version_id = v.id if v else None
        cot.scores_detailles = json.dumps(scores)
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
