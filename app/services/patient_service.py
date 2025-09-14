"""
Services pour la gestion des patients
"""
import contextlib
from typing import List, Optional

from flask_login import current_user  # type: ignore
from sqlalchemy.exc import SQLAlchemyError

from app.models import Patient, db

# NOTE: Les appels de construction Patient(...) et PatientGrille(...) génèrent des
# faux positifs mypy/pyright (params non reconnus) car SQLAlchemy injecte dynamiquement
# les attributs de colonnes. On garde les signatures explicites pour la clarté et on
# ignore les avertissements avec type: ignore[call-arg].

# Helper interne
def _get_owned_patient(patient_id: int) -> Optional[Patient]:
    """Retourne le patient appartenant à l'utilisateur courant (ou None)."""
    try:
        user_id = current_user.id  # type: ignore[attr-defined]
        return Patient.query.filter_by(id=patient_id, user_id=user_id).first()
    except Exception:
        return Patient.query.get(patient_id)


class PatientService:
    @staticmethod
    def delete_patient(patient_id: int) -> tuple[bool, str]:
        """
        Supprime définitivement un patient et ses données associées
        Args:
            patient_id: ID du patient à supprimer
        Returns:
            Tuple (succès, message)
        """
        try:
            patient = _get_owned_patient(patient_id)
            if not patient:
                return False, "Patient non trouvé"
            db.session.delete(patient)
            db.session.commit()
            return True, "Patient supprimé avec succès"
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Erreur lors de la suppression: {str(e)}"
    """Service pour la gestion des patients"""
    
    @staticmethod
    def get_all_patients(actifs_seulement: bool = True) -> List[Patient]:
        """
        Récupère tous les patients
        
        Args:
            actifs_seulement: Si True, ne récupère que les patients actifs
            
        Returns:
            Liste des patients
        """
        query = Patient.query
        with contextlib.suppress(Exception):
            user_id = current_user.id  # type: ignore[attr-defined]
            query = query.filter_by(user_id=user_id)
        if actifs_seulement:
            query = query.filter_by(actif=True)
        
        return query.order_by(Patient.nom, Patient.prenom).all()
    
    @staticmethod
    def get_patient_by_id(patient_id: int) -> Optional[Patient]:
        """
        Récupère un patient par son ID
        
        Args:
            patient_id: ID du patient
            
        Returns:
            Patient ou None si non trouvé
        """
        return _get_owned_patient(patient_id)
    
    @staticmethod
    def create_patient(data: dict) -> tuple[bool, str, Optional[Patient]]:
        """
        Crée un nouveau patient
        
        Args:
            data: Données du patient (incluant grilles_ids optionnelles)
            
        Returns:
            Tuple (succès, message, patient)
        """
        try:
            # Validation & création patient
            
            # Validation des données requises
            nom = data.get('nom', '').strip()
            prenom = data.get('prenom', '').strip()
            
            if not nom or not prenom:
                return False, "Le nom et le prénom sont obligatoires", None
            
            
            # Gestion de la date de naissance
            date_naissance = None
            if data.get('date_naissance'):
                try:
                    from datetime import datetime
                    date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
                except ValueError:
                    # format date invalide ignoré
                    # Continuer sans date plutôt que d'échouer
                    pass
            
            # Associer au thérapeute courant
            owner_id = None
            with contextlib.suppress(Exception):
                owner_id = current_user.id  # type: ignore[attr-defined]
            patient = Patient(  # type: ignore[call-arg]
                nom=nom,
                prenom=prenom,
                date_naissance=date_naissance,
                telephone=data.get('telephone', '').strip() or None,
                email=data.get('email', '').strip() or None,
                adresse=data.get('adresse', '').strip() or None,
                pathologie=data.get('pathologie', '').strip() or None,
                objectifs_therapeutiques=data.get('objectifs_therapeutiques', '').strip() or None,
                commentaires=data.get('commentaires', '').strip() or None,
                actif=True,
                user_id=owner_id
            )
            
            db.session.add(patient)
            db.session.flush()  # Pour obtenir l'ID du patient
            
            # Assigner les grilles si spécifiées
            grilles_ids = data.get('grilles_ids', [])
            if grilles_ids:
                success, msg = PatientService._assigner_grilles(patient.id, grilles_ids)
                if not success:
                    pass
                    # Continuer même si l'assignation échoue
            
            db.session.commit()
            
            return True, f"Patient {prenom} {nom} créé avec succès", patient
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Erreur lors de la création du patient: {str(e)}", None
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur inattendue: {str(e)}", None
    
    @staticmethod
    def update_patient(patient_id: int, data: dict) -> tuple[bool, str, Optional[Patient]]:
        """
        Met à jour un patient
        
        Args:
            patient_id: ID du patient à mettre à jour
            data: Nouvelles données
            
        Returns:
            Tuple (succès, message, patient)
        """
        try:
            patient = _get_owned_patient(patient_id)
            if not patient:
                return False, "Patient non trouvé", None
            
            # Mise à jour des champs
            if 'nom' in data:
                patient.nom = data['nom'].strip()
            if 'prenom' in data:
                patient.prenom = data['prenom'].strip()
            if 'date_naissance' in data:
                patient.date_naissance = data['date_naissance']
            if 'telephone' in data:
                patient.telephone = data['telephone'].strip()
            if 'email' in data:
                patient.email = data['email'].strip()
            if 'adresse' in data:
                patient.adresse = data['adresse'].strip()
            if 'pathologie' in data:
                patient.pathologie = data['pathologie'].strip()
            if 'objectifs_therapeutiques' in data:
                patient.objectifs_therapeutiques = data['objectifs_therapeutiques'].strip()
            if 'commentaires' in data:
                patient.commentaires = data['commentaires'].strip()
            if 'actif' in data:
                patient.actif = data['actif']
            
            db.session.commit()
            return True, "Patient mis à jour avec succès", patient
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Erreur lors de la mise à jour: {str(e)}", None
    
    @staticmethod
    def archive_patient(patient_id: int) -> tuple[bool, str]:
        """
        Archive un patient (le marque comme inactif)
        
        Args:
            patient_id: ID du patient à archiver
            
        Returns:
            Tuple (succès, message)
        """
        try:
            patient = _get_owned_patient(patient_id)
            if not patient:
                return False, "Patient non trouvé"
            
            patient.actif = False
            db.session.commit()
            
            return True, "Patient archivé avec succès"
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Erreur lors de l'archivage: {str(e)}"
    
    @staticmethod
    def search_patients(query: str) -> List[Patient]:
        """
        Recherche des patients par nom ou prénom
        
        Args:
            query: Terme de recherche
            
        Returns:
            Liste des patients correspondants
        """
        search = f"%{query.lower()}%"
        base = Patient.query
        with contextlib.suppress(Exception):
            user_id = current_user.id  # type: ignore[attr-defined]
            base = base.filter_by(user_id=user_id)
        base = base.filter(db.or_(Patient.nom.ilike(search), Patient.prenom.ilike(search)))
        base = base.filter_by(actif=True)
        base = base.order_by(Patient.nom, Patient.prenom)
        return base.all()

    @staticmethod
    def _assigner_grilles(patient_id: int, grilles_ids: List[int]) -> tuple[bool, str]:
        """
        Assigne des grilles de cotation à un patient
        
        Args:
            patient_id: ID du patient
            grilles_ids: Liste des IDs des grilles à assigner
            
        Returns:
            Tuple (succès, message)
        """
        try:
            from app.models.cotation import PatientGrille
            
            # Supprimer les assignations existantes
            PatientGrille.query.filter_by(patient_id=patient_id).delete()
            
            # Ajouter les nouvelles assignations
            for priority, grille_id in enumerate(grilles_ids, 1):
                try:
                    grille_id = int(grille_id)
                    assignment = PatientGrille(  # type: ignore[call-arg]
                        patient_id=patient_id,  # type: ignore[arg-type]
                        grille_id=grille_id,    # type: ignore[arg-type]
                        priorite=priority,      # type: ignore[arg-type]
                        active=True             # type: ignore[arg-type]
                    )
                    db.session.add(assignment)
                except (ValueError, TypeError):
                    continue
            
            db.session.flush()
            return True, f"{len(grilles_ids)} grille(s) assignée(s) avec succès"
            
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur lors de l'assignation des grilles: {str(e)}"

    @staticmethod
    def get_grilles_patient(patient_id: int) -> List[dict]:
        """
        Récupère les grilles assignées à un patient
        
        Args:
            patient_id: ID du patient
            
        Returns:
            Liste des grilles assignées avec leurs détails
        """
        try:
            from app.models.cotation import GrilleEvaluation, PatientGrille
            
            assignments = db.session.query(PatientGrille, GrilleEvaluation).join(
                GrilleEvaluation, PatientGrille.grille_id == GrilleEvaluation.id
            ).filter(
                PatientGrille.patient_id == patient_id,
                PatientGrille.active.is_(True),
                GrilleEvaluation.active.is_(True)
            ).order_by(PatientGrille.priorite).all()
            
            return [
                {
                    'id': assignment.grille_id,
                    'nom': grille.nom,
                    'description': grille.description,
                    'type_grille': grille.type_grille,
                    'reference_scientifique': grille.reference_scientifique,
                    'priorite': assignment.priorite,
                    'date_assignation': assignment.date_assignation.isoformat() if assignment.date_assignation else None,
                    'nb_domaines': len(grille.domaines) if grille.domaines else 0
                }
                for assignment, grille in assignments
            ]
            
        except Exception as e:
            print(f"Erreur récupération grilles patient: {e}")
            return []

    @staticmethod
    def modifier_grilles_patient(patient_id: int, grilles_ids: List[int]) -> tuple[bool, str]:
        """
        Modifie les grilles assignées à un patient
        
        Args:
            patient_id: ID du patient
            grilles_ids: Nouvelle liste des IDs des grilles
            
        Returns:
            Tuple (succès, message)
        """
        try:
            # Vérifier que le patient existe et appartient à l'utilisateur
            try:
                user_id = current_user.id  # type: ignore[attr-defined]
                patient = Patient.query.filter_by(id=patient_id, user_id=user_id).first()
            except Exception:
                patient = Patient.query.get(patient_id)
            
            if not patient:
                return False, "Patient non trouvé"
            
            return PatientService._assigner_grilles(patient_id, grilles_ids)
            
        except Exception as e:
            return False, f"Erreur lors de la modification: {str(e)}"
