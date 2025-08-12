"""
Routes principales de l'application
"""
from flask import Blueprint, render_template
from app.services.patient_service import PatientService

main = Blueprint('main', __name__)

@main.route('/')
def index():
    """Page d'accueil"""
    return render_template('index.html')

@main.route('/dashboard')
def dashboard():
    """Tableau de bord principal"""
    # Récupérer les statistiques pour le dashboard
    patients = PatientService.get_all_patients()
    patients_actifs = [p for p in patients if p.actif]
    
    stats = {
        'total_patients': len(patients),
        'patients_actifs': len(patients_actifs),
        'total_seances': sum(len(p.seances) for p in patients),
        'seances_ce_mois': 0  # TODO: calculer les séances du mois en cours
    }
    
    return render_template('dashboard.html', stats=stats, patients_recents=patients[:5])
