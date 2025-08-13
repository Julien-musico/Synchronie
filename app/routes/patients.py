"""
Routes pour la gestion des patients (interface web)
"""
from datetime import datetime
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required  # type: ignore
from app.services.patient_service import PatientService

patients = Blueprint('patients', __name__)

@patients.route('/')
@login_required  # type: ignore
def list_patients():
    """Liste des patients"""
    patients_list = PatientService.get_all_patients()
    return render_template('patients/list.html', patients=patients_list)

@patients.route('/nouveau')
@login_required  # type: ignore
def new_patient():
    """Formulaire de création d'un nouveau patient"""
    return render_template('patients/form_simple.html', patient=None)

@patients.route('/create', methods=['POST'])
@login_required  # type: ignore
def create_patient():
    """Traitement de la création d'un patient"""
    data = request.form.to_dict()
    success, message, patient = PatientService.create_patient(data)
    
    if success:
        flash(message, 'success')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))  # type: ignore[attr-defined]
    else:
        flash(message, 'error')
        return render_template('patients/form_simple.html', patient=None)

@patients.route('/<int:patient_id>')
@login_required  # type: ignore
def view_patient(patient_id):
    """Affichage d'un patient"""
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    # Rendre la fonction datetime disponible dans le template
    return render_template('patients/detail.html', patient=patient, now=datetime.now)

@patients.route('/<int:patient_id>/modifier')
@login_required  # type: ignore
def edit_patient(patient_id):
    """Formulaire de modification d'un patient"""
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    return render_template('patients/form_simple.html', patient=patient)

@patients.route('/<int:patient_id>/update', methods=['POST'])
@login_required  # type: ignore
def update_patient(patient_id):
    """Traitement de la modification d'un patient"""
    data = request.form.to_dict()
    success, message, patient = PatientService.update_patient(patient_id, data)
    
    if success:
        flash(message, 'success')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))  # type: ignore[attr-defined]
    else:
        flash(message, 'error')
        return redirect(url_for('patients.edit_patient', patient_id=patient_id))
