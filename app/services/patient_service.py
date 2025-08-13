"""
Services pour la gestion des patients
"""
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, Patient
from flask_login import current_user  # type: ignore

class PatientService:
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
        try:
            user_id = current_user.id  # type: ignore[attr-defined]
            query = query.filter_by(musicotherapeute_id=user_id)
        except Exception:
            pass
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
        try:
            user_id = current_user.id  # type: ignore[attr-defined]
            return Patient.query.filter_by(id=patient_id, musicotherapeute_id=user_id).first()
        except Exception:
            return Patient.query.get(patient_id)
    
    @staticmethod
    def create_patient(data: dict) -> tuple[bool, str, Optional[Patient]]:
        """
        Crée un nouveau patient
        
        Args:
            data: Données du patient
            
        Returns:
            Tuple (succès, message, patient)
        """
        try:
            print(f"DEBUG: Données reçues pour création patient: {data}")
            
            # Validation des données requises
            nom = data.get('nom', '').strip()
            prenom = data.get('prenom', '').strip()
            
            if not nom or not prenom:
                return False, "Le nom et le prénom sont obligatoires", None
            
            print(f"DEBUG: Création patient {prenom} {nom}")
            
            # Gestion de la date de naissance
            date_naissance = None
            if data.get('date_naissance'):
                try:
                    from datetime import datetime
                    date_naissance = datetime.strptime(data['date_naissance'], '%Y-%m-%d').date()
                except ValueError:
                    print(f"DEBUG: Erreur format date: {data.get('date_naissance')}")
                    # Continuer sans date plutôt que d'échouer
                    pass
            
            # Associer au thérapeute courant
            owner_id = None
            try:
                owner_id = current_user.id  # type: ignore[attr-defined]
            except Exception:
                pass
            patient = Patient(  # type: ignore[call-arg]
                nom=nom,  # type: ignore[arg-type]
                prenom=prenom,  # type: ignore[arg-type]
                date_naissance=date_naissance,  # type: ignore[arg-type]
                telephone=data.get('telephone', '').strip() or None,  # type: ignore[arg-type]
                email=data.get('email', '').strip() or None,  # type: ignore[arg-type]
                adresse=data.get('adresse', '').strip() or None,  # type: ignore[arg-type]
                pathologie=data.get('pathologie', '').strip() or None,  # type: ignore[arg-type]
                objectifs_therapeutiques=data.get('objectifs_therapeutiques', '').strip() or None,  # type: ignore[arg-type]
                commentaires=data.get('commentaires', '').strip() or None,  # type: ignore[arg-type]
                actif=True,  # type: ignore[arg-type]
                musicotherapeute_id=owner_id  # type: ignore[arg-type]
            )
            
            print("DEBUG: Tentative d'ajout en base...")
            db.session.add(patient)
            db.session.commit()
            print(f"DEBUG: Patient créé avec ID: {patient.id}")
            
            return True, f"Patient {prenom} {nom} créé avec succès", patient
            
        except SQLAlchemyError as e:
            print(f"DEBUG: Erreur SQLAlchemy: {str(e)}")
            db.session.rollback()
            return False, f"Erreur lors de la création du patient: {str(e)}", None
        except Exception as e:
            print(f"DEBUG: Erreur générale: {str(e)}")
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
            try:
                user_id = current_user.id  # type: ignore[attr-defined]
                patient = Patient.query.filter_by(id=patient_id, musicotherapeute_id=user_id).first()
            except Exception:
                patient = Patient.query.get(patient_id)
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
            try:
                user_id = current_user.id  # type: ignore[attr-defined]
                patient = Patient.query.filter_by(id=patient_id, musicotherapeute_id=user_id).first()
            except Exception:
                patient = Patient.query.get(patient_id)
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
        return Patient.query.filter(
            db.or_(
                Patient.nom.ilike(search),
                Patient.prenom.ilike(search)
            )
        ).filter_by(actif=True).order_by(Patient.nom, Patient.prenom).all()
