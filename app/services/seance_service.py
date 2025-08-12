"""
Service métier pour la gestion des séances de musicothérapie
"""
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from sqlalchemy.exc import SQLAlchemyError
from app.models import db, Patient, Seance


class SeanceService:
    """Service pour toutes les opérations liées aux séances"""
    
    @staticmethod
    def create_seance(patient_id: int, data: Dict[str, Any]) -> Tuple[bool, str, Optional[Seance]]:
        """
        Créer une nouvelle séance pour un patient
        
        Args:
            patient_id: ID du patient
            data: Données de la séance
            
        Returns:
            Tuple[bool, str, Optional[Seance]]: (success, message, seance)
        """
        try:
            # Vérifier que le patient existe
            patient = Patient.query.get(patient_id)
            if not patient:
                return False, "Patient non trouvé", None
            
            # Validation des données requises
            if not data.get('date_seance'):
                return False, "La date de séance est obligatoire", None
            
            # Conversion de la date
            try:
                if isinstance(data['date_seance'], str):
                    # Format HTML datetime-local: "2023-12-25T14:30"
                    date_seance = datetime.fromisoformat(data['date_seance'].replace('T', ' '))
                    date_seance = date_seance.replace(tzinfo=timezone.utc)
                else:
                    date_seance = data['date_seance']
            except ValueError:
                return False, "Format de date invalide", None
            
            # Créer la nouvelle séance
            seance = Seance(
                patient_id=patient_id,
                date_seance=date_seance,
                type_seance=data.get('type_seance', '').strip() or None,
                duree_minutes=int(data['duree_minutes']) if data.get('duree_minutes') else None,
                objectifs_seance=data.get('objectifs_seance', '').strip() or None,
                activites_realisees=data.get('activites_realisees', '').strip() or None,
                observations=data.get('observations', '').strip() or None,
                score_engagement=float(data['score_engagement']) if data.get('score_engagement') else None,
                fichier_audio=data.get('fichier_audio', '').strip() or None,
                fichier_video=data.get('fichier_video', '').strip() or None
            )
            
            db.session.add(seance)
            db.session.commit()
            
            return True, f"Séance créée avec succès pour {patient.prenom} {patient.nom}", seance
            
        except ValueError as e:
            db.session.rollback()
            return False, f"Erreur de validation : {str(e)}", None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Erreur base de données : {str(e)}", None
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur inattendue : {str(e)}", None
    
    @staticmethod
    def get_seance_by_id(seance_id: int) -> Optional[Seance]:
        """Récupérer une séance par son ID"""
        try:
            return Seance.query.get(seance_id)
        except Exception:
            return None
    
    @staticmethod
    def get_seances_by_patient(patient_id: int) -> List[Seance]:
        """Récupérer toutes les séances d'un patient"""
        try:
            return Seance.query.filter_by(patient_id=patient_id).order_by(Seance.date_seance.desc()).all()
        except Exception:
            return []
    
    @staticmethod
    def update_seance(seance_id: int, data: Dict[str, Any]) -> Tuple[bool, str, Optional[Seance]]:
        """
        Mettre à jour une séance existante
        
        Args:
            seance_id: ID de la séance
            data: Nouvelles données
            
        Returns:
            Tuple[bool, str, Optional[Seance]]: (success, message, seance)
        """
        try:
            seance = Seance.query.get(seance_id)
            if not seance:
                return False, "Séance non trouvée", None
            
            # Mise à jour des champs
            if 'date_seance' in data and data['date_seance']:
                try:
                    if isinstance(data['date_seance'], str):
                        date_seance = datetime.fromisoformat(data['date_seance'].replace('T', ' '))
                        seance.date_seance = date_seance.replace(tzinfo=timezone.utc)
                    else:
                        seance.date_seance = data['date_seance']
                except ValueError:
                    return False, "Format de date invalide", None
            
            # Mise à jour des autres champs
            fields_to_update = [
                'type_seance', 'duree_minutes', 'objectifs_seance', 
                'activites_realisees', 'observations', 'score_engagement',
                'fichier_audio', 'fichier_video'
            ]
            
            for field in fields_to_update:
                if field in data:
                    value = data[field]
                    if field == 'duree_minutes' and value:
                        value = int(value)
                    elif field == 'score_engagement' and value:
                        value = float(value)
                    elif isinstance(value, str):
                        value = value.strip() or None
                    
                    setattr(seance, field, value)
            
            seance.date_modification = datetime.now(timezone.utc)
            db.session.commit()
            
            return True, "Séance mise à jour avec succès", seance
            
        except ValueError as e:
            db.session.rollback()
            return False, f"Erreur de validation : {str(e)}", None
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Erreur base de données : {str(e)}", None
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur inattendue : {str(e)}", None
    
    @staticmethod
    def delete_seance(seance_id: int) -> Tuple[bool, str]:
        """
        Supprimer une séance
        
        Args:
            seance_id: ID de la séance
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            seance = Seance.query.get(seance_id)
            if not seance:
                return False, "Séance non trouvée"
            
            db.session.delete(seance)
            db.session.commit()
            
            return True, "Séance supprimée avec succès"
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, f"Erreur base de données : {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, f"Erreur inattendue : {str(e)}"
    
    @staticmethod
    def get_all_seances() -> List[Seance]:
        """Récupérer toutes les séances"""
        try:
            return Seance.query.order_by(Seance.date_seance.desc()).all()
        except Exception:
            return []
    
    @staticmethod
    def get_recent_seances(limit: int = 10) -> List[Seance]:
        """Récupérer les séances les plus récentes"""
        try:
            return Seance.query.order_by(Seance.date_seance.desc()).limit(limit).all()
        except Exception:
            return []
    
    @staticmethod
    def get_seances_statistics() -> Dict[str, Any]:
        """Calculer les statistiques générales des séances"""
        try:
            all_seances = SeanceService.get_all_seances()
            
            if not all_seances:
                return {
                    'total_seances': 0,
                    'duree_moyenne': 0,
                    'engagement_moyen': 0,
                    'seances_ce_mois': 0,
                    'types_seances': {}
                }
            
            # Calculs statistiques
            total_seances = len(all_seances)
            
            # Durée moyenne (en excluant les séances sans durée)
            durees = [s.duree_minutes for s in all_seances if s.duree_minutes]
            duree_moyenne = sum(durees) / len(durees) if durees else 0
            
            # Engagement moyen
            scores = [s.score_engagement for s in all_seances if s.score_engagement]
            engagement_moyen = sum(scores) / len(scores) if scores else 0
            
            # Séances ce mois
            now = datetime.now(timezone.utc)
            seances_ce_mois = len([
                s for s in all_seances 
                if s.date_seance.year == now.year and s.date_seance.month == now.month
            ])
            
            # Types de séances
            types_seances = {}
            for seance in all_seances:
                if seance.type_seance:
                    types_seances[seance.type_seance] = types_seances.get(seance.type_seance, 0) + 1
            
            return {
                'total_seances': total_seances,
                'duree_moyenne': round(duree_moyenne, 1),
                'engagement_moyen': round(engagement_moyen, 1),
                'seances_ce_mois': seances_ce_mois,
                'types_seances': types_seances
            }
            
        except Exception as e:
            print(f"Erreur calcul statistiques séances: {e}")
            return {
                'total_seances': 0,
                'duree_moyenne': 0,
                'engagement_moyen': 0,
                'seances_ce_mois': 0,
                'types_seances': {}
            }
    
    @staticmethod
    def search_seances(query: str, patient_id: Optional[int] = None) -> List[Seance]:
        """
        Rechercher des séances par mots-clés
        
        Args:
            query: Terme de recherche
            patient_id: Optionnel, filtrer par patient
            
        Returns:
            Liste des séances correspondantes
        """
        try:
            base_query = Seance.query
            
            if patient_id:
                base_query = base_query.filter_by(patient_id=patient_id)
            
            if query:
                search_term = f"%{query}%"
                base_query = base_query.filter(
                    db.or_(
                        Seance.type_seance.ilike(search_term),
                        Seance.objectifs_seance.ilike(search_term),
                        Seance.activites_realisees.ilike(search_term),
                        Seance.observations.ilike(search_term)
                    )
                )
            
            return base_query.order_by(Seance.date_seance.desc()).all()
            
        except Exception:
            return []
