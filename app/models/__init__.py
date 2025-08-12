# Importation de tous les modèles pour les migrations
from .user import User, UserRole
from .patient import Patient, Gender, PatientStatus
from .session import Session, SessionStatus, SessionType
from .grille import Grille, GrilleAssignment, GrilleType, DomainType
from .rapport import Rapport, RapportType, RapportStatus

__all__ = [
    'User', 'UserRole',
    'Patient', 'Gender', 'PatientStatus', 
    'Session', 'SessionStatus', 'SessionType',
    'Grille', 'GrilleAssignment', 'GrilleType', 'DomainType',
    'Rapport', 'RapportType', 'RapportStatus'
]
