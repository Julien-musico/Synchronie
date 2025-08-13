"""Service pur (stateless) pour le calcul des scores de cotation.

Permet de tester isolément la logique sans dépendre de Flask/SQLAlchemy.
"""
from __future__ import annotations
from typing import Dict, Any, Tuple, List
import json

class CalculCotationService:
    @staticmethod
    def extraire_domaines(domaines_config: Any) -> List[Dict[str, Any]]:
        """Accepte domaines déjà chargés (list[dict]) ou JSON str."""
        if isinstance(domaines_config, list):
            return domaines_config  # type: ignore
        if isinstance(domaines_config, str):
            try:
                return json.loads(domaines_config)  # type: ignore
            except Exception:
                return []
        return []

    @staticmethod
    def calculer_score_global(domaines_config: Any, scores_detailles: Dict[str, Any]) -> Tuple[float, float, float]:
        """Calcule score total, score max et pourcentage.

        Clé attendue dans scores_detailles: "<NomDomaine>_<NomIndicateur>"
        Les valeurs non numériques sont ignorées.
        """
        domaines = CalculCotationService.extraire_domaines(domaines_config)
        total = 0.0
        max_total = 0.0
        for domaine in domaines:
            d_nom = domaine.get('nom')
            for ind in domaine.get('indicateurs', []) or []:
                cle = f"{d_nom}_{ind.get('nom')}"
                # Valeur obtenue
                if cle in scores_detailles:
                    try:
                        total += float(scores_detailles[cle])
                    except Exception:
                        pass
                # Valeur maximale possible
                try:
                    max_total += float(ind.get('max', 0))
                except Exception:
                    pass
        pct = (total / max_total * 100) if max_total > 0 else 0.0
        return total, max_total, pct
