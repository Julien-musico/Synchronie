"""
Routes pour la gestion des patients (interface web)
"""
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
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
    from app.services.cotation_service import CotationService
    
    try:
        # Récupérer les grilles disponibles
        grilles_disponibles = CotationService.get_grilles_disponibles_pour_patient()
        return render_template('patients/form_simple.html', patient=None, grilles_disponibles=grilles_disponibles)
    except Exception as e:
        flash(f"Erreur lors du chargement des grilles: {e}", 'warning')
        return render_template('patients/form_simple.html', patient=None, grilles_disponibles={'standards': [], 'personnalisees': []})

@patients.route('/create', methods=['POST'])
@login_required  # type: ignore
def create_patient():
    """Traitement de la création d'un patient"""
    data = request.form.to_dict()
    
    # Gérer la grille sélectionnée (radio button unique)
    grille_id = request.form.get('grille_id')
    if grille_id and grille_id.isdigit():
        data['grilles_ids'] = [int(grille_id)]  # Convertir en liste pour compatibilité
    
    success, message, patient = PatientService.create_patient(data)
    
    if success:
        flash(message, 'success')
        return redirect(url_for('patients.view_patient', patient_id=patient.id))  # type: ignore[attr-defined]
    flash(message, 'error')
    
    # En cas d'erreur, recharger les grilles pour le formulaire
    from app.services.cotation_service import CotationService
    try:
        grilles_disponibles = CotationService.get_grilles_disponibles_pour_patient()
    except Exception:
        grilles_disponibles = {'standards': [], 'personnalisees': []}
    
    return render_template('patients/form_simple.html', patient=None, grilles_disponibles=grilles_disponibles)

@patients.route('/<int:patient_id>')
@login_required  # type: ignore
def view_patient(patient_id):
    """Affichage d'un patient"""
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    # Récupérer les grilles assignées
    grilles_assignees = PatientService.get_grilles_patient(patient_id)
    
    # Rendre la fonction datetime disponible dans le template
    return render_template('patients/detail.html', 
                         patient=patient, 
                         grilles_assignees=grilles_assignees,
                         now=datetime.now)

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
    flash(message, 'error')
    return redirect(url_for('patients.edit_patient', patient_id=patient_id))


@patients.route('/<int:patient_id>/grilles', methods=['GET', 'POST'])
@login_required  # type: ignore
def manage_grilles_patient(patient_id):
    """Gestion des grilles assignées à un patient"""
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    if request.method == 'POST':
        # Traitement de la mise à jour des grilles
        grilles_ids = request.form.getlist('grilles_ids')
        grilles_ids = [int(gid) for gid in grilles_ids if gid.isdigit()]
        
        success, message = PatientService.modifier_grilles_patient(patient_id, grilles_ids)
        flash(message, 'success' if success else 'error')
        return redirect(url_for('patients.view_patient', patient_id=patient_id))
    
    # Affichage du formulaire de gestion des grilles
    from app.services.cotation_service import CotationService
    try:
        grilles_disponibles = CotationService.get_grilles_disponibles_pour_patient()
        grilles_assignees = PatientService.get_grilles_patient(patient_id)
        
        return render_template('patients/manage_grilles.html', 
                             patient=patient,
                             grilles_disponibles=grilles_disponibles,
                             grilles_assignees=grilles_assignees)
    except Exception as e:
        flash(f"Erreur lors du chargement des grilles: {e}", 'error')
        return redirect(url_for('patients.view_patient', patient_id=patient_id))
