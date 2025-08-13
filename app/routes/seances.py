"""
Routes pour la gestion des séances
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required  # type: ignore

from app.services.patient_service import PatientService
from app.services.seance_service import SeanceService

seances = Blueprint('seances', __name__)

@seances.route('/')
@login_required  # type: ignore
def list_seances():
    """Liste de toutes les séances"""
    seances_list = SeanceService.get_all_seances()
    return render_template('seances/list.html', seances=seances_list)

@seances.route('/patient/<int:patient_id>')
@login_required  # type: ignore
def list_seances_patient(patient_id):
    """Liste des séances d'un patient spécifique"""
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    seances_list = SeanceService.get_seances_by_patient(patient_id)
    return render_template('seances/list.html', seances=seances_list, patient=patient)

@seances.route('/patient/<int:patient_id>/nouvelle')
@login_required  # type: ignore
def new_seance(patient_id):
    """Formulaire de création d'une nouvelle séance"""
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    return render_template('seances/form.html', patient=patient, seance=None, mode='create')

@seances.route('/patient/<int:patient_id>/create', methods=['POST'])
@login_required  # type: ignore
def create_seance(patient_id):
    """Traitement de la création d'une séance"""
    
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    data = request.form.to_dict()
    success, message, seance = SeanceService.create_seance(patient_id, data)
    
    if success:
        flash(message, 'success')
        return redirect(url_for('patients.view_patient', patient_id=patient_id))
    flash(message, 'error')
    return render_template('seances/form.html', patient=patient, seance=None, mode='create', data=data)

@seances.route('/<int:seance_id>')
@login_required  # type: ignore
def view_seance(seance_id):
    """Affichage d'une séance"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        flash('Séance non trouvée', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('seances/detail.html', seance=seance)

@seances.route('/<int:seance_id>/modifier')
@login_required  # type: ignore
def edit_seance(seance_id):
    """Formulaire de modification d'une séance"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        flash('Séance non trouvée', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('seances/form.html', patient=seance.patient, seance=seance, mode='edit')  # type: ignore[attr-defined]

@seances.route('/<int:seance_id>/update', methods=['POST'])
@login_required  # type: ignore
def update_seance(seance_id):
    """Traitement de la modification d'une séance"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        flash('Séance non trouvée', 'error')
        return redirect(url_for('main.dashboard'))
    
    data = request.form.to_dict()
    success, message, updated_seance = SeanceService.update_seance(seance_id, data)
    
    if success:
        flash(message, 'success')
        return redirect(url_for('seances.view_seance', seance_id=seance_id))
    flash(message, 'error')
    return render_template('seances/form.html', patient=seance.patient, seance=seance, mode='edit', data=data)  # type: ignore[attr-defined]

@seances.route('/<int:seance_id>/coter')
@login_required  # type: ignore
def coter_seance(seance_id):
    """Interface simple de cotation d'une séance"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        flash('Séance non trouvée', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Récupérer la grille assignée au patient (la première active)
    from app.models.cotation import GrilleEvaluation
    from app.services.patient_service import PatientService
    
    grilles_patient = PatientService.get_grilles_patient(seance.patient.id)
    grille_data = None
    
    if grilles_patient:
        # Récupérer l'objet GrilleEvaluation complet avec les domaines
        grille_id = grilles_patient[0]['id']
        grille_obj = GrilleEvaluation.query.get(grille_id)
        if grille_obj:
            grille_data = {
                'id': grille_obj.id,
                'nom': grille_obj.nom,
                'description': grille_obj.description,
                'domaines': grille_obj.domaines  # Utilise la propriété qui decode le JSON
            }
    
    return render_template('seances/cotation_simple.html', seance=seance, grille=grille_data)

@seances.route('/<int:seance_id>/cotation/save', methods=['POST'])
@login_required  # type: ignore
def save_cotation(seance_id):
    """Sauvegarde d'une cotation de séance"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        flash('Séance non trouvée', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        from app.services.cotation_service import CotationService
        from app.services.patient_service import PatientService
        
        # Récupérer la grille du patient
        grilles_patient = PatientService.get_grilles_patient(seance.patient.id)
        if not grilles_patient:
            flash('Aucune grille assignée à ce patient', 'error')
            return redirect(url_for('seances.coter_seance', seance_id=seance_id))
        
        grille_id = grilles_patient[0]['id']
        
        # Extraire les scores du formulaire
        scores = {}
        observations = request.form.get('observations', '')
        
        for key, value in request.form.items():
            if key.startswith('score_'):
                # Nettoyer le nom de l'indicateur
                indicator_name = key.replace('score_', '').replace('_', ' ')
                scores[indicator_name] = int(value)
        
        # Sauvegarder la cotation
        success = CotationService.sauvegarder_cotation_seance(
            seance_id=seance_id,
            grille_id=grille_id,
            scores=scores,
            observations=observations
        )
        
        if success:
            flash('Cotation sauvegardée avec succès', 'success')
            return redirect(url_for('patients.view_patient', patient_id=seance.patient.id))
        
        flash('Erreur lors de la sauvegarde', 'error')
        return redirect(url_for('seances.coter_seance', seance_id=seance_id))
            
    except Exception as e:
        flash(f'Erreur: {str(e)}', 'error')
        return redirect(url_for('seances.coter_seance', seance_id=seance_id))

@seances.route('/<int:seance_id>/delete', methods=['POST'])
@login_required  # type: ignore
def delete_seance(seance_id):
    """Suppression d'une séance"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        flash('Séance non trouvée', 'error')
        return redirect(url_for('main.dashboard'))
    
    patient_id = seance.patient_id
    success, message = SeanceService.delete_seance(seance_id)
    
    flash(message, 'success' if success else 'error')
    return redirect(url_for('patients.view_patient', patient_id=patient_id))
