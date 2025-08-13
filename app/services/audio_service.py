"""
Service de transcription audio et analyse IA pour Synchronie
Utilise OpenAI Whisper pour la transcription et GPT pour l'analyse
"""
import os
import tempfile
from typing import Optional, Tuple, Dict, Any
from werkzeug.datastructures import FileStorage
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
        
        # Initialisation robuste du client OpenAI avec gestion complète des problèmes de proxy
        self.client = None
        last_error = None
        
        # Stratégie 1: Initialisation standard
        try:
            import openai
            logger.info(f"Version OpenAI: {getattr(openai, '__version__', 'unknown')}")
            self.client = OpenAI(api_key=api_key)
            logger.info("✅ Client OpenAI initialisé avec succès (méthode standard)")
            return
        except TypeError as e:
            last_error = e
            logger.warning(f"⚠️ Erreur de type lors de l'initialisation standard: {e}")
        except Exception as e:
            last_error = e
            logger.warning(f"⚠️ Erreur inattendue lors de l'initialisation standard: {e}")
        
        # Stratégie 2: Client HTTP personnalisé sans proxy
        if 'proxies' in str(last_error) or 'unexpected keyword argument' in str(last_error):
            try:
                import httpx
                logger.info("🔄 Tentative avec client HTTP personnalisé (sans proxy)")
                
                # Créer un client HTTP explicitement sans configuration de proxy
                http_client = httpx.Client(
                    timeout=30.0,
                    follow_redirects=True
                )
                self.client = OpenAI(api_key=api_key, http_client=http_client)
                logger.info("✅ Client OpenAI initialisé avec client HTTP personnalisé")
                return
            except Exception as e2:
                last_error = e2
                logger.warning(f"⚠️ Échec avec client HTTP personnalisé: {e2}")
        
        # Stratégie 3: Variable d'environnement uniquement
        try:
            logger.info("🔄 Tentative avec variable d'environnement uniquement")
            os.environ['OPENAI_API_KEY'] = api_key
            self.client = OpenAI()
            logger.info("✅ Client OpenAI initialisé via variable d'environnement")
            return
        except Exception as e3:
            last_error = e3
            logger.warning(f"⚠️ Échec avec variable d'environnement: {e3}")
        
        # Stratégie 4: Client HTTP minimal
        try:
            import httpx
            logger.info("🔄 Tentative avec client HTTP minimal")
            
            # Client HTTP le plus basique possible
            http_client = httpx.Client(
                timeout=httpx.Timeout(30.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
            self.client = OpenAI(api_key=api_key, http_client=http_client)
            logger.info("✅ Client OpenAI initialisé avec client HTTP minimal")
            return
        except Exception as e4:
            last_error = e4
            logger.warning(f"⚠️ Échec avec client HTTP minimal: {e4}")
        
        # Si toutes les stratégies échouent
        logger.error("❌ Toutes les stratégies d'initialisation ont échoué")
        logger.error(f"❌ Dernière erreur: {last_error}")
        raise ValueError(f"Impossible d'initialiser le client OpenAI après toutes les tentatives. Dernière erreur: {last_error}")
    
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
        # Vérifier que le client OpenAI est initialisé
        if self.client is None:
            logger.error("Client OpenAI non initialisé")
            return False, "Service de transcription non disponible", None
            
        try:
            # Validation du fichier
            is_valid, error_msg = self.validate_audio_file(audio_file)
            if not is_valid:
                return False, error_msg, None
            
            logger.info(f"Début de la transcription pour: {audio_file.filename}")
            
            # Créer un fichier temporaire pour l'upload vers OpenAI
            filename = audio_file.filename or 'audio.mp3'
            with tempfile.NamedTemporaryFile(
                suffix=f".{filename.rsplit('.', 1)[1].lower()}", 
                delete=False
            ) as temp_file:
                
                # Sauvegarder le fichier temporairement
                audio_file.save(temp_file.name)
                temp_file_path = temp_file.name
            
            try:
                # Transcription avec Whisper - version simplifiée
                with open(temp_file_path, 'rb') as audio_data:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_data,
                        language="fr",  # Français
                        response_format="text"
                    )
                
                transcription_text = str(transcript) if transcript else ""
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
        # Vérifier que le client OpenAI est initialisé
        if self.client is None:
            logger.error("Client OpenAI non initialisé")
            return False, "Service d'analyse non disponible", None
            
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
            
            analysis = response.choices[0].message.content or ""
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
            if transcription:  # Vérifier que transcription n'est pas None
                success, message, analysis = self.generate_session_analysis(transcription, patient_info)
                if not success:
                    logger.warning(f"Analyse IA échouée: {message}")
                    analysis = "Analyse automatique non disponible"
            else:
                analysis = "Transcription non disponible pour l'analyse"
            
            # Mettre à jour la séance avec les résultats
            seance.transcription_audio = transcription
            seance.synthese_ia = analysis
            # Ne pas sauvegarder le fichier audio, juste la transcription
            
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
        info: Dict[str, Any] = {
            'filename': file.filename,
            'content_type': file.content_type,
            'size': getattr(file, 'content_length', 0)
        }
        
        try:
            # Vérifier que le nom de fichier existe
            if not file.filename:
                return info
                
            # Utiliser mutagen pour obtenir plus d'infos si possible
            try:
                from mutagen import File as MutagenFile  # type: ignore
            except ImportError:
                logger.warning("Mutagen non installé - informations audio limitées")
                return info
            
            with tempfile.NamedTemporaryFile(
                suffix=f".{file.filename.rsplit('.', 1)[1].lower()}"
            ) as temp_file:
                file.save(temp_file.name)
                file.seek(0)  # Reset pour une utilisation ultérieure
                
                audio_file = MutagenFile(temp_file.name)  # type: ignore
                if audio_file and hasattr(audio_file, 'info'):  # type: ignore
                    info.update({
                        'duration': getattr(audio_file.info, 'length', 0),  # type: ignore
                        'bitrate': getattr(audio_file.info, 'bitrate', 0),  # type: ignore
                        'channels': getattr(audio_file.info, 'channels', 0)  # type: ignore
                    })
        
        except Exception as e:
            logger.warning(f"Impossible de lire les métadonnées audio: {e}")
        
        return info
