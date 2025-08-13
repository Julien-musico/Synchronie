"""Service pour la gestion des objectifs thérapeutiques liés aux versions de grilles."""
from __future__ import annotations
from typing import List
from app.models import db
from app.models.cotation import ObjectifTherapeutique, GrilleEvaluation, GrilleVersion
from flask_login import current_user  # type: ignore

class ObjectifService:
    @staticmethod
    def creer_objectif(patient_id: int, grille_id: int, domaine_cible: str, indicateur_cible: str,
                       score_cible: float, score_initial: float | None = None, echeance=None,
                       description: str | None = None) -> ObjectifTherapeutique:
        grille = GrilleEvaluation.query.get(grille_id)
        if not grille:
            raise ValueError("Grille introuvable")
        # Version active au moment de la définition
        version = GrilleVersion.query.filter_by(grille_id=grille_id, active=True).order_by(GrilleVersion.version_num.desc()).first()
        obj = ObjectifTherapeutique()  # type: ignore
        obj.patient_id = patient_id
        obj.grille_id = grille_id
        obj.grille_version_id = version.id if version else None
        obj.domaine_cible = domaine_cible
        obj.indicateur_cible = indicateur_cible
        obj.score_cible = score_cible
        obj.score_initial = score_initial
        obj.echeance = echeance
        obj.description = description
        obj.actif = True
        try:
            obj.musicotherapeute_id = current_user.id  # type: ignore[attr-defined]
        except Exception:
            pass
        db.session.add(obj)
        db.session.commit()
        return obj

    @staticmethod
    def desactiver_objectif(objectif_id: int) -> bool:
        obj = ObjectifTherapeutique.query.get(objectif_id)
        if not obj:
            return False
        obj.actif = False
        db.session.commit()
        return True

    @staticmethod
    def lister_objectifs_patient(patient_id: int, actifs_seulement: bool = True) -> List[ObjectifTherapeutique]:
        q = ObjectifTherapeutique.query.filter_by(patient_id=patient_id)
        if actifs_seulement:
            q = q.filter_by(actif=True)
        return q.order_by(ObjectifTherapeutique.date_creation.desc()).all()  # type: ignore
