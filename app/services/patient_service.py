"""
Services pour la gestion des patients
"""
from typing import List, Optional
from sqlalchemy.exc import SQLAlchemyError
from app import db
from app.models import Patient

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
            # Validation des données requises
            if not data.get('nom') or not data.get('prenom'):
                return False, "Le nom et le prénom sont obligatoires", None
            
            patient = Patient(
                nom=data['nom'].strip(),
                prenom=data['prenom'].strip(),
                date_naissance=data.get('date_naissance'),
                telephone=data.get('telephone', '').strip(),
                email=data.get('email', '').strip(),
                adresse=data.get('adresse', '').strip(),
                pathologie=data.get('pathologie', '').strip(),
                objectifs_therapeutiques=data.get('objectifs_therapeutiques', '').strip(),
                commentaires=data.get('commentaires', '').strip()
            )
            
            db.session.add(patient)
            db.session.commit()
            
            return True, "Patient créé avec succès", patient
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Erreur lors de la création du patient: {str(e)}", None
    
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
