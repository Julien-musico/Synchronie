"""
Routes pour la gestion des enregistrements audio et transcriptions
"""
import os

from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for
from flask_login import login_required  # type: ignore

from app.services.audio_service import AudioTranscriptionService
from app.services.patient_service import PatientService
from app.services.seance_service import SeanceService

audio = Blueprint('audio', __name__, url_prefix='/audio')

@audio.route('/upload/<int:seance_id>')
@login_required  # type: ignore
def upload_form(seance_id: int):
    """Formulaire d'upload d'enregistrement audio pour une séance"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        flash('Séance non trouvée', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('audio/upload.html', seance=seance)

@audio.route('/upload/<int:seance_id>', methods=['POST'])
@login_required  # type: ignore
def upload_audio(seance_id: int):
    """Traitement de l'upload et transcription d'un fichier audio"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        flash('Séance non trouvée', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Vérifier qu'un fichier a été uploadé
    if 'audio_file' not in request.files:
        flash('Aucun fichier sélectionné', 'error')
        return redirect(url_for('audio.upload_form', seance_id=seance_id))
    
    file = request.files['audio_file']
    if file.filename == '':
        flash('Aucun fichier sélectionné', 'error')
        return redirect(url_for('audio.upload_form', seance_id=seance_id))
    
    try:
        # Vérifier la clé API OpenAI
        if not os.environ.get('OPENAI_API_KEY'):
            flash('Service de transcription non configuré (clé API manquante)', 'error')
            return redirect(url_for('audio.upload_form', seance_id=seance_id))
        
        # Initialiser le service de transcription
        audio_service = AudioTranscriptionService()
        
        # Traiter l'enregistrement
        success, message = audio_service.process_session_recording(file, seance_id)
        
        if success:
            flash('Enregistrement traité avec succès ! Transcription et analyse générées.', 'success')
            return redirect(url_for('seances.view_seance', seance_id=seance_id))
        flash(f'Erreur lors du traitement: {message}', 'error')
        return redirect(url_for('audio.upload_form', seance_id=seance_id))
            
    except Exception as e:
        flash(f'Erreur inattendue: {str(e)}', 'error')
        return redirect(url_for('audio.upload_form', seance_id=seance_id))

