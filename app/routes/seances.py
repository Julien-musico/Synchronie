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
    
    # Récupérer la grille du patient pour la cotation optionnelle
    from app.models.cotation import GrilleEvaluation
    grilles_patient = PatientService.get_grilles_patient(patient_id)
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
                'domaines': grille_obj.domaines
            }
    
    return render_template('seances/form.html', patient=patient, seance=None, mode='create', grille=grille_data)

@seances.route('/patient/<int:patient_id>/create', methods=['POST'])
@login_required  # type: ignore
def create_seance(patient_id):
    """Traitement de la création d'une séance"""
    
    patient = PatientService.get_patient_by_id(patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('patients.list_patients'))
    
    data = request.form.to_dict()
    files = request.files
    
    success, message, seance = SeanceService.create_seance(patient_id, data)
    
    if success and seance:
        # Vérifier si des scores de cotation ont été soumis
        cotation_scores = {}
        cotation_observations = request.form.get('cotation_observations', '')
        
        for key, value in request.form.items():
            if key.startswith('cotation_score_'):
                try:
                    indicator_name = key.replace('cotation_score_', '').replace('_', ' ')
                    score_value = int(value)
                    if score_value > 0:  # Ne sauvegarder que les scores non-zéro
                        cotation_scores[indicator_name] = score_value
                except (ValueError, TypeError):
                    continue
        
        # Si des scores ont été saisis, sauvegarder la cotation
        cotation_message = ""
        if cotation_scores or cotation_observations:
            from app.services.cotation_service import CotationService
            grilles_patient = PatientService.get_grilles_patient(patient_id)
            
            if grilles_patient:
                grille_id = grilles_patient[0]['id']
                cotation_success = CotationService.sauvegarder_cotation_simple(
                    seance_id=seance.id,
                    grille_id=grille_id,
                    scores=cotation_scores,
                    observations=cotation_observations
                )
                
                if cotation_success and cotation_scores:
                    cotation_message = " - Cotation également sauvegardée"
        
        # Gérer la transcription audio en arrière-plan si un fichier a été uploadé
        transcription_message = ""
        if 'fichier_audio' in files and files['fichier_audio'].filename:
            audio_file = files['fichier_audio']
            try:
                import os
                if os.environ.get('OPENAI_API_KEY'):
                    from app.services.audio_service import AudioTranscriptionService
                    
                    # Lancer la transcription en arrière-plan
                    audio_service = AudioTranscriptionService()
                    transcription_success, transcription_msg = audio_service.process_session_recording(audio_file, seance.id)
                    
                    if transcription_success:
                        transcription_message = " - Transcription en cours"
                    else:
                        transcription_message = f" - Erreur transcription: {transcription_msg}"
                else:
                    transcription_message = " - Service de transcription non configuré"
            except Exception as e:
                transcription_message = f" - Erreur transcription: {str(e)}"
        
        # Message final combiné
        final_message = f"{message}{cotation_message}{transcription_message}"
        flash(final_message, 'success')
        return redirect(url_for('seances.edit_seance', seance_id=seance.id))  # Rediriger vers la modification pour continuer le workflow
    
    # En cas d'erreur, recharger le formulaire avec les données et la grille
    from app.models.cotation import GrilleEvaluation
    grilles_patient = PatientService.get_grilles_patient(patient_id)
    grille_data = None
    
    if grilles_patient:
        grille_id = grilles_patient[0]['id']
        grille_obj = GrilleEvaluation.query.get(grille_id)
        if grille_obj:
            grille_data = {
                'id': grille_obj.id,
                'nom': grille_obj.nom,
                'description': grille_obj.description,
                'domaines': grille_obj.domaines
            }
    
    flash(message, 'error')
    return render_template('seances/form.html', patient=patient, seance=None, mode='create', data=data, grille=grille_data)

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
    
    # Récupérer le patient de la séance
    patient = PatientService.get_patient_by_id(seance.patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Récupérer la grille du patient pour la cotation (même interface qu'en création)
    from app.models.cotation import GrilleEvaluation
    grilles_patient = PatientService.get_grilles_patient(seance.patient_id)
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
                'domaines': grille_obj.domaines
            }
    
    return render_template('seances/form.html', patient=patient, seance=seance, mode='edit', grille=grille_data)

@seances.route('/<int:seance_id>/update', methods=['POST'])
@login_required  # type: ignore
def update_seance(seance_id):
    """Traitement de la modification d'une séance"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        flash('Séance non trouvée', 'error')
        return redirect(url_for('main.dashboard'))
    
    patient = PatientService.get_patient_by_id(seance.patient_id)
    if not patient:
        flash('Patient non trouvé', 'error')
        return redirect(url_for('main.dashboard'))
    
    data = request.form.to_dict()
    files = request.files
    
    success, message, updated_seance = SeanceService.update_seance(seance_id, data)
    
    if success:
        # Vérifier si des scores de cotation ont été soumis (même logique qu'en création)
        cotation_scores = {}
        cotation_observations = request.form.get('cotation_observations', '')
        
        for key, value in request.form.items():
            if key.startswith('cotation_score_'):
                try:
                    indicator_name = key.replace('cotation_score_', '').replace('_', ' ')
                    score_value = int(value)
                    if score_value > 0:  # Ne sauvegarder que les scores non-zéro
                        cotation_scores[indicator_name] = score_value
                except (ValueError, TypeError):
                    continue
        
        # Si des scores ont été saisis, sauvegarder la cotation
        cotation_message = ""
        if cotation_scores or cotation_observations:
            from app.services.cotation_service import CotationService
            grilles_patient = PatientService.get_grilles_patient(seance.patient_id)
            
            if grilles_patient:
                grille_id = grilles_patient[0]['id']
                cotation_success = CotationService.sauvegarder_cotation_simple(
                    seance_id=seance_id,
                    grille_id=grille_id,
                    scores=cotation_scores,
                    observations=cotation_observations
                )
                
                if cotation_success and cotation_scores:
                    cotation_message = " - Cotation mise à jour"
        
        # Gérer la transcription audio en arrière-plan si un nouveau fichier a été uploadé
        transcription_message = ""
        if 'fichier_audio' in files and files['fichier_audio'].filename:
            audio_file = files['fichier_audio']
            try:
                import os
                if os.environ.get('OPENAI_API_KEY'):
                    from app.services.audio_service import AudioTranscriptionService
                    
                    # Lancer la transcription en arrière-plan
                    audio_service = AudioTranscriptionService()
                    transcription_success, transcription_msg = audio_service.process_session_recording(audio_file, seance_id)
                    
                    if transcription_success:
                        transcription_message = " - Nouvelle transcription en cours"
                    else:
                        transcription_message = f" - Erreur transcription: {transcription_msg}"
                else:
                    transcription_message = " - Service de transcription non configuré"
            except Exception as e:
                transcription_message = f" - Erreur transcription: {str(e)}"
        
        # Message final combiné
        final_message = f"{message}{cotation_message}{transcription_message}"
        flash(final_message, 'success')
        return redirect(url_for('seances.edit_seance', seance_id=seance_id))  # Rester sur la même page
    
    # En cas d'erreur, recharger le formulaire avec les données et la grille
    from app.models.cotation import GrilleEvaluation
    grilles_patient = PatientService.get_grilles_patient(seance.patient_id)
    grille_data = None
    
    if grilles_patient:
        grille_id = grilles_patient[0]['id']
        grille_obj = GrilleEvaluation.query.get(grille_id)
        if grille_obj:
            grille_data = {
                'id': grille_obj.id,
                'nom': grille_obj.nom,
                'description': grille_obj.description,
                'domaines': grille_obj.domaines
            }
    
    flash(message, 'error')
    return render_template('seances/form.html', patient=patient, seance=seance, mode='edit', data=data, grille=grille_data)

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
    
    grilles_patient = PatientService.get_grilles_patient(seance.patient_id)
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
        grilles_patient = PatientService.get_grilles_patient(seance.patient_id)
        if not grilles_patient:
            flash('Aucune grille assignée à ce patient', 'error')
            return redirect(url_for('seances.coter_seance', seance_id=seance_id))
        
        grille_id = grilles_patient[0]['id']
        
        # Extraire les scores du formulaire
        scores = {}
        observations = request.form.get('observations', '')
        
        # Debug: afficher les données reçues
        print(f"DEBUG - Données formulaire reçues: {dict(request.form)}")
        
        for key, value in request.form.items():
            if key.startswith('score_'):
                try:
                    # Nettoyer le nom de l'indicateur
                    indicator_name = key.replace('score_', '').replace('_', ' ')
                    score_value = int(value)
                    scores[indicator_name] = score_value
                    print(f"DEBUG - Score extrait: {indicator_name} = {score_value}")
                except (ValueError, TypeError):
                    print(f"DEBUG - Erreur conversion score: {key} = {value}")
                    continue
        
        print(f"DEBUG - Scores finaux: {scores}")
        print(f"DEBUG - Observations: {observations}")
        
        if not scores:
            flash('Aucun score trouvé dans le formulaire', 'warning')
            return redirect(url_for('seances.coter_seance', seance_id=seance_id))
        
        # Sauvegarder la cotation avec méthode simplifiée
        success = CotationService.sauvegarder_cotation_simple(
            seance_id=seance_id,
            grille_id=grille_id,
            scores=scores,
            observations=observations
        )
        
        if success:
            flash('Cotation sauvegardée avec succès', 'success')
            return redirect(url_for('patients.view_patient', patient_id=seance.patient_id))
        
        flash('Erreur lors de la sauvegarde', 'error')
        return redirect(url_for('seances.coter_seance', seance_id=seance_id))
            
    except Exception as e:
        print(f"DEBUG - Exception: {str(e)}")
        import traceback
        traceback.print_exc()
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
