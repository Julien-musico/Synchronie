"""
Routes pour la gestion des séances
"""
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.services.patient_service import PatientService

seances = Blueprint('seances', __name__)

@seances.route('/patient/<int:patient_id>/nouvelle')
def new_seance(patient_id):
    """Formulaire de création d'une nouvelle séance"""
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    return render_template('seances/form.html', patient=patient, seance=None, mode='create')

@seances.route('/patient/<int:patient_id>/create', methods=['POST'])
def create_seance(patient_id):
    """Traitement de la création d'une séance"""
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    data = request.form.to_dict()
    # TODO: Implémenter la création de séance via SeanceService
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('patients.view_patient', patient_id=patient_id))

@seances.route('/<int:seance_id>')
def view_seance(seance_id):
    """Affichage d'une séance"""
    # TODO: Implémenter la récupération de séance via SeanceService
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('main.dashboard'))

@seances.route('/<int:seance_id>/modifier')
def edit_seance(seance_id):
    """Formulaire de modification d'une séance"""
    # TODO: Implémenter la récupération de séance via SeanceService
    flash('Fonctionnalité en cours de développement', 'info')
    return redirect(url_for('main.dashboard'))
