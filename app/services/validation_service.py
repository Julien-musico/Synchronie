"""Validation stricte pour les données de cotation et grilles d'évaluation."""
import re
from typing import Any, Dict, List, Tuple


class ValidationError(Exception):
    """Erreur de validation des données."""
    pass

class CotationValidator:
    """Validateur pour les données de cotation thérapeutique."""

    @staticmethod
    def valider_domaine(domaine: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et nettoie un domaine d'évaluation."""
        if not isinstance(domaine, dict):
            raise ValidationError("Domaine doit être un objet")
        
        nom = str(domaine.get('nom', '')).strip()
        if not nom or len(nom) < 2:
            raise ValidationError("Nom du domaine requis (min 2 caractères)")
        if len(nom) > 100:
            raise ValidationError("Nom du domaine trop long (max 100 caractères)")
        if not re.match(r'^[a-zA-ZÀ-ÿ0-9\s\-_]+$', nom):
            raise ValidationError("Nom du domaine contient des caractères invalides")

        couleur = domaine.get('couleur', '#667eea')
        if not re.match(r'^#[0-9a-fA-F]{6}$', couleur):
            couleur = '#667eea'

        description = str(domaine.get('description', '')).strip()[:500]  # Limiter à 500 chars

        indicateurs = domaine.get('indicateurs', [])
        if not isinstance(indicateurs, list) or len(indicateurs) == 0:
            raise ValidationError(f"Domaine '{nom}' doit avoir au moins 1 indicateur")
        
        indicateurs_valides = []
        for i, ind in enumerate(indicateurs):
            try:
                ind_valide = CotationValidator.valider_indicateur(ind)
                indicateurs_valides.append(ind_valide)
            except ValidationError as e:
                raise ValidationError(f"Domaine '{nom}', indicateur {i+1}: {e}") from e

        return {
            'nom': nom,
            'couleur': couleur,
            'description': description,
            'indicateurs': indicateurs_valides
        }

    @staticmethod
    def valider_indicateur(indicateur: Dict[str, Any]) -> Dict[str, Any]:
        """Valide et nettoie un indicateur."""
        if not isinstance(indicateur, dict):
            raise ValidationError("Indicateur doit être un objet")

        nom = str(indicateur.get('nom', '')).strip()
        if not nom or len(nom) < 2:
            raise ValidationError("Nom indicateur requis (min 2 caractères)")
        if len(nom) > 100:
            raise ValidationError("Nom indicateur trop long (max 100 caractères)")

        try:
            min_val = float(indicateur.get('min', 0))
            max_val = float(indicateur.get('max', 5))
        except (ValueError, TypeError) as err:
            raise ValidationError("Valeurs min/max doivent être numériques") from err

        if min_val >= max_val:
            raise ValidationError("Valeur max doit être supérieure à min")
        if min_val < 0 or max_val > 100:
            raise ValidationError("Valeurs min/max doivent être entre 0 et 100")

        unite = str(indicateur.get('unite', 'points')).strip()[:20]
        if not unite:
            unite = 'points'

        return {
            'nom': nom,
            'min': min_val,
            'max': max_val,
            'unite': unite
        }

    @staticmethod
    def valider_grille_complete(domaines: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Valide une grille complète (tous ses domaines)."""
        if not isinstance(domaines, list) or len(domaines) == 0:
            raise ValidationError("Grille doit contenir au moins 1 domaine")
        if len(domaines) > 20:
            raise ValidationError("Grille ne peut pas avoir plus de 20 domaines")

        domaines_valides = []
        noms_vus = set()
        
        for i, domaine in enumerate(domaines):
            try:
                dom_valide = CotationValidator.valider_domaine(domaine)
                if dom_valide['nom'] in noms_vus:
                    raise ValidationError(f"Nom de domaine dupliqué: '{dom_valide['nom']}'")
                noms_vus.add(dom_valide['nom'])
                domaines_valides.append(dom_valide)
            except ValidationError as e:
                raise ValidationError(f"Domaine {i+1}: {e}") from e

        return domaines_valides

    @staticmethod
    def valider_scores_cotation(scores: Dict[str, Any], domaines: List[Dict[str, Any]]) -> Tuple[Dict[str, float], List[str]]:
        """Valide les scores d'une cotation par rapport aux domaines."""
        scores_valides = {}
        erreurs = []

        # Construire la liste des clés attendues
        cles_attendues = set()
        for domaine in domaines:
            for indicateur in domaine.get('indicateurs', []):
                cle = f"{domaine['nom']}_{indicateur['nom']}"
                cles_attendues.add(cle)

        # Valider chaque score fourni
        for cle, valeur in scores.items():
            if cle not in cles_attendues:
                erreurs.append(f"Score inattendu: {cle}")
                continue
            
            try:
                val_num = float(valeur)
                # Trouver les limites pour cette clé
                domaine_nom, indicateur_nom = cle.split('_', 1)
                limites = None
                for dom in domaines:
                    if dom['nom'] == domaine_nom:
                        for ind in dom.get('indicateurs', []):
                            if ind['nom'] == indicateur_nom:
                                limites = (ind['min'], ind['max'])
                                break
                        break
                
                if limites and (val_num < limites[0] or val_num > limites[1]):
                    erreurs.append(f"Score {cle} hors limites [{limites[0]}-{limites[1]}]: {val_num}")
                else:
                    scores_valides[cle] = val_num
            except (ValueError, TypeError):
                erreurs.append(f"Score {cle} non numérique: {valeur}")

        return scores_valides, erreurs