@audio.route('/transcribe-only/<int:seance_id>', methods=['POST'])
@login_required  # type: ignore
def transcribe_only(seance_id: int):
    """Transcription seule sans analyse IA (plus rapide)"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        return jsonify({'success': False, 'message': 'Séance non trouvée'}), 404
    
    if 'audio_file' not in request.files:
        return jsonify({'success': False, 'message': 'Aucun fichier fourni'}), 400
    
    file = request.files['audio_file']
    
    try:
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({'success': False, 'message': 'Service non configuré'}), 500
        
        audio_service = AudioTranscriptionService()
        success, message, transcription = audio_service.transcribe_audio(file)
        
        if success:
            # Mettre à jour seulement la transcription
            seance.transcription_audio = transcription
            from app.models import db
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Transcription réussie',
                'transcription': transcription
            })
        return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@audio.route('/transcribe-temp', methods=['POST'])
@login_required  # type: ignore
def transcribe_temp():
    """Transcrit un fichier audio sans associer à une séance (mode création)"""
    if 'audio_file' not in request.files:
        return jsonify({'success': False, 'message': 'Aucun fichier fourni'}), 400
    file = request.files['audio_file']

    try:
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({'success': False, 'message': 'Service non configuré'}), 500

        audio_service = AudioTranscriptionService()
        success, message, transcription = audio_service.transcribe_audio(file)

        if success:
            return jsonify({
                'success': True,
                'message': 'Transcription réussie',
                'transcription': transcription
            })
        return jsonify({'success': False, 'message': message}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@audio.route('/analyze/<int:seance_id>', methods=['POST'])
@login_required  # type: ignore
def generate_analysis(seance_id: int):
    """Génère une analyse IA à partir d'une transcription existante"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        return jsonify({'success': False, 'message': 'Séance non trouvée'}), 404
    
    if not seance.transcription_audio:
        return jsonify({'success': False, 'message': 'Aucune transcription disponible'}), 400
    
    try:
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({'success': False, 'message': 'Service non configuré'}), 500
        
        audio_service = AudioTranscriptionService()
        
        # Informations du patient à partir du service
        patient = PatientService.get_patient_by_id(seance.patient_id)
        patient_info = {
            'prenom': getattr(patient, 'prenom', '') if patient else '',
            'pathologie': getattr(patient, 'pathologie', '') if patient else '',
            'objectifs_therapeutiques': getattr(patient, 'objectifs_therapeutiques', '') if patient else ''
        }
        
        # Contexte de séance
        session_context = {
            'objectifs_seance': getattr(seance, 'objectifs_seance', ''),
            'activites_realisees': getattr(seance, 'activites_realisees', ''),
            'observations': getattr(seance, 'observations', ''),
        }
        
        success, message, analysis = audio_service.generate_session_analysis(
            seance.transcription_audio,
            patient_info,
            session_context=session_context
        )
        
        if success:
            seance.synthese_ia = analysis
            from app.models import db
            db.session.commit()
            return jsonify({
                'success': True,
                'message': 'Analyse générée avec succès',
                'analysis': analysis
            })
        return jsonify({'success': False, 'message': message}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@audio.route('/generate-with-context/<int:seance_id>', methods=['POST'])
@login_required  # type: ignore
def generate_with_context(seance_id: int):
    """Génère une synthèse IA en utilisant la transcription si dispo sinon les observations et le contexte de séance"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        return jsonify({'success': False, 'message': 'Séance non trouvée'}), 404

    try:
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({'success': False, 'message': 'Service non configuré'}), 500

        # Payload optionnel
        req_json = {}
        try:
            req_json = request.get_json(silent=True) or {}
        except Exception:
            req_json = {}

        use_transcription = req_json.get('use_transcription', True)
        override_text = req_json.get('text')  # Permet de passer un texte alternatif (ex: observations)

        # Construire le texte source
        source_text = None
        if use_transcription and getattr(seance, 'transcription_audio', None):
            source_text = seance.transcription_audio
        elif override_text:
            source_text = override_text
        else:
            # fallback: concaténer observations + objectifs + activités
            parts = [
                getattr(seance, 'observations', '') or '',
                getattr(seance, 'objectifs_seance', '') or '',
                getattr(seance, 'activites_realisees', '') or ''
            ]
            source_text = "\n\n".join([p for p in parts if p])

        if not source_text:
            return jsonify({'success': False, 'message': 'Aucune donnée disponible pour générer la synthèse'}), 400

        audio_service = AudioTranscriptionService()

        # Informations patient et contexte séance
        patient = PatientService.get_patient_by_id(seance.patient_id)
        patient_info = {
            'prenom': getattr(patient, 'prenom', '') if patient else '',
            'pathologie': getattr(patient, 'pathologie', '') if patient else '',
            'objectifs_therapeutiques': getattr(patient, 'objectifs_therapeutiques', '') if patient else ''
        }

        session_context = {
            'objectifs_seance': getattr(seance, 'objectifs_seance', ''),
            'activites_realisees': getattr(seance, 'activites_realisees', ''),
            'observations': getattr(seance, 'observations', ''),
        }

        success, message, analysis = audio_service.generate_session_analysis(
            source_text,
            patient_info,
            session_context=session_context
        )

        if success:
            # Persist synthèse
            seance.synthese_ia = analysis
            from app.models import db
            db.session.commit()
            return jsonify({'success': True, 'message': 'Synthèse générée', 'analysis': analysis})
        return jsonify({'success': False, 'message': message}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@audio.route('/generate-temp', methods=['POST'])
@login_required  # type: ignore
def generate_temp():
    """Génère une synthèse IA temporaire sans sauvegarde (mode création)"""
    try:
        if not os.environ.get('OPENAI_API_KEY'):
            return jsonify({'success': False, 'message': 'Service non configuré'}), 500

        payload = request.get_json(silent=True) or {}
        text = payload.get('text')
        patient_info = payload.get('patient_info') or {}
        session_context = payload.get('session_context') or {}

        if not text:
            return jsonify({'success': False, 'message': 'Aucun texte fourni pour la synthèse'}), 400

        audio_service = AudioTranscriptionService()
        success, message, analysis = audio_service.generate_session_analysis(
            text,
            patient_info,
            session_context=session_context
        )
        if success:
            return jsonify({'success': True, 'message': 'Synthèse générée', 'analysis': analysis})
        return jsonify({'success': False, 'message': message}), 500
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@audio.route('/info', methods=['POST'])
@login_required  # type: ignore
def get_audio_info():
    """Récupère les informations d'un fichier audio sans le traiter"""
    if 'audio_file' not in request.files:
        return jsonify({'success': False, 'message': 'Aucun fichier fourni'}), 400
    
    file = request.files['audio_file']
    
    try:
        # Validation
        is_valid, error_msg = AudioTranscriptionService.validate_audio_file(file)
        if not is_valid:
            return jsonify({'success': False, 'message': error_msg}), 400
        
        # Informations du fichier
        info = AudioTranscriptionService.get_audio_info(file)
        
        return jsonify({
            'success': True,
            'info': info
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@audio.route('/formats')
@login_required  # type: ignore
def supported_formats():
    """Retourne les formats audio supportés"""
    return jsonify({
        'formats': list(AudioTranscriptionService.ALLOWED_EXTENSIONS),
        'max_size_mb': AudioTranscriptionService.MAX_FILE_SIZE // (1024 * 1024),
        'note': 'Transcription automatique via OpenAI Whisper'
    })
