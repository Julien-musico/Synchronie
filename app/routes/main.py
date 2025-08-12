"""
Routes principales de l'application
"""
from flask import Blueprint, render_template, jsonify
from app.services.patient_service import PatientService
from app.services.seance_service import SeanceService

main = Blueprint('main', __name__)

@main.route('/api/health')
def health_check():
    """Endpoint de santé pour Render"""
    return jsonify({'status': 'healthy', 'service': 'synchronie'}), 200

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
    
    # Statistiques des séances
    seances_stats = SeanceService.get_seances_statistics()
    
    stats = {
        'total_patients': len(patients),
        'patients_actifs': len(patients_actifs),
        'total_seances': seances_stats['total_seances'],
        'seances_ce_mois': seances_stats['seances_ce_mois'],
        'duree_moyenne': seances_stats['duree_moyenne'],
        'engagement_moyen': seances_stats['engagement_moyen']
    }
    
    # Séances récentes
    seances_recentes = SeanceService.get_recent_seances(5)
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         patients_recents=patients[:5],
                         seances_recentes=seances_recentes)
