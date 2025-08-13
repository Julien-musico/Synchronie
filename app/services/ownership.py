"""Utilitaires centralisés pour la gestion d'ownership multi-thérapeute.

Objectif: unifier la logique d'accès par musicotherapeute_id afin de réduire
la duplication et préparer une future gestion fine des permissions.
"""
from __future__ import annotations
from typing import Optional, Any
from flask_login import current_user  # type: ignore

def _CURRENT_UID():  # type: ignore
    try:
        return getattr(current_user, 'id', None)  # type: ignore[attr-defined]
    except Exception:  # pragma: no cover
        return None


def current_owner_id() -> Optional[int]:
    """Retourne l'id de l'utilisateur courant ou None hors contexte."""
    try:
        return _CURRENT_UID()
    except Exception:  # pragma: no cover
        return None


def owned_query(query, model) -> Any:  # type: ignore
    """Applique un filtre ownership si le modèle possède musicotherapeute_id.

    Si aucun utilisateur courant ou modèle sans champ => renvoie la query intacte.
    """
    uid = current_owner_id()
    if not uid:
        return query
    if hasattr(model, 'musicotherapeute_id'):
        try:
            return query.filter_by(musicotherapeute_id=uid)
        except Exception:
            return query
    return query


def assert_owns(instance) -> bool:
    """Vérifie que l'utilisateur courant possède l'instance si applicable."""
    if instance is None:
        return False
    uid = current_owner_id()
    if not uid:
        return True  # contexte système
    if hasattr(instance, 'musicotherapeute_id'):
        return getattr(instance, 'musicotherapeute_id') == uid
    return True
