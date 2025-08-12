"""
Routes pour la gestion des enregistrements audio et transcriptions
"""
import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from app.services.audio_service import AudioTranscriptionService
from app.services.seance_service import SeanceService

audio = Blueprint('audio', __name__, url_prefix='/audio')

@audio.route('/upload/<int:seance_id>')
def upload_form(seance_id: int):
    """Formulaire d'upload d'enregistrement audio pour une séance"""
    seance = SeanceService.get_seance_by_id(seance_id)
    if not seance:
        flash('Séance non trouvée', 'error')
        return redirect(url_for('main.dashboard'))
    
    return render_template('audio/upload.html', seance=seance)

@audio.route('/upload/<int:seance_id>', methods=['POST'])
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
        else:
            flash(f'Erreur lors du traitement: {message}', 'error')
            return redirect(url_for('audio.upload_form', seance_id=seance_id))
            
    except Exception as e:
        flash(f'Erreur inattendue: {str(e)}', 'error')
        return redirect(url_for('audio.upload_form', seance_id=seance_id))

@audio.route('/transcribe-only/<int:seance_id>', methods=['POST'])
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
            # Ne pas sauvegarder le fichier audio physiquement
            
            from app.models import db
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Transcription réussie',
                'transcription': transcription
            })
        else:
            return jsonify({'success': False, 'message': message}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@audio.route('/analyze/<int:seance_id>', methods=['POST'])
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
        
        # Informations du patient depuis la relation
        patient_info = {
            'prenom': getattr(seance, 'patient_prenom', ''),
            'pathologie': getattr(seance, 'pathologie', ''),
            'objectifs_therapeutiques': getattr(seance, 'objectifs', '')
        }
        
        success, message, analysis = audio_service.generate_session_analysis(
            seance.transcription_audio, 
            patient_info
        )
        
        if success:
            # Mettre à jour l'analyse
            seance.synthese_ia = analysis
            
            from app.models import db
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Analyse générée avec succès',
                'analysis': analysis
            })
        else:
            return jsonify({'success': False, 'message': message}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@audio.route('/info', methods=['POST'])
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
def supported_formats():
    """Retourne les formats audio supportés"""
    return jsonify({
        'formats': list(AudioTranscriptionService.ALLOWED_EXTENSIONS),
        'max_size_mb': AudioTranscriptionService.MAX_FILE_SIZE // (1024 * 1024),
        'note': 'Transcription automatique via OpenAI Whisper'
    })
