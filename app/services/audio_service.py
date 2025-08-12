"""
Service de transcription audio et analyse IA pour Synchronie
Utilise OpenAI Whisper pour la transcription et GPT pour l'analyse
"""
import os
import tempfile
from typing import Optional, Tuple, Dict, Any
from werkzeug.datastructures import FileStorage
from werkzeug.utils import secure_filename
from openai import OpenAI
from app.models import db, Seance
import logging

logger = logging.getLogger(__name__)

class AudioTranscriptionService:
    """Service pour la transcription d'enregistrements audio de séances"""
    
    # Formats audio supportés
    ALLOWED_EXTENSIONS = {'mp3', 'wav', 'm4a', 'flac', 'ogg', 'webm'}
    MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB (limite OpenAI Whisper)
    
    def __init__(self):
        """Initialise le service avec la clé API OpenAI"""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY n'est pas configurée")
        
        self.client = OpenAI(api_key=api_key)
    
    @staticmethod
    def is_allowed_file(filename: str) -> bool:
        """Vérifie si le fichier a une extension autorisée"""
        return ('.' in filename and 
                filename.rsplit('.', 1)[1].lower() in AudioTranscriptionService.ALLOWED_EXTENSIONS)
    
    @staticmethod
    def validate_audio_file(file: FileStorage) -> Tuple[bool, str]:
        """
        Valide un fichier audio uploadé
        
        Returns:
            Tuple[bool, str]: (is_valid, error_message)
        """
        if not file or not file.filename:
            return False, "Aucun fichier sélectionné"
        
        if not AudioTranscriptionService.is_allowed_file(file.filename):
            return False, f"Format non supporté. Formats autorisés: {', '.join(AudioTranscriptionService.ALLOWED_EXTENSIONS)}"
        
        # Vérifier la taille (si possible)
        if hasattr(file, 'content_length') and file.content_length:
            if file.content_length > AudioTranscriptionService.MAX_FILE_SIZE:
                return False, "Fichier trop volumineux. Taille maximum: 25 MB"
        
        return True, ""
    
    def transcribe_audio(self, audio_file: FileStorage) -> Tuple[bool, str, Optional[str]]:
        """
        Transcrit un fichier audio en texte
        
        Args:
            audio_file: Fichier audio à transcrire
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, transcription)
        """
        try:
            # Validation du fichier
            is_valid, error_msg = self.validate_audio_file(audio_file)
            if not is_valid:
                return False, error_msg, None
            
            logger.info(f"Début de la transcription pour: {audio_file.filename}")
            
            # Créer un fichier temporaire pour l'upload vers OpenAI
            with tempfile.NamedTemporaryFile(
                suffix=f".{audio_file.filename.rsplit('.', 1)[1].lower()}", 
                delete=False
            ) as temp_file:
                
                # Sauvegarder le fichier temporairement
                audio_file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                # Transcription avec Whisper
                with open(temp_file_path, 'rb') as audio_data:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_data,
                        language="fr",  # Français
                        response_format="verbose_json",
                        timestamp_granularities=["segment"]
                    )
                
                transcription_text = transcript.text
                logger.info(f"Transcription réussie: {len(transcription_text)} caractères")
                
                return True, "Transcription réussie", transcription_text
                
            finally:
                # Nettoyer le fichier temporaire
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Impossible de supprimer le fichier temporaire: {e}")
        
        except Exception as e:
            logger.error(f"Erreur lors de la transcription: {e}")
            return False, f"Erreur de transcription: {str(e)}", None
    
    def generate_session_analysis(self, transcription: str, patient_info: Dict[str, Any]) -> Tuple[bool, str, Optional[str]]:
        """
        Génère une analyse IA de la séance à partir de la transcription
        
        Args:
            transcription: Texte transcrit de la séance
            patient_info: Informations sur le patient
            
        Returns:
            Tuple[bool, str, Optional[str]]: (success, message, analysis)
        """
        try:
            logger.info("Génération de l'analyse IA de la séance")
            
            # Prompt spécialisé pour l'analyse de musicothérapie
            system_prompt = """Tu es un assistant spécialisé en musicothérapie. Analyse cette transcription de séance et génère une synthèse thérapeutique structurée.

La synthèse doit inclure :
1. **Observations générales** - Ambiance et déroulement de la séance
2. **Engagement du patient** - Niveau de participation et réceptivité
3. **Moments significatifs** - Réactions particulières, progrès observés
4. **Activités musicales** - Instruments utilisés, préférences exprimées
5. **Évolution émotionnelle** - Changements d'humeur ou d'expression
6. **Recommandations** - Suggestions pour les prochaines séances

Reste professionnel, bienveillant et utilise un vocabulaire approprié au domaine de la musicothérapie."""
            
            user_prompt = f"""Informations du patient :
- Prénom : {patient_info.get('prenom', 'Non renseigné')}
- Pathologie : {patient_info.get('pathologie', 'Non renseignée')}
- Objectifs thérapeutiques : {patient_info.get('objectifs_therapeutiques', 'Non renseignés')}

Transcription de la séance :
{transcription}

Génère une synthèse thérapeutique détaillée de cette séance de musicothérapie."""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            analysis = response.choices[0].message.content
            logger.info(f"Analyse IA générée: {len(analysis)} caractères")
            
            return True, "Analyse générée avec succès", analysis
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération d'analyse: {e}")
            return False, f"Erreur d'analyse IA: {str(e)}", None
    
    def process_session_recording(self, audio_file: FileStorage, seance_id: int) -> Tuple[bool, str]:
        """
        Traite complètement un enregistrement de séance
        
        Args:
            audio_file: Fichier audio de la séance
            seance_id: ID de la séance à mettre à jour
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Récupérer la séance
            seance = Seance.query.get(seance_id)
            if not seance:
                return False, "Séance non trouvée"
            
            # Transcription
            success, message, transcription = self.transcribe_audio(audio_file)
            if not success:
                return False, f"Échec de la transcription: {message}"
            
            # Informations du patient pour l'analyse
            patient_info = {
                'prenom': seance.patient.prenom,
                'pathologie': seance.patient.pathologie,
                'objectifs_therapeutiques': seance.patient.objectifs_therapeutiques
            }
            
            # Génération de l'analyse IA
            success, message, analysis = self.generate_session_analysis(transcription, patient_info)
            if not success:
                logger.warning(f"Analyse IA échouée: {message}")
                analysis = "Analyse automatique non disponible"
            
            # Mettre à jour la séance avec les résultats
            seance.transcription_audio = transcription
            seance.synthese_ia = analysis
            seance.fichier_audio = secure_filename(audio_file.filename)
            
            db.session.commit()
            
            logger.info(f"Traitement complet réussi pour la séance {seance_id}")
            return True, "Enregistrement traité avec succès"
            
        except Exception as e:
            logger.error(f"Erreur lors du traitement de l'enregistrement: {e}")
            db.session.rollback()
            return False, f"Erreur de traitement: {str(e)}"
    
    @staticmethod
    def get_audio_info(file: FileStorage) -> Dict[str, Any]:
        """
        Récupère les informations d'un fichier audio
        
        Args:
            file: Fichier audio
            
        Returns:
            Dict contenant les informations du fichier
        """
        info = {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': getattr(file, 'content_length', 0)
        }
        
        try:
            # Utiliser mutagen pour obtenir plus d'infos si possible
            from mutagen import File as MutagenFile
            
            with tempfile.NamedTemporaryFile(
                suffix=f".{file.filename.rsplit('.', 1)[1].lower()}"
            ) as temp_file:
                file.save(temp_file.name)
                file.seek(0)  # Reset pour une utilisation ultérieure
                
                audio_file = MutagenFile(temp_file.name)
                if audio_file:
                    info.update({
                        'duration': getattr(audio_file.info, 'length', 0),
                        'bitrate': getattr(audio_file.info, 'bitrate', 0),
                        'channels': getattr(audio_file.info, 'channels', 0)
                    })
        
        except Exception as e:
            logger.warning(f"Impossible de lire les métadonnées audio: {e}")
        
        return info
